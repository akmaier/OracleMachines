from collections import Counter
from copy import deepcopy
from itertools import product
from unittest.mock import patch
import unittest
from experiments.cnf_propagated_reuse import select, probe
from experiments.cnf_local_guard import probe as old_probe
from experiments.cnf_assumption_guard import publish_guard
from experiments.cnf_guard_chain import make_record, check_record
from experiments.cnf_partition_screen import publish_screened_branch
from experiments.cnf_residual_dag import ResidualSolver, holds


class PropagatedReuseTests(unittest.TestCase):
    def solver(self, **options):
        s = ResidualSolver(**options); self.addCleanup(s.close); return s

    def execute(self, s, source):
        with patch.object(s, '_expand', side_effect=AssertionError('Selection search')), patch.object(s, '_store', side_effect=AssertionError('Selection publication')):
            choice, record = select(s, source)
        guards = []; target = source
        if choice and choice['kind'] == 'guard':
            g, _, target, _ = publish_guard(s, source, choice); guards.append(g)
            child = s.solve(target) if choice['child']['known'] else publish_screened_branch(s, target, choice['child']['screen'])
        elif choice:
            child = publish_screened_branch(s, target, choice['screen'])
        else: child = s.solve(target)
        result = make_record(s, source, guards, child); check_record(s, result)
        return choice, record, child, result

    def test_cached_positive_lifts_and_publishes_without_expansion(self):
        s = self.solver(); s.solve([[20, 30], [-20, -30]])
        source = [[10], [-10, 20, 30], [-10, -20, -30]]; counts = Counter()
        choice, trace = select(s, source, counts=counts)
        self.assertEqual(trace['reason'], 'known-propagated'); self.assertTrue(choice['exposed']['answer'])
        self.assertEqual(counts['local_premise_probes'], 0)
        with patch.object(s, '_expand', side_effect=AssertionError('Cached child search')):
            child = publish_screened_branch(s, source, choice['screen'])
        self.assertTrue(child['answer']); self.assertTrue(holds(source, child['model']))
        self.assertEqual(child['metrics']['inserted_nodes'], 1)

    def test_cached_negative_uses_checked_dependency(self):
        residual = [[20 * a, 30 * b] for a, b in product((-1, 1), repeat=2)]
        s = self.solver(); old = s.solve(residual); self.assertFalse(old['answer'])
        source = [[10]] + [[-10] + c for c in residual]
        with patch.object(s, '_expand', side_effect=AssertionError('Cached child search')):
            choice, trace, child, result = self.execute(s, source)
        self.assertEqual(trace['reason'], 'known-propagated'); self.assertFalse(result['answer'])
        self.assertEqual(child['metrics']['inserted_nodes'], 1)
        self.assertFalse(choice['exposed']['answer'])

    def test_uncached_family_uses_one_native_leaf(self):
        s = self.solver(); source = [[10], [-10, 20, 30], [-10, -20, -30]]
        choice, trace, child, result = self.execute(s, source)
        self.assertEqual(trace['reason'], 'native-propagated'); self.assertEqual(choice['exposed']['family'], 'two-cnf')
        self.assertTrue(result['answer']); self.assertEqual(child['metrics']['expanded_nodes'], 1)
        self.assertEqual(child['metrics']['inserted_nodes'], 2)
        self.assertEqual(trace['discovery']['attempts'], [])

    def test_uncached_empty_residual(self):
        s = self.solver(); source = [[10], [10, 20, 30], [10, -20, -30]]
        choice, trace, child, result = self.execute(s, source)
        self.assertEqual(choice['exposed']['family'], 'constant'); self.assertTrue(result['answer'])
        self.assertEqual(child['metrics']['expanded_nodes'], 1)

    def test_nonfamily_miss_preserves_ranking_and_probe_trace(self):
        s = self.solver(); source = [[10], [-10, 20, 30, 40], [-10, -20, -30, -40]]
        old, previous = old_probe(s, source); choice, trace = probe(s, source)
        self.assertEqual(choice, old); self.assertIsNone(trace['exposed']['family'])
        self.assertFalse(trace.pop('exposed')['known']); self.assertEqual(trace, previous)
        self.assertEqual(s.archive_storage()[0], 0)

    def test_leaves_disabled_do_not_admit_missing_family(self):
        s = self.solver(leaves=False); source = [[10], [-10, 20, 30], [-10, -20, -30]]
        choice, trace = select(s, source)
        self.assertIsNone(trace['discovery']['exposed']['family']); self.assertIsNone(choice)

    def test_invalid_retained_trace_rejected(self):
        s = self.solver(); source = [[10], [-10, 20, 30], [-10, -20, -30]]
        choice, _ = select(s, source); bad = deepcopy(choice['screen']); bad['trace'][0][0] *= -1
        with self.assertRaises(ValueError): publish_screened_branch(s, source, bad)
        self.assertEqual(s.archive_storage()[0], 0)

    def test_limits_native_priority_and_tautology(self):
        s = self.solver()
        for bad in (-1, True, 1.5):
            with self.assertRaises(ValueError): select(s, [[1]], bad)
        self.assertEqual(select(s, [[1]], 0)[1]['reason'], 'disabled')
        self.assertEqual(select(s, [[1, 2], [-1, -2]])[1]['reason'], 'native-two-cnf')
        source = [[10], [-10, 20, 30], [-10, -20, -30], [40, -40]]
        self.assertEqual(select(s, source)[1]['reason'], 'tautological-source')

    def test_exhaustive_forced_mixtures_and_transports(self):
        clauses = [[i * sign for i, sign in enumerate(signs, 2) if sign] for signs in product((-1, 0, 1), repeat=2)]
        for mask in range(512):
            residual = [c for i, c in enumerate(clauses) if mask >> i & 1]
            source = [[1]] + [[-1] + c for c in residual]
            expected = any(holds(residual, dict(zip((2, 3), bits))) for bits in product((False, True), repeat=2))
            for transformed in (source, [[-10 * l for l in c[::-1]] for c in source[::-1]]):
                s = ResidualSolver()
                try:
                    _, _, _, result = self.execute(s, transformed)
                    self.assertEqual(result['answer'], expected)
                    if expected: self.assertTrue(holds(transformed, result['model']))
                finally: s.close()


if __name__ == '__main__': unittest.main()
