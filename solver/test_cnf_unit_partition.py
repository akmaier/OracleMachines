from collections import Counter
from copy import deepcopy
from itertools import product
from unittest import TestCase
from unittest.mock import patch
from experiments import cnf_unit_partition as e


def seed(source, values=None):
    names=sorted({abs(v) for c in source for v in c})
    return dict(format=e.prior.previous.FORMAT,names=names,values=[False]*len(names) if values is None else values)


def unsat_square():return [[1,2],[1,-2],[-1,2],[-1,-2]]


class UnitPartitionTests(TestCase):
    def test_empty_true(self):
        self.assertTrue(e.prior.previous.check([],e.discover([])['witness'])['answer'])

    def test_empty_false(self):
        self.assertFalse(e.check_exclusion([[]],e.discover([[]])['exclusion'])['answer'])

    def test_zero_budget_unknown(self):
        r=e.discover([[1]],node_limit=0)
        self.assertEqual(r['diagnostic']['reason'],'budget');self.assertIsNone(r['witness']);self.assertIsNone(r['exclusion'])

    def test_forced_keep_and_flip(self):
        source=[[1],[-1,2],[-2]];counts=Counter();r=e.search(source,seed(source,[True,False]),counts)
        self.assertGreater(counts['unit_forced_keeps'],0);self.assertGreater(counts['unit_forced_flips'],0)
        self.assertFalse(e.check_exclusion(source,r['exclusion'])['answer'])

    def test_all_small_seeds(self):
        for source in (unsat_square(),[[1,2],[-1,3],[-2,-3]],[[1],[3,-3]]):
            names=seed(source)['names'];truth=any(all(any(dict(zip(names,vs))[abs(v)]==(v>0) for v in c) for c in source) for vs in product((False,True),repeat=len(names)))
            for initial in product((False,True),repeat=len(names)):
                r=e.search(source,seed(source,list(initial)))
                self.assertEqual(r['witness'] is not None,truth)
                if not truth:self.assertFalse(e.check_exclusion(source,r['exclusion'])['answer'])

    def test_sparse_signed_duplicates_tautologies(self):
        source=[[-70,9],[70,100],[-9,-100],[-70,9],[800,-800]]
        r=e.discover(source);self.assertTrue(e.prior.previous.check(source,r['witness'])['answer'])

    def test_branch_undo_restores_state(self):
        source=unsat_square();counts=Counter();r=e.search(source,seed(source),counts)
        self.assertGreater(counts['unit_undo_occurrences'],0);self.assertGreater(len(r['exclusion']['nodes']),1)
        self.assertFalse(e.check_exclusion(source,r['exclusion'])['answer'])

    def test_no_recursion_depth_limit(self):
        source=[[1]]+[[-i,i+1] for i in range(1,1500)]+[[-1500]];r=e.discover(source)
        self.assertEqual(r['diagnostic']['expanded'],1)
        self.assertFalse(e.check_exclusion(source,r['exclusion'])['answer'])
        self.assertGreaterEqual(len(r['exclusion']['nodes']['0:0']['units']),1499)

    def test_checker_without_discovery(self):
        source=unsat_square();p=e.discover(source)['exclusion']
        with patch.object(e,'search',side_effect=AssertionError),patch.object(e,'discover',side_effect=AssertionError):
            self.assertFalse(e.check_exclusion(source,p)['answer'])

    def test_missing_child(self):
        source=unsat_square();p=e.discover(source)['exclusion'];p['nodes'].pop(next(k for k in p['nodes'] if k!='0:0'))
        with self.assertRaises(ValueError):e.check_exclusion(source,p)

    def test_missing_unit(self):
        source=[[1],[-1,2],[-2]];p=e.discover(source)['exclusion'];p['nodes']['0:0']['units']=[]
        with self.assertRaises(ValueError):e.check_exclusion(source,p)

    def test_nonunit_premise(self):
        source=unsat_square();p=e.discover(source)['exclusion'];p['nodes']['0:0']['units']=[0]
        with self.assertRaises(ValueError):e.check_exclusion(source,p)

    def test_changed_source(self):
        source=[[1],[-1]];p=e.discover(source)['exclusion']
        with self.assertRaises(ValueError):e.check_exclusion([[1]],p)

    def test_incomplete_branch_order(self):
        source=unsat_square();p=e.discover(source)['exclusion'];p['nodes']['0:0']['order'].pop()
        with self.assertRaises(ValueError):e.check_exclusion(source,p)

    def test_invalid_masks(self):
        p=e.discover([[]])['exclusion']
        for key in ('00:0','1:1','-1:0','1:0','٠:0','0:0:0'):
            q=deepcopy(p);q['nodes']={key:q['nodes']['0:0']}
            with self.assertRaises(ValueError):e.check_exclusion([[]],q)

    def test_invalid_seed(self):
        for p in ({},None,seed([[1]],[0]),dict(format=e.prior.previous.FORMAT,names=[True],values=[False])):
            with self.assertRaises(ValueError):e.search([[1]],p)

    def test_invalid_budget_and_input(self):
        for n in (-1,True,1.5):
            with self.assertRaises(ValueError):e.discover([[1]],node_limit=n)
        for source in ([[0]],[[True]],[['x']]):
            with self.assertRaises(ValueError):e.discover(source)

    def test_interruption_has_no_refutation(self):
        r=e.discover(unsat_square(),node_limit=1)
        self.assertEqual(r['diagnostic']['reason'],'budget');self.assertIsNone(r['exclusion'])

    def test_recording_does_not_change_search(self):
        for source in (unsat_square(),[[1,2],[-1,3],[-2,-3]]):
            a=e.search(source,seed(source),record=True);b=e.search(source,seed(source),record=False)
            self.assertEqual(a['diagnostic'],b['diagnostic']);self.assertEqual(a['witness'],b['witness']);self.assertIsNone(b['exclusion'])

    def test_clause_edit_invalidates_model(self):
        source=[[1]];w=e.discover(source)['witness']
        with self.assertRaises(ValueError):e.prior.previous.check(source+[[-1]],w)
