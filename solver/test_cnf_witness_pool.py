from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json,sqlite3,unittest
from experiments.cnf_witness_pool import WitnessPoolSolver
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_residual_dag import FORMAT,normalize,holds
from experiments.cnf_cross_family import truth_table
from experiments.cnf_larger_mixtures import generate,FAMILIES,attempt
from solver.test_cnf_publication_batches import blocking,replay


class WitnessPoolTests(unittest.TestCase):
    def test_automatic_reuse_on_changed_formula(self):
        s=WitnessPoolSolver();self.addCleanup(s.close)
        s.solve([[7],[11]])
        with patch.object(BatchedPublicationSolver,'_expand',side_effect=AssertionError('Fresh solving')):
            r=s.solve([[70,110]])
        self.assertTrue(r['answer']);self.assertEqual(r['metrics']['witness_hits'],1)
        self.assertTrue(holds([[70,110]],r['model']))

    def test_failed_candidates_never_certify_unsat(self):
        s=WitnessPoolSolver(leaves=False);self.addCleanup(s.close);s._admit([True,True])
        r=s.solve(blocking(2));self.assertFalse(r['answer']);self.assertFalse(r['metrics'].get('witness_hits',0))

    def test_candidate_limit_and_capacity(self):
        s=WitnessPoolSolver(pool_capacity=4,candidate_limit=2,max_variables=8);self.addCleanup(s.close)
        for i in range(10):s._admit([bool(i&(1<<j)) for j in range(4)])
        self.assertEqual(len(s.witness_pool),4);self.assertGreater(s.counts['witness_evictions'],0)
        for model in ([True]*9,[1],None):s._admit(model)
        before=len(s.witness_pool)
        with patch.object(BatchedPublicationSolver,'_expand',return_value=({},None)):
            s.counts=Counter();s._expand(tuple(tuple(c) for c in blocking(4)))
        self.assertEqual(s.counts['witness_candidates'],2);self.assertEqual(len(s.witness_pool),before)

    def test_seeded_hints_have_no_proof_authority(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=BatchedPublicationSolver(path);s.close()
            con=sqlite3.connect(path)
            with con:con.execute('INSERT INTO cnf_residual_v1 VALUES (?,?)',('untrusted hint',json.dumps(dict(format=FORMAT,answer=True,model=[True,True]))))
            con.close();s=WitnessPoolSolver(path,leaves=False);self.addCleanup(s.close)
            self.assertEqual(s.witness_setup_counts['witness_seed_rows'],1)
            r=s.solve(blocking(2));self.assertFalse(r['answer']);self.assertFalse(r['metrics'].get('witness_hits',0))

    def test_reopen_reconstructs_bounded_pool(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=WitnessPoolSolver(path)
            try:s.solve([[7],[11]])
            finally:s.close()
            s=WitnessPoolSolver(path,seed_rows=2)
            try:
                self.assertLessEqual(s.witness_setup_counts['witness_seed_rows'],2)
                with patch.object(BatchedPublicationSolver,'_expand',side_effect=AssertionError('Fresh solving')):
                    self.assertTrue(s.solve([[70,110]])['answer'])
            finally:s.close()
            self.assertTrue(replay(path))

    def test_rollback_keeps_only_pure_candidates(self):
        s=WitnessPoolSolver();self.addCleanup(s.close);s.solve([[7],[11]])
        with patch.object(s.db,'_commit',side_effect=sqlite3.OperationalError('Injected')):
            with self.assertRaises(sqlite3.OperationalError):s.solve([[70,110]])
        self.assertFalse(s.db.pending);self.assertFalse(s.db.in_transaction)
        self.assertTrue(s.solve([[70,110]])['answer'])

    def test_small_stream_matches_truth_and_original_models_are_checked(self):
        s=WitnessPoolSolver();self.addCleanup(s.close)
        for family in FAMILIES:
            for source in generate(family,12,1):
                r=s.solve(source);self.assertEqual(r['answer'],truth_table(source)['answer'])
                if r['answer']:self.assertTrue(holds(source,r['model']))
        with self.assertRaises(ValueError):s.solve([[],[True]])

    def test_invalid_limits(self):
        for options in (dict(pool_capacity=0),dict(candidate_limit=65),dict(seed_rows=-1),dict(max_variables=True)):
            with self.assertRaises(ValueError):WitnessPoolSolver(**options)


if __name__=='__main__':unittest.main()
