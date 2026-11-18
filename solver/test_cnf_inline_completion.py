from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from experiments.cnf_inline_completion import select
from experiments.cnf_uniform_premise import select as late_select
from experiments.cnf_binary_probe import select as binary_select
from experiments.cnf_positive_child import publish_model
from experiments.cnf_residual_dag import ResidualSolver, holds, restrict

SOURCE = [[1, 2], [-1, -2], [1, 3, 4], [-1, -3, -4]]


class InlineCompletionTests(unittest.TestCase):
    def solver(self, **options):
        s = ResidualSolver(**options); self.addCleanup(s.close); return s

    def test_first_model_stops_without_evaluating_candidate_suffix(self):
        s = self.solver(node_limit=0); counts = Counter()
        with patch.object(s, '_expand', side_effect=AssertionError('Search')), patch.object(s, '_store', side_effect=AssertionError('Publication')):
            choice, trace = select(s, SOURCE, counts=counts)
        self.assertEqual(trace['reason'], 'inline-positive-model')
        self.assertEqual(counts['local_premise_probes'], 1)
        self.assertEqual(len(trace['discovery']['attempts']), 1)
        self.assertEqual(len(trace['discovery']['candidates']), 8)
        self.assertEqual(trace['discovery']['positive_selected'], 0)
        self.assertEqual(trace['discovery']['binary_filter']['skipped'], [])
        late_counts = Counter(); late, _ = late_select(self.solver(), SOURCE, counts=late_counts)
        self.assertEqual(choice, late); self.assertEqual(late_counts['local_premise_probes'], 4)
        with patch.object(s, '_visit', side_effect=AssertionError('Acquisition')):
            result = publish_model(s, SOURCE, choice)
        self.assertTrue(holds(SOURCE, result['model']))
        self.assertEqual(result['metrics']['inserted_nodes'], 1)

    def test_positive_terminal_and_nonterminal_models(self):
        for raw in (SOURCE, [[1, 2], [-1, -2], [1, 2, 3], [-1, -2, -3]]):
            s = self.solver(); choice, trace = select(s, raw)
            self.assertEqual(trace['reason'], 'inline-positive-model')
            self.assertTrue(holds(raw, publish_model(s, raw, choice)['model']))

    def test_positive_witness_can_preempt_a_later_guard(self):
        source = [[-1, 2], [-1, -2], [1, 3], [-3, 4], [1, 5, -6], [1, -5, 6]]
        a = self.solver(); b = self.solver()
        for s in (a, b): s.solve(restrict(source, {1: False}))
        late, trace = late_select(a, source)
        self.assertEqual(late['kind'], 'guard'); self.assertEqual(trace['reason'], 'known-child')
        choice, trace = select(b, source)
        self.assertEqual(trace['reason'], 'inline-positive-model')
        self.assertIsNone(trace['child']); self.assertEqual(len(trace['discovery']['attempts']), 1)
        self.assertTrue(holds(source, publish_model(b, source, choice)['model']))

    def test_negative_guard_and_positive_child_path_preserved(self):
        source = [[1, 2], [1, -2], [-1, 3], [-3, 4], [1, 5, 6], [1, -5, -6]]
        s = self.solver(); choice, trace = select(s, source)
        self.assertEqual(trace['reason'], 'positive-child-model')
        self.assertEqual(trace['discovery']['selected'], 0)
        self.assertEqual(trace['discovery']['completions'], [])
        self.assertTrue(holds(source, publish_model(s, source, choice)['model']))

    def test_budget_filter_and_known_inputs(self):
        source = [[1], [-1, 10, 11], [-1, 10, -11], [2, 3, 4], [-2, -3, -4]]
        s = self.solver(leaves=False); c, t = select(s, source, 1)
        self.assertEqual(c['kind'], 'fallback-trace')
        self.assertEqual(t['discovery']['candidates'], [[-2], [2]])
        self.assertEqual(t['discovery']['binary_filter']['skipped'], [[-2], [2]])
        self.assertEqual(t['discovery']['attempts'], [])
        for source in ([], [[]], [[1]], [[1], [-1]], [[1, 2, 3], [1, -2, -3]]):
            a = self.solver(); b = self.solver()
            got = select(a, source); old = binary_select(b, source)
            if got[1]['discovery'] is not None:
                got[1]['discovery'].pop('completions'); got[1]['discovery'].pop('positive_selected')
            self.assertEqual(got, old)
        for cap in (-1, True, 1.5):
            with self.assertRaises(ValueError): select(s, SOURCE, cap)
        self.assertEqual(select(s, SOURCE, 0)[1]['reason'], 'disabled')

    def test_source_model_verification_is_required(self):
        s = self.solver()
        with patch('experiments.cnf_inline_completion.holds', return_value=False):
            with self.assertRaises(ValueError): select(s, SOURCE)
        self.assertEqual(s.archive_storage()[0], 0)
        choice, _ = select(s, SOURCE); choice['model'][0][1] = True
        with self.assertRaises(ValueError): publish_model(s, SOURCE, choice)
        self.assertEqual(s.archive_storage()[0], 0)

    def test_baseline_prefix_and_persistence_with_transport(self):
        source = [[10]] + [[-10] + c for c in SOURCE]
        for raw in (source, [[-7*l for l in c[::-1]] for c in source[::-1]]):
            with TemporaryDirectory() as td:
                path = Path(td)/'proofs'; s = ResidualSolver(path, leaves=False, node_limit=0)
                try:
                    counts = Counter(); choice, trace = select(s, raw, counts=counts)
                    self.assertEqual(trace['reason'], 'inline-positive-model')
                    self.assertEqual(counts['fallback_trace_reuses'], 0)
                    result = publish_model(s, raw, choice)
                finally: s.close()
                s = ResidualSolver(path)
                try:
                    s.db.execute('PRAGMA query_only=ON')
                    with patch.object(s, '_expand', side_effect=AssertionError('Cold search')), patch.object(s, '_store', side_effect=AssertionError('Cold publication')):
                        self.assertEqual(s.solve(raw)['model'], result['model'])
                        self.assertEqual(select(s, raw)[1]['reason'], 'known-target')
                finally: s.close()

    def test_exhaustive_small_sources_and_transports(self):
        pool = [[1, 2], [-1, -2], [1, 3, 4], [-1, -3, -4], [3, 4], [-3, -4], [1, 3, -4], [-1, -3, 4], [1], [-1]]
        successes = 0
        for mask in range(1024):
            source = [c for i, c in enumerate(pool) if mask >> i & 1]
            truth = any(all(any(bits[abs(l)-1] == (l > 0) for l in c) for c in source) for bits in product((False, True), repeat=4))
            for raw in (source, [[-7*l for l in c[::-1]] for c in source[::-1]]):
                s = ResidualSolver(); other = ResidualSolver()
                try:
                    choice, trace = select(s, raw)
                    if trace['reason'] == 'inline-positive-model':
                        successes += 1; self.assertTrue(truth)
                        self.assertTrue(holds(raw, publish_model(s, raw, choice)['model']))
                        d = trace['discovery']; self.assertEqual(d['positive_selected'], len(d['attempts'])-1)
                        self.assertIsNone(d['selected'])
                    else:
                        trace = deepcopy(trace)
                        if trace['discovery'] is not None:
                            trace['discovery'].pop('completions'); trace['discovery'].pop('positive_selected')
                        self.assertEqual((choice, trace), binary_select(other, raw))
                finally: s.close(); other.close()
        self.assertGreater(successes, 0)


if __name__ == '__main__': unittest.main()
