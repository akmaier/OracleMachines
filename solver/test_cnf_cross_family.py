from itertools import product
import unittest
from experiments.cnf_cross_family import FAMILIES, SIZES, generate, truth_table


class CrossFamilyTests(unittest.TestCase):
    def test_truth_table_exhaustive_small_formulas(self):
        pool = [[], [1], [-1], [2, 3], [-2, 3], [2, -3], [-2, -3], [1, -1]]
        for mask in range(256):
            source = [c for i, c in enumerate(pool) if mask >> i & 1]
            names = sorted({abs(l) for c in source for l in c})
            expected = sum(all(any(dict(zip(names, bits))[abs(l)] == (l > 0) for l in c) for c in source)
                           for bits in product((False, True), repeat=len(names)))
            result = truth_table(source)
            self.assertEqual(result['satisfying_assignments'], expected)
            self.assertEqual(result['answer'], bool(expected))

    def test_truth_budget_and_invalid_literals(self):
        for source in ([[0]], [[True]], [['1']]):
            with self.assertRaises(ValueError): truth_table(source)
        with self.assertRaises(ValueError): truth_table([[1, 2, 3]], max_variables=2)
        self.assertTrue(truth_table([])['answer'])
        self.assertFalse(truth_table([[]])['answer'])

    def test_deterministic_valid_unlabelled_inputs(self):
        for family in FAMILIES:
            for size in SIZES:
                for sample in range(4):
                    source = generate(family, size, sample)
                    self.assertEqual(source, generate(family, size, sample))
                    self.assertNotEqual(source, generate(family, size, sample, 1))
                    self.assertTrue(all(type(l) is int and l != 0 for c in source for l in c))
                    self.assertTrue(all(len({abs(l) for l in c}) == len(c) for c in source))
        with self.assertRaises(ValueError): generate('unknown', 12, 0)

    def test_gated_family_has_two_certifiable_restrictions(self):
        for size in SIZES:
            for sample in range(4):
                source = generate('gated-horn', size, sample)
                names = {abs(l) for c in source for l in c}
                gates = []
                for variable in names:
                    residuals = [[[l for l in c if abs(l) != variable] for c in source
                                  if not any(abs(l) == variable and (l > 0) == bit for l in c)]
                                 for bit in (False, True)]
                    if (all(sum(l > 0 for l in c) <= 1 for c in residuals[0]) and
                        all(sum(l < 0 for l in c) <= 1 for c in residuals[1])):
                        gates.append(variable)
                self.assertTrue(gates)


if __name__ == '__main__': unittest.main()
