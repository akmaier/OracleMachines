from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,sqlite3,subprocess,sys,unittest
from experiments.cnf_publication_batches import BatchedPublicationSolver,NATIVE,V2,V3
from experiments.cnf_canonical_verify import CanonicalVerifySolver,CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_cross_family import generate,truth_table
from solver.test_cnf_multiblock_equivalence import two_blocks,table
from solver.test_cnf_binary_equivalence import negative


def blocking(n):return [list(c) for c in product(*[(v,-v) for v in range(1,n+1)])]


def replay(path):
    s=CanonicalVerifySnapshot(path)
    try:
        native=table(s,NATIVE);store=MultiEquivalenceStore(s)
        for key in native:assert s._read(key) is not None
        for t in (V2,V3):
            for key in table(s,t):assert store.read(key) is not None
        return native
    finally:s.close()


class PublicationBatchTests(unittest.TestCase):
    def test_limits_require_positive_exact_integers(self):
        for field in ('batch_rows','batch_payload_bytes'):
            for value in (0,-1,True,1.0):
                with self.assertRaises(ValueError):BatchedPublicationSolver(**{field:value})

    def test_success_flushes_dependency_closed_answer_and_matches_control(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';a=CanonicalVerifySolver();b=BatchedPublicationSolver(path,leaves=False)
            try:
                a.leaves=False;x=a.solve(blocking(4));y=b.solve(blocking(4))
                self.assertFalse(y['answer']);self.assertEqual(x['root'],y['root']);self.assertEqual(table(a,NATIVE),table(b,NATIVE))
                self.assertEqual(y['metrics']['batch_commits'],1);self.assertEqual(y['metrics']['batch_committed_records'],4)
                self.assertFalse(b.db.in_transaction);self.assertEqual(b.db.pending,[]);self.assertFalse(b.db.active)
                self.assertEqual(replay(path),table(b,NATIVE))
            finally:a.close();b.close()

    def test_row_limit_commits_only_closed_prefixes(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=BatchedPublicationSolver(path,batch_rows=2,leaves=False);observed=[]
            try:
                s.publication_hook=lambda event,table,key:observed.append(len(replay(path))) if event=='after_commit' else None
                r=s.solve(blocking(5));self.assertEqual(observed,[2,4,5]);self.assertEqual(r['metrics']['batch_commits'],3)
                self.assertLessEqual(r['metrics']['batch_peak_records'],2)
            finally:s.close()

    def test_byte_limit_and_single_oversized_record(self):
        for capacity in (1,800):
            s=BatchedPublicationSolver(batch_rows=32,batch_payload_bytes=capacity,leaves=False);self.addCleanup(s.close);sizes=[]
            def observe(event,table,key):
                if event=='after_insert':
                    self.assertTrue(s.db.payload<=capacity or len(s.db.pending)==1);sizes.append(s.db.payload)
            s.publication_hook=observe;r=s.solve(blocking(5))
            self.assertFalse(r['answer']);self.assertTrue(sizes)
            if capacity==1:self.assertEqual(r['metrics']['batch_oversized_records'],5);self.assertEqual(r['metrics']['batch_commits'],5)

    def test_failed_suffix_invalidates_only_pending_native_checks(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=BatchedPublicationSolver(path,batch_rows=2,leaves=False)
            try:
                saved=s.solve([]);saved_node=s.checked[saved['root']];insertions=0
                def fail(event,table,key):
                    nonlocal insertions
                    if event=='after_insert':
                        insertions+=1
                        if insertions==4:raise RuntimeError('Injected suffix failure')
                s.publication_hook=fail
                with self.assertRaisesRegex(RuntimeError,'suffix failure'):s.solve(blocking(4))
                self.assertEqual(len(table(s,NATIVE)),3);self.assertEqual(len(s.checked),3)
                self.assertIs(s.checked[saved['root']],saved_node);self.assertEqual(s.counts['batch_discarded_checks_records'],2)
                self.assertFalse(s.db.in_transaction);self.assertFalse(s.db.active);self.assertEqual(s.db.pending,[])
                self.assertEqual(replay(path),table(s,NATIVE));s.publication_hook=None
                self.assertFalse(s.solve(blocking(4))['answer'])
            finally:s.close()

    def test_commit_failure_invalidates_native_and_extension_layers(self):
        for source in (negative(),two_blocks(True)):
            with TemporaryDirectory() as td:
                path=Path(td)/'db';s=BatchedPublicationSolver(path)
                try:
                    saved=s.solve([]);before=table(s,NATIVE)
                    with patch.object(s.db,'_commit',side_effect=sqlite3.OperationalError('Injected commit failure')):
                        with self.assertRaises(sqlite3.OperationalError):s.solve(source)
                    self.assertEqual(table(s,NATIVE),before);self.assertEqual(set(s.checked),set(before))
                    for store in (s.equivalences,s.equivalences.old,s.equivalences.old.legacy):self.assertFalse(store.checked)
                    for t in (V2,V3):self.assertEqual(table(s,t),{})
                    self.assertFalse(s.db.in_transaction);self.assertEqual(replay(path),before)
                    self.assertFalse(s.solve(source)['answer'])
                finally:s.close()

    def test_exception_after_commit_preserves_that_prefix(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=BatchedPublicationSolver(path,batch_rows=2,leaves=False)
            try:
                def fail(event,table,key):
                    if event=='after_commit':raise RuntimeError('After durable commit')
                s.publication_hook=fail
                with self.assertRaises(RuntimeError):s.solve(blocking(4))
                self.assertEqual(len(table(s,NATIVE)),2);self.assertEqual(len(replay(path)),2)
                s.publication_hook=None;self.assertFalse(s.solve(blocking(4))['answer'])
            finally:s.close()

    def test_rollback_failure_poisoning_requires_reopen(self):
        s=BatchedPublicationSolver(leaves=False);self.addCleanup(s.close)
        def fail(event,table,key):
            if event=='after_insert':raise RuntimeError('Query failure')
        s.publication_hook=fail
        with patch.object(s.db,'_rollback',side_effect=sqlite3.OperationalError('Rollback uncertain')):
            with self.assertRaises(sqlite3.OperationalError):s.solve(blocking(3))
        self.assertTrue(s.db.poisoned);self.assertFalse(s.db.active);self.assertEqual(s.db.pending,[]);self.assertEqual(s.checked,{})
        with self.assertRaises(RuntimeError):s.solve([[1]])

    def test_existing_transaction_and_untracked_writes_rejected(self):
        s=BatchedPublicationSolver();self.addCleanup(s.close);s.db.execute('BEGIN')
        with self.assertRaises(RuntimeError):s.solve([[1]])
        self.assertTrue(s.db.in_transaction);s.db.rollback();s.db.start()
        try:
            for action in (s.db.commit,s.db.rollback,s.db.close,lambda:s.db.cursor(),lambda:s.db.executemany('SELECT 1',[]),lambda:s.db.executescript('SELECT 1')):
                with self.assertRaises(RuntimeError):action()
            with self.assertRaises(ValueError):s.db.execute('DELETE FROM cnf_residual_v1')
        finally:s.db.abort();s.db.active=False

    def test_duplicate_accounting_and_warm_queries(self):
        s=BatchedPublicationSolver(reuse=False);self.addCleanup(s.close)
        first=s.solve([[1]]);second=s.solve([[1]])
        self.assertEqual(first['archive_nodes'],second['archive_nodes']);self.assertGreater(second['metrics']['batch_ignored_inserts'],0)
        self.assertEqual(s.archive_storage(),(len(table(s,NATIVE)),sum(len(k)+len(v) for k,v in table(s,NATIVE).items())))
        s.reuse=True
        with patch.object(s,'_expand',side_effect=AssertionError('Warm search')):warm=s.solve([[1]])
        self.assertFalse(warm['metrics'].get('batch_commits',0));self.assertFalse(s.db.in_transaction)

    def test_generated_stream_and_extensions_match(self):
        a=CanonicalVerifySolver();b=BatchedPublicationSolver();self.addCleanup(a.close);self.addCleanup(b.close)
        for source in [negative(),two_blocks(True),two_blocks()]+[generate(f,12,i,832) for f in ('random-three','coupled-parity','gated-horn','graph-colouring') for i in (0,1)]:
            x=a.solve(source);y=b.solve(source)
            for key in ('answer','model','root','authority','quotient_choice'):self.assertEqual(x[key],y[key])
            self.assertEqual(y['answer'],truth_table(source)['answer'])
            self.assertEqual(x['metrics'],{k:v for k,v in y['metrics'].items() if not k.startswith('batch_')})
        for t in (NATIVE,V2,V3):self.assertEqual(table(a,t),table(b,t))

    def test_process_death_recovers_committed_prefix(self):
        program='''import os,sys
from experiments.cnf_publication_batches import BatchedPublicationSolver
from solver.test_cnf_publication_batches import blocking
s=BatchedPublicationSolver(sys.argv[1],batch_rows=2,leaves=False)
n=0
def crash(event,table,key):
 global n
 if event=='after_insert':
  n+=1
  if n==int(sys.argv[2]):os._exit(73)
s.publication_hook=crash
s.solve(blocking(4))
raise AssertionError('Crash was not reached')
'''
        for crash_at,expected in ((1,1),(3,3)):
            with TemporaryDirectory() as td:
                path=Path(td)/'db';s=BatchedPublicationSolver(path);saved=s.solve([]);s.close()
                result=subprocess.run([sys.executable,'-c',program,str(path),str(crash_at)],capture_output=True,text=True)
                self.assertEqual(result.returncode,73,result.stderr)
                # A writable reopen permits SQLite's hot-journal recovery before
                # the independently read-only proof audit.
                s=BatchedPublicationSolver(path,leaves=False)
                try:
                    self.assertEqual(len(table(s,NATIVE)),expected);self.assertIn(saved['root'],table(s,NATIVE))
                    self.assertEqual(s.db.execute('PRAGMA integrity_check').fetchone(),('ok',))
                    self.assertFalse(s.solve(blocking(4))['answer'])
                finally:s.close()
                self.assertEqual(len(replay(path)),5)


if __name__=='__main__':unittest.main()
