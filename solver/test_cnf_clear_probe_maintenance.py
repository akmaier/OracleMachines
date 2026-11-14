from collections import Counter
import copy
from pathlib import Path
import sqlite3
import tempfile
import unittest

from experiments.cnf_clear_probe_maintenance import ClearProbeMaintenance
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.cnf_source_local import SourceProbeRoutes, advance_one
from experiments.cnf_trace_split import candidates
from experiments.cnf_route_composition import compose
from experiments.compare_cnf_projection_bridge import routes_for
from solver.test_cnf_source_local import seed, OPTIONS


class ClearMaintenanceTests(unittest.TestCase):
    def prepared(self, path, name='clear', limit=32):
        source, _ = seed(path, name)
        h = BudgetedInventory(path, **OPTIONS); h.set_admission_budget(limit)
        evidence = [[], [], [], [], []]
        maintained = ClearProbeMaintenance(h, evidence, [], routes_for)
        return h, source, evidence, maintained

    def assert_catalog(self, h, maintained, evidence, source):
        fresh = routes_for(h, evidence, [])
        self.assertEqual(dict(maintained.routes.by_source), dict(fresh.by_source))
        self.assertEqual(maintained.routes.windows, fresh.windows)
        self.assertEqual(maintained.routes.continuations, fresh.continuations)
        if not any(r['source'] == source and r['edge'] is not None
                   for r in [*fresh.windows.values(), *fresh.continuations.values()]):
            self.assertEqual(candidates(h, source, maintained.routes, Counter(), candidate_limit=64),
                             candidates(h, source, fresh, Counter(), candidate_limit=64))
        self.assertEqual(compose(h, [source], maintained.routes, Counter()), compose(h, [source], fresh, Counter()))

    def test_clear_prefixes_preserve_routes_and_expose_every_new_pair(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, evidence, maintained = self.prepared(Path(td)/'h')
            try:
                engine = WarmExpansion(h); original = maintained.routes
                for _ in range(5):
                    op = engine.advance(source, maintained.routes, Counter())
                    self.assertEqual(maintained.refresh(op, evidence, [])['mode'], 'clear_append')
                    self.assertIs(maintained.routes, original)
                    self.assert_catalog(h, maintained, evidence, source)
                self.assertFalse(h.admitted)
                # An exact reused window is harmless, without adding an edge.
                inner = advance_one(h, SourceProbeRoutes(h, source), source, Counter())
                # This source is exhausted: no record must take the general path.
                self.assertIsNone(inner['record'])
                op = dict(mode='no_saved_pair', operation=inner, source=source, added=[], pending=False)
                self.assertEqual(maintained.refresh(op, evidence, [])['mode'], 'full_rebuild')
            finally: h.close()

    def test_forcing_rebuilds_pending_and_activates_after_acquisition(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, evidence, maintained = self.prepared(Path(td)/'h', 'forced', 0)
            try:
                engine = WarmExpansion(h, state_limit=0)
                clear = engine.advance(source, maintained.routes, Counter())
                self.assertEqual(maintained.refresh(clear, evidence, [])['mode'], 'clear_append')
                forced = engine.advance(source, maintained.routes, Counter()); self.assertTrue(forced['pending'])
                self.assertEqual(maintained.refresh(forced, evidence, [])['mode'], 'full_rebuild')
                self.assert_catalog(h, maintained, evidence, source)
                h.set_admission_budget(32); engine = WarmExpansion(h)
                resumed = engine.advance(source, maintained.routes, Counter()); self.assertFalse(resumed['pending'])
                self.assertEqual(maintained.refresh(resumed, evidence, [])['mode'], 'full_rebuild')
                self.assert_catalog(h, maintained, evidence, source)
                self.assertTrue(maintained.routes.by_source[source])
            finally: h.close()

    def test_sidecar_change_and_unrelated_write_cannot_skip_rebuild(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, evidence, maintained = self.prepared(Path(td)/'h')
            try:
                engine = WarmExpansion(h); op = engine.advance(source, maintained.routes, Counter())
                # Same payload write still invalidates the single-insert guard.
                with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=payload WHERE id=?', (source,))
                self.assertEqual(maintained.refresh(op, evidence, [])['mode'], 'full_rebuild')
                op = engine.advance(source, maintained.routes, Counter())
                record = candidates(h, source, maintained.routes, Counter())[0]['record']
                evidence[3].append(record)
                self.assertEqual(maintained.refresh(op, evidence, [])['mode'], 'full_rebuild')
                self.assert_catalog(h, maintained, evidence, source)
            finally: h.close()

    def test_forged_clear_payload_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, evidence, maintained = self.prepared(Path(td)/'h')
            try:
                op = WarmExpansion(h).advance(source, maintained.routes, Counter())
                bad = copy.deepcopy(op); bad['operation']['record']['probing']['attempts'].pop()
                with self.assertRaisesRegex(ValueError, 'persisted exactly'): maintained.refresh(bad, evidence, [])
                self.assertEqual(maintained.refresh(op, evidence, [])['mode'], 'clear_append')
                self.assertEqual(maintained.refresh(op, evidence, [])['mode'], 'clear_reuse')
            finally: h.close()

    def test_external_writer_requires_reopening_checked_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h, source, evidence, maintained = self.prepared(path)
            try:
                op = WarmExpansion(h).advance(source, maintained.routes, Counter())
                with sqlite3.connect(path) as db:
                    db.execute("UPDATE cnf_patterns_v1 SET payload=payload || ' ' WHERE id=?", (source,))
                with self.assertRaisesRegex(ValueError, 'reopen'): maintained.refresh(op, evidence, [])
            finally: h.close()


if __name__ == '__main__': unittest.main()
