from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_forcing_buckets as k
from experiments.cnf_forcing_bucket_panel import panel,funnel
from experiments.cnf_fresh_seed_panel import truth


class ForcingBucketTests(unittest.TestCase):
    def checked(self,source,**options):
        p,d=k.discover(source,**options);r=k.check_certificate(source,p)
        if r['answer'] is not None:
            self.assertEqual(r['answer'],truth(source)['answer'])
            if r['answer']:self.assertTrue(k.native.holds(source,r['model']))
        return p,d

    def test_exhaustive_two_variable_formulas(self):
        clauses=[[s*(i+1) for i,s in enumerate(signs) if s] for signs in product((-1,0,1),repeat=2)]
        for bits in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if bits>>i&1]
            for mode in k.MODES:
                p,_=self.checked(source,mode=mode,bag_limit=1);self.assertNotEqual(p['status'],'unresolved')

    def test_seeded_mixed_cnf(self):
        rng=random.Random(2711270748)
        for _ in range(65):
            n=rng.randrange(3,8);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),rng.choice((2,3)))] for _ in range(4*n)]
            for mode in k.MODES:self.checked(source,mode=mode,bag_limit=2)

    def test_one_way_path_forces_without_converse(self):
        cnf,_=k.native.normalize([[-1,2],[-2,3],[-3,-1]])
        ev,_=k.discover_forcing(cnf,'paths',k.DEFAULTS,Counter());forced=k.check_forcing(cnf,ev,'paths',k.DEFAULTS,Counter())
        self.assertEqual(forced,(-1,))
        models=[vals for vals in product((False,True),repeat=3) if k.native.holds(cnf,dict(enumerate(vals,1)))]
        self.assertTrue(models);self.assertTrue(all(not v[0] for v in models))

    def test_shared_edges_are_checked_once(self):
        cnf,_=k.native.normalize(funnel(12));plain,_=k.discover_forcing(cnf,'paths',k.DEFAULTS,Counter());shared,_=k.discover_forcing(cnf,'shared',k.DEFAULTS,Counter())
        a=Counter();b=Counter();self.assertEqual(k.check_forcing(cnf,plain,'paths',k.DEFAULTS,a),k.check_forcing(cnf,shared,'shared',k.DEFAULTS,b))
        self.assertLess(b['forcing_checked_support_edges'],a['forcing_checked_support_edges']);self.assertEqual(a['forcing_path_walk_edges'],b['forcing_path_walk_edges'])
        self.assertEqual(len(shared['edges']),11);self.assertEqual(a['forcing_checked_support_edges'],20)

    def test_deleted_middle_edge_invalidates_paths(self):
        source=funnel(12);cnf,_=k.native.normalize(source);ev,_=k.discover_forcing(cnf,'shared',k.DEFAULTS,Counter())
        changed,_=k.native.normalize([c for c in source if c!=[-14,15]])
        self.assertIsNone(k.discover_forcing(changed,'shared',k.DEFAULTS,Counter())[0])
        with self.assertRaises(ValueError):k.check_forcing(changed,ev,'shared',k.DEFAULTS,Counter())

    def test_shared_pool_corruption(self):
        cnf,_=k.native.normalize(funnel(12));ev,_=k.discover_forcing(cnf,'shared',k.DEFAULTS,Counter())
        changes=[lambda p:p['edges'].append(p['edges'][0][:]),lambda p:p['paths'][0]['path'].__setitem__(0,True),lambda p:p['paths'][0]['path'].pop(),lambda p:p['edges'][0].__setitem__(2,999),lambda p:p['paths'][0].__setitem__('literal',True)]
        for change in changes:
            bad=deepcopy(ev);change(bad)
            with self.assertRaises(ValueError):k.check_forcing(cnf,bad,'shared',k.DEFAULTS,Counter())
        bad=deepcopy(ev);u,v,cid=bad['edges'][0];bad['edges'].append([-v,-u,cid])
        with self.assertRaises(ValueError):k.check_forcing(cnf,bad,'shared',k.DEFAULTS,Counter())

    def test_separate_path_corruption(self):
        cnf,_=k.native.normalize(funnel(12));ev,_=k.discover_forcing(cnf,'paths',k.DEFAULTS,Counter())
        for change in (lambda p:p['paths'][0]['path'][0].__setitem__(1,999),lambda p:p['paths'][0]['path'].reverse(),lambda p:p['paths'].append(deepcopy(p['paths'][0]))):
            bad=deepcopy(ev);change(bad)
            with self.assertRaises(ValueError):k.check_forcing(cnf,bad,'paths',k.DEFAULTS,Counter())
        with self.assertRaises(ValueError):k.check_forcing(cnf,ev,'relations',k.DEFAULTS,Counter())

    def test_forcing_and_wide_clause_produce_conflict(self):
        source=funnel(9,True)+[[-1,-2,-3]]
        p,_=self.checked(source,mode='relations',depth_limit=0,bag_limit=1);self.assertEqual(p['status'],'unresolved')
        for mode in ('paths','shared'):
            p,_=self.checked(source,mode=mode,depth_limit=0,bag_limit=1);self.assertEqual(p['status'],'unsat');self.assertTrue(p['edges'][0]['forced_units'])
            q=deepcopy(p);q['mode']='relations'
            with self.assertRaises(ValueError):k.check_certificate(source,q)

    def test_partial_search_quota_is_not_refutation(self):
        cnf,_=k.native.normalize(funnel(12))
        for cap in (1,5,10,25):
            limits={**k.DEFAULTS,'work_limit':cap};ev,d=k.discover_forcing(cnf,'shared',limits,Counter());self.assertLessEqual(d['spent'],cap);k.check_forcing(cnf,ev,'shared',limits,Counter())
        source=funnel(9)+[[1,2,3]];p,_=self.checked(source,depth_limit=0,bag_limit=1,work_limit=1);self.assertEqual(p['status'],'unresolved')
        for cap in (0,-1,True):
            with self.assertRaises(ValueError):k.discover(source,work_limit=cap)

    def test_sparse_signed_model_transport(self):
        source=funnel(9,True)+[[1,4,5],[-1,6,7],[-4,-5,-6]]
        for mode in ('paths','shared'):
            p,_=self.checked(source,mode=mode);self.assertTrue(any(e['forcing'] for e in p['edges']))
            mapped=[[(1 if l>0 else -1)*(-1 if abs(l)%2 else 1)*(31*abs(l)+17) for l in c] for c in source];self.checked(mapped,mode=mode)

    def test_cold_replay_without_forcing_search(self):
        source=funnel(9,True)+[[-1,-2,-3]];p,_=self.checked(source,bag_limit=1,depth_limit=0)
        with patch.object(k,'discover_forcing',side_effect=AssertionError('forcing')),patch.object(k.symbolic,'preprocess',side_effect=AssertionError('units')),patch.object(k.prior.equivalence,'discover',side_effect=AssertionError('SCC')),patch.object(k.native,'two_cnf',side_effect=AssertionError('binary')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket')),patch.object(k.bucket,'project',side_effect=AssertionError('projection')):
            self.assertFalse(k.check_certificate(source,json.loads(json.dumps(p)))['answer'])

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-forcing-buckets')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
