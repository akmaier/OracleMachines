from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_probe_buckets as k
from experiments.cnf_probe_bucket_panel import panel
from experiments.cnf_fresh_seed_panel import truth

WIDE=[[-1,2],[-1,3],[-2,-3,4],[-2,-3,5],[-4,-5]]


class ProbeBucketTests(unittest.TestCase):
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
            for mode in k.MODES:self.checked(source,mode=mode,bag_limit=1)

    def test_scan_indexed_probe_agreement_and_soundness(self):
        rng=random.Random(2711271006)
        for _ in range(90):
            n=rng.randrange(2,8);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),rng.randrange(1,min(n,4)+1))] for _ in range(3*n)]
            cnf,_=k.native.normalize(source);idx=k.prepare_index(cnf,Counter())
            for v in sorted({abs(l) for c in cnf for l in c}):
                for l in (v,-v):
                    a=k.scan_probe(cnf,l,Counter());b=k.indexed_probe(cnf,l,idx,Counter());self.assertEqual(a is None,b is None)
                    for proof in (a,b):
                        if proof is not None:self.assertEqual(k.check_probe(cnf,proof,Counter()),-l);self.assertFalse(truth(list(cnf)+[(l,)])['answer'])

    def test_wide_consequence_missed_by_binary_graph(self):
        cnf,_=k.native.normalize(WIDE);ev,_=k.prior.prior.discover_forcing(cnf,'paths',k.DEFAULTS,Counter());self.assertIsNone(ev)
        for mode in ('scan','indexed'):
            p,_=self.checked(WIDE,mode=mode,depth_limit=0);self.assertTrue(p['edges'][0]['probe_rounds'])
            self.assertIn(1,[ev['assumption'] for ev in p['edges'][0]['probe_rounds'][0]['failures']])

    def test_shared_index_is_immutable_between_probes(self):
        cnf,_=k.native.normalize(WIDE);cc=Counter();idx=k.prepare_index(cnf,cc);before=deepcopy(idx)
        for _ in range(3):
            for l in (1,-1,2,-2):k.indexed_probe(cnf,l,idx,cc)
        self.assertEqual(idx,before);self.assertEqual(cc['probe_index_builds'],1)

    def test_deleted_clause_invalidates_certificate(self):
        cnf,_=k.native.normalize(WIDE);p=k.scan_probe(cnf,1,Counter());self.assertIsNotNone(p)
        altered,_=k.native.normalize(WIDE[:-1]);self.assertIsNone(k.scan_probe(altered,1,Counter()))
        with self.assertRaises(ValueError):k.check_probe(altered,p,Counter())

    def test_corrupted_probe_rejected(self):
        cnf,_=k.native.normalize(WIDE);p=k.scan_probe(cnf,1,Counter())
        changes=[lambda q:q.__setitem__('assumption',True),lambda q:q.__setitem__('conflict',999),lambda q:q['trace'].reverse(),lambda q:q['trace'][0].__setitem__(0,-2),lambda q:q['trace'].append(q['trace'][0]),lambda q:q.__setitem__('conflict',True)]
        for change in changes:
            q=deepcopy(p);change(q)
            with self.assertRaises(ValueError):k.check_probe(cnf,q,Counter())

    def test_binary_control_matches_old_closure(self):
        for source in (WIDE,WIDE+[[-2,5],[1,2,3]],[[1,2],[-1,2],[-2,3]]):
            p,_=k.discover(source,mode='binary',bag_limit=2);q,_=k.prior.discover(source,bag_limit=2)
            p['format']=q['format'];p['mode']='closure'
            for key in ('probe_limit','probe_round_limit'):del p['limits'][key]
            for e in p['edges']:self.assertEqual(e.pop('probe_rounds'),[])
            self.assertEqual(p,q)

    def test_caps_and_nonfailed_probes_remain_unknown(self):
        for cap in (1,3,8):
            p,d=self.checked(WIDE,probe_limit=cap,probe_round_limit=1,depth_limit=0,bag_limit=1)
            self.assertLessEqual(d['edges'][0]['diagnostic']['spent'],cap)
        for key in ('probe_limit','probe_round_limit'):
            for cap in (0,-1,True,513):
                with self.assertRaises(ValueError):k.discover(WIDE,**{key:cap})
        p,_=self.checked([[1,2,3]],bag_limit=1,depth_limit=0);self.assertEqual(p['status'],'unresolved')

    def test_probe_round_corruption(self):
        p,_=self.checked(WIDE,depth_limit=0);q=deepcopy(p);q['mode']='binary'
        with self.assertRaises(ValueError):k.check_certificate(WIDE,q)
        q=deepcopy(p);q['edges'][0]['probe_rounds'][0]['failures'].append(deepcopy(q['edges'][0]['probe_rounds'][0]['failures'][0]))
        with self.assertRaises(ValueError):k.check_certificate(WIDE,q)

    def test_sparse_signed_sat_lift(self):
        source=[[(1 if l>0 else -1)*(-1 if abs(l)%2 else 1)*(31*abs(l)+29) for l in c] for c in WIDE]
        for mode in ('scan','indexed'):
            p,_=self.checked(source,mode=mode);self.assertEqual(p['status'],'sat')

    def test_cold_replay_disables_search_and_index(self):
        p,_=self.checked(WIDE)
        with patch.object(k,'scan_probe',side_effect=AssertionError('scan')),patch.object(k,'indexed_probe',side_effect=AssertionError('index')),patch.object(k,'prepare_index',side_effect=AssertionError('build')),patch.object(k.symbolic,'preprocess',side_effect=AssertionError('units')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket')):
            self.assertTrue(k.check_certificate(WIDE,json.loads(json.dumps(p)))['answer'])

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-probe-buckets');self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
