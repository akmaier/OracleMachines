from collections import Counter
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_early_saved import EarlySavedExpansion
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.cnf_trace_split import verify, attach
from experiments.cnf_route_composition import compose
from experiments.cnf_probe_continuation import ContinuationRoutes
from experiments.cnf_coupled_pivots import BudgetedInventory
from solver.test_cnf_source_local import seed, OPTIONS
from solver import test_cnf_trace_split as fixture


class EarlySavedTests(unittest.TestCase):
    def prepared(self, path):
        f=fixture.TraceSplitTests();h=f.history(path);source,_,record=f.seed(h)
        self.assertTrue(all(h._load(e['key']) is None for e in record['edges']))
        return h,source,record

    def test_unacquired_pair_avoids_probes_and_keeps_both_branches(self):
        with tempfile.TemporaryDirectory() as td:
            h,source,record=self.prepared(Path(td)/'h');h.set_admission_budget(32)
            try:
                routes=ContinuationRoutes(h)
                with patch.object(h,'set_admission_budget',side_effect=AssertionError('reset')),patch(
                    'experiments.cnf_probe_window.discover_probes',side_effect=AssertionError('fresh external probe')):
                    row=EarlySavedExpansion(h).advance(source,routes,Counter())
                self.assertEqual(row['mode'],'early_saved_split');self.assertEqual(row['record'],record)
                self.assertFalse(row['closed_children']);self.assertFalse(row['pending'])
                self.assertEqual(len(row['acquisition']['branches']),2)
                verify(h,record,Counter());attach(h,routes,record,Counter())
                self.assertEqual(compose(h,[source],routes,Counter())[0],[True])
            finally:h.close()

    def test_partial_pair_preserves_pending_and_cold_resumes_exactly(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';h,source,_=self.prepared(path);h.set_admission_budget(1)
            try:
                routes=ContinuationRoutes(h);row=EarlySavedExpansion(h,state_limit=1).advance(source,routes,Counter())
                self.assertTrue(row['pending']);self.assertEqual(len(h.admitted),1)
                self.assertFalse(attach(h,routes,row['record'],Counter()))
                self.assertEqual(compose(h,[source],routes,Counter())[0],[False])
            finally:h.close()
            h=fixture.TraceSplitTests().history(path);h.set_admission_budget(32)
            try:
                with patch('experiments.cnf_early_saved.candidates',side_effect=AssertionError('reranking')):
                    resumed=EarlySavedExpansion(h).advance(source,ContinuationRoutes(h),Counter(),pending_split=row['record'])
                self.assertEqual(resumed['mode'],'resume_split');self.assertEqual(resumed['record'],row['record'])
                self.assertFalse(resumed['pending'])
            finally:h.close()

    def test_no_pair_with_zero_candidate_budget_uses_ordinary(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';source,_=seed(path);h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(32)
            try:
                counts=Counter();row=EarlySavedExpansion(h,candidate_limit=0).advance(source,ContinuationRoutes(h),counts)
                self.assertEqual(row['mode'],'ordinary');self.assertEqual(counts['early_saved_pair_misses'],1)
                self.assertFalse(h.admitted)
            finally:h.close()

    def test_saved_forcing_precedes_new_split_even_when_target_pending(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';source,_=seed(path,'forced');h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(0)
            engine=WarmExpansion(h,state_limit=0)
            engine.advance(source,ContinuationRoutes(h),Counter());forced=engine.advance(source,ContinuationRoutes(h),Counter())
            self.assertTrue(forced['pending']);h.close()
            h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(32)
            try:
                counts=Counter()
                with patch('experiments.cnf_early_saved.candidates',side_effect=AssertionError('split search')),patch(
                    'experiments.cnf_probe_continuation.discover_probes',side_effect=AssertionError('reprobe')):
                    row=EarlySavedExpansion(h).advance(source,ContinuationRoutes(h),counts)
                self.assertEqual(row['operation']['record'],forced['operation']['record']);self.assertFalse(row['pending'])
                self.assertEqual(counts['early_saved_forcing_resumed'],1)
            finally:h.close()

    def test_mismatched_budget_rejected_before_search(self):
        with tempfile.TemporaryDirectory() as td:
            h,source,_=self.prepared(Path(td)/'h');h.set_admission_budget(1)
            try:
                with patch('experiments.cnf_early_saved.candidates',side_effect=AssertionError('search')):
                    with self.assertRaises(ValueError):EarlySavedExpansion(h).advance(source,ContinuationRoutes(h),Counter())
                self.assertFalse(h.admitted)
            finally:h.close()


if __name__=='__main__':unittest.main()
