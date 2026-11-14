from collections import Counter
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pending_split_maintenance import PendingSplitMaintenance
from experiments.cnf_trace_split import candidates, verify
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.compare_cnf_projection_bridge import routes_for, add_splits, select
from experiments.cnf_route_composition import compose
from experiments.compare_cnf_probe_continuation import TABLES
from solver.test_cnf_source_local import OPTIONS


class PendingSplitMaintenanceTests(unittest.TestCase):
    def prepared(self, path, limit=0):
        h = BudgetedInventory(path, **OPTIONS); self.addCleanup(h.close)
        for table in TABLES:
            h.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        h.db.commit(); h.set_admission_budget(32)
        cnf = json.loads(Path('solver/fixtures/trace-split.json').read_text())
        source = h._edge(cnf, 0)['key']; h.set_admission_budget(limit)
        evidence = [[], [], [], [], []]
        maintained = PendingSplitMaintenance(h, evidence, [], routes_for)
        record = candidates(h, source, maintained.routes, Counter())[0]['record']
        return h, source, evidence, maintained, record

    def pending(self, h, source, maintained, record, limit=0):
        return WarmExpansion(h, state_limit=limit).advance(source, maintained.routes, Counter(), pending_split=record)

    def assert_equivalent(self, h, source, evidence, maintained):
        fresh = routes_for(h, evidence, [])
        self.assertEqual(dict(maintained.routes.by_source), dict(fresh.by_source))
        self.assertEqual(maintained.routes.windows, fresh.windows)
        self.assertEqual(maintained.routes.continuations, fresh.continuations)
        flags, plan = compose(h, [source], fresh, Counter())
        self.assertEqual(compose(h, [source], maintained.routes, Counter()), (flags, plan))
        self.assertEqual(select(h, maintained.routes, evidence, [source], flags, Counter()),
                         select(h, fresh, evidence, [source], flags, Counter()))

    def test_pending_append_reuse_and_later_activation(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, evidence, m, record = self.prepared(Path(td)/'h')
            op = self.pending(h, source, m, record); evidence = add_splits(evidence, [record])
            original = m.routes
            self.assertEqual(m.refresh(op, evidence, [])['mode'], 'pending_split_append')
            self.assertIs(m.routes, original); self.assert_equivalent(h, source, evidence, m)
            self.assertEqual(m.refresh(op, evidence, [])['mode'], 'pending_split_reuse')
            h.set_admission_budget(32)
            resumed = self.pending(h, source, m, record, 32)
            self.assertFalse(resumed['pending'])
            self.assertEqual(m.refresh(resumed, evidence, [])['mode'], 'full_rebuild')
            self.assert_equivalent(h, source, evidence, m)
            self.assertEqual(compose(h, [source], m.routes, Counter())[0], [True])

    def test_one_missing_target_is_sufficient_and_other_target_stays_required(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, evidence, m, record = self.prepared(Path(td)/'h')
            targets, _ = verify(h, record, Counter()); h.set_admission_budget(32)
            h._edge(targets[0], h._load(source)['depth']); h.set_admission_budget(0)
            m = PendingSplitMaintenance(h, evidence, [], routes_for)
            op = self.pending(h, source, m, record); evidence = add_splits(evidence, [record])
            result = m.refresh(op, evidence, [])
            self.assertEqual(result['mode'], 'pending_split_append'); self.assertEqual(result['missing_targets'], 1)
            self.assert_equivalent(h, source, evidence, m)
            self.assertEqual(compose(h, [source], m.routes, Counter())[0], [False])

    def test_unstored_admissions_are_accounted_without_becoming_routes(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, evidence, m, record = self.prepared(Path(td)/'h')
            evidence = add_splits(evidence, [record]); h.set_admission_budget(1)
            # Isolate the admission-accounting contract without requiring this
            # small fixture to interrupt at a particular recursive depth.
            m = PendingSplitMaintenance(h, evidence, [], routes_for)
            h.admitted.add('entered-but-not-stored')
            op = dict(mode='resume_split', source=source, record=record, pending=True,
                      added=['entered-but-not-stored'])
            result = m.refresh(op, evidence, [])
            self.assertEqual(result['mode'], 'pending_split_reuse'); self.assertEqual(result['entered_unstored'], 1)
            self.assert_equivalent(h, source, evidence, m)
            self.assertEqual(m.refresh(op, evidence, [])['mode'], 'full_rebuild')

    def test_unrelated_writes_and_sidecar_changes_rebuild(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, evidence, m, record = self.prepared(Path(td)/'h')
            op = self.pending(h, source, m, record); evidence = add_splits(evidence, [record])
            with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=payload WHERE id=?', (source,))
            self.assertEqual(m.refresh(op, evidence, [])['mode'], 'full_rebuild')
            records = candidates(h, source, m.routes, Counter())
            other = next(row['record'] for row in records if row['record'] != record)
            changed = add_splits(evidence, [other])
            self.assertEqual(m.refresh(op, changed, [])['mode'], 'full_rebuild')
            self.assert_equivalent(h, source, changed, m)

    def test_forged_polarity_binding_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, evidence, m, record = self.prepared(Path(td)/'h')
            op = self.pending(h, source, m, record); bad = copy.deepcopy(op)
            bad['record']['edges'][1] = bad['record']['edges'][0]
            with self.assertRaises(ValueError): m.refresh(bad, add_splits(evidence, [bad['record']]), [])
            self.assertEqual(m.refresh(op, add_splits(evidence, [record]), [])['mode'], 'pending_split_append')

    def test_external_write_requires_reopen(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h, source, evidence, m, record = self.prepared(path)
            op = self.pending(h, source, m, record)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE cnf_patterns_v1 SET payload=payload || ' ' WHERE id=?", (source,))
            with self.assertRaisesRegex(ValueError, 'reopen'): m.refresh(op, add_splits(evidence, [record]), [])


if __name__ == '__main__': unittest.main()
