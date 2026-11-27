from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from unittest.mock import patch
import json,random,unittest
from experiments import cnf_closed_buckets as k
from experiments.cnf_closed_bucket_panel import panel,forced_guard
from experiments.cnf_fresh_seed_panel import truth


def transport_case():
    return forced_guard([[1,2,3],[-1,-2,3],[1,-2,-3],[-1,2,-3]],3)


class ClosedBucketTests(unittest.TestCase):
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
            for mode in ('root','closed'):
                p,_=self.checked(source,mode=mode,bag_limit=1);self.assertNotEqual(p['status'],'unresolved')

    def test_random_cnf_and_sparse_witnesses(self):
        rng=random.Random(2711270543)
        for _ in range(60):
            n=rng.randrange(3,8);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(4*n)]
            for mode in ('tree','closed'):self.checked(source,mode=mode,bag_limit=3)
            self.checked([[(1 if l>0 else -1)*(37*abs(l)+13) for l in c] for c in source],bag_limit=3)

    def test_shared_closed_node_keeps_opposite_edge_units(self):
        source=transport_case();c=Counter();memo,_=k.discover(source,c,bag_limit=2);tree,_=self.checked(source,mode='tree',bag_limit=2)
        self.assertTrue(k.check_certificate(source,memo)['answer']);self.assertLess(len(memo['nodes']),len(tree['nodes']));self.assertGreater(c['closed_memo_hits'],0)
        root=memo['nodes'][-1];low=memo['edges'][root['low']];high=memo['edges'][root['high']]
        self.assertEqual(low['target'],high['target']);self.assertNotEqual(low['units'],high['units']);self.assertEqual(low['residual'],high['residual'])
        bad=deepcopy(memo);bad['edges'][root['high']]['units']=deepcopy(low['units'])
        with self.assertRaises(ValueError):k.check_certificate(source,bad)

    def test_unknown_and_partial_closure_are_not_unsat(self):
        source=transport_case()
        for opts in (dict(bag_limit=1,depth_limit=0),dict(bag_limit=1,depth_limit=1,index_work_limit=1)):
            p,_=self.checked(source,**opts);self.assertEqual(p['status'],'unresolved')
            q=deepcopy(p);q['status']='unsat';q['nodes'][-1]['status']='unsat'
            with self.assertRaises(ValueError):k.check_certificate(source,q)
        for depth in (-1,9,True):
            with self.assertRaises(ValueError):k.discover(source,depth_limit=depth)

    def test_graph_depth_and_model_corruption(self):
        source=transport_case();p,_=self.checked(source,bag_limit=2)
        changes=[lambda q:q['edges'][0].__setitem__('target',len(q['nodes'])),lambda q:q['edges'][0].__setitem__('depth',8),
                 lambda q:q['nodes'][-1].__setitem__('low',q['root']),lambda q:q.__setitem__('model',[False]*5),
                 lambda q:q['edges'][0]['cnf'].append([99]),lambda q:q['nodes'][0]['bucket'].__setitem__('status','unsat'),
                 lambda q:q.__setitem__('mode','root'),lambda q:q.__setitem__('root',0)]
        for change in changes:
            q=deepcopy(p);change(q)
            with self.assertRaises(ValueError):k.check_certificate(source,q)

    def test_root_fold_and_sparse_assignment_transport(self):
        source=[[101,203],[-101,203],[-203,307]];p,_=self.checked(source)
        self.assertTrue(p['prefix']);self.assertTrue(k.check_certificate(source,p)['model'][203]);self.assertTrue(k.check_certificate(source,p)['model'][307])
        self.checked(source+[[-307]])
        with self.assertRaises(ValueError):k.check_certificate(source[:-1],p)

    def test_cold_replay_without_search_or_preprocessing(self):
        source=transport_case();p,_=self.checked(source,bag_limit=2);p=json.loads(json.dumps(p))
        with patch.object(k.symbolic,'preprocess',side_effect=AssertionError('preprocess')),patch.object(k.bucket,'discover',side_effect=AssertionError('search')),patch.object(k.bucket,'project',side_effect=AssertionError('projection')):
            self.assertTrue(k.check_certificate(source,p)['answer'])

    def test_frozen_panel(self):
        rows,desc=panel();out=Path('experiments/results/cnf-closed-buckets')
        self.assertEqual(rows,json.loads((out/'heldout.json').read_text()));self.assertEqual(desc,json.loads((out/'heldout-descriptions.json').read_text()))


if __name__=='__main__':unittest.main()
