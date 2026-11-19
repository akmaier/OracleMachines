from unittest.mock import patch
import unittest
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_cross_family import truth_table
from experiments.cnf_residual_dag import holds


class AffineInputTests(unittest.TestCase):
    def test_one_shot_outer_and_inner_iterators_preserve_sat_and_unsat(self):
        # The second CNF has a consistent extracted subsystem but UNSAT coupling.
        for source in ([[10,20,30]],[[1,2],[-1,2],[1,-2],[-1,-2,3],[-3,4],[-3,-4]],[[1],[-1]]):
            s=InputSafeAffineProbeSolver()
            try:
                result=s.solve((iter(c) for c in source))
                self.assertEqual(result['answer'],truth_table(source)['answer'])
                if result['answer']:self.assertTrue(holds(source,result['model']))
                self.assertEqual(result['metrics']['affine_input_snapshot_literals'],sum(map(len,source)))
            finally:s.close()

    def test_snapshot_cost_survives_failed_fallback(self):
        s=InputSafeAffineProbeSolver()
        try:
            with patch.object(s,'_expand',side_effect=RuntimeError('Injected')):
                with self.assertRaises(RuntimeError):s.solve((iter(c) for c in [[1,2,3]]))
            self.assertEqual(s.counts['affine_input_snapshot_literals'],3)
            self.assertFalse(s.db.in_transaction)
        finally:s.close()


if __name__=='__main__':unittest.main()
