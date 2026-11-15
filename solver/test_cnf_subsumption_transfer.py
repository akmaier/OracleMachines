import copy
import itertools
import unittest
from collections import Counter

from experiments.cnf_residual_dag import holds
from experiments.cnf_subsumption_transfer import CoreIndex, check_transfer, lift_transfer


def assignments(source):
    variables = sorted({abs(l) for c in source for l in c})
    return (dict(zip(variables, values)) for values in itertools.product((False, True), repeat=len(variables)))


class SubsumptionTransferTests(unittest.TestCase):
    def test_renamed_redundancies_reuse_with_extra_variables_and_model_lift(self):
        template = [[1], [-1, 2], [1, 3]]
        source = [[20], [-20, 30], [20, 900], [20, -700], [41, -41]]
        index = CoreIndex({'proof': template}); cert = index.lookup(source)
        self.assertIsNotNone(cert)
        self.assertEqual(check_transfer(source, template, 'proof', cert), [(1, 20), (2, 30)])
        for model in assignments(template):
            if holds(template, model):
                self.assertTrue(holds(source, lift_transfer(source, template, 'proof', cert, model)))

    def test_exhaustive_two_variable_inputs_preserve_satisfiability(self):
        clauses = [[], [-1], [1], [-2], [2], [-1, -2], [-1, 2], [1, -2], [1, 2]]
        templates = {'false': [[]], 'true': [], 'unit': [[1]],
                     'binary': [[-1, 2]], 'pair': [[-1, 2], [1, -2]],
                     'units': [[1], [2]], 'contradictory': [[1], [-1]]}
        index = CoreIndex(templates); hits = 0
        for bits in itertools.product((False, True), repeat=len(clauses)):
            source = [c for c, use in zip(clauses, bits) if use]
            cert = index.lookup(source)
            if cert is None:
                continue
            hits += 1; target = templates[cert['target']]
            check_transfer(source, target, cert['target'], cert)
            self.assertEqual(any(holds(source, m) for m in assignments(source)),
                             any(holds(target, m) for m in assignments(target)))
        self.assertGreater(hits, 256)

    def test_changed_clause_or_literal_does_not_inherit_certificate(self):
        template = [[-1, 2], [1, -2]]
        source = template + [[-1, 2, 3]]
        cert = CoreIndex({'p': template}).lookup(source)
        for changed in (source + [[1]], source[1:], [[1, 2], [1, -2], [-1, 2, 3]]):
            with self.assertRaises(ValueError):
                check_transfer(changed, template, 'p', cert)

    def test_signed_subsumption_and_complete_coverage_are_required(self):
        template = [[1], [-1, 2]]; source = template + [[1, 3]]
        cert = CoreIndex({'p': template}).lookup(source)
        for field in ('query_subsumption', 'template_subsumption'):
            bad = copy.deepcopy(cert); bad[field]['kept'].pop()
            with self.assertRaises(ValueError):
                check_transfer(source, template, 'p', bad)
        bad = copy.deepcopy(cert); bad['query_subsumption']['removed'][0][1] = 0
        # The first clause is (-1,2), not a signed subsumer of (1,3).
        with self.assertRaises(ValueError):
            check_transfer(source, template, 'p', bad)

    def test_name_maps_identity_and_model_are_checked(self):
        template = [[1], [-1, 2]]; source = [[10], [-10, 20], [10, 30]]
        cert = CoreIndex({'p': template}).lookup(source)
        for field in ('query_names', 'template_names'):
            bad = copy.deepcopy(cert); bad[field].reverse()
            with self.assertRaises(ValueError):
                check_transfer(source, template, 'p', bad)
        with self.assertRaises(ValueError):
            check_transfer(source, template, 'foreign', cert)
        with self.assertRaises(ValueError):
            lift_transfer(source, template, 'p', cert, {1: False, 2: True})

    def test_value_snapshots_and_misses_do_not_assert_unsatisfiability(self):
        templates = {'p': [[1], [-1, 2]]}; index = CoreIndex(templates)
        templates['p'].append([-1]); cert = index.lookup([[1], [-1, 2]])
        cert['template_subsumption']['kept'].clear()
        self.assertIsNotNone(index.lookup([[1], [-1, 2]]))
        counts = Counter()
        self.assertIsNone(index.lookup([[1, 2]], counts))
        self.assertEqual(counts['core_misses'], 1)

    def test_invalid_literals_rejected_even_after_empty_clause(self):
        index = CoreIndex({'p': [[]]})
        for source in ([[], [0]], [[], [True]], [[], ['1']]):
            with self.assertRaises(ValueError):
                index.lookup(source)


if __name__ == '__main__':
    unittest.main()
