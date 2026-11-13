from collections import Counter
import copy
import json
from pathlib import Path
import tempfile
import sqlite3
import shutil
import unittest
from unittest.mock import patch

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_continuation import TABLE, ContinuationRoutes, search, record_key
from experiments.cnf_route_composition import compose, verify_plan


class ProbeContinuationTests(unittest.TestCase):
    def test_eight_table_preservation_roundtrip_and_conflict_rollback(self):
        from experiments.compare_cnf_probe_continuation import TABLES, export_delta, apply_delta, digests
        with tempfile.TemporaryDirectory() as tmp:
            seed, history, delta, rebuilt = [Path(tmp)/n for n in ('seed','history','delta','rebuilt')]
            db = sqlite3.connect(seed)
            for table in TABLES:
                db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                db.execute(f'INSERT INTO {table} VALUES (?,?)', ('old','retained'))
            db.commit(); db.close(); shutil.copyfile(seed,history)
            db = sqlite3.connect(history)
            for table in TABLES: db.execute(f'INSERT INTO {table} VALUES (?,?)', ('new','added'))
            db.commit(); db.close()
            preserved, added = export_delta(seed,history,delta)
            self.assertTrue(all(preserved[t] == added[t] == 1 for t in TABLES))
            shutil.copyfile(seed,rebuilt); apply_delta(rebuilt,delta)
            self.assertEqual(digests(history),digests(rebuilt))
            before = rebuilt.read_bytes(); apply_delta(rebuilt,delta)
            self.assertEqual(before,rebuilt.read_bytes())
            db = sqlite3.connect(delta)
            db.execute(f'UPDATE {TABLE} SET payload=? WHERE id=?', ('conflict','new'))
            db.commit(); db.close()
            with self.assertRaises(ValueError): apply_delta(rebuilt,delta)
            self.assertEqual(before,rebuilt.read_bytes())

    def history(self, path):
        h = BudgetedInventory(path, max_depth=2, probe_limit=4, learn_limit=4, clause_growth_limit=2)
        for table in ('cnf_pivot_trials_v1','cnf_coupled_trials_v1','cnf_growth_trials_v1',
                      'cnf_probe_windows_v1',TABLE):
            h.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        h.db.commit()
        return h

    def seed(self, h, name):
        source = json.loads(Path('solver/fixtures/probe-continuation.json').read_text())[name]
        h.set_admission_budget(32)
        root = h._edge(source, 0)['key']
        self.assertEqual(h._load(root)['kind'], 'unresolved')
        return root

    def test_forced_prefix_pending_restart_and_refresh(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history'; h = self.history(path); root = self.seed(h, 'forced')
            routes = ContinuationRoutes(h)
            search(h, root, routes, Counter(), state_limit=0)
            before = dict(h.db.execute('SELECT id,payload FROM cnf_probe_windows_v1'))
            counts = Counter(); result = search(h, root, routes, counts, state_limit=0)
            self.assertIsNotNone(result['budget_stop'])
            self.assertEqual(counts['reused_prefix_attempts'], 8)
            self.assertEqual(counts['probe_attempts'], 5)
            record = next(iter(routes.continuations.values()))
            self.assertEqual(record['offset'], 4)
            self.assertNotIn(root, routes.by_source)
            h.close(); h = self.history(path)
            with patch('experiments.cnf_probe_continuation.discover_probes', side_effect=AssertionError('rediscovery')):
                with patch('experiments.cnf_probe_window.discover_probes', side_effect=AssertionError('rediscovery')):
                    routes = ContinuationRoutes(h)
                    kind, reused, target = routes.advance(h, root, Counter())
            self.assertEqual(kind, 'probe_continuation'); self.assertEqual(reused, record)
            self.assertEqual(dict(h.db.execute('SELECT id,payload FROM cnf_probe_windows_v1')), before)
            # Simulate acquisition through another path, then refresh availability.
            h.set_admission_budget(32); edge = h._edge(target, 0)
            self.assertEqual(edge, record['edge']); routes.refresh(h)
            self.assertIn(root, routes.by_source)
            closed, plan = compose(h, [root], routes, Counter())
            verify_plan(h, plan, [root] if closed[0] else [], routes, Counter())
            for field, value in [('offset',True),('offset',0),('offset',8),('width',5),
                                 ('source','foreign'),('edge',None)]:
                bad = copy.deepcopy(record); bad[field] = value
                with self.assertRaises(ValueError): routes.verify(h, bad, Counter())
            bad = copy.deepcopy(record); bad['probing']['attempts'][0]['value'] = True
            with self.assertRaises(ValueError): routes.verify(h, bad, Counter())
            # A forced predecessor cannot authorize any later block.
            bad = copy.deepcopy(record); bad['offset'] = 8
            with self.assertRaises(ValueError): routes.verify(h, bad, Counter())
            h.close()

    def test_clear_chain_exhaustion_missing_prefix_and_cold_reuse(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history'; h = self.history(path); root = self.seed(h, 'clear')
            routes = ContinuationRoutes(h)
            offsets = []
            for _ in range(10):
                _, record, _ = routes.advance(h, root, Counter())
                if record is None: break
                self.assertEqual(record['probing']['status'], 'clear')
                offsets.append(record.get('offset', 0))
            self.assertEqual(offsets, [0,4,8,12,16])
            self.assertEqual(compose(h, [root], routes, Counter())[0], [False])
            saved = h.storage(); h.close(); h = self.history(path)
            with patch('experiments.cnf_probe_continuation.discover_probes', side_effect=AssertionError('rediscovery')):
                routes = ContinuationRoutes(h)
                counts = Counter(); self.assertEqual(routes.advance(h, root, counts), (None,None,None))
            self.assertEqual(counts['reused_prefix_attempts'], 36)
            self.assertEqual(h.storage(), saved)
            # No unsupported jump survives cold verification even if its own
            # assumption traces are otherwise valid.
            with h.db:
                h.db.execute(f'DELETE FROM {TABLE} WHERE id=?', (encode([root,4,4]),))
            h.close(); h = self.history(path)
            with self.assertRaises(ValueError): ContinuationRoutes(h)
            h.close()

    def test_cross_source_record_cannot_supply_a_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            h = self.history(Path(tmp)/'history')
            root = self.seed(h, 'clear'); other = self.seed(h, 'forced')
            routes = ContinuationRoutes(h)
            routes.advance(h, root, Counter()); _, record, _ = routes.advance(h, root, Counter())
            bad = copy.deepcopy(record); bad['source'] = other
            with self.assertRaises(ValueError): routes.verify(h, bad, Counter())
            # A canonical key cannot be retargeted without changing row identity.
            with h.db:
                h.db.execute(f'UPDATE {TABLE} SET payload=? WHERE id=?', (encode(bad), record_key(record)))
            h.close(); h = self.history(Path(tmp)/'history')
            with self.assertRaises(ValueError): ContinuationRoutes(h)
            h.close()


if __name__ == '__main__': unittest.main()
