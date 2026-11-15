from collections import Counter
import copy
from itertools import permutations, product
import unittest

from experiments.cnf_renaming_invariant import exclusion, profile, verify_exclusion


class RenamingInvariantTests(unittest.TestCase):
    def test_every_two_variable_clause_set_and_signed_bijection(self):
        clauses = [[], [-1], [1], [-2], [2], [-1, -2], [-1, 2], [1, -2], [1, 2]]
        for mask in range(1 << len(clauses)):
            cnf = [c for i, c in enumerate(clauses) if mask & (1 << i)]
            expected = profile(cnf)
            for perm in permutations([7, 31]):
                for signs in product((-1, 1), repeat=2):
                    mapping = {i+1: perm[i]*signs[i] for i in range(2)}
                    other = [[mapping[abs(l)]*(1 if l > 0 else -1) for l in reversed(c)]
                             for c in reversed(cnf)]
                    self.assertEqual(expected, profile(other))
                    self.assertIsNone(exclusion(cnf, other))

    def test_same_shape_can_be_excluded_and_both_inputs_can_be_sat(self):
        left = [[1, 2], [1, 3], [1, 4]]
        right = [[1, 2], [2, 3], [3, 4]]
        counts = Counter(); certificate = exclusion(left, right, counts)
        self.assertEqual(certificate['field'], 'paired_occurrences')
        self.assertTrue(verify_exclusion(left, right, certificate, counts))
        self.assertEqual(counts['renaming_profiles'], 4)
        self.assertEqual(counts['renaming_profile_literal_visits'], 24)
        self.assertEqual(counts['normalization_literal_visits'], 24)

    def test_equal_profiles_are_inconclusive_even_for_nonisomorphic_graphs(self):
        bipartite = [[a, b] for a in (1, 2, 3) for b in (4, 5, 6)]
        prism = [[1, 2], [2, 3], [1, 3], [4, 5], [5, 6], [4, 6], [1, 4], [2, 5], [3, 6]]
        # The prism contains triangles; K3,3 does not. Both have degree 3.
        self.assertEqual(profile(bipartite), profile(prism))
        self.assertIsNone(exclusion(bipartite, prism))

    def test_tampering_and_wrong_source_rejected(self):
        a, b = [[1, 2], [1, 3], [1, 4]], [[1, 2], [2, 3], [3, 4]]
        certificate = exclusion(a, b)
        for field, value in [('format', 'wrong'), ('field', 'variables'), ('left', profile(b))]:
            bad = copy.deepcopy(certificate); bad[field] = value
            with self.assertRaises(ValueError): verify_exclusion(a, b, bad)
        with self.assertRaises(ValueError): verify_exclusion(a, a, certificate)
        with self.assertRaises(ValueError): verify_exclusion(a, b, {**certificate, 'extra': 1})

    def test_normalization_edges_and_invalid_literals(self):
        self.assertEqual(profile([[1, 1], [1], [2, -2]]), profile([[9]]))
        self.assertEqual(profile([[], [1, 2]]), profile([[]]))
        self.assertIsNotNone(exclusion([], [[]]))
        for literal in [0, True, 1.0, '1']:
            with self.assertRaises(ValueError): profile([[literal]])


if __name__ == '__main__':
    unittest.main()
