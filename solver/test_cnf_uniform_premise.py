from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from experiments.cnf_uniform_premise import select, complete_premise
from experiments.cnf_positive_premise import select as previous_select
from experiments.cnf_positive_child import publish_model
from experiments.cnf_partition_screen import screen_branch
from experiments.cnf_residual_dag import ResidualSolver, holds

SOURCE = [[1, 2], [-1, -2], [1, 3, 4], [-1, -3, -4]]


class UniformPremiseTests(unittest.TestCase):
    def solver(self, **options):
        s = ResidualSolver(**options); self.addCleanup(s.close); return s

    def attempt(self, s, source, literal):
        return dict(clause=[literal], screen=screen_branch(s, source + [[literal]], Counter()))

    def test_nonterminal_completion_and_publication_without_search(self):
        s = self.solver(node_limit=0)
        with patch.object(s, '_expand', side_effect=AssertionError('Search')), patch.object(s, '_store', side_effect=AssertionError('Publication')):
            choice, trace = select(s, SOURCE)
        self.assertEqual(trace['reason'], 'uniform-premise-model')
        detail = trace['uniform_premise']['attempts'][0]
        self.assertEqual(detail, dict(index=0, residual_literals=2, false_valid=False, true_valid=True, fill=True))
        self.assertEqual(dict(choice['model']), {1: False, 2: True, 3: True, 4: True})
        with patch.object(s, '_visit', side_effect=AssertionError('Acquisition')):
            result = publish_model(s, SOURCE, choice)
        self.assertTrue(holds(SOURCE, result['model']))
        self.assertEqual(result['metrics']['inserted_nodes'], 1)
        self.assertEqual(result['metrics'].get('expanded_nodes', 0), 0)

    def test_horn_dual_and_broader_uniform_residuals(self):
        s = self.solver()
        for literal, fill in ((-1, True), (1, False)):
            model, d = complete_premise(s, SOURCE, self.attempt(s, SOURCE, literal))
            self.assertEqual(d['fill'], fill)
            self.assertTrue(holds(SOURCE + [[literal]], dict(model['model'])))
        broader = [[1, 2], [-1, -2], [1, 3, 4, -5, -6], [-1, -3, -4, 5, 6]]
        model, d = complete_premise(s, broader, self.attempt(s, broader, -1))
        self.assertTrue(d['false_valid'] and d['true_valid'])
        self.assertEqual(d['residual_literals'], 4)
        self.assertTrue(holds(broader, dict(model['model'])))

    def test_uniform_failure_is_not_unsat(self):
        source = [[1, 2], [-1, -2], [3, 4], [-3, -4]]
        s = self.solver(); model, d = complete_premise(s, source, self.attempt(s, source, -1))
        self.assertIsNone(model); self.assertFalse(d['false_valid'] or d['true_valid'])
        self.assertTrue(any(holds(source, dict(zip(range(1, 5), bits))) for bits in product((False, True), repeat=4)))

    def test_invalid_trace_binding_and_assumption_rejected(self):
        s = self.solver(); a = self.attempt(s, SOURCE, -1); variants = []
        for clause in ([0], [True], [99], [], [1, 2], [1]):
            bad = deepcopy(a); bad['clause'] = clause; variants.append(bad)
        for field, value in (('root', 'wrong'), ('conflict', 0), ('trace', [[0, 0]]), ('trace', [[True, 0]]), ('trace', None), ('trace', [[-1, -1]]), ('trace', [[-1, 999]])):
            bad = deepcopy(a); bad['screen'][field] = value; variants.append(bad)
        bad = deepcopy(a); bad['screen']['trace'] *= 2; variants.append(bad)
        for bad in variants:
            with self.assertRaises(ValueError): complete_premise(s, SOURCE, bad)
        self.assertEqual(s.archive_storage()[0], 0)

    def test_hints_not_trusted_and_no_negative_inference(self):
        s = self.solver(); a = self.attempt(s, SOURCE, -1)
        for hint in (0, 999):
            a['screen']['residual_literals'] = hint
            model, d = complete_premise(s, SOURCE, a)
            self.assertTrue(holds(SOURCE, dict(model['model'])))
            self.assertEqual(d['residual_literals'], 2)
        source = [[1], [2, 3]]; a = self.attempt(s, source, -1)
        with self.assertRaises(ValueError): complete_premise(s, source, a)
        self.assertTrue(s.solve(source)['answer'])

    def test_baseline_prefix_transport_and_counter_accounting(self):
        source = [[10]] + [[-10] + c for c in SOURCE]
        for raw in (source, [[-7*l for l in c[::-1]] for c in source[::-1]]):
            s = self.solver(leaves=False); counts = Counter(); choice, trace = select(s, raw, counts=counts)
            self.assertEqual(trace['previous_reason'], 'retained-prefix')
            self.assertEqual(counts['fallback_trace_reuses'], 0)
            self.assertEqual(counts['fallback_forced_variables'], 0)
            self.assertEqual(counts['uniform_premise_models'], 1)
            self.assertEqual(counts['uniform_premise_recognition_literal_visits'], sum(d['residual_literals'] for d in trace['uniform_premise']['attempts']))
            self.assertTrue(holds(raw, publish_model(s, raw, choice)['model']))

    def test_prior_positive_and_native_choices_preserved(self):
        for raw in ([], [[]], [[1]], [[1], [-1]], [[1, 2], [-1, -2], [1, 2, 3], [-1, -2, -3]], [[1, 2, 3], [1, -2, -3]]):
            self.assertEqual(select(self.solver(), raw), previous_select(self.solver(), raw))
        for limit in (-1, True, 0.5):
            with self.assertRaises(ValueError): select(self.solver(), SOURCE, limit)
        self.assertEqual(select(self.solver(), SOURCE, 0)[1]['reason'], 'disabled')

    def test_persistence(self):
        with TemporaryDirectory() as td:
            path = Path(td) / 'proofs'; s = ResidualSolver(path)
            try: choice, _ = select(s, SOURCE); result = publish_model(s, SOURCE, choice)
            finally: s.close()
            s = ResidualSolver(path)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s, '_expand', side_effect=AssertionError('Cold search')), patch.object(s, '_store', side_effect=AssertionError('Cold publication')):
                    self.assertEqual(s.solve(SOURCE)['model'], result['model'])
                    self.assertEqual(select(s, SOURCE)[1]['reason'], 'known-target')
            finally: s.close()

    def test_exhaustive_uniform_coverage_and_transports(self):
        pool = [[1, 2], [-1, -2], [1, 3, 4], [-1, -3, -4], [3, 4], [-3, -4], [1, 3, -4], [-1, -3, 4]]
        successes = misses = 0
        for mask in range(256):
            source = [[1, 2], [-1, -2]] + [c for i, c in enumerate(pool) if mask >> i & 1]
            for raw in (source, [[-7*l for l in c[::-1]] for c in source[::-1]]):
                s = ResidualSolver()
                try:
                    for literal in (-min(abs(l) for c in raw for l in c), min(abs(l) for c in raw for l in c)):
                        a = self.attempt(s, raw, literal)
                        if a['screen']['conflict'] is not None: continue
                        model, d = complete_premise(s, raw, a)
                        cnf, names, _ = s._canonical(raw + [[literal]])
                        fixed = {abs(l): l > 0 for l, _ in a['screen']['trace']}
                        brute = [all(any(fixed.get(abs(l), bit) == (l > 0) for l in c) for c in cnf) for bit in (False, True)]
                        self.assertEqual([d['false_valid'], d['true_valid']], brute)
                        if model is None: misses += 1; self.assertFalse(any(brute))
                        else: successes += 1; self.assertTrue(holds(raw + [[literal]], dict(model['model'])))
                finally: s.close()
        self.assertGreater(successes, 0); self.assertGreater(misses, 0)


if __name__ == '__main__': unittest.main()
