from collections import Counter
from itertools import product
from unittest.mock import patch
import unittest
from experiments.cnf_trace_fallback import select
from experiments.cnf_propagated_reuse import select as previous_select
from experiments.cnf_partition_screen import publish_screened_branch
from experiments.cnf_residual_dag import ResidualSolver, holds


def forced(core):
    return [[1]] + [[-1] + list(c) for c in core]


PARITY = [[2 * a, 3 * b, 4 * c] for a, b, c in product((-1, 1), repeat=3) if a * b * c == 1]


class TraceFallbackTests(unittest.TestCase):
    def solver(self, **options):
        s = ResidualSolver(**options); self.addCleanup(s.close); return s

    def rows(self, s):
        return dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))

    def compare(self, source, **options):
        native = self.solver(**options); reused = self.solver(**options)
        original = native.solve(source); counts = Counter()
        with patch.object(reused, '_expand', side_effect=AssertionError('Discovery search')), patch.object(reused, '_store', side_effect=AssertionError('Discovery publication')):
            choice, trace = select(reused, source, counts=counts)
        self.assertEqual(choice['kind'], 'fallback-trace')
        result = publish_screened_branch(reused, source, choice['screen'])
        self.assertEqual((original['answer'], original['model']), (result['answer'], result['model']))
        self.assertEqual(self.rows(native), self.rows(reused))
        self.assertEqual(original['metrics']['expanded_nodes'], result['metrics']['expanded_nodes'] + 1)
        self.assertEqual(result['metrics']['screen_trace_publications'], 1)
        self.assertLess(result['metrics'].get('propagation_literal_visits', 0), original['metrics']['propagation_literal_visits'])
        self.assertEqual(counts['fallback_trace_reuses'], 1)
        return trace, result

    def test_unknown_positive_keeps_native_payloads(self):
        trace, result = self.compare(forced(PARITY))
        self.assertEqual(trace['fallback_reason'], 'no-proposal')
        self.assertTrue(result['answer'])

    def test_unknown_negative_keeps_native_payloads(self):
        core = [[2 * a, 3 * b, 4 * c] for a, b, c in product((-1, 1), repeat=3)]
        _, result = self.compare(forced(core)); self.assertFalse(result['answer'])

    def test_native_dependency_and_model_transport(self):
        source = forced(PARITY)
        for transformed in (source, [[-7 * l for l in c[::-1]] for c in source[::-1]]):
            self.compare(transformed, leaves=False, decompose=False)

    def test_rejected_guard_is_not_published(self):
        # Variable 5 is forced only by failed-literal probing; the independent
        # baseline unit prefix is variable 1. Its nonterminal child is rejected.
        core = PARITY + [[-5, 6], [-5, -6]]
        trace, result = self.compare(forced(core), decompose=False)
        self.assertEqual(trace['fallback_reason'], 'nonterminal-child')
        self.assertEqual(trace['proposal']['kind'], 'guard')
        self.assertTrue(result['answer'])

    def test_without_forced_prefix_previous_choice_unchanged(self):
        a = self.solver(); b = self.solver()
        old, old_trace = previous_select(a, PARITY)
        choice, trace = select(b, PARITY)
        self.assertEqual((choice, trace), (old, old_trace))
        self.assertEqual(self.rows(b), {})

    def test_existing_known_family_terminal_and_disabled_choices_preserved(self):
        for source, limit in (([[1]], 4), (forced([[2, 3], [-2, -3]]), 4),
                              (forced(PARITY), 0), ([[1], [-1]], 4)):
            a = self.solver(); b = self.solver()
            self.assertEqual(previous_select(a, source, limit), select(b, source, limit))

    def test_residual_budget_still_refuses_unfinished_search(self):
        s = self.solver(node_limit=0); source = forced(PARITY)
        choice, _ = select(s, source)
        with self.assertRaisesRegex(RuntimeError, 'budget exhausted'):
            publish_screened_branch(s, source, choice['screen'])
        self.assertEqual(self.rows(s), {})

    def test_cold_recheck_and_corrupted_trace(self):
        s = self.solver(); source = forced(PARITY); choice, _ = select(s, source)
        good = choice['screen']; bad = dict(good, trace=[[99, 0]])
        with self.assertRaises(ValueError): publish_screened_branch(s, source, bad)
        self.assertEqual(self.rows(s), {})
        result = publish_screened_branch(s, source, good); s.checked.clear()
        with patch.object(s, '_expand', side_effect=AssertionError('Cold acquisition')):
            checked = s.solve(source)
        self.assertEqual(result['model'], checked['model'])
        self.assertTrue(holds(source, checked['model']))

    def test_exhaustive_three_variable_cores_preserve_native_payloads(self):
        pool = [[2 * a, 3 * b, 4 * c] for a, b, c in product((-1, 1), repeat=3)]
        fallbacks = 0
        for mask in range(256):
            core = [c for i, c in enumerate(pool) if mask >> i & 1]
            expected = any(holds(core, dict(zip((2, 3, 4), bits))) for bits in product((False, True), repeat=3))
            source = forced(core)
            for transformed in (source, [[-7 * l for l in c[::-1]] for c in source[::-1]]):
                native = ResidualSolver(); reused = ResidualSolver()
                try:
                    choice, trace = select(reused, transformed)
                    if choice is None or choice['kind'] != 'fallback-trace':
                        self.assertEqual((choice, trace), previous_select(native, transformed))
                        continue
                    fallbacks += 1
                    original = native.solve(transformed)
                    result = publish_screened_branch(reused, transformed, choice['screen'])
                    self.assertEqual(result['answer'], expected)
                    self.assertEqual(result['model'], original['model'])
                    self.assertEqual(self.rows(native), self.rows(reused))
                    if expected: self.assertTrue(holds(transformed, result['model']))
                finally:
                    native.close(); reused.close()
        self.assertGreater(fallbacks, 0)


if __name__ == '__main__': unittest.main()
