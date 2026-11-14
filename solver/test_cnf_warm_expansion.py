from collections import Counter
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_probe_continuation import ContinuationRoutes
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.cnf_trace_split import verify
from experiments.cnf_source_local import advance_one
from solver.test_cnf_source_local import seed, OPTIONS


class WarmExpansionTests(unittest.TestCase):
    def test_clear_prefix_then_split_without_resetting_allowance(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';source,_=seed(path)
            h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(32)
            try:
                session=WarmExpansion(h);rows=[]
                with patch.object(h,'set_admission_budget',side_effect=AssertionError('budget reset')):
                    for _ in range(6):rows.append(session.advance(source,ContinuationRoutes(h),Counter()))
                self.assertEqual([r['mode'] for r in rows],['ordinary']*5+['split_after_ordinary_exhaustion'])
                self.assertTrue(all(r['operation']['record']['probing']['status']=='clear' for r in rows[:5]))
                self.assertEqual(len(rows[-1]['acquisition']['branches']),2)
                verify(h,rows[-1]['record'],Counter());self.assertLessEqual(len(h.admitted),32)
            finally:h.close()

    def test_zero_budget_keeps_both_split_obligations_and_resumes_exactly(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';source,_=seed(path)
            h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(0)
            try:
                session=WarmExpansion(h,state_limit=0)
                for _ in range(6):row=session.advance(source,ContinuationRoutes(h),Counter())
                self.assertTrue(row['pending']);self.assertFalse(h.admitted)
                record=row['record'];h.close()
                h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(32)
                session=WarmExpansion(h)
                with patch.object(h,'set_admission_budget',side_effect=AssertionError('budget reset')),patch(
                    'experiments.cnf_warm_expansion.candidates',side_effect=AssertionError('reranked pending pair')):
                    resumed=session.advance(source,ContinuationRoutes(h),Counter(),pending_split=record)
                self.assertEqual(resumed['record'],record)
                self.assertEqual(resumed['mode'],'resume_split');self.assertFalse(resumed['pending'])
                before=set(h.admitted)
                again=session.advance(source,ContinuationRoutes(h),Counter(),pending_split=record)
                self.assertFalse(again['added']);self.assertEqual(h.admitted,before)
            finally:h.close()

    def test_forced_resume_reuses_probes_and_keeps_admission_history(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';source,_=seed(path,'forced')
            h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(0)
            try:
                routes=ContinuationRoutes(h)
                advance_one(h,routes,source,Counter());pending=advance_one(h,routes,source,Counter())
                self.assertTrue(pending['admission_stopped']);h.close()
                h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(1)
                session=WarmExpansion(h,state_limit=1)
                with patch.object(h,'set_admission_budget',side_effect=AssertionError('budget reset')),patch(
                    'experiments.cnf_probe_continuation.discover_probes',side_effect=AssertionError('reprobe')):
                    first=session.advance(source,ContinuationRoutes(h),Counter());before=set(h.admitted)
                    second=session.advance(source,ContinuationRoutes(h),Counter())
                self.assertEqual(first['operation']['record'],pending['record'])
                self.assertEqual(h.admitted,before);self.assertLessEqual(len(before),1)
                self.assertFalse(second['added'])
            finally:h.close()

    def test_mismatched_allowance_or_pending_source_rejected_before_work(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';source,_=seed(path)
            h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(1)
            try:
                routes=ContinuationRoutes(h)
                with self.assertRaises(ValueError):WarmExpansion(h).advance(source,routes,Counter())
                with self.assertRaises(ValueError):WarmExpansion(h,state_limit=1).advance(
                    source,routes,Counter(),pending_split={'source':'different'})
                self.assertFalse(h.admitted)
            finally:h.close()


if __name__=='__main__':unittest.main()
