from collections import Counter
import copy
import itertools
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_additive_elimination import check_additive_elimination, lift_additive_elimination
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_growth_escape import search, verify_escape, trial_key
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds


class GrowthEscapeTests(unittest.TestCase):
    def test_six_table_delta_roundtrip_idempotence_and_conflict(self):
        from experiments.compare_cnf_growth_escape import TABLES, apply_delta, export_delta, digests
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            seed, history, delta, rebuilt = [Path(tmp) / n for n in ('seed', 'history', 'delta', 'rebuilt')]
            db = sqlite3.connect(seed)
            for table in TABLES:
                db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                db.execute(f'INSERT INTO {table} VALUES (?,?)', ('old', 'old-payload'))
            db.commit(); db.close(); shutil.copyfile(seed, history)
            db = sqlite3.connect(history)
            for table in TABLES: db.execute(f'INSERT INTO {table} VALUES (?,?)', ('new', 'new-payload'))
            db.commit(); db.close()
            preserved, added = export_delta(seed, history, delta)
            self.assertTrue(all(preserved[t] == added[t] == 1 for t in TABLES))
            shutil.copyfile(seed, rebuilt); apply_delta(rebuilt, delta)
            self.assertEqual(digests(rebuilt), digests(history))
            before = rebuilt.read_bytes(); apply_delta(rebuilt, delta)
            self.assertEqual(before, rebuilt.read_bytes())
            db = sqlite3.connect(delta)
            db.execute(f'UPDATE {TABLES[-1]} SET payload=? WHERE id=?', ('conflict', 'new'))
            db.commit(); db.close()
            with self.assertRaises(ValueError): apply_delta(rebuilt, delta)
            self.assertEqual(before, rebuilt.read_bytes())

    def test_exact_growth_boundary_and_every_projected_model(self):
        # 3 positive x-clauses and 3 negative ones yield 9 distinct resolvents:
        # six source clauses become nine, with no tautology or deduplication.
        source = ((1, 2), (1, 3), (1, 4), (-1, 5), (-1, 6), (-1, 7))
        with self.assertRaises(ValueError):
            check_additive_elimination(source, dict(variable=1), Counter(), clause_growth_limit=2)
        target = check_additive_elimination(source, dict(variable=1), Counter(), clause_growth_limit=3)
        self.assertEqual(len(target) - len(source), 3)
        for bits in itertools.product((False, True), repeat=6):
            model = dict(zip(range(2, 8), bits))
            projected = holds(target, model)
            self.assertEqual(projected, any(holds(source, model | {1: b}) for b in (False, True)))
            if projected:
                self.assertTrue(holds(source, lift_additive_elimination(source, dict(variable=1), model,
                    Counter(), clause_growth_limit=3)))

    def test_actual_core_binding_budget_stop_restart_and_reuse(self):
        core = json.loads(Path('experiments/results/cnf-coupled-pivots-originals/core-admission-audit.json').read_text())['cores'][0]
        options = dict(max_depth=0, probe_limit=4, learn_limit=4, clause_growth_limit=2)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'history'
            h = BudgetedInventory(path, **options); h.set_admission_budget(32)
            root = h.inspect(core['source'])['root']['key']
            self.assertEqual(h._load(root)['kind'], 'unresolved')
            original = dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1'))
            rows, stop = search(h, root, {}, Counter(), state_limit=0)
            self.assertEqual(rows, []); self.assertEqual(stop['variable'], 15)
            self.assertEqual(dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1')), original)
            counts = Counter(); rows, stop = search(h, root, {}, counts)
            self.assertIsNone(stop); self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['variable'], 15)
            self.assertEqual(h.config['clause_growth_limit'], 2)
            self.assertLessEqual(len(h.admitted), 32)
            for key, payload in original.items():
                self.assertEqual(h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (key,)).fetchone(), (payload,))
            record = json.loads(encode(rows[0])); h.close()
            h = BudgetedInventory(path, **options); h.set_admission_budget(0)
            with patch('experiments.cnf_growth_escape.alternatives', side_effect=AssertionError('rediscovery')):
                verify_escape(h, record, Counter())
            counts = Counter(); repeated, stop = search(h, root, {trial_key(record): record}, counts, state_limit=0)
            self.assertEqual(repeated, []); self.assertIsNone(stop)
            self.assertEqual(counts['reused_growth_trials'], 1); self.assertEqual(len(h.admitted), 0)
            for field, value in [('source', 'absent'), ('variable', True), ('growth_limit', True),
                                 ('growth_limit', 4), ('edge', dict(key=record['edge']['key'], names=[]))]:
                bad = copy.deepcopy(record); bad[field] = value
                with self.assertRaises(ValueError): verify_escape(h, bad, Counter())
            with self.assertRaises(ValueError): verify_escape(h, record, Counter(), growth_limit=2)
            bad = copy.deepcopy(record); bad['summary']['closed'] = not bad['summary']['closed']
            with self.assertRaises(ValueError): verify_escape(h, bad, Counter())
            h.close()


if __name__ == '__main__':
    unittest.main()
