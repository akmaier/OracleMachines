from collections import Counter
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from experiments.cnf_nested_refinement import NestedRefinement, base
from experiments.cnf_scoped_refinement import ScopedNestedRefinement, ScopedSplitRegistry
from experiments.cnf_split_registry import SplitRegistry


class ScopedRefinementTests(unittest.TestCase):
    def history(self, path=':memory:'):
        h = base.CompleteAdmissionInventory(path, **base.OPTIONS)
        base.split.initialize(h); h.set_admission_budget(256)
        return h

    def source(self, h):
        return h._edge(json.loads(Path('solver/fixtures/trace-split.json').read_text()), 0)['key']

    def proof(self, h, root, routes):
        closed, plan = base.compose(h, [root], routes, Counter())
        proof = base.expand(h, plan, [root], routes, Counter())
        records = [json.loads(p) for p, in h.db.execute(f'SELECT payload FROM {base.split.TABLE} ORDER BY rowid')]
        base.split.verify_positive(h, proof, proof['roots'], records, Counter())
        return closed, proof

    def test_matches_full_policy_rows_choices_and_proof(self):
        results = []
        for cls in (NestedRefinement, ScopedNestedRefinement):
            h = self.history()
            try:
                root = self.source(h)
                other = h._edge(((1, 2), (-1, 2)), 0)['key']
                base.split.acquire_record(h, other, 1, Counter())
                base.split.acquire_record(h, root, 5, Counter())
                before = base.rows(h); session = cls(h, root)
                if cls is ScopedNestedRefinement:
                    self.assertEqual(session.registry.statistics()['deferred_records'], 1)
                data = session.batch(state_limit=64, pair_limit=8)
                self.assertTrue(data['closed']); self.assertTrue(before.items() <= base.rows(h).items())
                results.append((data['operations'], data['decisions'], data['probes'], base.rows(h),
                                self.proof(h, root, session.registry)))
            finally:
                h.close()
        self.assertEqual(results[0], results[1])

    def test_pending_activation_exposes_previously_unreachable_split(self):
        h = self.history()
        try:
            root = self.source(h); pair = base.split.acquire_record(h, root, 1, Counter())
            targets, _ = base.split.verify(h, pair, Counter())
            first = h._edge(targets[0], 0)['key']
            self.assertIsNone(h._load(pair['branches'][1]['edge']['key']))
            variable = next(abs(l) for c in h._load(first)['cnf'] for l in c)
            nested = base.split.acquire_record(h, first, variable, Counter())
            identity = base.split.record_key(nested)
            registry = ScopedSplitRegistry(h, [root])
            self.assertNotIn(identity, registry._records)
            h._edge(targets[1], 0); registry.refresh()
            self.assertIn(identity, registry._records)
            self.assertEqual(self.proof(h, root, registry), self.proof(h, root, SplitRegistry(h)))
        finally:
            h.close()

    def test_interrupted_pair_cold_resume_reuses_saved_assumptions(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h = self.history(path)
            try:
                root = self.source(h); session = ScopedNestedRefinement(h, root)
                first = session.batch(state_limit=0, pair_limit=1)
                self.assertFalse(first['closed']); before = base.rows(h)
            finally:
                h.close()
            h = self.history(path)
            try:
                with patch.object(base.split, 'discover_simplification', side_effect=AssertionError('reacquired')):
                    resumed = ScopedNestedRefinement(h, root, first['decisions'])
                    final = resumed.batch(state_limit=64, pair_limit=1)
                self.assertTrue(before.items() <= base.rows(h).items())
                self.assertEqual(final['selection_counts'].get('bootstrap_fresh_assumptions', 0), 0)
                self.assertEqual(final['decisions'], first['decisions'])
            finally:
                h.close()

    def test_unrelated_corruption_is_deferred_but_never_certified(self):
        h = self.history()
        try:
            root = self.source(h); other = h._edge(((1, 2), (-1, 2)), 0)['key']
            record = base.split.acquire_record(h, other, 1, Counter()); bad = copy.deepcopy(record)
            bad['branches'].pop()
            h.db.execute(f'UPDATE {base.split.TABLE} SET payload=? WHERE id=?',
                         (base.encode(bad), base.split.record_key(record))); h.db.commit()
            scoped = ScopedSplitRegistry(h, [root])
            self.assertEqual(scoped.statistics()['deferred_records'], 1)
            with self.assertRaises(ValueError): ScopedSplitRegistry(h, [other])
            with self.assertRaises(ValueError): SplitRegistry(h)
        finally:
            h.close()

    def test_writer_mutation_and_policy_changes_invalidate(self):
        for change in ('same_connection', 'external', 'policy', 'schema'):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as td:
                path = Path(td)/'h'; h = self.history(path)
                try:
                    root = self.source(h); registry = ScopedSplitRegistry(h, [root])
                    if change == 'same_connection':
                        h.db.execute('UPDATE cnf_patterns_v1 SET payload=payload WHERE id=?', (root,)); h.db.commit()
                    elif change == 'external':
                        db = sqlite3.connect(path)
                        try:
                            db.execute("UPDATE cnf_patterns_v1 SET payload=payload || ' ' WHERE id=?", (root,)); db.commit()
                        finally: db.close()
                    elif change == 'policy': h.config['candidate_limit'] += 1
                    else: h.db.execute('CREATE TABLE unrelated (id INTEGER)'); h.db.commit()
                    with self.assertRaises(ValueError): registry.refresh()
                    with self.assertRaises(ValueError): registry.refresh()
                finally:
                    h.close()

    def test_missing_root_and_wrong_pair_identity_fail_closed(self):
        h = self.history()
        try:
            with self.assertRaises(ValueError): ScopedSplitRegistry(h, ['missing'])
            root = self.source(h); record = base.split.acquire_record(h, root, 1, Counter())
            h.db.execute(f'UPDATE {base.split.TABLE} SET id=?', ('wrong',)); h.db.commit()
            with self.assertRaises(ValueError): ScopedSplitRegistry(h, [root])
        finally:
            h.close()


if __name__ == '__main__': unittest.main()
