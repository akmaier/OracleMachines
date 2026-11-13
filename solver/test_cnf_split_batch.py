from collections import Counter
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from solver import test_cnf_trace_split as fixture
from experiments.cnf_split_batch import acquire_pair,run,children
from experiments.cnf_route_composition import compose
from experiments.cnf_trace_split import attach


class SplitBatchTests(unittest.TestCase):
    def test_zero_budget_retains_both_pending_obligations(self):
        with tempfile.TemporaryDirectory() as td:
            f=fixture.TraceSplitTests();h=f.history(Path(td)/'h');source,routes,record=f.seed(h)
            rows=run(h,routes,[record],state_limit=0,pair_limit=0)
            self.assertEqual(rows[0]['admitted'],[])
            self.assertEqual([x['pending'] for x in rows[0]['branches']],[True,True])
            self.assertEqual(compose(h,[source],routes,Counter())[0],[False])
            self.assertTrue(all(x['pending'] for x in children(h,routes,[record])[0]['children']))
            h.close()

    def test_shared_pair_cap_and_later_resume(self):
        with tempfile.TemporaryDirectory() as td:
            f=fixture.TraceSplitTests();h=f.history(Path(td)/'h');source,routes,record=f.seed(h)
            h.set_admission_budget(32)
            first=acquire_pair(h,record,state_limit=32,pair_limit=1)
            self.assertEqual(len(first['admitted']),1)
            self.assertTrue(any(x['pending'] for x in first['branches']))
            self.assertFalse(attach(h,routes,record,Counter()))
            # A subsequent pair cannot silently reset the globally shared cap.
            second=acquire_pair(h,record,state_limit=1,pair_limit=32)
            self.assertEqual(second['admitted'],[])
            self.assertEqual(len(h.admitted),1)
            run(h,routes,[record],state_limit=32,pair_limit=32)
            self.assertEqual(compose(h,[source],routes,Counter())[0],[True])
            self.assertFalse(any(x['pending'] for x in children(h,routes,[record])[0]['children']))
            h.close()

    def test_duplicate_sources_skip_and_cold_reuse_without_discovery(self):
        with tempfile.TemporaryDirectory() as td:
            f=fixture.TraceSplitTests();path=Path(td)/'h';h=f.history(path);source,routes,record=f.seed(h)
            rows=run(h,routes,[record,record],state_limit=32,pair_limit=32)
            self.assertTrue(rows[1]['skipped_covered']);self.assertEqual(rows[1]['admitted'],[])
            h.close();h=f.history(path)
            from experiments.cnf_learning_continuation import ContinuedLearningRoutes
            routes=ContinuedLearningRoutes(h)
            with patch.object(h,'_discover',side_effect=AssertionError('rediscovery')):
                result=run(h,routes,[record],state_limit=0,pair_limit=0)
                self.assertEqual(result[0]['admitted'],[])
                self.assertEqual(compose(h,[source],routes,Counter())[0],[True])
            h.close()

    def test_invalid_allowances_are_rejected_before_acquisition(self):
        with tempfile.TemporaryDirectory() as td:
            f=fixture.TraceSplitTests();h=f.history(Path(td)/'h');_,routes,record=f.seed(h)
            for bad in (-1,True,1.5):
                with self.assertRaises(ValueError):run(h,routes,[record],state_limit=bad)
                with self.assertRaises(ValueError):acquire_pair(h,record,state_limit=32,pair_limit=bad)
            h.close()


if __name__=='__main__':unittest.main()
