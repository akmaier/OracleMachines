from collections import Counter
from copy import deepcopy
from itertools import product
from unittest import TestCase
from unittest.mock import patch
from experiments import cnf_watched_learning as e
from solver.test_cnf_selective_learning import independent,SQUARE


def seed_for(source,values=None):
    names=sorted({abs(v) for c in source for v in c})
    return dict(format=e.prior.prior.previous.FORMAT,names=names,values=[False]*len(names) if values is None else list(values))


class WatchedLearningTests(TestCase):
    def compare(self,source,values=None,limit=20000):
        seed=seed_for(source,values);a=e.baseline.search(source,seed,node_limit=limit);b=e.search(source,seed,node_limit=limit);self.assertEqual(a,b);return b
    def test_empty_true(self):self.assertEqual(self.compare([])[0]['kind'],'sat')
    def test_empty_false(self):self.assertEqual(self.compare([[]])[0]['kind'],'unsat')
    def test_contradictory_units(self):self.compare([[1],[-1]])
    def test_learned_asserting_clause(self):self.assertTrue(self.compare(SQUARE)[0]['derivations'])
    def test_long_root_chain(self):self.compare([[1]]+[[-i,i+1] for i in range(1,600)]+[[-600]])
    def test_sparse_names(self):self.compare([[57,901],[-57,901],[57,-901],[-57,-901],[8000,-8000]])
    def test_duplicates_and_tautologies(self):self.compare(SQUARE+SQUARE+[[999,-999]])
    def test_watch_movement(self):
        source=[[1,2,3,4],[-1],[-2],[-3]];c=Counter();p,d=e.search(source,seed_for(source),c);self.assertGreater(c['watch_moves'],0);self.compare(source)
    def test_satisfied_watch_skip(self):
        source=[[1,2,3],[1],[-1,-2]];c=Counter();e.search(source,seed_for(source),c);self.assertGreater(c['watch_satisfied_skips'],0);self.compare(source)
    def test_minimum_actual_unit(self):self.compare([[-7],[-6],[-5],[1,5],[2,6],[3,7],[-1,-2,-3]])
    def test_all_seed_values(self):
        source=[[1,2],[-1,3],[-2,-3]]
        for vs in product((False,True),repeat=3):self.compare(source,vs)
    def test_capped_partial_proof(self):self.assertEqual(self.compare(SQUARE,limit=2)[0]['kind'],'unknown')
    def test_zero_budget(self):self.assertEqual(self.compare(SQUARE,limit=0)[0]['kind'],'unknown')
    def test_invalid_budget(self):
        for n in (-1,True,.5):
            with self.assertRaises(ValueError):e.search(SQUARE,seed_for(SQUARE),node_limit=n)
    def test_checker_without_search(self):
        p,d=self.compare(SQUARE)
        with patch.object(e,'search',side_effect=AssertionError),patch.object(e.baseline,'search',side_effect=AssertionError):self.assertFalse(e.check_result(SQUARE,p)['answer'])
    def test_deletion_transport(self):
        source,p=independent();target=source[1:]+[[-3]];self.assertEqual(e.solve(source,p,target),e.selective.solve(source,p,target))
    def test_shared_addition_transport(self):
        source,p=independent();target=source+[[-3,99],[-99]];self.assertEqual(e.solve(source,p,target),e.selective.solve(source,p,target))
    def test_retained_negative(self):
        p=e.baseline.solve(SQUARE)[0]
        with patch.object(e,'search',side_effect=AssertionError):r,d=e.expand(SQUARE,p,node_limit=0)
        self.assertFalse(e.check_result(SQUARE,r)['answer']);self.assertEqual(d['expanded'],0)
    def test_corrupt_retained_evidence(self):
        source,p=independent();p['derivations'][0][2]=[]
        with self.assertRaises(ValueError):e.expand(source,p)
    def test_input_preserved(self):
        source,p=independent();before=deepcopy((source,p));e.solve(source,p,source);self.assertEqual(before,(source,p))
