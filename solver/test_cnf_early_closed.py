from collections import Counter
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_early_closed import EarlyClosedExpansion
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.cnf_trace_split import verify,attach
from experiments.cnf_route_composition import compose
from experiments.cnf_probe_continuation import ContinuationRoutes
from experiments.cnf_coupled_pivots import BudgetedInventory
from solver.test_cnf_source_local import seed,OPTIONS
from solver import test_cnf_trace_split as split_fixture


class EarlyClosedTests(unittest.TestCase):
    def prepared(self,path):
        fixture=split_fixture.TraceSplitTests();h=fixture.history(path);source,routes,record=fixture.seed(h)
        targets,_=verify(h,record,Counter());h._edge(targets[0],0)
        return h,source,record

    def test_existing_closed_child_avoids_probes_and_keeps_both_obligations(self):
        with tempfile.TemporaryDirectory() as td:
            h,source,record=self.prepared(Path(td)/'h');h.set_admission_budget(32)
            try:
                routes=ContinuationRoutes(h);counts=Counter()
                with patch.object(h,'set_admission_budget',side_effect=AssertionError('reset')),patch(
                    'experiments.cnf_probe_window.discover_probes',side_effect=AssertionError('fresh probe')):
                    result=EarlyClosedExpansion(h).advance(source,routes,counts)
                self.assertEqual(result['mode'],'early_closed_split');self.assertFalse(result['pending'])
                self.assertEqual(len(result['acquisition']['branches']),2)
                self.assertIn(record['edges'][0]['key'],result['closed_children'])
                attach(h,routes,result['record'],Counter())
                self.assertEqual(compose(h,[source],routes,Counter())[0],[True])
                self.assertLessEqual(len(h.admitted),32)
            finally:h.close()

    def test_missing_second_child_stays_pending_then_cold_resumes_without_ranking(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';h,source,_=self.prepared(path);h.set_admission_budget(0)
            routes=ContinuationRoutes(h)
            result=EarlyClosedExpansion(h,state_limit=0).advance(source,routes,Counter())
            self.assertTrue(result['pending']);self.assertEqual(sum(b['pending'] for b in result['acquisition']['branches']),1)
            self.assertFalse(attach(h,routes,result['record'],Counter()))
            self.assertEqual(compose(h,[source],routes,Counter())[0],[False]);h.close()
            h=split_fixture.TraceSplitTests().history(path);h.set_admission_budget(32)
            try:
                with patch('experiments.cnf_early_closed.candidates',side_effect=AssertionError('reranking')):
                    resumed=EarlyClosedExpansion(h).advance(source,ContinuationRoutes(h),Counter(),pending_split=result['record'])
                self.assertEqual(resumed['mode'],'resume_split');self.assertFalse(resumed['pending'])
                self.assertEqual(resumed['record'],result['record'])
            finally:h.close()

    def test_no_closed_pair_falls_back_to_ordinary(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';source,_=seed(path);h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(32)
            try:
                counts=Counter();result=EarlyClosedExpansion(h).advance(source,ContinuationRoutes(h),counts)
                self.assertEqual(result['mode'],'ordinary');self.assertEqual(counts['early_closed_pair_misses'],1)
                self.assertFalse(h.admitted)
            finally:h.close()

    def test_saved_forced_target_precedes_new_split_search(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';source,_=seed(path,'forced');h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(0)
            engine=WarmExpansion(h,state_limit=0)
            engine.advance(source,ContinuationRoutes(h),Counter());forced=engine.advance(source,ContinuationRoutes(h),Counter())
            self.assertTrue(forced['pending']);h.close()
            h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(32)
            try:
                counts=Counter()
                with patch('experiments.cnf_early_closed.candidates',side_effect=AssertionError('split priority')),patch(
                    'experiments.cnf_probe_continuation.discover_probes',side_effect=AssertionError('reprobe')):
                    result=EarlyClosedExpansion(h).advance(source,ContinuationRoutes(h),counts)
                self.assertEqual(result['operation']['record'],forced['operation']['record'])
                self.assertFalse(result['pending']);self.assertEqual(counts['early_saved_forcing_resumed'],1)
            finally:h.close()

    def test_mismatched_budget_rejected_before_search(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';source,_=seed(path);h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(1)
            try:
                with patch('experiments.cnf_early_closed.candidates',side_effect=AssertionError('search')):
                    with self.assertRaises(ValueError):EarlyClosedExpansion(h).advance(source,ContinuationRoutes(h),Counter())
                self.assertFalse(h.admitted)
            finally:h.close()


if __name__=='__main__':unittest.main()
