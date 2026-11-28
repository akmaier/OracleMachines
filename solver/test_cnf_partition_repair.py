from collections import Counter
from copy import deepcopy
from itertools import product
from unittest import TestCase
from unittest.mock import patch
from experiments import cnf_partition_repair as e


def seed(source, values=None):
    names = sorted({abs(v) for c in source for v in c})
    return dict(format=e.previous.FORMAT, names=names,
                values=[False]*len(names) if values is None else values)


class PartitionRepairTests(TestCase):
    def test_empty_true(self):
        got=e.search([],seed([]),0)
        self.assertEqual(got['diagnostic']['reason'],'sat')
        self.assertTrue(e.previous.check([],got['witness'])['answer'])

    def test_empty_false(self):
        s=[[]];p=e.search(s,seed(s),0,record=True)['exclusion']
        self.assertTrue(e.check_exclusion(s,p)['global_unsat'])

    def test_zero_budget_unknown(self):
        got=e.search([[1]],seed([[1]]),1,node_limit=0,record=True)
        self.assertEqual(got['diagnostic']['reason'],'budget')
        self.assertIsNone(got['exclusion'])

    def test_radius_not_global_unsat(self):
        s=[[1],[2]];p=e.search(s,seed(s),1,record=True)['exclusion']
        self.assertEqual(e.check_exclusion(s,p),dict(no_model_within_radius=True,radius=1,global_unsat=False))
        self.assertIsNotNone(e.search(s,seed(s),2)['witness'])

    def test_signed_sparse_seed(self):
        s=[[-500],[7,500],[999,-999]];p=seed(s,[True,True,False])
        got=e.search(s,p,2)
        self.assertTrue(e.previous.check(s,got['witness'])['answer'])
        self.assertEqual(got['diagnostic']['distance'],1)

    def test_duplicates_tautologies(self):
        s=[[1,1],[-1,2],[-1,2],[8,-8]]
        got=e.search(s,seed(s),3)
        self.assertTrue(e.previous.check(s,got['witness'])['answer'])

    def test_all_seeds_small_balls(self):
        s=[[1,2],[-1,3],[-2,-3]]
        for initial in product((False,True),repeat=3):
            for radius in range(4):
                truth=any(sum(a!=b for a,b in zip(initial,values))<=radius
                          and all(any(values[abs(v)-1]==(v>0) for v in c) for c in s)
                          for values in product((False,True),repeat=3))
                got=e.search(s,seed(s,list(initial)),radius,record=True)
                self.assertEqual(got['witness'] is not None,truth)
                if not truth:self.assertTrue(e.check_exclusion(s,got['exclusion'])['no_model_within_radius'])

    def test_checker_without_search(self):
        s=[[1],[-1]];p=e.search(s,seed(s),1,record=True)['exclusion']
        with patch.object(e,'search',side_effect=AssertionError('discovery called')):
            self.assertTrue(e.check_exclusion(s,p)['global_unsat'])

    def test_missing_child(self):
        s=[[1,2],[-1],[-2]];p=e.search(s,seed(s),2,record=True)['exclusion']
        p['nodes'].pop(next(k for k in p['nodes'] if k!='0:0'))
        with self.assertRaises(ValueError):e.check_exclusion(s,p)

    def test_changed_source(self):
        s=[[1],[-1]];p=e.search(s,seed(s),1,record=True)['exclusion']
        with self.assertRaises(ValueError):e.check_exclusion([[1]],p)

    def test_packing_overlap(self):
        s=[[1],[2]];p=e.search(s,seed(s),1,record=True)['exclusion']
        p['nodes']['0:0']['packing']=[0,0]
        with self.assertRaises(ValueError):e.check_exclusion(s,p)

    def test_invalid_seed(self):
        s=[[1]]
        for p in (seed(s,[0]),seed(s,[]),dict(format=e.previous.FORMAT,names=[True],values=[False])):
            with self.assertRaises(ValueError):e.search(s,p,1)

    def test_invalid_budgets(self):
        for r in (-1,True,2):
            with self.assertRaises(ValueError):e.search([[1]],seed([[1]]),r)
        for b in (-1,True,1.5):
            with self.assertRaises(ValueError):e.search([[1]],seed([[1]]),1,node_limit=b)

    def test_invalid_raw_literals(self):
        for s in ([[True]],[[0]],[['1']]):
            with self.assertRaises(ValueError):e.proposal(s)

    def test_bad_masks(self):
        s=[[]];p=e.search(s,seed(s),0,record=True)['exclusion']
        for key in ('00:0','-1:0','1:0','٠:0','0:0:0'):
            q=deepcopy(p);q['nodes']={key:q['nodes']['0:0']}
            with self.assertRaises(ValueError):e.check_exclusion(s,q)

    def test_source_edit_invalidates_witness(self):
        s=[[1]];p=e.search(s,seed(s),1)['witness']
        self.assertTrue(e.previous.check(s+[[1,1]],p)['answer'])
        with self.assertRaises(ValueError):e.previous.check(s+[[-1]],p)

    def test_budget_cannot_be_exclusion(self):
        s=[[1,2],[-1],[-2]];r=e.search(s,seed(s),2,node_limit=1,record=True)
        self.assertEqual(r['diagnostic']['reason'],'budget')
        self.assertIsNone(r['exclusion'])

    def test_kept_contexts_are_recorded(self):
        s=[[1,2],[-1],[-2]]
        r=e.search(s,seed(s),2,record=True)
        self.assertTrue(e.check_exclusion(s,r['exclusion'])['global_unsat'])
        self.assertTrue(any(int(k.split(':')[1]) for k in r['exclusion']['nodes']))

    def test_missing_branch_order(self):
        s=[[1,2],[-1],[-2]];p=e.search(s,seed(s),2,record=True)['exclusion']
        p['nodes']['0:0']['order'].pop()
        with self.assertRaises(ValueError):e.check_exclusion(s,p)

    def test_duplicate_branch_order(self):
        s=[[1,2],[-1],[-2]];p=e.search(s,seed(s),2,record=True)['exclusion']
        p['nodes']['0:0']['order']=[1,1]
        with self.assertRaises(ValueError):e.check_exclusion(s,p)

    def test_child_keep_constraint_required(self):
        s=[[1,2],[-1],[-2]];p=e.search(s,seed(s),2,record=True)['exclusion']
        k=next(k for k in p['nodes'] if int(k.split(':')[1]))
        p['nodes'][k.split(':')[0]+':0']=p['nodes'].pop(k)
        with self.assertRaises(ValueError):e.check_exclusion(s,p)

    def test_flip_keep_overlap_rejected(self):
        s=[[]];p=e.search(s,seed(s),0,record=True)['exclusion']
        p['nodes']['1:1']=p['nodes']['0:0']
        with self.assertRaises(ValueError):e.check_exclusion(s,p)

    def test_boolean_order_rejected(self):
        s=[[1,2],[-1],[-2]];p=e.search(s,seed(s),2,record=True)['exclusion']
        p['nodes']['0:0']['order']=[True,2]
        with self.assertRaises(ValueError):e.check_exclusion(s,p)
