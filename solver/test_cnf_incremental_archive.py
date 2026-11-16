from itertools import product
from pathlib import Path
import sqlite3,tempfile,unittest
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_accounted_residuals import AccountedResidualSolver,CENSUS
from experiments.cnf_incremental_archive import ResidualAppendCursor


def rows(s):return dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))


class IncrementalArchiveTests(unittest.TestCase):
    def make(self,**kwargs):
        s=AccountedResidualSolver(**kwargs);self.addCleanup(s.close);return s
    def test_exhaustive_decisions_metrics_and_exact_deltas(self):
        s=self.make();cursor=ResidualAppendCursor(s);plain=ResidualSolver();self.addCleanup(plain.close);seen={}
        clauses=[tuple(sign*(i+1) for i,sign in enumerate(signs) if sign) for signs in product((-1,0,1),repeat=2)]
        for mask in range(512):
            source=[c for i,c in enumerate(clauses) if mask>>i&1];a=plain.solve(source);b=s.solve(source)
            for field in ('answer','model','root','archive_nodes','archive_payload_bytes'):self.assertEqual(a[field],b[field])
            delta=cursor.take();self.assertFalse(set(delta)&set(seen));seen.update(delta)
            self.assertEqual(seen,rows(s));self.assertEqual(s.archive_storage(),s.db.execute(CENSUS).fetchone())
        self.assertEqual(rows(plain),rows(s));self.assertEqual(s.accounting_censuses,1);self.assertFalse(cursor.take())
    def test_existing_history_and_budget_failure_preserve_completed_prefix(self):
        s=self.make(node_limit=2,leaves=False,reuse=False);s.solve([[1]]);before=rows(s);cursor=ResidualAppendCursor(s)
        with self.assertRaisesRegex(RuntimeError,'no verdict'):s.solve([[1,2],[1,-2],[-1,2],[-1,-2]])
        delta=cursor.take();self.assertEqual({**before,**delta},rows(s));self.assertTrue(delta)
        s.node_limit=100;self.assertFalse(s.solve([[1,2],[1,-2],[-1,2],[-1,-2]])['answer']);cursor.take()
    def test_rollback_savepoints_and_uncommitted_boundaries(self):
        s=self.make();cursor=ResidualAppendCursor(s);s.db.execute('BEGIN');s.db.execute("INSERT INTO cnf_residual_v1 VALUES ('a','abc')")
        with self.assertRaises(ValueError):cursor.take()
        self.assertEqual(s.archive_storage(),(1,4));s.db.rollback();self.assertFalse(cursor.take())
        s.db.execute('SAVEPOINT phase');s.db.execute("INSERT INTO cnf_residual_v1 VALUES ('a','abc')");s.db.execute('ROLLBACK TO phase');s.db.execute('RELEASE phase')
        self.assertFalse(cursor.take())
        with s.db:s.db.execute("INSERT INTO cnf_residual_v1 VALUES ('b','xy')")
        self.assertEqual(cursor.take(),{'b':'xy'});self.assertFalse(cursor.take())
    def test_local_update_delete_replace_and_old_rowid_reject(self):
        s=self.make();s.solve([[1]]);before=rows(s);cursor=ResidualAppendCursor(s)
        commands=["UPDATE cnf_residual_v1 SET payload=payload || ' '","DELETE FROM cnf_residual_v1",
                  "INSERT OR REPLACE INTO cnf_residual_v1 SELECT id,payload FROM cnf_residual_v1",
                  "INSERT INTO cnf_residual_v1(rowid,id,payload) VALUES (0,'late','x')"]
        for sql in commands:
            with self.assertRaises(sqlite3.IntegrityError):
                with s.db:s.db.execute(sql)
            self.assertEqual(rows(s),before);self.assertFalse(cursor.take())
    def test_ignored_duplicate_reconstructs_counts_but_adds_no_delta(self):
        s=self.make();s.solve([[1]]);cursor=ResidualAppendCursor(s)
        with s.db:s.db.execute('INSERT OR IGNORE INTO cnf_residual_v1 SELECT id,payload FROM cnf_residual_v1')
        self.assertFalse(cursor.take());self.assertEqual(s.archive_storage(),s.db.execute(CENSUS).fetchone())
        self.assertEqual(s.accounting_censuses,2)
    def test_sql_text_length_semantics(self):
        s=self.make();cursor=ResidualAppendCursor(s)
        with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[('é','☃'),('a\0b','x\0y')])
        self.assertEqual(len(cursor.take()),2);self.assertEqual(s.archive_storage(),(2,4));self.assertEqual(cursor.stats['delta_payload_units'],4)
    def test_external_commit_and_schema_change_invalidate(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';s=AccountedResidualSolver(path);cursor=ResidualAppendCursor(s);other=ResidualSolver(path)
            try:
                other.solve([[1]])
                with self.assertRaisesRegex(RuntimeError,'external'):cursor.take()
                with self.assertRaisesRegex(RuntimeError,'Invalidated'):cursor.take()
            finally:other.close();s.close()
        s=self.make();cursor=ResidualAppendCursor(s);s.db.execute('CREATE TEMP TABLE unrelated(x)')
        with self.assertRaisesRegex(RuntimeError,'schema'):cursor.take()
    def test_reopen_requires_new_cursor_and_preserves_proof_rows(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'history';s=AccountedResidualSolver(path);cursor=ResidualAppendCursor(s);s.solve([[1],[-1]]);delta=cursor.take();s.close()
            s=AccountedResidualSolver(path)
            try:
                cursor=ResidualAppendCursor(s);self.assertFalse(cursor.take());self.assertEqual(rows(s),delta)
                self.assertFalse(s.solve([[1],[-1]])['answer']);self.assertFalse(cursor.take())
            finally:s.close()


if __name__=='__main__':unittest.main()
