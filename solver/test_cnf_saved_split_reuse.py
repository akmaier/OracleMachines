from collections import Counter
from pathlib import Path
import tempfile
import unittest
from experiments.cnf_saved_split_reuse import base, candidates, restore_variant
from experiments.cnf_scoped_refinement import ScopedNestedRefinement


class SavedSplitReuseTests(unittest.TestCase):
    def fixture(self, path):
        h=base.CompleteAdmissionInventory(path,**base.OPTIONS);base.split.initialize(h);h.set_admission_budget(128)
        source=base.load('solver/fixtures/trace-split.json');root=h._edge(source,0)['key']
        record=base.split.acquire_record(h,root,5,Counter());base.acquire(h,record)
        other=h._edge(((1,2),(-1,2)),0)['key'];base.split.acquire_record(h,other,1,Counter())
        return h,root

    def test_isolated_omission_preserves_authority_patterns_and_other_splits(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);h,root=self.fixture(p/'parent');rows=base.rows(h)
            pairs=dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'));h.close()
            cp=dict(archive=base.archive(p/'parent',p));before=base.sha(p/'parent');archive_sha=base.sha(cp['archive']['path'])
            for ablate in (False,True):
                dest=p/str(ablate);result=restore_variant(cp,dest,root,ablate=ablate)
                h=base.CompleteAdmissionInventory(dest,**base.OPTIONS)
                try:
                    self.assertEqual(rows,base.rows(h));actual=dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
                    expected={k:v for k,v in pairs.items() if not ablate or base.load_json(v)['source']!=root}
                    self.assertEqual(actual,expected);self.assertEqual(result['omitted_pairs'],len(pairs)-len(expected))
                    session=ScopedNestedRefinement(h,root);final=session.batch(state_limit=128,pair_limit=8)
                    self.assertTrue(final['closed'])
                    _,plan=base.compose(h,[root],session.registry,Counter());proof=base.expand(h,plan,[root],session.registry,Counter())
                    base.split.verify_positive(h,proof,[root],list(session.records.values()),Counter())
                finally:h.close()
            self.assertEqual(before,base.sha(p/'parent'));self.assertEqual(archive_sha,base.sha(cp['archive']['path']))

    def test_existing_destination_and_nonboolean_control_are_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td);h,root=self.fixture(p/'parent');h.close();cp=dict(archive=base.archive(p/'parent',p));before=base.sha(p/'parent')
            with self.assertRaises(FileExistsError):restore_variant(cp,p/'parent',root,ablate=True)
            with self.assertRaises(ValueError):restore_variant(cp,p/'new',root,ablate=1)
            self.assertEqual(before,base.sha(p/'parent'));self.assertFalse((p/'new').exists())

    def test_rank_diagnostic_is_read_only_and_charges_existing_closure(self):
        with tempfile.TemporaryDirectory() as td:
            h,root=self.fixture(Path(td)/'h')
            try:
                session=ScopedNestedRefinement(h,root);before=base.rows(h);decisions=dict(session.decisions)
                rows=candidates(session,root);self.assertEqual(len(rows),1)
                self.assertEqual(rows[0]['closed_children'],[True,True]);self.assertEqual(rows[0]['open_distinct_rank'][:2],[0,0])
                self.assertEqual(before,base.rows(h));self.assertEqual(decisions,session.decisions)
            finally:h.close()


if __name__=='__main__':unittest.main()
