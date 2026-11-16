from pathlib import Path
from tempfile import TemporaryDirectory
import json,sqlite3,unittest
from unittest.mock import patch
from itertools import product
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_snapshot_replay import SnapshotResidualSolver,audit
from experiments import compare_cnf_clause_witness_reuse as frozen


class SnapshotReplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'proofs'
    def seed(self,formulas):
        solver=ResidualSolver(self.path);records=[]
        try:
            for source in formulas:
                child=solver.solve(source);records.append(dict(source=source,guard=None,witness=None,child=child,answer=child['answer'],model=child['model']))
        finally:solver.close()
        return records
    def test_exhaustive_small_proofs_and_metadata_equal(self):
        clauses=[tuple(sign*(i+1) for i,sign in enumerate(signs) if sign) for signs in product((-1,0,1),repeat=2)]
        records=self.seed([[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(512)])
        before=self.path.read_bytes();plain=ResidualSolver(self.path);snapshot=SnapshotResidualSolver(self.path)
        try:
            for row in records:
                a=plain.solve(row['source']);b=snapshot.solve(row['source'])
                self.assertEqual({k:v for k,v in a.items() if k!='seconds'},{k:v for k,v in b.items() if k!='seconds'})
            self.assertEqual(snapshot.snapshot_censuses,1);self.assertEqual(snapshot.snapshot_reads,512)
        finally:plain.close();snapshot.close()
        self.assertEqual(before,self.path.read_bytes())
        a=frozen.audit(self.path,records);b=audit(self.path,records)
        self.assertEqual({k:v for k,v in a.items() if k!='seconds'},{k:v for k,v in b.items() if k not in ('seconds','snapshot')})
    def test_transaction_and_mutation_attempts_reject(self):
        self.seed([[[1]],[[1],[-1]]]);solver=SnapshotResidualSolver(self.path)
        try:
            for sql in ('COMMIT','ROLLBACK','SAVEPOINT x','END','PRAGMA query_only=OFF',
                        'DELETE FROM cnf_residual_v1','CREATE TEMP TABLE x(a)',"ATTACH ':memory:' AS x"):
                with self.subTest(sql=sql),self.assertRaises(sqlite3.DatabaseError):solver.db.execute(sql)
                self.assertTrue(solver.db.in_transaction);self.assertTrue(solver.solve([[1]])['answer'])
            with self.assertRaises(sqlite3.DatabaseError):solver.db.commit()
            with self.assertRaises(sqlite3.DatabaseError):solver.db.rollback()
        finally:solver.close()
    def test_missing_source_is_not_created(self):
        with self.assertRaises(FileNotFoundError):SnapshotResidualSolver(self.path)
        self.assertFalse(self.path.exists())
    def test_unknown_query_never_searches_or_publishes(self):
        self.seed([]);solver=SnapshotResidualSolver(self.path)
        try:
            with self.assertRaisesRegex(RuntimeError,'Fresh snapshot'):solver.solve([[1]])
            with self.assertRaisesRegex(RuntimeError,'publication'):solver._store('key',{})
            self.assertEqual(solver.archive_storage(),(0,0))
        finally:solver.close()
    def test_wal_writer_does_not_change_pinned_snapshot(self):
        self.seed([[[1]]]);writer=ResidualSolver(self.path);writer.db.execute('PRAGMA journal_mode=WAL')
        reader=SnapshotResidualSolver(self.path)
        try:
            initial=reader.archive_storage();writer.solve([[1],[-1]])
            self.assertEqual(reader.archive_storage(),initial)
            with self.assertRaisesRegex(RuntimeError,'Fresh snapshot'):reader.solve([[1],[-1]])
            self.assertTrue(reader.solve([[1]])['answer'])
        finally:reader.close();writer.close()
        reader=SnapshotResidualSolver(self.path)
        try:self.assertFalse(reader.solve([[1],[-1]])['answer']);self.assertGreater(reader.archive_storage()[0],initial[0])
        finally:reader.close()
    def test_corrupt_unqueried_node_is_still_checked(self):
        records=self.seed([[[1]],[[1],[-1]]]);db=sqlite3.connect(self.path)
        key=records[1]['child']['root'];payload=json.loads(db.execute('SELECT payload FROM cnf_residual_v1 WHERE id=?',(key,)).fetchone()[0])
        payload['format']='corrupt';db.execute('UPDATE cnf_residual_v1 SET payload=? WHERE id=?',(json.dumps(payload),key));db.commit();db.close()
        for checker in (frozen.audit,audit):
            with self.assertRaises(ValueError):checker(self.path,records[:1])
    def test_wrong_answer_and_identity_reject(self):
        records=self.seed([[[1]],[[1],[-1]]])
        for field,value in (('answer',False),('root','foreign'),('model',{1:False})):
            bad=json.loads(json.dumps(records[:1]));bad[0]['child'][field]=value
            for checker in (frozen.audit,audit):
                with self.subTest(field=field),self.assertRaises(ValueError):checker(self.path,bad)
    def test_snapshot_retains_guard_and_witness_checks(self):
        records=self.seed([[[1]]]);records[0]['witness']={'invalid':'witness'}
        with patch.object(frozen,'check_witness',side_effect=ValueError('checked witness')) as verify:
            with self.assertRaisesRegex(ValueError,'checked witness'):audit(self.path,records)
            verify.assert_called_once()
        records[0]['witness']=None;records[0]['guard']={'invalid':'guard'}
        with patch('experiments.cnf_clause_deletion_guard.check_guard',side_effect=ValueError('checked guard')) as verify:
            with self.assertRaisesRegex(ValueError,'checked guard'):audit(self.path,records)
            verify.assert_called_once()


if __name__=='__main__':unittest.main()
