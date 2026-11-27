from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_probe_relations as k
from experiments.cnf_probe_relation_panel import panel,failure
from experiments.cnf_fresh_seed_panel import truth

ALIAS=failure(0)+[[1,-6,7],[1,6,-7]]


class ProbeRelationTests(unittest.TestCase):
    def checked(self,source,**options):
        p,d=k.discover(source,**options);got=k.check_certificate(source,p)
        if got['answer'] is not None:
            self.assertEqual(got['answer'],truth(source)['answer'])
            if got['answer']:self.assertTrue(k.native.holds(source,got['model']))
        return p,d

    def test_exhaustive_two_variable_formulas(self):
        clauses=[[s*(i+1) for i,s in enumerate(signs) if s] for signs in product((-1,0,1),repeat=2)]
        for bits in range(1<<len(clauses)):
            source=[c for i,c in enumerate(clauses) if bits>>i&1]
            for mode in k.MODES:self.checked(source,mode=mode,bag_limit=1)

    def test_random_wider_and_signed_models(self):
        rng=random.Random(2711271113)
        for _ in range(100):
            n=rng.randrange(2,8);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),rng.randrange(1,min(n,4)+1))] for _ in range(3*n)]
            self.checked(source,bag_limit=2)

    def test_alias_exposed_by_nonfolding_failed_assumption(self):
        p,_=self.checked(ALIAS,depth_limit=0)
        self.assertTrue(p['edges'][0]['probe_rounds']);tail=p['edges'][0]['tail']
        self.assertEqual(tail['relation']['kind'],'equivalence')
        self.assertEqual(p['status'],'sat')
        cnf,_=k.native.normalize(failure(0));steps,_,_=k.symbolic.preprocess(cnf,'fold',k.DEFAULTS,Counter())
        self.assertFalse(steps)

    def test_sparse_negative_alias_lifts(self):
        source=[[(1 if l>0 else -1)*(-1 if abs(l)%2 else 1)*(29*abs(l)+13) for l in c] for c in ALIAS]
        p,_=self.checked(source,depth_limit=0)
        self.assertTrue(any(e['tail'] for e in p['edges']))

    def test_probe_control_exactly_translates(self):
        for source in (ALIAS,[],[[]],[[1,2,3]],ALIAS+[[-6,2,3]]):
            p,_=k.discover(source,mode='probe',bag_limit=2);q,_=k.prior.discover(source,mode='indexed',bag_limit=2)
            p['format']=q['format'];p['mode']='indexed'
            for edge in p['edges']:self.assertIsNone(edge.pop('tail'))
            self.assertEqual(p,q)

    def test_removed_alias_direction_not_treated_as_equality(self):
        p,_=self.checked(ALIAS[:-1],depth_limit=0)
        self.assertIsNone(p['edges'][0]['tail'])
        original,_=k.discover(ALIAS,depth_limit=0)
        with self.assertRaises(ValueError):k.check_certificate(ALIAS[:-1],original)

    def test_corrupt_tail_and_progress_rejected(self):
        p,_=self.checked(ALIAS,depth_limit=0)
        for change in (
            lambda q:q.__setitem__('mode','probe'),
            lambda q:q['edges'][0].__setitem__('tail',{}),
            lambda q:q['edges'][0]['tail']['relation']['evidence'].__setitem__('representative',999),
            lambda q:q['edges'][0]['tail']['relation']['evidence']['forward'].clear(),
            lambda q:q['edges'][0].__setitem__('tail',dict(units=[],relation=None,after_units=[])),
            lambda q:q.__setitem__('model',[not x for x in q['model']]),
        ):
            altered=deepcopy(p);change(altered)
            with self.assertRaises(ValueError):k.check_certificate(ALIAS,altered)

    def test_last_exposed_gap_now_has_whole_root_authority(self):
        source=json.loads(Path('experiments/results/cnf-probe-buckets/remaining.json').read_text())['cases'][0]['source']
        before,_=k.discover(source,mode='probe');after,_=self.checked(source)
        self.assertEqual(before['status'],'unresolved');self.assertEqual(after['status'],'sat')
        self.assertTrue(any(e['tail'] for e in after['edges']))

    def test_cold_replay_has_no_recognition(self):
        p,_=self.checked(ALIAS)
        with patch.object(k.prior,'prepare_edge',side_effect=AssertionError('probes')),patch.object(k.relations,'prepare_edge',side_effect=AssertionError('relations')),patch.object(k.relations.equivalence,'discover',side_effect=AssertionError('scc')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket')):
            self.assertTrue(k.check_certificate(ALIAS,json.loads(json.dumps(p)))['answer'])

    def test_limits_and_unknown_remain_explicit(self):
        for mode in k.MODES:
            p,_=self.checked([[1,2,3]],mode=mode,bag_limit=1,depth_limit=0)
            self.assertEqual(p['status'],'unresolved')
        with self.assertRaises(ValueError):k.discover(ALIAS,mode='bad')
        with self.assertRaises(ValueError):k.discover(ALIAS,probe_limit=True)

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-probe-relations')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()))
        self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
