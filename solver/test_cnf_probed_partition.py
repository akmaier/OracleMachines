from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sqlite3,unittest
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_probed_partition import acquire,run
from experiments.cnf_transported_partition import native_query
from experiments.cnf_residual_dag import normalize,holds
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_clause_partition import check_record,PartitionBank

class ProbedPartitionTests(unittest.TestCase):
    def make(self,**kw):
        s=InputSafeAffineProbeSolver(**kw);self.addCleanup(s.close);return s
    def candidate(self,s,source,core=None):
        core=core or [list(c) for c in product((-1,1),(-2,2),(-3,3))]
        root=native_query(s,core,256)['root'];cnf,names=normalize(source)
        return dict(origin=root,origin_names=list(normalize(core)[1]),target=[list(c) for c in cnf],target_names=list(names))
    def test_probe_finishes_without_candidate_preparation(self):
        s=self.make();cnf,names=normalize([[1],[-1]])
        c=dict(target=[list(x) for x in cnf],target_names=names,origin='absent',origin_names=[])
        with patch('experiments.cnf_probed_partition.prepare_support',side_effect=AssertionError('Unnecessary plan')):r=run(s,c,'probe6')
        self.assertEqual(r['route'],'probe');self.assertEqual(r['status'],'unsat');self.assertEqual(r['expanded_nodes'],1)
    def test_six_missing_clauses_partition_lifts_sat(self):
        s=self.make();source=[[-3,-2,-1],[1,2,3]];c=self.candidate(s,source)
        r=run(s,c,'reverse6');self.assertEqual(r['status'],'sat');self.assertEqual(len(r['missing']),6)
        self.assertTrue(holds(source,r['result']['model']));check_record(s,r['partition'])
    def test_seven_missing_clauses_fall_back(self):
        s=self.make();c=self.candidate(s,[[1,2,3]]);r=run(s,c,'reverse6')
        self.assertEqual(r['route'],'fallback');self.assertTrue(r['result']['answer'])
    def test_probe_commits_only_checked_completed_prefix(self):
        source=[[1,2,3],[1,2,-3],[1,-2,3],[1,-2,-3],[-1,4],[-1,5]]
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=InputSafeAffineProbeSolver(path,leaves=False,decompose=False,positive_subsumption=False)
            try:
                r=acquire(s,source,3,retain_stop=True);self.assertIsNone(r['result'])
                self.assertGreater(r['metrics']['probe_retained_pending_records'],0)
                self.assertIsNone(s._read(s._canonical(source)[2]));keys=[k for k, in s.db.execute('SELECT id FROM cnf_residual_v1')];self.assertTrue(keys)
                self.assertFalse(s.db.pending);self.assertFalse(s.db.in_transaction)
            finally:s.close()
            s=CanonicalVerifySnapshot(path)
            try:
                for key in keys:self.assertIsNotNone(s._read(key))
            finally:s.close()
    def test_commit_failure_rolls_back_and_recovers(self):
        s=self.make(leaves=False,decompose=False,positive_subsumption=False);source=[[1,2,3],[1,2,-3],[1,-2,3],[1,-2,-3],[-1,4],[-1,5]]
        with patch.object(s.db,'_commit',side_effect=sqlite3.OperationalError('Injected')):
            with self.assertRaises(sqlite3.OperationalError):acquire(s,source,3,retain_stop=True)
        self.assertFalse(s.db.active);self.assertFalse(s.db.pending);self.assertEqual(s.archive_storage()[0],0)
        self.assertTrue(acquire(s,source,256)['result']['answer'])
    def test_unexpected_error_does_not_commit_pending_prefix(self):
        s=self.make();original=s._store
        def broken(key,node):original(key,node);raise ValueError('Injected after checked store')
        with patch.object(s,'_store',side_effect=broken):
            with self.assertRaises(ValueError):acquire(s,[[1]],8,retain_stop=True)
        self.assertEqual(s.archive_storage()[0],0);self.assertFalse(s.db.active)
    def test_shared_budget_includes_probe_and_fallback(self):
        s=self.make(leaves=False,decompose=False,positive_subsumption=False)
        source=[list(c) for c in product(*[(-i,i) for i in range(1,12)])];cnf,names=normalize(source)
        c=dict(target=[list(x) for x in cnf],target_names=names)
        r=run(s,c,'probe-native',10);self.assertEqual(r['expanded_nodes'],10);self.assertIsNone(r['result'])
        self.assertEqual(r['probe']['metrics']['expanded_nodes'],8);self.assertEqual(r['branches'][0]['metrics']['expanded_nodes'],2)
    def test_zero_invalid_budget_and_iterables(self):
        s=self.make();r=acquire(s,iter(iter(c) for c in [[1],[-1,2]]),8);self.assertTrue(holds([[1],[-1,2]],r['result']['model']))
        cnf,names=normalize([[-1]]);r=run(s,dict(target=[list(c) for c in cnf],target_names=names),'probe6',0)
        self.assertIsNone(r['result']);self.assertEqual(r['route'],'probe-stop')
        for budget in (True,-1,1.5):
            with self.assertRaises(ValueError):run(s,{},'probe6',budget)
    def test_cold_partition_without_probe_or_search(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=InputSafeAffineProbeSolver(path);source=[[-3,-2,-1],[1,2,3]]
            try:c=self.candidate(s,source);r=run(s,c,'reverse6')
            finally:s.close()
            s=CanonicalVerifySnapshot(path)
            try:self.assertTrue(PartitionBank(s,[r['partition']]).lookup(source)['answer'])
            finally:s.close()
    def test_exhaustive_two_variable_inputs(self):
        clauses=[[i*sign for i,sign in enumerate(bits,1) if sign] for bits in product((-1,0,1),repeat=2)]
        s=self.make()
        for mask in range(512):
            source=[c for i,c in enumerate(clauses) if mask>>i&1];cnf,names=normalize(source)
            c=dict(target=[list(x) for x in cnf],target_names=names)
            r=run(s,c,'probe6');expected=any(holds(source,dict(zip((1,2),bits))) for bits in product((False,True),repeat=2))
            self.assertEqual(r['result']['answer'],expected)
            if expected:self.assertTrue(holds(source,r['result']['model']))

if __name__=='__main__':unittest.main()
