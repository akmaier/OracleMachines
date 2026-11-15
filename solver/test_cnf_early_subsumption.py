import copy
import itertools
import unittest

from experiments.cnf_early_subsumption import discover_family, check_family
from experiments.cnf_pattern_inventory import classify
from experiments.cnf_residual_dag import holds
from collections import Counter


class EarlySubsumptionTests(unittest.TestCase):
    def test_exposes_binary_family_with_extra_variables(self):
        source = [[-1, 2], [1, -2], [-1, 2, 31], [1, -2, -41]]
        cert = discover_family(source)
        self.assertIsNotNone(cert)
        core = check_family(source, cert)
        self.assertTrue(all(len(c) <= 2 for c in core))
        for values in itertools.product((False, True), repeat=4):
            assignment = dict(zip([1, 2, 31, 41], values))
            local = {i: assignment[v] for i, v in enumerate(cert['names'], 1)}
            self.assertEqual(holds(source, assignment), holds(core, local))

    def test_missing_signed_witness_and_names_are_rejected(self):
        source = [[1], [-1, 2], [1, 3]]; cert = discover_family(source)
        bad = copy.deepcopy(cert); bad['subsumption']['removed'].clear()
        with self.assertRaises(ValueError):
            check_family(source, bad)
        bad = copy.deepcopy(cert); bad['names'].reverse()
        with self.assertRaises(ValueError):
            check_family(source, bad)

    def test_family_label_is_checked_instead_of_trusted(self):
        source = [[1, 2], [-1, -2]]; cert = discover_family(source)
        self.assertEqual(classify(check_family(source, cert), 8, Counter())['outcomes']['zero_valid'], 'excluded')
        cert['family'] = 'zero_valid'
        with self.assertRaises(ValueError):
            check_family(source, cert)

    def test_true_and_false_are_coverage_not_same_truth_value(self):
        for source, answer in (([], True), ([[]], False)):
            cert = discover_family(source); core = check_family(source, cert)
            self.assertEqual(holds(core, {}), answer)

    def test_all_three_variable_formulas_with_at_most_two_clauses_check_pointwise(self):
        clauses = [list(c) for c in itertools.product((-1, 0, 1), repeat=3)]
        clauses = [[sign*(i+1) for i, sign in enumerate(c) if sign] for c in clauses]
        for a, b in itertools.combinations_with_replacement(clauses, 2):
            source = [a, b]; cert = discover_family(source)
            if cert is None:
                continue
            core = check_family(source, cert)
            for values in itertools.product((False, True), repeat=3):
                assignment = dict(zip(range(1, 4), values))
                local = {i: assignment[v] for i, v in enumerate(cert['names'], 1)}
                self.assertEqual(holds(source, assignment), holds(core, local))


if __name__ == '__main__':
    unittest.main()
