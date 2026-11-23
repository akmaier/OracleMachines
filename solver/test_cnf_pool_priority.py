from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sqlite3,unittest
from experiments.cnf_pool_priority import try_pools,witness_candidate
from experiments.cnf_consequence_priority import ConsequencePrioritySolver
from experiments.cnf_witness_pool import WitnessPoolSolver
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_residual_dag import holds
from experiments.cnf_probed_partition import acquire


class PoolPriorityTests(unittest.TestCase):
    def solver(self,**kw):
        s=ConsequencePrioritySolver(**kw);self.addCleanup(s.close);return s

    def probe(self,s,source):
        cnf,names,key=s._canonical(source)
        with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
            route=try_pools(s,cnf,key)
        return route,key,names

    def test_full_negative_core_and_near_edit(self):
        for source in ([[1],[-1],[2,3],[4]],[[1],[-1],[2,-3]]):
            s=self.solver();acquire(s,[[1],[-1],[2,3]],256)['result']
            route,key,_=self.probe(s,source)
            self.assertEqual(route,'negative-pool');self.assertFalse(s._read(key)['answer'])
            self.assertFalse(s.db.active);self.assertFalse(s.db.pending)

    def test_positive_vector_checks_sparse_target(self):
        s=self.solver();s._admit([True,False]);route,key,names=self.probe(s,[[70,-110]])
        self.assertEqual(route,'witness-pool');self.assertTrue(holds([[70,-110]],dict(zip(names,s._read(key)['model']))))

    def test_witness_candidates_match_existing_scan(self):
        clauses=[list(c) for c in product((-1,1),(-2,2))]
        for mask in range(16):
            s=self.solver(candidate_limit=2);s._admit([False,False]);s._admit([True,False]);s._admit([True,True])
            cnf,_,_=s._canonical([cl for i,cl in enumerate(clauses) if mask>>i&1]);s.counts=Counter();model=witness_candidate(s,cnf);counts=dict(s.counts)
            s.counts=Counter()
            with patch.object(BatchedPublicationSolver,'_expand',return_value=(None,None)):
                old,_=WitnessPoolSolver._expand(s,cnf)
            self.assertEqual(model,None if old is None else [old[i+1] for i in range(len(old))]);self.assertEqual(dict(s.counts),counts)

    def test_needed_reason_deletion_misses_and_never_refutes(self):
        s=self.solver();acquire(s,[[1],[-1],[2,3]],256)['result'];route,key,_=self.probe(s,[[1],[2,3]])
        self.assertIsNone(route);self.assertIsNone(s._read(key));self.assertTrue(acquire(s,[[1],[2,3]],256)['result']['answer'])

    def test_false_witness_and_constants_do_not_publish(self):
        s=self.solver();s._admit([True,True])
        for source in ([],[[]],[[-1],[-2]]):
            route,key,_=self.probe(s,source);self.assertIsNone(route);self.assertIsNone(s._read(key))

    def test_stale_negative_origin_not_authority(self):
        s=self.solver();r=acquire(s,[[1],[-1],[2,3]],256)['result'];key=r['root'];s.checked.pop(key,None)
        with s.db:s.db.execute('DELETE FROM cnf_residual_v1 WHERE id=?',(key,))
        route,_,_=self.probe(s,[[1],[-1],[2,-3]])
        self.assertIsNone(route);self.assertGreater(s.counts['negative_stale_origins'],0)

    def test_invalid_key_and_commit_failure_do_not_leave_checked_answer(self):
        s=self.solver();s._admit([True,True]);cnf,_,key=s._canonical([[1,2]])
        with self.assertRaises(ValueError):try_pools(s,cnf,'wrong')
        self.assertFalse(s.db.active);self.assertNotIn('wrong',s.checked)
        with patch.object(s.db,'_commit',side_effect=sqlite3.OperationalError('Injected')):
            with self.assertRaises(sqlite3.OperationalError):try_pools(s,cnf,key)
        self.assertFalse(s.db.active);self.assertFalse(s.db.pending);self.assertIsNone(s._read(key))
        self.assertEqual(try_pools(s,cnf,key),'witness-pool')

    def test_cold_native_replay_with_both_readers(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=ConsequencePrioritySolver(path)
            try:
                acquire(s,[[1],[-1],[2,3]],256)['result'];_,negative,_=self.probe(s,[[1],[-1],[2,-3]])
                s._admit([True,True]);_,positive,_=self.probe(s,[[1,2]])
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                rd=cls(path)
                try:self.assertFalse(rd._read(negative)['answer']);self.assertTrue(rd._read(positive)['answer'])
                finally:rd.close()

    def test_small_stream_matches_exhaustive_truth_on_hits(self):
        s=self.solver();clauses=[[v*sign for v,sign in enumerate(bits,1) if sign] for bits in product((-1,0,1),repeat=2)]
        hits=Counter()
        for mask in range(512):
            source=[cl for i,cl in enumerate(clauses) if mask>>i&1];route,key,names=self.probe(s,source)
            if route is None:acquire(s,source,256)
            else:
                hits[route]+=1;node=s._read(key);truth=any(holds(source,dict(zip((1,2),bits))) for bits in product((False,True),repeat=2))
                self.assertEqual(node['answer'],truth)
                if truth:self.assertTrue(holds(source,dict(zip(names,node['model']))))
        self.assertTrue(hits['negative-pool']);self.assertTrue(hits['witness-pool'])
