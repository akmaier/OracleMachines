from collections import Counter
import copy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_activation import PatternActivationMaintenance
from experiments.cnf_trace_split import candidates, verify
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.compare_cnf_projection_bridge import routes_for, add_splits, select
from experiments.cnf_route_composition import compose
from experiments.compare_cnf_probe_continuation import TABLES
from solver.test_cnf_source_local import OPTIONS, seed


class PatternActivationTests(unittest.TestCase):
    def prepare(self, path):
        h = BudgetedInventory(path, **OPTIONS); self.addCleanup(h.close)
        for table in TABLES:
            h.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        h.db.commit(); h.set_admission_budget(32)
        source = h._edge(json.loads(Path('solver/fixtures/trace-split.json').read_text()), 0)['key']
        h.set_admission_budget(0); ev = [[], [], [], [], []]
        m = PatternActivationMaintenance(h, ev, [])
        rec = candidates(h, source, m.routes, Counter())[0]['record']
        return h, source, ev, m, rec

    def equal(self, h, source, ev, m):
        fresh = routes_for(h, ev, [])
        self.assertEqual(dict(m.routes.by_source), dict(fresh.by_source))
        self.assertEqual(m.routes.windows, fresh.windows)
        self.assertEqual(m.routes.continuations, fresh.continuations)
        actual = compose(h, [source], m.routes, Counter())
        self.assertEqual(actual, compose(h, [source], fresh, Counter()))
        self.assertEqual(select(h, m.routes, ev, [source], actual[0], Counter()),
                         select(h, fresh, ev, [source], actual[0], Counter()))

    def test_pending_pair_waits_for_both_children_and_activates_once(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, ev, m, rec = self.prepare(Path(td)/'h')
            ev = add_splits(ev, [rec])
            empty = WarmExpansion(h, state_limit=0).advance(source, m.routes, Counter(), pending_split=rec)
            self.assertEqual(m.refresh(empty, ev, [])['activated_routes'], 0)
            targets, _ = verify(h, rec, Counter()); h.set_admission_budget(32)
            previous = set(h.admitted)
            h._edge(targets[0], h._load(source)['depth'])
            op = dict(mode='resume_split', source=source, record=rec, added=sorted(h.admitted-previous), pending=True)
            self.assertEqual(m.refresh(op, ev, [])['activated_routes'], 0)
            self.equal(h, source, ev, m)
            self.assertEqual(compose(h, [source], m.routes, Counter())[0], [False])
            original = m.routes
            result = WarmExpansion(h).advance(source, m.routes, Counter(), pending_split=rec)
            update = m.refresh(result, ev, [])
            self.assertEqual(update['mode'], 'pattern_activation')
            self.assertEqual(update['activated_routes'], 1); self.assertEqual(update['pending_routes'], 0)
            self.assertIs(m.routes, original); self.equal(h, source, ev, m)
            repeated = WarmExpansion(h).advance(source, m.routes, Counter(), pending_split=rec)
            self.assertEqual(m.refresh(repeated, ev, [])['activated_routes'], 0)
            self.equal(h, source, ev, m)

    def test_new_split_attaches_after_acquisition_without_rebuild(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, ev, m, rec = self.prepare(Path(td)/'h'); h.set_admission_budget(32)
            original = m.routes
            op = WarmExpansion(h).advance(source, m.routes, Counter(), pending_split=rec)
            ev = add_splits(ev, [rec]); update = m.refresh(op, ev, [])
            self.assertEqual(update['mode'], 'pattern_activation'); self.assertGreater(update['inserted_patterns'], 0)
            self.assertEqual(update['activated_routes'], 1); self.assertIs(m.routes, original)
            self.equal(h, source, ev, m)

    def test_reverse_arrival_preserves_original_split_order(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, ev, m, first = self.prepare(Path(td)/'h')
            second = next(c['record'] for c in candidates(h, source, m.routes, Counter()) if c['record'] != first)
            ev = add_splits(ev, [first, second])
            h.set_admission_budget(32); m = PatternActivationMaintenance(h, ev, [])
            for rec in (second, first):
                op = WarmExpansion(h).advance(source, m.routes, Counter(), pending_split=rec)
                self.assertEqual(m.refresh(op, ev, [])['mode'], 'pattern_activation')
                self.equal(h, source, ev, m)

    def test_forced_continuation_is_activated_by_pattern_only_resumption(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; source, _ = seed(path, 'forced')
            h = BudgetedInventory(path, **OPTIONS); self.addCleanup(h.close); h.set_admission_budget(0)
            ev = [[], [], [], [], []]; m = PatternActivationMaintenance(h, ev, [])
            engine = WarmExpansion(h, state_limit=0)
            clear = engine.advance(source, m.routes, Counter())
            self.assertEqual(m.refresh(clear, ev, [])['mode'], 'clear_append')
            forced = engine.advance(source, m.routes, Counter())
            self.assertTrue(forced['pending']); self.assertEqual(m.refresh(forced, ev, [])['mode'], 'full_rebuild')
            self.assertEqual(m.statistics()['pending_routes'], 1)
            h.set_admission_budget(32)
            op = WarmExpansion(h).advance(source, m.routes, Counter()); update = m.refresh(op, ev, [])
            self.assertEqual(update['mode'], 'pattern_activation'); self.assertEqual(update['activated_routes'], 1)
            self.equal(h, source, ev, m)

    def test_extra_writes_and_sidecars_force_full_checking(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, ev, m, rec = self.prepare(Path(td)/'h'); h.set_admission_budget(32)
            op = WarmExpansion(h).advance(source, m.routes, Counter(), pending_split=rec)
            ev = add_splits(ev, [rec])
            with h.db: h.db.execute('UPDATE cnf_patterns_v1 SET payload=payload WHERE id=?', (source,))
            self.assertEqual(m.refresh(op, ev, [])['mode'], 'full_rebuild'); self.equal(h, source, ev, m)
            other = next(c['record'] for c in candidates(h, source, m.routes, Counter()) if c['record'] != rec)
            ev = add_splits(ev, [other]); op['added'] = []
            self.assertEqual(m.refresh(op, ev, [])['mode'], 'full_rebuild'); self.equal(h, source, ev, m)

    def test_forged_split_rejected_and_unreported_admission_cannot_fast_update(self):
        with tempfile.TemporaryDirectory() as td:
            h, source, ev, m, rec = self.prepare(Path(td)/'h'); h.set_admission_budget(32)
            op = WarmExpansion(h).advance(source, m.routes, Counter(), pending_split=rec)
            bad = copy.deepcopy(op); bad['record']['edges'][1] = bad['record']['edges'][0]
            with self.assertRaises(ValueError): m.refresh(bad, add_splits(ev, [bad['record']]), [])
            bad = copy.deepcopy(op); bad['added'] = []
            ev = add_splits(ev, [rec]); self.assertEqual(m.refresh(bad, ev, [])['mode'], 'full_rebuild')
            self.equal(h, source, ev, m)

    def test_external_writer_and_unknown_builder_require_new_checked_state(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'h'; h, source, ev, m, rec = self.prepare(path)
            with self.assertRaises(ValueError): PatternActivationMaintenance(h, ev, [], lambda *args: m.routes)
            db = sqlite3.connect(path)
            try:
                with db: db.execute("UPDATE cnf_patterns_v1 SET payload=payload || ' ' WHERE id=?", (source,))
            finally: db.close()
            op = dict(mode='resume_split', source=source, record=rec, added=[], pending=True)
            with self.assertRaisesRegex(ValueError, 'reopen'): m.refresh(op, add_splits(ev, [rec]), [])


if __name__ == '__main__': unittest.main()
