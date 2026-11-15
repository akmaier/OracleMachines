from collections import Counter
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_indexed_navigation import select as indexed_select
from experiments.cnf_original_frontier import select
from experiments.cnf_incremental_coverage import CoverageIndex
from experiments.cnf_route_composition import compose
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.cnf_probe_continuation import ContinuationRoutes
from experiments.continue_cnf_reused_branch import routes_for
from solver.test_cnf_source_local import seed, OPTIONS
from solver import test_cnf_trace_split as split_fixture
from solver import test_cnf_split_frontier as frontier_fixture


class IndexedNavigationTests(unittest.TestCase):
    def compare(self,h,routes,evidence,roots,index=None):
        index=index or CoverageIndex(h,roots,routes,Counter());flags=compose(h,roots,routes,Counter())[0]
        changes=h.db.total_changes;admitted=set(h.admitted);counts=Counter()
        with patch.object(h,'_discover',side_effect=AssertionError('new acquisition')):
            expected=select(h,routes,evidence,roots,flags,Counter())
            got=indexed_select(h,routes,evidence,roots,flags,counts,index)
        self.assertEqual(got,expected);self.assertEqual(changes,h.db.total_changes);self.assertEqual(admitted,h.admitted)
        return index,got,counts

    def test_shared_original_and_detached_result(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';key,_=seed(path);h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(0)
            try:
                ev=[[] for _ in range(5)];routes=routes_for(h,ev)
                index,got,counts=self.compare(h,routes,ev,[key,key])
                self.assertEqual(got['selected_original_cases'],[0,1]);self.assertGreater(counts['indexed_closure_queries'],0)
                self.assertFalse(counts['outside_index_compositions']);got['navigation']['frontiers'].clear()
                self.compare(h,routes,ev,[key,key],index)
            finally:h.close()

    def test_pending_forced_target_and_activation(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';key,_=seed(path,'forced');h=BudgetedInventory(path,**OPTIONS);h.set_admission_budget(0)
            try:
                h.set_admission_budget(0);engine=WarmExpansion(h,state_limit=0,pair_limit=0)
                engine.advance(key,ContinuationRoutes(h),Counter());engine.advance(key,ContinuationRoutes(h),Counter())
                ev=[[] for _ in range(5)];routes=routes_for(h,ev);index,got,_=self.compare(h,routes,ev,[key])
                self.assertEqual(got['mode'],'resume_original_probe')
                h.set_admission_budget(32);WarmExpansion(h).advance(key,routes,Counter())
                new=routes_for(h,ev)
                with self.assertRaisesRegex(ValueError,'Refresh'):indexed_select(h,new,ev,[key],index.closed(),Counter(),index)
                index.refresh(h,new,Counter());self.compare(h,new,ev,[key],index)
            finally:h.close()

    def test_both_pending_split_children_and_closed_transition(self):
        with tempfile.TemporaryDirectory() as td:
            fixture=split_fixture.TraceSplitTests();h=fixture.history(Path(td)/'h')
            try:
                source,_,record=fixture.seed(h);ev=[[],[],[],[record],[]];routes=routes_for(h,ev)
                index,got,_=self.compare(h,routes,ev,[source]);self.assertEqual(len(got['retained']['pending']),2)
                h.set_admission_budget(32);WarmExpansion(h).advance(source,routes,Counter(),pending_split=record)
                routes=routes_for(h,ev);index.refresh(h,routes,Counter());_,got,_=self.compare(h,routes,ev,[source],index)
                self.assertEqual(got['mode'],'all_originals_closed')
            finally:h.close()

    def test_retained_frontier_outside_original_graph_uses_full_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            h,_,record=frontier_fixture.SplitFrontierTests().seed(Path(td)/'h')
            try:
                ev=[[],[],[],[record],[]];routes=routes_for(h,ev)
                _,got,counts=self.compare(h,routes,ev,[])
                self.assertEqual(got['mode'],'retained_leaf');self.assertGreater(counts['outside_index_compositions'],0)
            finally:h.close()

    def test_root_flags_catalog_and_forged_record_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            f=split_fixture.TraceSplitTests();h=f.history(Path(td)/'h')
            try:
                source,_,record=f.seed(h);ev=[[],[],[],[record],[]];routes=routes_for(h,ev)
                index=CoverageIndex(h,[source],routes,Counter())
                for roots,flags in [([] ,[]),([source],[True])]:
                    with self.assertRaises(ValueError):indexed_select(h,routes,ev,roots,flags,Counter(),index)
                bad=copy.deepcopy(record);bad['edges'][1]['names']=[999]
                with self.assertRaises(ValueError):indexed_select(h,routes,[[],[],[],[bad],[]],[source],index.closed(),Counter(),index)
            finally:h.close()


if __name__=='__main__':unittest.main()
