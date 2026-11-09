"""Exact accounting under cold reuse, legacy writers and SQL conflict policies."""
import hashlib
import itertools
from pathlib import Path
import sqlite3
import tempfile
import unittest

from experiments.cnf_accounted_residuals import AccountedResidualSolver, CENSUS, TABLE
from experiments.cnf_residual_dag import ResidualSolver


class AccountedResidualTests(unittest.TestCase):
    def assert_census(self, solver):
        self.assertEqual(solver.archive_storage(), solver.db.execute(CENSUS).fetchone())

    def test_exhaustive_small_results_and_unchanged_proofs(self):
        clauses = [tuple(s * (i + 1) for i, s in enumerate(p) if s)
                   for p in itertools.product((-1, 0, 1), repeat=2)]
        baseline, candidate = ResidualSolver(), AccountedResidualSolver()
        try:
            for mask in range(1 << len(clauses)):
                cnf = [c for i, c in enumerate(clauses) if mask >> i & 1]
                a, b = baseline.solve(cnf), candidate.solve(cnf)
                for field in ('answer', 'model', 'root', 'archive_nodes', 'archive_payload_bytes'):
                    self.assertEqual(a[field], b[field])
                self.assertEqual(a['metrics'], {k: v for k, v in b['metrics'].items()
                                               if not k.startswith('accounting_')})
            self.assertEqual(candidate.accounting_censuses, 1)
            self.assertEqual(baseline.db.execute('SELECT * FROM cnf_residual_v1 ORDER BY id').fetchall(),
                             candidate.db.execute('SELECT * FROM cnf_residual_v1 ORDER BY id').fetchall())
        finally:
            baseline.close(); candidate.close()

    def test_two_connections_old_writer_and_unrelated_commits(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'history.db'
            old = ResidualSolver(path)
            old.solve([(1,), (-1,)])
            candidate = AccountedResidualSolver(path)
            try:
                old.solve([(1, 2, 3), (-1, -2, -3)])
                self.assert_census(candidate)
                candidate.solve([(1,)])
                self.assertEqual(old.archive_storage(), candidate.archive_storage())
                with old.db:
                    old.db.execute('CREATE TABLE unrelated (x)')
                    old.db.execute('INSERT INTO unrelated VALUES (1)')
                self.assert_census(candidate)
                self.assertEqual(candidate.accounting_censuses, 1)
                with old.db:
                    old.db.execute("UPDATE cnf_residual_v1 SET payload=payload || ' '")
                self.assert_census(candidate)
                with old.db:
                    old.db.execute('DELETE FROM cnf_residual_v1')
                self.assertEqual(candidate.archive_storage(), (0, 0))
                self.assertEqual(candidate.accounting_censuses, 1)
            finally:
                old.close(); candidate.close()

    def test_conflicts_replace_and_rollback_with_both_recursive_modes(self):
        for recursive in (0, 1):
            s = AccountedResidualSolver()
            try:
                s.db.execute(f'PRAGMA recursive_triggers={recursive}')
                with s.db:
                    s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', [('a', 'one'), ('b', 'two')])
                for statement in (
                    "INSERT OR IGNORE INTO cnf_residual_v1 VALUES ('a','ignored')",
                    "INSERT OR REPLACE INTO cnf_residual_v1 VALUES ('a','replacement')",
                    "UPDATE OR IGNORE cnf_residual_v1 SET id='a' WHERE id='b'",
                    "UPDATE OR REPLACE cnf_residual_v1 SET id='a' WHERE id='b'",
                    "INSERT OR REPLACE INTO cnf_residual_v1(rowid,id,payload) SELECT rowid,'c','r' FROM cnf_residual_v1 LIMIT 1",
                    "INSERT INTO cnf_residual_v1 VALUES ('d','four')",
                    "UPDATE OR REPLACE cnf_residual_v1 SET rowid=(SELECT rowid FROM cnf_residual_v1 WHERE id='c') WHERE id='d'",
                    "INSERT INTO cnf_residual_v1 VALUES ('d','upsert') ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                ):
                    with s.db:
                        s.db.execute(statement)
                    self.assert_census(s)
                before = s.archive_storage()
                s.db.execute('BEGIN')
                s.db.execute("INSERT OR REPLACE INTO cnf_residual_v1 VALUES ('d','temporary')")
                self.assert_census(s)
                self.assertTrue(s.db.in_transaction)  # No premature commit by reconstruction.
                s.db.rollback()
                self.assertEqual(s.archive_storage(), before)
                s.db.execute('BEGIN')
                s.db.execute('DELETE FROM cnf_residual_v1')
                self.assertEqual(s.archive_storage(), (0, 0))
                s.db.rollback()
                self.assertEqual(s.archive_storage(), before)
            finally:
                s.close()

    def test_sql_length_semantics_null_keys_unicode_and_nul(self):
        s = AccountedResidualSolver()
        try:
            with s.db:
                s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',
                                 [('é', '☃'), ('nul\x00key', 'p\x00q'), (None, 'ignored by sum')])
            self.assertEqual(s.archive_storage(), (3, 6))
            self.assert_census(s)
            with s.db:
                s.db.execute('UPDATE cnf_residual_v1 SET id=? WHERE id IS NULL', ('new',))
            self.assert_census(s)
        finally:
            s.close()

    def test_cold_reconstruction_preservation_and_repair(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'history.db'
            s = ResidualSolver(path); result = s.solve([(1,), (-1,)])
            rows = s.db.execute('SELECT * FROM cnf_residual_v1').fetchall(); s.close()
            s = AccountedResidualSolver(path)
            self.assertEqual(rows, s.db.execute('SELECT * FROM cnf_residual_v1').fetchall())
            self.assert_census(s); s.close()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            s = AccountedResidualSolver(path)
            cold = s.solve([(1,), (-1,)])
            self.assertEqual(result['root'], cold['root'])
            self.assertEqual(s.accounting_censuses, 1); s.close()
            self.assertEqual(digest, hashlib.sha256(path.read_bytes()).hexdigest())
            db = sqlite3.connect(path)
            with db:
                db.execute(f'UPDATE {TABLE} SET nodes=-999,payload_units=-1')
            db.close()
            s = AccountedResidualSolver(path)
            self.assert_census(s); s.close()

    def test_budget_failure_keeps_completed_work_and_exact_accounting(self):
        s = AccountedResidualSolver(node_limit=2, leaves=False, reuse=False)
        try:
            # All assignments are excluded: one child commits before the
            # second child reaches the expansion limit. Reuse is disabled here:
            # both conditioned children otherwise have the same canonical key.
            cnf = [(1, 2), (1, -2), (-1, 2), (-1, -2)]
            with self.assertRaisesRegex(RuntimeError, 'no verdict'):
                s.solve(cnf)
            self.assertGreater(s.archive_storage()[0], 0)
            self.assert_census(s)
            s.node_limit = 100
            self.assertFalse(s.solve(cnf)['answer'])
            self.assert_census(s)
        finally:
            s.close()

    def test_rejects_changed_accounting_trigger(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'history.db'
            s = AccountedResidualSolver(path); s.close()
            db = sqlite3.connect(path)
            with db:
                db.execute(f'DROP TRIGGER {TABLE}_delete')
                db.execute(f'CREATE TRIGGER {TABLE}_delete AFTER DELETE ON cnf_residual_v1 BEGIN SELECT 1; END')
            db.close()
            with self.assertRaisesRegex(ValueError, 'Unrecognized'):
                AccountedResidualSolver(path)


if __name__ == '__main__':
    unittest.main()
