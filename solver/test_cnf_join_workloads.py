from collections import Counter
from itertools import product
import unittest
from experiments.cnf_join_workloads import parent_case, check_image
from experiments.cnf_variable_elimination import check_elimination, lift_elimination
from experiments.cnf_residual_dag import holds
from experiments.compare_cnf_bootstrap import CompleteAdmissionInventory, OPTIONS


class JoinWorkloadTests(unittest.TestCase):
    cnf = [[1,2], [-1,2], [1,-2]]

    def test_existential_projection_and_model_lifting_exhaustively(self):
        for variant in range(3):
            case = parent_case(self.cnf, 0, variant)
            for bits in product((False, True), repeat=2):
                original = dict(zip((1,2), bits)); mapped = {10*k:v for k,v in original.items()}
                exists = any(holds(case['source'], {**mapped, case['witness_variable']:v}) for v in (False,True))
                self.assertEqual(exists, holds(self.cnf, original))
                if exists:
                    lifted = lift_elimination(case['source'], {'variable':case['witness_variable']}, mapped, Counter())
                    self.assertTrue(holds(case['source'], lifted))

    def test_all_variants_have_the_exact_same_image_key(self):
        h = CompleteAdmissionInventory(':memory:', **OPTIONS); h.set_admission_budget(0)
        try:
            expected = h._canonical(self.cnf, 0)[2]
            parents = set()
            for variant in range(3):
                case = parent_case(self.cnf, 0, variant)
                self.assertEqual(check_image(h, case['source'], case['witness_variable'], expected), expected)
                parents.add(h._canonical(case['source'], 0)[2])
            self.assertEqual(len(parents), 3)
            self.assertFalse(h.admitted)
        finally:
            h.close()

    def test_deleted_clause_breaks_claimed_image(self):
        h = CompleteAdmissionInventory(':memory:', **OPTIONS); h.set_admission_budget(0)
        try:
            original_key = h._canonical(self.cnf, 0)[2]
            for variant in range(3):
                case = parent_case(self.cnf, 0, variant, edited=True)
                with self.assertRaises(ValueError):
                    check_image(h, case['source'], case['witness_variable'], original_key)
                key = h._canonical(case['expected_image'], 0)[2]
                self.assertEqual(check_image(h, case['source'], case['witness_variable'], key), key)
        finally:
            h.close()

    def test_workload_is_deterministic_and_has_one_opposing_pair(self):
        for edited in (False, True):
            a = parent_case(self.cnf, 0, 1, edited=edited)
            self.assertEqual(a, parent_case(self.cnf, 0, 1, edited=edited))
            counts = Counter()
            check_elimination(a['source'], {'variable':a['witness_variable']}, counts)
            self.assertEqual(counts['elimination_checked_pairs'], 1)


if __name__ == '__main__':
    unittest.main()
