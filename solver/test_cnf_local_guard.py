from collections import Counter
from itertools import product
import unittest
from unittest.mock import patch
from experiments.cnf_local_guard import probe
from experiments.cnf_assumption_guard import publish_guard
from experiments.cnf_guard_chain import make_record, check_record
from experiments.cnf_partition_screen import publish_screened_branch
from experiments.cnf_residual_dag import ResidualSolver, holds, propagate


class LocalGuardTests(unittest.TestCase):
    def solver(self):
        s = ResidualSolver(); self.addCleanup(s.close); return s

    def test_ranking_excludes_units_and_transports_names(self):
        s = self.solver(); source = [[10], [20, 30], [20, -30]]; counts = Counter()
        with patch.object(s, '_expand', side_effect=AssertionError('Probe search')), patch.object(s, '_store', side_effect=AssertionError('Probe publication')):
            choice, trace = probe(s, source, 1, counts)
        self.assertEqual(trace['fixed'], [[10, True]])
        self.assertEqual(trace['candidates'], [[-20], [20]])
        self.assertEqual(choice['clause'], [-20]); self.assertEqual(len(trace['attempts']), 1)
        self.assertEqual(s.archive_storage()[0], 0)
        guard, _, child_source, _ = publish_guard(s, source, choice)
        record = make_record(s, source, [guard], s.solve(child_source))
        self.assertTrue(record['answer']); self.assertTrue(holds(source, record['model']))

    def test_terminal_avoids_ranking_and_premise_probes(self):
        s = self.solver(); counts = Counter(); choice, trace = probe(s, [[1], [-1]], counts=counts)
        self.assertEqual(choice['kind'], 'terminal')
        self.assertEqual(trace['ranks'], []); self.assertEqual(trace['attempts'], [])
        self.assertEqual(counts['local_premise_probes'], 0)

    def test_shared_baseline_is_propagated_once(self):
        s = self.solver(); source = [[1], [2, 3]]; counts = Counter()
        choice, trace = probe(s, source, 1, counts)
        self.assertIsNone(choice); self.assertEqual(len(trace['attempts']), 2)
        expected = Counter(); propagate(s._canonical(source)[0], expected)
        for row in trace['attempts']:
            propagate(s._canonical(source + [row['clause']])[0], expected)
        self.assertEqual(counts['propagation_literal_visits'], expected['propagation_literal_visits'])

    def test_bounds_and_empty_sources(self):
        s = self.solver()
        for bad in (-1, True, 1.5):
            with self.assertRaises(ValueError): probe(s, [[1]], bad)
        self.assertIsNone(probe(s, [[1]], 0)[0])
        choice, trace = probe(s, [], 4)
        self.assertIsNone(choice); self.assertEqual(trace['candidates'], [])
        self.assertEqual(probe(s, [[]], 4)[0]['kind'], 'terminal')

    def test_exhaustive_truth_with_both_polarities_and_edits(self):
        clauses = [[i * sign for i, sign in enumerate(signs, 1) if sign] for signs in product((-1, 0, 1), repeat=2)]
        for mask in range(1 << len(clauses)):
            source = [c for i, c in enumerate(clauses) if mask >> i & 1]
            expected = any(holds(source, dict(zip((1, 2), bits))) for bits in product((False, True), repeat=2))
            for transformed in (source, [[-l * 10 for l in c[::-1]] for c in source[::-1]]):
                s = ResidualSolver()
                try:
                    choice, _ = probe(s, transformed, 2); guards = []
                    if choice is None: child = s.solve(transformed)
                    elif choice['kind'] == 'terminal': child = publish_screened_branch(s, transformed, choice['screen'])
                    else:
                        guard, _, target, _ = publish_guard(s, transformed, choice); guards.append(guard); child = s.solve(target)
                    record = make_record(s, transformed, guards, child); check_record(s, record)
                    self.assertEqual(record['answer'], expected)
                    if expected: self.assertTrue(holds(transformed, record['model']))
                finally: s.close()


if __name__ == '__main__': unittest.main()
