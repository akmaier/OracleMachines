import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from experiments.cnf_checked_replay import CheckedReplay, DELTA_TABLES, TABLES
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_source_local import check_delta
from solver.test_cnf_source_local import OPTIONS


def empty(path):
    with sqlite3.connect(path) as db:
        for table in DELTA_TABLES:
            db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
    db.close()


class CheckedReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.seed = self.path/'seed'; empty(self.seed)
        h = BudgetedInventory(self.path/'acquired', **OPTIONS)
        try:
            h.set_admission_budget(32)
            h._edge([[1]], 0); h._edge([[-1]], 0)
            self.rows = list(h.db.execute('SELECT id,payload FROM cnf_patterns_v1 ORDER BY id'))
        finally:
            h.close()
        self.assertEqual(len(self.rows), 2)
        self.state = CheckedReplay(self.seed, OPTIONS)
        self.addCleanup(self.state.close)

    def delta(self, name, rows, table='cnf_patterns_v1'):
        path = self.path/name; empty(path)
        with sqlite3.connect(path) as db:
            db.executemany(f'INSERT INTO {table} VALUES (?,?)', rows)
        db.close()
        return path

    def test_repeated_rows_reuse_checked_nodes_and_keep_cold_results(self):
        first = self.delta('first', self.rows[:1]); second = self.delta('second', self.rows)
        with patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('discovery')):
            self.assertEqual(self.state.merge(first)['appended_rows'], 1)
            before = self.state.h.counts['verified_pattern_nodes']
            self.state.check(lambda h: h._load(self.rows[0][0]))
            self.assertEqual(self.state.h.counts['verified_pattern_nodes'], before)
            self.assertEqual(self.state.merge(second)['appended_rows'], 1)
            self.assertEqual(self.state.merge(second)['appended_rows'], 0)
            self.assertEqual(self.state.h.counts['verified_pattern_nodes'], 2)
            self.assertEqual(check_delta(self.seed, second, OPTIONS)['checked_delta_rows'], 2)
        self.assertFalse(self.state.h.admitted)

    def test_conflicting_old_payload_invalidates_and_preserves_rows(self):
        first = self.delta('first', self.rows[:1]); self.state.merge(first)
        key, payload = self.rows[0]
        bad = self.delta('conflict', [(key, payload+' ')])
        with self.assertRaisesRegex(ValueError, 'Conflicting'):
            self.state.merge(bad)
        with self.assertRaises(ValueError): self.state.handoff()
        self.assertEqual(self.state.h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(key,)).fetchone(), (payload,))

    def test_forged_new_certificate_rolls_back_whole_suffix(self):
        key, payload = self.rows[1]; node = json.loads(payload); node['summary']['closed'] = False
        bad = self.delta('forged', [self.rows[0], (key, json.dumps(node))])
        with self.assertRaises(ValueError): self.state.merge(bad)
        self.assertEqual(self.state.h.db.execute('SELECT count(*) FROM cnf_patterns_v1').fetchone()[0], 0)
        with self.assertRaises(ValueError): self.state.check(lambda h: None)

    def test_unsupported_delta_rows_are_rejected_and_rolled_back(self):
        table = next(t for t in DELTA_TABLES if t not in TABLES)
        bad = self.delta('unsupported', [('x', '{}')], table)
        with self.assertRaisesRegex(ValueError, 'other record types'): self.state.merge(bad)
        self.assertEqual(self.state.h.db.execute(f'SELECT count(*) FROM {table}').fetchone()[0], 0)

    def test_external_writer_invalidates_cached_authority(self):
        first = self.delta('first', self.rows[:1]); self.state.merge(first)
        with sqlite3.connect(self.seed) as db:
            db.execute("UPDATE cnf_patterns_v1 SET payload=payload || ' '")
        db.close()
        with self.assertRaisesRegex(ValueError, 'authority'): self.state.check(lambda h: None)

    def test_direct_same_connection_write_is_not_a_checked_append(self):
        with self.state.h.db:
            self.state.h.db.execute('INSERT INTO cnf_patterns_v1 VALUES (?,?)', self.rows[0])
        with self.assertRaisesRegex(ValueError, 'authority'): self.state.check(lambda h: None)

    def test_policy_and_unfinished_state_invalidate(self):
        self.state.h.prepared.config['max_depth'] += 1
        with self.assertRaisesRegex(ValueError, 'policy'): self.state.check(lambda h: None)
        self.state.close(); self.state = CheckedReplay(self.seed, OPTIONS)
        self.state.h.active.add('unfinished')
        with self.assertRaisesRegex(ValueError, 'Finish'): self.state.handoff()
        self.state.close()

    def test_writing_verification_callback_rolls_back_and_invalidates(self):
        def write(h): h.db.execute('INSERT INTO cnf_patterns_v1 VALUES (?,?)', self.rows[0])
        with self.assertRaisesRegex(ValueError, 'changed replay'): self.state.check(write)
        self.assertEqual(self.state.h.db.execute('SELECT count(*) FROM cnf_patterns_v1').fetchone()[0], 0)
        with self.assertRaises(ValueError): self.state.handoff()

    def test_handoff_transfers_existing_checks_without_closing_verifier(self):
        first = self.delta('first', self.rows[:1]); self.state.merge(first)
        h = self.state.handoff()
        try:
            self.state.close()
            self.assertIn(self.rows[0][0], h.checked)
            self.assertIsNotNone(h._load(self.rows[0][0]))
            with self.assertRaises(ValueError): self.state.handoff()
        finally: h.close()


if __name__ == '__main__': unittest.main()
