from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json, unittest
from experiments.cnf_whole_pool_priority import WholePoolPrioritySolver
from experiments.cnf_whole_proof_reuse import WholeProofReuseSolver
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import holds
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot

CUBE=list(product((-1,1),(-2,2),(-3,3)))


class WholePoolPriorityTests(unittest.TestCase):
    def solver(self, **kwargs):
        s=WholePoolPrioritySolver(leaves=False,node_limit=256,**kwargs)
        self.addCleanup(s.close);return s

    def seed_negative(self,s):
        acquire(s,CUBE,256)
        acquire(s,[(1,),(-1,)],256)
        return CUBE[1:]+[(1,),(-1,)]

    def test_complete_negative_precedes_extraction_even_at_zero_search_budget(self):
        s=self.solver();target=self.seed_negative(s);s.node_limit=0
        with patch('experiments.cnf_whole_pool_priority.extract_partial',side_effect=AssertionError('partial extraction')):
            r=s.solve(target)
        self.assertFalse(r['answer']);self.assertEqual(r['whole_pool']['route'],'negative-pool')
        self.assertEqual(r['metrics'].get('expanded_nodes',0),0)
        self.assertNotIn('whole_plan',r);self.assertFalse(s.db.in_transaction)

    def test_checked_witness_precedes_extraction_and_lifts_sparse_labels(self):
        s=self.solver();s.solve([(1,),(2,),(3,)]);acquire(s,CUBE,256);s.node_limit=0
        target=[[19*x for x in c] for c in CUBE[1:]]
        with patch('experiments.cnf_whole_pool_priority.extract_partial',side_effect=AssertionError('partial extraction')):
            r=s.solve(iter(iter(c) for c in target))
        self.assertTrue(r['answer']);self.assertEqual(r['whole_pool']['route'],'witness-pool')
        self.assertTrue(holds(target,r['model']));self.assertEqual(r['metrics'].get('expanded_nodes',0),0)

    def test_miss_keeps_partial_reuse_and_charges_pool_work(self):
        s=self.solver();acquire(s,CUBE,256);r=s.solve(CUBE[1:])
        self.assertTrue(r['answer']);self.assertEqual(r['metrics']['whole_pool_misses'],1)
        self.assertEqual(r['metrics']['whole_plan_attempts'],1)
        self.assertEqual(r['metrics']['pool_priority_calls'],1)
        self.assertGreater(r['metrics']['negative_clause_tests'],0)

    def test_small_edits_match_exhaustive_truth(self):
        for removed in range(len(CUBE)):
            for extra in ([],[(1,)],[(1,),(-1,)]):
                s=self.solver();acquire(s,CUBE,256)
                target=CUBE[:removed]+CUBE[removed+1:]+extra
                r=s.solve(target)
                truth=any(holds(target,dict(enumerate(bits,1))) for bits in product((False,True),repeat=3))
                self.assertEqual(r['answer'],truth)
                if truth:self.assertTrue(holds(target,r['model']))

    def test_known_and_no_candidate_skip_gate(self):
        s=self.solver()
        with patch('experiments.cnf_whole_pool_priority.try_pools',side_effect=AssertionError('pool gate')):
            first=s.solve([(1,)]);again=s.solve([(1,)])
        self.assertEqual(first['answer'],again['answer'])

    def test_budget_stop_never_publishes_an_incomplete_root(self):
        s=self.solver();acquire(s,CUBE,256);s.node_limit=0
        r=attempt(s,CUBE[1:]);self.assertEqual(r['status'],'unresolved')
        self.assertEqual(r['metrics']['whole_pool_misses'],1)
        self.assertEqual(r['metrics'].get('expanded_nodes',0),0)
        self.assertIsNone(s._read(s._canonical(CUBE[1:])[2]))
        self.assertFalse(s.db.active);self.assertFalse(s.db.in_transaction)
        self.assertIsNone(s._support_plan)

    def test_cold_readers_and_old_solver_accept_complete_hit(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=WholePoolPrioritySolver(path,leaves=False,node_limit=256)
            try:
                target=self.seed_negative(s);r=s.solve(target)
                rows=dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
            finally:s.close()
            for cls in (SnapshotResidualSolver,CanonicalVerifySnapshot):
                reader=cls(path)
                try:
                    for key,payload in rows.items():self.assertEqual(reader._read(key),json.loads(payload))
                finally:reader.close()
            reader=WholeProofReuseSolver(path,leaves=False,node_limit=0)
            try:self.assertEqual(reader.solve(target)['answer'],r['answer'])
            finally:reader.close()


if __name__=='__main__':unittest.main()
