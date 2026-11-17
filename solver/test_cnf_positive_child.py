from copy import deepcopy
from itertools import product
from unittest.mock import patch
import unittest
from experiments.cnf_positive_child import select, recover_model, publish_model
from experiments.cnf_trace_fallback import select as previous_select
from experiments.cnf_residual_dag import ResidualSolver, holds


SOURCE = [[1, 2], [1, -2], [-1, 3], [-3, 4], [1, 5, 6], [1, -5, -6]]


class PositiveChildTests(unittest.TestCase):
    def solver(self, **options):
        s = ResidualSolver(**options); self.addCleanup(s.close); return s

    def test_direct_target_publication_without_premise_or_child_acquisition(self):
        s = self.solver()
        with patch.object(s, '_expand', side_effect=AssertionError('Discovery search')), patch.object(s, '_store', side_effect=AssertionError('Discovery publication')):
            choice, trace = select(s, SOURCE)
        self.assertEqual(trace['reason'], 'positive-child-model')
        self.assertEqual(choice['kind'], 'positive-model')
        self.assertGreater(len(trace['child']['screen']['trace']), 0)
        with patch.object(s, '_visit', side_effect=AssertionError('Child acquisition')):
            result = publish_model(s, SOURCE, choice)
        self.assertTrue(holds(SOURCE, result['model']))
        self.assertEqual(result['metrics']['inserted_nodes'], 1)
        self.assertEqual(result['metrics']['positive_model_publications'], 1)
        self.assertEqual(result['metrics'].get('expanded_nodes', 0), 0)
        self.assertEqual(result['archive_nodes'], 1)

    def test_empty_child_and_unassigned_variables(self):
        source = [[1, 2], [1, -2], [1, 3, 4], [1, -3, -4]]
        s = self.solver(); choice, trace = select(s, source)
        self.assertEqual(trace['child']['screen']['trace'], [])
        result = publish_model(s, source, choice)
        self.assertEqual(result['model'], {1: True, 2: False, 3: False, 4: False})

    def test_baseline_prefix_transport_and_disabled_leaves(self):
        source = [[10]] + [[-10] + c for c in SOURCE]
        for raw in (source, [[-7*l for l in c[::-1]] for c in source[::-1]]):
            s = self.solver(leaves=False); choice, _ = select(s, raw)
            self.assertEqual(choice['kind'], 'positive-model')
            result = publish_model(s, raw, choice); self.assertTrue(holds(raw, result['model']))

    def test_invalid_child_binding_trace_and_nonterminal_residual(self):
        s = self.solver(); _, trace = select(s, SOURCE); screen = trace['child']['screen']
        bad = deepcopy(screen); bad['root'] += ' '
        with self.assertRaises(ValueError): recover_model(s, SOURCE, trace['proposal'], bad)
        bad = deepcopy(screen); bad['trace'][0][0] *= -1
        with self.assertRaises(ValueError): recover_model(s, SOURCE, trace['proposal'], bad)
        bad = deepcopy(screen); bad['trace'] = []
        with self.assertRaises(ValueError): recover_model(s, SOURCE, trace['proposal'], bad)
        self.assertEqual(s.archive_storage()[0], 0)

    def test_invalid_target_model_never_published(self):
        s = self.solver(); choice, _ = select(s, SOURCE)
        variants = []
        bad = deepcopy(choice); bad['model'][0][1] = False; variants.append(bad)
        bad = deepcopy(choice); bad['root'] += ' '; variants.append(bad)
        bad = deepcopy(choice); bad['model'][0][1] = 1; variants.append(bad)
        bad = deepcopy(choice); bad['model'].pop(); variants.append(bad)
        bad = deepcopy(choice); bad['model'][0][0] = True; variants.append(bad)
        for candidate in variants:
            with self.assertRaises(ValueError): publish_model(s, SOURCE, candidate)
        self.assertEqual(s.archive_storage()[0], 0)

    def test_known_target_and_other_choices_preserved(self):
        sources = ([[1]], [[1], [-1]], [[1, 2, 3], [-1, -2, -3]])
        for source in sources:
            a = self.solver(); b = self.solver()
            self.assertEqual(previous_select(a, source), select(b, source))
        s = self.solver(); s.solve(SOURCE)
        self.assertEqual(select(s, SOURCE)[1]['reason'], 'known-target')
        self.assertEqual(select(s, SOURCE, 0)[1]['reason'], 'disabled')

    def test_no_expansion_budget_needed_and_cold_recheck(self):
        s = self.solver(node_limit=0); choice, _ = select(s, SOURCE)
        result = publish_model(s, SOURCE, choice); s.checked.clear()
        with patch.object(s, '_expand', side_effect=AssertionError('Cold search')):
            replay = s.solve(SOURCE)
            again = publish_model(s, SOURCE, choice)
        self.assertEqual(result['model'], replay['model'])
        self.assertEqual(again['metrics'].get('inserted_nodes', 0), 0)

    def test_exhaustive_lifted_candidates_and_polarity_transports(self):
        pool = [[1, 3, 4], [1, -3, -4], [-1, 3], [-1, -3], [-1, 4], [-1, -4], [-3, 4], [3, -4]]
        recovered = 0
        for mask in range(256):
            source = [[1, 2], [1, -2]] + [c for i, c in enumerate(pool) if mask >> i & 1]
            expected = any(holds(source, dict(zip((1, 2, 3, 4), bits))) for bits in product((False, True), repeat=4))
            for raw in (source, [[-7*l for l in c[::-1]] for c in source[::-1]]):
                s = ResidualSolver(); old = ResidualSolver()
                try:
                    choice, trace = select(s, raw)
                    if choice is None or choice['kind'] != 'positive-model':
                        self.assertEqual((choice, trace), previous_select(old, raw)); continue
                    recovered += 1; self.assertTrue(expected)
                    result = publish_model(s, raw, choice)
                    self.assertTrue(holds(raw, result['model']))
                    self.assertEqual(result['metrics']['inserted_nodes'], 1)
                finally: s.close(); old.close()
        self.assertGreater(recovered, 0)


if __name__ == '__main__': unittest.main()
