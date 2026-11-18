from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from experiments.cnf_checked_model_reuse import reuse_checked_model
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_residual_dag import normalize,token
from collections import Counter


class CheckedModelReuseTests(unittest.TestCase):
    def test_valid_target_persists_without_expansion(self):
        with TemporaryDirectory() as td:
            path=Path(td)/'db';s=BatchedPublicationSolver(path)
            try:
                s.solve([[7]]);s.node_limit=0
                with patch.object(s,'_expand',side_effect=AssertionError('Fresh search')):
                    result=reuse_checked_model(s,[[7]],[[7,99],[-99]])
                self.assertEqual(result['status'],'sat');self.assertEqual(result['model'],{7:True,99:False})
                self.assertFalse(result['metrics'].get('expanded_nodes',0));self.assertFalse(s.db.in_transaction)
            finally:s.close()
            reader=CanonicalVerifySnapshot(path)
            try:self.assertTrue(reader._read(result['root'])['answer'])
            finally:reader.close()

    def test_original_names_not_canonical_positions_bind_candidate(self):
        s=BatchedPublicationSolver();self.addCleanup(s.close);s.solve([[7]])
        self.assertEqual(reuse_checked_model(s,[[7]],[[2]])['status'],'miss')
        self.assertEqual(reuse_checked_model(s,[[7]],[[-7]])['status'],'miss')

    def test_missing_or_negative_donor_is_only_a_miss(self):
        s=BatchedPublicationSolver();self.addCleanup(s.close)
        for donor in ([[8]],[[]]):
            if donor==[[]]:s.solve(donor)
            result=reuse_checked_model(s,donor,[[9]])
            self.assertEqual(result['status'],'miss');self.assertNotIn('answer',result)

    def test_invalid_targets_validate_even_after_empty_or_tautology(self):
        s=BatchedPublicationSolver();self.addCleanup(s.close);s.solve([[7]])
        for source in ([[],[True]],[[7,-7,1.0]],[[0]]):
            with self.assertRaises(ValueError):reuse_checked_model(s,[[7]],source)

    def test_empty_and_tautological_targets(self):
        s=BatchedPublicationSolver();self.addCleanup(s.close);s.solve([[7]])
        self.assertEqual(reuse_checked_model(s,[[7]],[])['status'],'sat')
        self.assertEqual(reuse_checked_model(s,[[7]],[[99,-99]])['status'],'sat')
        self.assertEqual(reuse_checked_model(s,[[7]],[[]])['status'],'miss')

    def test_rejects_active_publication(self):
        s=BatchedPublicationSolver();self.addCleanup(s.close);s.db.start()
        try:
            with self.assertRaises(RuntimeError):reuse_checked_model(s,[],[])
        finally:s.db.active=False


if __name__=='__main__':unittest.main()
