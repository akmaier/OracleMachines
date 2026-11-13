from collections import Counter
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.continue_cnf_original_splits import add_splits, select, routes_for
from experiments.cnf_affine_clause import discover
from experiments.cnf_split_batch import run
from experiments.cnf_route_composition import compose
from solver import test_cnf_trace_split as split_fixture
from solver.test_cnf_pattern_inventory import parity


class OriginalSplitTests(unittest.TestCase):
    def test_new_original_and_resumed_pending_keep_affine_route(self):
        with tempfile.TemporaryDirectory() as td:
            fixture=split_fixture.TraceSplitTests();path=Path(td)/'history';h=fixture.history(path)
            source,_,record=fixture.seed(h)
            cnf=parity(range(1,6),0)+parity(range(6,12),1)+[tuple(range(1,12))]
            h.set_admission_budget(32);affine=h._edge(cnf,0)['key'];node=h._load(affine)
            self.assertFalse(node['summary']['closed'])
            family=dict(source=affine,proof=discover(node['cnf']))
            evidence=[[],[],[],[],[family]];routes=routes_for(h,evidence)
            roots=[affine,source];self.assertEqual(compose(h,roots,routes,Counter())[0],[True,False])
            selected=select(h,routes,evidence,roots,[True,False],Counter())
            self.assertEqual(selected['mode'],'original_leaf');self.assertEqual(selected['record'],record)
            self.assertEqual(selected['leaf']['selected_original_cases'],[1])
            run(h,routes,[record],state_limit=0,pair_limit=0)
            evidence=add_splits(evidence,[record]);self.assertEqual(evidence[4],[family])
            pending=select(h,routes,evidence,roots,[True,False],Counter())
            self.assertEqual(pending['mode'],'resume_pending');self.assertEqual(pending['record'],record)
            run(h,routes,[record],state_limit=32,pair_limit=32)
            self.assertEqual(compose(h,roots,routes,Counter())[0],[True,True]);h.close()
            h=fixture.history(path);h.set_admission_budget(0)
            with patch.object(h,'_discover',side_effect=AssertionError('new recognition')):
                cold=routes_for(h,evidence)
                self.assertEqual(compose(h,roots,cold,Counter())[0],[True,True])
            h.close()

    def test_duplicate_resume_preserves_other_evidence_and_rejects_conflicts(self):
        record=dict(source='source',references=[dict(index=0),dict(index=1)],edges=['a','b'])
        evidence=[['rewrite'],['learning'],['block'],[record],['family']]
        before=copy.deepcopy(evidence);self.assertEqual(add_splits(evidence,[record]),before)
        bad=copy.deepcopy(record);bad['edges'][0]='different'
        with self.assertRaises(ValueError):add_splits(evidence,[bad])
        self.assertEqual(evidence,before)
        with self.assertRaises(ValueError):add_splits(evidence[:4],[record])


if __name__=='__main__':unittest.main()
