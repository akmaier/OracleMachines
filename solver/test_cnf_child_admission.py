from collections import Counter
from itertools import product
from unittest.mock import patch
import unittest
from experiments.cnf_child_admission import select
from experiments.cnf_assumption_guard import publish_guard
from experiments.cnf_guard_chain import make_record, check_record
from experiments.cnf_partition_screen import publish_screened_branch
from experiments.cnf_residual_dag import ResidualSolver, holds, restrict


class ChildAdmissionTests(unittest.TestCase):
    def solver(self):
        s = ResidualSolver(); self.addCleanup(s.close); return s

    def evaluate(self, s, source):
        with patch.object(s, '_expand', side_effect=AssertionError('Selection search')), patch.object(s, '_store', side_effect=AssertionError('Selection publication')):
            choice, record = select(s, source)
        guards = []; target = source
        if choice and choice['kind'] == 'guard':
            guard, _, target, _ = publish_guard(s, source, choice); guards.append(guard)
            screen = choice['child']['screen']
            with patch.object(s, '_expand', side_effect=AssertionError('Admitted child search')):
                child = s.solve(target) if screen is None else publish_screened_branch(s, target, screen)
        elif choice:
            child = publish_screened_branch(s, target, choice['screen'])
        else:
            child = s.solve(target)
        result = make_record(s, source, guards, child); check_record(s, result)
        return record, result

    def test_native_families_skip_discovery(self):
        for source in ([[1, 2], [1, -2], [-1, 2], [-1, -2]],
                       [[-1, -2, 3]], [[1, 2, -3]]):
            s = self.solver()
            with patch('experiments.cnf_child_admission.local_probe', side_effect=AssertionError('Family discovery')):
                choice, trace = select(s, source)
            self.assertIsNone(choice); self.assertTrue(trace['reason'].startswith('native-'))
            self.assertEqual(s.archive_storage()[0], 0)

    def test_nonterminal_rejected_without_publication(self):
        s = self.solver(); source = [[1, 2], [1, -2], [3, 4, 5], [-3, -4, -5]]
        choice, trace = select(s, source)
        self.assertIsNone(choice); self.assertEqual(trace['reason'], 'nonterminal-child')
        self.assertEqual(s.archive_storage()[0], 0)

    def test_known_positive_child_and_lift(self):
        s = self.solver(); source = [[1, 2], [1, -2], [3, 4, 5], [-3, -4, -5]]
        s.solve(restrict(source, {1: True}))
        trace, result = self.evaluate(s, source)
        self.assertEqual(trace['reason'], 'known-child'); self.assertTrue(result['answer'])
        self.assertTrue(holds(source, result['model']))

    def test_conflict_child_reuses_trace(self):
        # Neither branch on variable 1 survives, while the unassigned formula
        # has no initial units and is outside the cheap syntactic families.
        source = [[1, 2], [1, -2], [-1, 3], [-1, -3], [4, 5, 6], [-4, -5, -6]]
        s = self.solver(); trace, result = self.evaluate(s, source)
        self.assertEqual(trace['reason'], 'unit-conflict-child'); self.assertFalse(result['answer'])
        self.assertEqual(s.archive_storage()[0], 2)

    def test_limits_and_known_target(self):
        s = self.solver()
        for limit in (-1, True, 1.5):
            with self.assertRaises(ValueError): select(s, [[1]], limit)
        self.assertEqual(select(s, [[1]], 0)[1]['reason'], 'disabled')
        s.solve([[1]]); self.assertEqual(select(s, [[1]])[1]['reason'], 'known-target')

    def test_tautological_source_uses_native_fallback(self):
        s = self.solver()
        source = [[1, 2], [1, -2], [3, 4, 5], [-3, -4, -5], [6, -6]]
        trace, result = self.evaluate(s, source)
        self.assertEqual(trace['reason'], 'tautological-source')
        self.assertTrue(result['answer']); self.assertTrue(holds(source, result['model']))

    def test_exhaustive_guarded_mixtures_and_transports(self):
        clauses = [[i * sign for i, sign in enumerate(signs, 2) if sign] for signs in product((-1, 0, 1), repeat=2)]
        for mask in range(512):
            residual = [c for i, c in enumerate(clauses) if mask >> i & 1]
            source = [[1, 4], [1, -4]] + [[-1] + c for c in residual] + [[5, 6, 7], [-5, -6, -7]]
            expected = any(holds(residual, dict(zip((2, 3), bits))) for bits in product((False, True), repeat=2))
            for transformed in (source, [[-10 * l for l in c[::-1]] for c in source[::-1]]):
                s = ResidualSolver()
                try:
                    _, result = self.evaluate(s, transformed)
                    self.assertEqual(result['answer'], expected)
                    if expected: self.assertTrue(holds(transformed, result['model']))
                finally: s.close()


if __name__ == '__main__': unittest.main()
