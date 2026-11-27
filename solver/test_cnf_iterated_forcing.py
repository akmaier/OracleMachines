from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_iterated_forcing as k
from experiments.cnf_iterated_forcing_panel import cascade,panel
from experiments.cnf_fresh_seed_panel import truth


class IteratedForcingTests(unittest.TestCase):
    def checked(self,source,**options):
        proof,diag=k.discover(source,**options);r=k.check_certificate(source,proof)
        if r['answer'] is not None:
            self.assertEqual(r['answer'],truth(source)['answer'])
            if r['answer']:self.assertTrue(k.native.holds(source,r['model']))
        return proof,diag

    def test_exhaustive_two_variable_cnf(self):
        clauses=[[s*(i+1) for i,s in enumerate(signs) if s] for signs in product((-1,0,1),repeat=2)]
        for bits in range(1<<len(clauses)):
            for mode in k.MODES:
                p,_=self.checked([c for i,c in enumerate(clauses) if bits>>i&1],mode=mode,bag_limit=1)
                self.assertNotEqual(p['status'],'unresolved')

    def test_seeded_mixtures_and_signs(self):
        rng=random.Random(2711270904)
        for _ in range(70):
            n=rng.randrange(3,8);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),rng.choice((2,3)))] for _ in range(4*n)]
            for mode in k.MODES:self.checked(source,mode=mode,bag_limit=2)

    def test_cascade_needs_new_rounds(self):
        source=cascade(5)+[[-13,-10]]
        one,_=self.checked(source,mode='once',depth_limit=0,bag_limit=1);many,_=self.checked(source,depth_limit=0,bag_limit=1)
        self.assertEqual(one['status'],'unresolved');self.assertEqual(many['status'],'unsat');self.assertEqual(len(many['edges'][0]['rounds']),4)

    def test_deleted_link_remains_satisfiable(self):
        source=cascade(4);source.pop(4);source.append([-10,-7])
        self.assertTrue(truth(source)['answer'])
        self.checked(source,bag_limit=2)

    def test_once_exactly_matches_previous_path_policy(self):
        for source in (cascade(4),cascade(4)+[[-10,-7]],[[1,2,3],[-1,2],[-2,3]]):
            got,_=k.discover(source,mode='once',bag_limit=2);expected,_=k.prior.discover(source,mode='paths',bag_limit=2)
            got['format']=expected['format'];got['mode']='paths';del got['limits']['round_limit']
            for e in got['edges']:
                rounds=e.pop('rounds');self.assertLessEqual(len(rounds),1)
                e.update(forcing=rounds[0]['forcing'] if rounds else None,forced_units=rounds[0]['units'] if rounds else [])
            self.assertEqual(got,expected)

    def test_round_caps_remain_partial(self):
        source=cascade(5)+[[-13,-10]]
        for limit in (1,2,3):
            p,_=self.checked(source,depth_limit=0,bag_limit=1,round_limit=limit);self.assertEqual(p['status'],'unresolved')
            self.assertEqual(len(p['edges'][0]['rounds']),limit)
        self.assertEqual(self.checked(source,depth_limit=0,bag_limit=1,round_limit=4)[0]['status'],'unsat')
        for limit in (0,-1,True,513):
            with self.assertRaises(ValueError):k.discover(source,round_limit=limit)

    def test_cumulative_traversal_cap(self):
        for cap in (1,5,20,80,200):
            p,d=self.checked(cascade(4),bag_limit=1,depth_limit=0,work_limit=cap)
            self.assertLessEqual(d['edges'][0]['diagnostic']['spent'],cap)
            self.assertLessEqual(sum(len(path['path']) for r in p['edges'][0]['rounds'] for path in r['forcing']['paths']),cap)

    def test_nonprogress_round_cannot_repeat(self):
        cnf,_=k.native.normalize(cascade(3));ev,_=k.prior.discover_forcing(cnf,'paths',k.DEFAULTS,Counter())
        record=dict(forcing=ev,units=[])
        # With no equivalence/unit preparation this certificate is valid once,
        # but the next round must not repeat it on the unchanged variable set.
        k.replay_edge(cnf,[],None,[],[record],'closure',k.DEFAULTS,Counter())
        with self.assertRaises(ValueError):k.replay_edge(cnf,[],None,[],[record,record],'closure',k.DEFAULTS,Counter())

    def test_round_transport_corruptions(self):
        source=cascade(4)+[[-10,-7]];p,_=self.checked(source,bag_limit=1,depth_limit=0)
        changes=[lambda q:q['edges'][0]['rounds'].reverse(),lambda q:q['edges'][0]['rounds'][1]['forcing']['paths'][0]['path'][0].__setitem__(1,999),lambda q:q.__setitem__('mode','once'),lambda q:q['edges'][0]['rounds'][0].__setitem__('forcing',None),lambda q:q['edges'][0]['rounds'][0]['units'][0].__setitem__('literal',999)]
        for change in changes:
            q=deepcopy(p);change(q)
            with self.assertRaises(ValueError):k.check_certificate(source,q)

    def test_sparse_signed_sat_lifting(self):
        source=cascade(4)+[[1,-4,13],[-7,14,15]]
        mapped=[[(1 if l>0 else -1)*(-1 if abs(l)%2 else 1)*(29*abs(l)+23) for l in c] for c in source]
        p,_=self.checked(mapped);self.assertEqual(p['status'],'sat');self.assertGreaterEqual(len(p['edges'][-1]['rounds']),2)

    def test_cold_replay_without_recognition(self):
        source=cascade(4)+[[-10,-7]];p,_=self.checked(source,depth_limit=0,bag_limit=1)
        with patch.object(k.prior,'discover_forcing',side_effect=AssertionError('search')),patch.object(k.symbolic,'preprocess',side_effect=AssertionError('units')),patch.object(k.prior.prior.equivalence,'discover',side_effect=AssertionError('SCC')),patch.object(k.native,'two_cnf',side_effect=AssertionError('binary')),patch.object(k.bucket,'discover',side_effect=AssertionError('bucket')):
            self.assertFalse(k.check_certificate(source,json.loads(json.dumps(p)))['answer'])

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-iterated-forcing');self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
