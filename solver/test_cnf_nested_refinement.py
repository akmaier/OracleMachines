from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from experiments.cnf_nested_refinement import NestedRefinement, base


class NestedRefinementTests(unittest.TestCase):
    def history(self,path=':memory:'):
        h=base.CompleteAdmissionInventory(path,**base.OPTIONS);base.split.initialize(h)
        h.set_admission_budget(256);return h

    def source(self,h):
        return h._edge(json.loads(Path('solver/fixtures/trace-split.json').read_text()),0)['key']

    def test_saved_split_is_followed_and_root_proof_replays(self):
        h=self.history()
        try:
            root=self.source(h);record=base.split.acquire_record(h,root,5,Counter())
            session=NestedRefinement(h,root)
            self.assertEqual(session.frontier()[0]['kind'],'pending')
            result=session.batch(state_limit=64,pair_limit=8)
            self.assertTrue(result['closed'])
            self.assertEqual(result['selection_counts'].get('bootstrap_fresh_assumptions',0),0)
            self.assertEqual(session.decisions[root],base.split.record_key(record))
            _,plan=base.compose(h,[root],session.registry,Counter())
            proof=base.expand(h,plan,[root],session.registry,Counter())
            base.split.verify_positive(h,proof,[root],list(session.records.values()),Counter())
        finally:h.close()

    def test_interrupted_pair_cold_resume_preserves_choice_and_rows(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';h=self.history(path)
            try:
                root=self.source(h);base.split.acquire_record(h,root,5,Counter())
                session=NestedRefinement(h,root);first=session.batch(state_limit=0,pair_limit=2)
                self.assertFalse(first['closed']);self.assertEqual(first['reason'],'state_limit')
                self.assertEqual(first['entered'],0);decisions=first['decisions'];before=base.rows(h)
            finally:h.close()
            h=self.history(path)
            try:
                with patch.object(base.split,'discover_simplification',side_effect=AssertionError('reacquired saved pair')):
                    session=NestedRefinement(h,root,decisions);final=session.batch(state_limit=64,pair_limit=2)
                self.assertTrue(final['closed']);self.assertEqual(final['decisions'],decisions)
                self.assertTrue(before.items()<=base.rows(h).items())
            finally:h.close()

    def test_new_selected_pair_is_persisted_before_child_admission(self):
        h=self.history()
        try:
            root=self.source(h);session=NestedRefinement(h,root)
            result=session.batch(state_limit=0,pair_limit=1)
            self.assertFalse(result['closed']);self.assertEqual(result['entered'],0)
            self.assertEqual(result['selection_counts']['bootstrap_fresh_assumptions'],2)
            identity=result['decisions'][root]
            self.assertIsNotNone(h.db.execute(f'SELECT payload FROM {base.split.TABLE} WHERE id=?',(identity,)).fetchone())
            self.assertEqual(session.frontier()[0]['kind'],'pending')
        finally:h.close()

    def test_unbound_choice_and_invalid_budgets_fail_closed(self):
        h=self.history()
        try:
            root=self.source(h)
            with self.assertRaises(ValueError):NestedRefinement(h,root,{root:'foreign'})
            session=NestedRefinement(h,root)
            for bad in (-1,True,1.5):
                with self.assertRaises(ValueError):session.batch(state_limit=bad)
            before=base.rows(h);result=session.batch(state_limit=0,pair_limit=0)
            self.assertFalse(result['closed']);self.assertEqual(result['operations'],[])
            self.assertEqual(before,base.rows(h))
        finally:h.close()


if __name__=='__main__':unittest.main()
