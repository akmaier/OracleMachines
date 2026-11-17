from collections import Counter
from copy import deepcopy
from itertools import product
from unittest.mock import patch
import unittest
from experiments.cnf_binary_probe import select, probe
from experiments.cnf_positive_child import select as previous
from experiments.cnf_residual_dag import ResidualSolver


class BinaryProbeTests(unittest.TestCase):
    def solver(self, **options):
        s = ResidualSolver(**options); self.addCleanup(s.close); return s

    def compare(self, s, source, limit=4):
        old_counts = Counter(); counts = Counter()
        with patch.object(s, '_expand', side_effect=AssertionError('Discovery search')), patch.object(s, '_store', side_effect=AssertionError('Discovery publication')):
            old, old_trace = previous(s, source, limit, old_counts)
            choice, trace = select(s, source, limit, counts)
        self.assertEqual(choice, old)
        adjusted = deepcopy(trace); d = adjusted['discovery']
        if d is not None:
            filtered = d.pop('binary_filter'); expected = deepcopy(old_trace)
            if filtered is not None:
                attempts = expected['discovery']['attempts']
                kept = [a for a in attempts if a['clause'] not in filtered['skipped']]
                self.assertTrue(all(a['screen']['conflict'] is None for a in attempts if a not in kept))
                expected['discovery']['attempts'] = kept
                if expected['discovery']['selected'] is not None:
                    expected['discovery']['selected'] = len(kept)-1
            self.assertEqual(adjusted, expected)
        else: self.assertEqual(adjusted, old_trace)
        self.assertEqual(old_counts['local_premise_probes']-counts['local_premise_probes'], counts['binary_probe_skips'])
        return choice, trace, counts

    def test_nonbinary_unsat_formula_skips_probes_but_does_not_decide_sat(self):
        source = [[i*sign for i, sign in enumerate(bits, 1)] for bits in product((-1, 1), repeat=3)]
        s = self.solver(); choice, trace, counts = self.compare(s, source)
        self.assertIsNone(choice); self.assertEqual(counts['binary_probe_skips'], 6)
        self.assertEqual(counts['local_premise_probes'], 0)
        self.assertEqual(counts['local_baseline_probes'], 1)
        self.assertEqual(trace['discovery']['binary_filter']['variables'], [])
        self.assertEqual(s.archive_storage()[0], 0)
        self.assertFalse(s.solve(source)['answer'])

    def test_propagated_binary_clauses_and_source_coordinate_transport(self):
        source = [[10], [-10, 20, 30], [-10, 20, -30]]
        for raw in (source, [[-7*l for l in c[::-1]] for c in source[::-1]]):
            self.assertTrue(all(len(c) != 2 for c in raw))
            s = self.solver(leaves=False); choice, trace, counts = self.compare(s, raw)
            self.assertEqual(choice['kind'], 'positive-model')
            self.assertIn(counts['local_premise_probes'], (1, 2))
            self.assertEqual(counts['binary_probe_skips'], 0)
            forced = {abs(v) for v, _ in trace['discovery']['fixed']}
            self.assertTrue(all(abs(c[0]) not in forced for c in trace['discovery']['candidates']))

    def test_candidate_budget_does_not_refill_after_skips(self):
        source = [[1], [-1, 10, 11], [-1, 10, -11], [2, 3, 4], [-2, -3, -4]]
        s = self.solver(); choice, trace, counts = self.compare(s, source, 1)
        self.assertEqual(choice['kind'], 'fallback-trace')
        self.assertEqual(trace['discovery']['candidates'], [[-2], [2]])
        self.assertEqual(counts['binary_probe_skips'], 2)
        self.assertEqual(counts['local_premise_probes'], 0)
        _, trace, counts = self.compare(s, source, 4)
        self.assertEqual(trace['proposal']['clause'], [-10])
        self.assertEqual(trace['discovery']['selected'], 0)
        self.assertEqual(counts['binary_probe_skips'], 6)
        self.assertEqual(counts['local_premise_probes'], 1)

    def test_positive_child_route_preserved(self):
        source = [[1, 2], [1, -2], [-1, 3], [-3, 4], [1, 5, 6], [1, -5, -6]]
        choice, _, counts = self.compare(self.solver(), source)
        self.assertEqual(choice['kind'], 'positive-model')
        self.assertEqual(counts['binary_probe_skips'], 0)

    def test_cached_residual_priority_and_known_target(self):
        s = self.solver(); s.solve([[20, 30], [-20, -30]])
        source = [[10], [-10, 20, 30], [-10, -20, -30]]
        choice, trace, counts = self.compare(s, source)
        self.assertEqual(choice['kind'], 'propagated')
        self.assertIsNone(trace['discovery']['binary_filter'])
        self.assertEqual(counts['binary_filter_clause_visits'], 0)
        s.solve(source); self.assertEqual(self.compare(s, source)[1]['reason'], 'known-target')

    def test_limits_native_families_tautologies_and_empty_inputs(self):
        s = self.solver()
        for bad in (-1, True, 1.5):
            with self.assertRaises(ValueError): select(s, [[1]], bad)
            with self.assertRaises(ValueError): probe(s, [[1]], bad)
        for source in ([], [[]], [[1]], [[1], [-1]], [[1, 2], [-1, -2]], [[1, 2, 3], [-1, -2, -3], [4, -4]]):
            self.compare(s, source); self.compare(s, source, 0)

    def test_exhaustive_mixtures_preserve_every_old_selection(self):
        pool = [[1, 2], [1, -2], [-1, 2], [-1, -2], [1, 2, 3], [-1, -2, -3],
                [1, -2, 3], [-1, 2, -3], [1], [-3]]
        skipped = 0
        for mask in range(1024):
            source = [c for i, c in enumerate(pool) if mask >> i & 1]
            for raw in (source, [[-11*l for l in c[::-1]] for c in source[::-1]]):
                s = ResidualSolver()
                try: skipped += self.compare(s, raw)[2]['binary_probe_skips']
                finally: s.close()
        self.assertGreater(skipped, 0)


if __name__ == '__main__': unittest.main()
