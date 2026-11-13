from collections import Counter
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from solver import test_cnf_trace_split as fixture
from experiments.cnf_trace_split import candidates
from experiments.cnf_split_batch import run
from experiments.cnf_split_frontier import frontier
from experiments.cnf_learning_continuation import ContinuedLearningRoutes


class SplitFrontierTests(unittest.TestCase):
    def seed(self,path):
        h=fixture.TraceSplitTests().history(path);h.set_admission_budget(32)
        cnf=json.loads(Path('solver/fixtures/split-frontier.json').read_text());key=h._edge(cnf,0)['key']
        routes=ContinuedLearningRoutes(h);record=candidates(h,key,routes,Counter())[0]['record']
        self.assertEqual(json.loads(record['source'])[-1],cnf)
        run(h,routes,[record],state_limit=32,pair_limit=32)
        return h,routes,record

    def test_open_child_replaces_parent_and_closed_sibling(self):
        with tempfile.TemporaryDirectory() as td:
            h,routes,record=self.seed(Path(td)/'h')
            with patch.object(h,'_discover',side_effect=AssertionError('new acquisition')):
                result=frontier(h,routes,[record],Counter())
            self.assertEqual([(row['variables'],row['clauses']) for row in result['leaves']],[(27,101)])
            self.assertNotEqual(result['leaves'][0]['source'],record['source']);self.assertFalse(result['pending'])
            self.assertEqual(result,frontier(h,routes,[record,record],Counter()));h.close()

    def test_nested_pending_split_retains_both_obligations(self):
        with tempfile.TemporaryDirectory() as td:
            h,routes,record=self.seed(Path(td)/'h');leaf=frontier(h,routes,[record],Counter())['leaves'][0]
            nested=next(row['record'] for row in candidates(h,leaf['source'],routes,Counter()) if not row['present'])
            result=frontier(h,routes,[record,nested],Counter())
            self.assertFalse(result['leaves']);self.assertEqual(len(result['pending']),2)
            self.assertEqual({row['value'] for row in result['pending']},{False,True})
            self.assertEqual({row['target'] for row in result['pending']},{edge['key'] for edge in nested['edges']})
            self.assertEqual(result,frontier(h,routes,[nested,record],Counter()));h.close()

    def test_closed_partition_has_no_scheduled_work(self):
        with tempfile.TemporaryDirectory() as td:
            f=fixture.TraceSplitTests();h=f.history(Path(td)/'h');_,routes,record=f.seed(h)
            run(h,routes,[record],state_limit=32,pair_limit=32)
            result=frontier(h,routes,[record],Counter())
            self.assertEqual(result,dict(leaves=[],pending=[],choices=[]));h.close()

    def test_forged_nested_record_cannot_steer_frontier(self):
        with tempfile.TemporaryDirectory() as td:
            h,routes,record=self.seed(Path(td)/'h');bad=copy.deepcopy(record);bad['edges'][1]['names']=[999]
            with self.assertRaises(ValueError):frontier(h,routes,[bad],Counter())
            h.close()


if __name__=='__main__':unittest.main()
