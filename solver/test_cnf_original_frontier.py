from collections import Counter
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_original_frontier import select
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_probe_continuation import ContinuationRoutes
from experiments.cnf_route_composition import compose
from experiments.continue_cnf_reused_branch import routes_for
from experiments.cnf_split_batch import run
from solver.test_cnf_source_local import seed, OPTIONS
from solver import test_cnf_trace_split as split_fixture


class OriginalFrontierTests(unittest.TestCase):
    def test_empty_retained_frontier_selects_shared_original_without_acquisition(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';source,_=seed(path)
            h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(32)
            try:
                evidence=[[] for _ in range(5)];routes=routes_for(h,evidence)
                with patch.object(h,'_discover',side_effect=AssertionError('new state')):
                    chosen=select(h,routes,evidence,[source,source],[False,False],Counter())
                self.assertEqual(chosen['mode'],'original_leaf')
                self.assertEqual(chosen['selected_original_cases'],[0,1])
                self.assertFalse(h.admitted)
                with patch.object(h,'set_admission_budget',side_effect=AssertionError('reset')):
                    result=WarmExpansion(h).advance(chosen['source'],routes,Counter())
                self.assertEqual(result['mode'],'ordinary')
                self.assertEqual(result['operation']['record']['probing']['status'],'clear')
            finally:h.close()

    def test_original_forced_target_cold_resume_reuses_trace(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';source,_=seed(path,'forced')
            h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(0)
            engine=WarmExpansion(h,state_limit=0,pair_limit=0)
            engine.advance(source,ContinuationRoutes(h),Counter())
            forced=engine.advance(source,ContinuationRoutes(h),Counter())
            self.assertTrue(forced['pending']);h.close()
            h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(32)
            try:
                evidence=[[] for _ in range(5)];routes=routes_for(h,evidence)
                chosen=select(h,routes,evidence,[source],[False],Counter())
                self.assertEqual(chosen['mode'],'resume_original_probe')
                self.assertEqual(chosen['leaf']['target'],forced['operation']['record']['edge']['key'])
                with patch('experiments.cnf_probe_continuation.discover_probes',side_effect=AssertionError('reprobe')):
                    resumed=WarmExpansion(h).advance(chosen['source'],routes,Counter())
                self.assertEqual(resumed['operation']['record'],forced['operation']['record'])
                self.assertFalse(resumed['pending'])
            finally:h.close()

    def test_retained_pending_split_precedes_new_original_and_keeps_both_branches(self):
        with tempfile.TemporaryDirectory() as td:
            fixture=split_fixture.TraceSplitTests();h=fixture.history(Path(td)/'history')
            try:
                source,_,record=fixture.seed(h);evidence=[[],[],[],[record],[]]
                routes=routes_for(h,evidence);run(h,routes,[record],state_limit=0,pair_limit=0)
                chosen=select(h,routes_for(h,evidence),evidence,[source],[False],Counter())
                self.assertEqual(chosen['mode'],'resume_retained_split')
                self.assertEqual(chosen['pending_split'],record)
                self.assertEqual(len(chosen['retained']['pending']),2)
                h.set_admission_budget(32)
                result=WarmExpansion(h).advance(source,routes_for(h,evidence),Counter(),pending_split=record)
                self.assertEqual(len(result['acquisition']['branches']),2)
                routes=routes_for(h,evidence);closed=compose(h,[source],routes,Counter())[0]
                self.assertEqual(closed,[True])
                self.assertEqual(select(h,routes,evidence,[source],closed,Counter())['mode'],'all_originals_closed')
            finally:h.close()

    def test_all_closed_and_malformed_scope(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';seed(path)
            h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(0)
            try:
                evidence=[[] for _ in range(5)];routes=routes_for(h,evidence)
                self.assertIsNone(select(h,routes,evidence,[],[],Counter())['source'])
                for ev,roots,closed in ((evidence[:4],[],[]),(evidence,['missing'],[])):
                    with self.assertRaises(ValueError):select(h,routes,ev,roots,closed,Counter())
            finally:h.close()

    def test_smallest_frontier_and_pending_priority_independent_of_input_order(self):
        class Inventory:
            def _load(self,source):
                return dict(cnf={'wide':[[1,2,3]],'narrow':[[1,2]],'pending':[[1,2,3,4]]}[source])
        def row(source,pending=False):
            return dict(source=source,closed=False,leaves=[dict(source=source,pending=pending)])
        empty=dict(pending=[],leaves=[],choices=[])
        with patch('experiments.cnf_original_frontier.frontier',return_value=empty):
            for names in (['wide','narrow'],['narrow','wide']):
                with patch('experiments.cnf_original_frontier.remaining',return_value=[row(s) for s in names]):
                    chosen=select(Inventory(),{},[[] for _ in range(5)],names,[False]*2,Counter())
                    self.assertEqual(chosen['source'],'narrow')
                    self.assertEqual(chosen['selected_original_cases'],[names.index('narrow')])
            with patch('experiments.cnf_original_frontier.remaining',return_value=[row('narrow'),row('pending',True)]):
                chosen=select(Inventory(),{},[[] for _ in range(5)],['narrow','pending'],[False]*2,Counter())
                self.assertEqual(chosen['mode'],'resume_original_probe')
                self.assertEqual(chosen['source'],'pending')

    def test_stale_negative_or_missing_frontier_rejected(self):
        with patch('experiments.cnf_original_frontier.frontier',return_value=dict(pending=[],leaves=[],choices=[])):
            for row in (dict(closed=True,leaves=[]),dict(closed=False,leaves=[])):
                with patch('experiments.cnf_original_frontier.remaining',return_value=[row]):
                    with self.assertRaises(ValueError):select(None,{},[[] for _ in range(5)],['x'],[False],Counter())


if __name__=='__main__':unittest.main()
