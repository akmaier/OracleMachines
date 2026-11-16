from collections import Counter
import copy
import json
from pathlib import Path
import tempfile
import unittest
from experiments.cnf_query_checkpoint import check_query, base
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
from experiments.cnf_split_registry import SplitRegistry


class QueryCheckpointTests(unittest.TestCase):
    def prepare(self, path):
        h = base.CompleteAdmissionInventory(path, **base.OPTIONS); base.split.initialize(h)
        h.set_admission_budget(128)
        source = json.loads(Path('solver/fixtures/trace-split.json').read_text())
        root = h._edge(source, 0)['key']; session = ScopedNestedRefinement(h, root)
        session.batch(state_limit=128, pair_limit=8)
        flags, plan = base.compose(h, [root], session.registry, Counter())
        self.assertTrue(flags[0])
        proof = base.expand(h, plan, [root], session.registry, Counter())
        return h, source, root, proof

    def test_positive_replay_is_cold_bound_and_read_only(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h, source, root, proof = self.prepare(path); h.close()
            before = base.sha(path)
            result = check_query(path, base.OPTIONS, source, root, proof, True)
            self.assertTrue(result['positive_claim_checked']); self.assertTrue(result['no_acquisition'])
            self.assertEqual(result['positive_steps'], len(proof['steps'])); self.assertEqual(base.sha(path), before)

    def test_foreign_source_or_claim_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h, source, root, proof = self.prepare(path); h.close()
            with self.assertRaises(ValueError): check_query(path, base.OPTIONS, [[1]], root, proof, True)
            with self.assertRaises(ValueError): check_query(path, base.OPTIONS, source, root, proof, False)
            with self.assertRaises(ValueError): check_query(path, base.OPTIONS, source, root, proof, 1)

    def test_missing_or_forged_required_split_is_rejected(self):
        for operation in ('delete', 'forge'):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as td:
                path = Path(td)/'h'; h, source, root, proof = self.prepare(path)
                try:
                    identity = next(s['rule']['id'] for s in proof['steps'] if s['rule']['kind']==base.split.KIND)
                    if operation=='delete': h.db.execute(f'DELETE FROM {base.split.TABLE} WHERE id=?',(identity,))
                    else:
                        record=base.load_json(h.db.execute(f'SELECT payload FROM {base.split.TABLE} WHERE id=?',(identity,)).fetchone()[0])
                        record['branches'].pop()
                        h.db.execute(f'UPDATE {base.split.TABLE} SET payload=? WHERE id=?',(base.encode(record),identity))
                    h.db.commit()
                finally: h.close()
                with self.assertRaises(ValueError): check_query(path, base.OPTIONS, source, root, proof, True)

    def test_unrelated_corruption_still_requires_full_checkpoint_audit(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h, source, root, proof = self.prepare(path)
            try:
                h.set_admission_budget(128); other=h._edge(((1,2),(-1,2)),0)['key']
                record=base.split.acquire_record(h,other,1,Counter()); bad=copy.deepcopy(record);bad['branches'].pop()
                h.db.execute(f'UPDATE {base.split.TABLE} SET payload=? WHERE id=?',(base.encode(bad),base.split.record_key(record)));h.db.commit()
            finally: h.close()
            self.assertTrue(check_query(path,base.OPTIONS,source,root,proof,True)['positive_claim_checked'])
            h=base.CompleteAdmissionInventory(path,**base.OPTIONS)
            try:
                with self.assertRaises(ValueError): SplitRegistry(h)
            finally: h.close()

    def test_empty_proof_carries_no_negative_verdict(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'h';h,source,root,proof=self.prepare(path);h.close()
            empty=dict(format=proof['format'],roots=[],steps=[])
            result=check_query(path,base.OPTIONS,source,root,empty,False)
            self.assertFalse(result['positive_claim_checked']);self.assertTrue(result['no_negative_claim'])
            with self.assertRaises(ValueError): check_query(path,base.OPTIONS,source,root,empty,True)


if __name__=='__main__': unittest.main()
