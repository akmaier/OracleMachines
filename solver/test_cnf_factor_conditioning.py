from collections import Counter
from copy import deepcopy
from itertools import product
from unittest.mock import patch
import json,random,unittest
from pathlib import Path
from experiments import cnf_factor_conditioning as f


def prefix(source,bag=3,work=65536):
    p,_=f.bucket.discover(source,bag_limit=bag,work_limit=1)
    p.update(status='unresolved',model=None);p['limits']['work_limit']=work
    return p


def truth(source):
    names=sorted({abs(v) for c in source for v in c})
    return any(f.native.holds(source,dict(zip(names,values))) for values in product((False,True),repeat=len(names)))


class FactorConditioningTests(unittest.TestCase):
    def test_exhaustive_two_variable_cnfs(self):
        clauses=[[s*v for v,s in enumerate(signs,1) if s] for signs in product((-1,0,1),repeat=2)]
        for bits in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if bits>>i&1];p=prefix(source,2)
            for depth in (0,1,2):
                cert,_=f.discover(source,p,cut_limit=depth);got=f.check(source,p,cert)
                self.assertEqual(got['answer'],truth(source))
                if got['answer']:self.assertTrue(f.native.holds(source,got['model']))

    def test_seeded_edits_and_mixtures(self):
        rng=random.Random(2711271900)
        for i in range(80):
            source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,8),3)] for _ in range(24)]
            if i%3==0:source.extend([[20],[-20,21]])
            if i%5==0:source.append([-v for v in source[0]])
            p=prefix(source,3,32768);cert,_=f.discover(source,p,cut_limit=4);got=f.check(source,p,cert)
            if got['answer'] is not None:self.assertEqual(got['answer'],truth(source))
            if got['answer']:self.assertTrue(f.native.holds(source,got['model']))

    def test_unsat_requires_all_branches(self):
        source=[[a,b] for a in (-1,1) for b in (-2,2)];p=prefix(source,2)
        cert,_=f.discover(source,p,cut_limit=2);self.assertEqual(cert['status'],'unsat')
        cert['branches'][0]['terminal']=None
        with self.assertRaises(ValueError):f.check(source,p,cert)
        cert['status']='unresolved';self.assertIsNone(f.check(source,p,cert)['answer'])

    def test_sat_can_coexist_with_unresolved_branches(self):
        source=[[1,2,3]];p=prefix(source)
        cert,_=f.discover(source,p,cut_limit=1);cert['branches'][1]['terminal']=None
        self.assertTrue(f.check(source,p,cert)['answer'])

    def test_partition_missing_duplicate_and_changed_value(self):
        source=[[1,2],[-1,3]];p=prefix(source);cert,_=f.discover(source,p,cut_limit=2)
        for change in (lambda c:c['branches'].pop(),lambda c:c['branches'].__setitem__(1,c['branches'][0]),lambda c:c['branches'][0]['values'].__setitem__(0,0)):
            bad=deepcopy(cert);change(bad)
            with self.assertRaises(ValueError):f.check(source,p,bad)

    def test_changed_cutset_and_cover(self):
        source=[[1,2],[-1,3]];p=prefix(source);cert,_=f.discover(source,p,cut_limit=2)
        for change in (lambda c:c['cutset'].__setitem__(0,99),lambda c:c['cutset'].__setitem__(1,c['cutset'][0]),lambda c:c['entries'].pop(),lambda c:c['entries'][0]['certificate']['clauses'].clear()):
            bad=deepcopy(cert);change(bad)
            with self.assertRaises(ValueError):f.check(source,p,bad)

    def test_shared_work_allowance_not_reset(self):
        source=[[1,2,3],[-1,-2,-3]];p=prefix(source,3,32)
        cert,diag=f.discover(source,p,cut_limit=1);self.assertLessEqual(diag['reserved_work'],32)
        bad=deepcopy(cert);bad['branches'][1]['terminal']['limits']['work_limit']=32
        with self.assertRaises(ValueError):f.check(source,p,bad)

    def test_exhausted_budget_is_not_refutation(self):
        source=[[1,2,3],[-1,-2,-3]];p=prefix(source,3,1)
        cert,diag=f.discover(source,p,cut_limit=0);self.assertEqual(cert['status'],'unresolved');self.assertLessEqual(diag['reserved_work'],1)
        cert['status']='unsat'
        with self.assertRaises(ValueError):f.check(source,p,cert)

    def test_wide_conditional_leaf_is_not_materialized(self):
        source=[[1,2,3]];p=prefix(source,3);cert,_=f.discover(source,p,cut_limit=0)
        p['limits']['bag_limit']=2
        with self.assertRaises(ValueError):f.check(source,p,cert)

    def test_unavailable_cover_is_explicit(self):
        source=[[1,2,3]];p=prefix(source,3);cert,_=f.discover(source,p,clause_width=2,clause_budget=0)
        self.assertEqual(cert['status'],'unresolved');self.assertEqual(cert['branches'],[]);f.check(source,p,cert)
        cert['status']='unsat'
        with self.assertRaises(ValueError):f.check(source,p,cert)

    def test_cold_checker_without_discovery_or_ranking(self):
        source=[[5,12],[-5,99]];p=prefix(source);cert,_=f.discover(source,p)
        with patch.object(f,'cutset',side_effect=AssertionError('ranking')),patch.object(f.covers,'discover',side_effect=AssertionError('cover')),patch.object(f.bucket,'discover',side_effect=AssertionError('bucket')):
            got=f.check(source,p,json.loads(json.dumps(cert)));self.assertTrue(got['answer']);self.assertTrue(f.native.holds(source,got['model']))

    def test_reuses_nonempty_prefix_and_restores_source(self):
        source=[[1],[2,3,4],[-2,3,5],[-3,4,5],[-4,-5,2]]
        p,_=f.bucket.discover(source,bag_limit=3);self.assertTrue(p['steps']);self.assertEqual(p['status'],'unresolved')
        cert,_=f.discover(source,p);got=f.check(source,p,cert);self.assertEqual(got['answer'],truth(source));self.assertTrue(f.native.holds(source,got['model']))

    def test_changed_source_witness_or_projection(self):
        source=[[1,2],[-1,3]];p=prefix(source);cert,_=f.discover(source,p,cut_limit=0)
        for change in (lambda c:c['model'].__setitem__(0,not c['model'][0]),lambda c:c['branches'][0]['terminal']['steps'][0].__setitem__('bits',0)):
            bad=deepcopy(cert);change(bad)
            with self.assertRaises(ValueError):f.check(source,p,bad)
        with self.assertRaises(ValueError):f.check(source+[[-2]],p,cert)

    def test_invalid_policy(self):
        source=[[1,2]];p=prefix(source)
        for opts in (dict(cut_limit=5),dict(cut_limit=True),dict(clause_width=-1),dict(clause_budget=-1)):
            with self.assertRaises(ValueError):f.discover(source,p,**opts)

    def root_fixture(self):
        root=Path(__file__).resolve().parents[1]
        rows=json.loads((root/'experiments/results/cnf-selective-width-buckets/remaining.json').read_text())['cases']
        case=rows[0];context=json.loads((root/case['proof']['path']).read_text());target=case['unresolved_leaves'][0]['node']
        source,prefix,_=f.frontier(case['source'],context,target);cert,_=f.discover(source,prefix)
        return case,context,target,source,prefix,cert

    def test_original_root_transport_without_discovery(self):
        case,context,target,source,prefix,cert=self.root_fixture();got=f.check(source,prefix,cert)
        with patch.object(f,'discover',side_effect=AssertionError('discovery')),patch.object(f.previous,'discover',side_effect=AssertionError('old discovery')):
            result=f.lift_root(case['source'],context,target,source,prefix,got)
        self.assertTrue(result['answer']);self.assertTrue(f.native.holds(case['source'],result['model']))

    def test_root_binding_tampering(self):
        case,context,target,source,prefix,cert=self.root_fixture();got=f.check(source,prefix,cert)
        bad=deepcopy(prefix);bad['limits']['work_limit']+=1
        with self.assertRaises(ValueError):f.lift_root(case['source'],context,target,source,bad,got)
        with self.assertRaises(ValueError):f.lift_root(case['source']+[[]],context,target,source,prefix,got)
        with self.assertRaises(ValueError):f.frontier(case['source'],context,True)


if __name__=='__main__':unittest.main()
