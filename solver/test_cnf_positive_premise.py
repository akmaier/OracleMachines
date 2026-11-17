from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
from experiments.cnf_positive_premise import select, recover_premise_model
from experiments.cnf_positive_child import publish_model
from experiments.cnf_binary_probe import select as previous_select
from experiments.cnf_partition_screen import screen_branch
from experiments.cnf_residual_dag import ResidualSolver, holds


SOURCE = [[1, 2], [-1, -2], [1, 2, 3], [-1, -2, -3]]


class PositivePremiseTests(unittest.TestCase):
    def solver(self, **options):
        s = ResidualSolver(**options); self.addCleanup(s.close); return s

    def test_positive_assumption_not_its_negation_is_lifted(self):
        s = self.solver(node_limit=0); counts = Counter()
        with patch.object(s, '_expand', side_effect=AssertionError('Discovery search')), patch.object(s, '_store', side_effect=AssertionError('Discovery publication')):
            choice, trace = select(s, SOURCE, counts=counts)
        self.assertEqual(trace['reason'], 'positive-premise-model')
        self.assertEqual(trace['positive_premise_attempt'], 0)
        self.assertEqual(dict(choice['model'])[1], False)
        self.assertEqual(dict(choice['model'])[3], False)
        self.assertEqual(counts['positive_premise_models'], 1)
        with patch.object(s, '_visit', side_effect=AssertionError('Fallback search')):
            answer = publish_model(s, SOURCE, choice)
        self.assertTrue(holds(SOURCE, answer['model']))
        self.assertEqual(answer['metrics']['inserted_nodes'], 1)
        self.assertEqual(answer['metrics'].get('expanded_nodes', 0), 0)

    def test_baseline_prefix_and_coordinate_transports(self):
        source = [[10]] + [[-10] + c for c in SOURCE]
        for raw in (source, [[-7*l for l in c[::-1]] for c in source[::-1]]):
            s = self.solver(leaves=False); counts = Counter()
            choice, trace = select(s, raw, counts=counts)
            self.assertEqual(trace['previous_reason'], 'retained-prefix')
            self.assertEqual(counts['fallback_trace_reuses'], 0)
            self.assertEqual(counts['fallback_forced_variables'], 0)
            self.assertTrue(holds(raw, publish_model(s, raw, choice)['model']))

    def test_malformed_and_incomplete_evidence_rejected_without_publication(self):
        s = self.solver(); _, trace = select(s, SOURCE)
        attempt = trace['discovery']['attempts'][0]; variants = []
        for clause in ([0], [True], [99], [], [-1, 2]):
            bad = deepcopy(attempt); bad['clause'] = clause; variants.append(bad)
        for field, value in (('root', 'wrong'), ('conflict', 0), ('trace', []), ('trace', None), ('trace', [[-1]])):
            bad = deepcopy(attempt); bad['screen'][field] = value; variants.append(bad)
        for idx, value in ((0, True), (0, 0), (0, 99), (1, True), (1, -1), (1, 999)):
            bad = deepcopy(attempt); bad['screen']['trace'][0][idx] = value; variants.append(bad)
        bad = deepcopy(attempt); bad['screen']['trace'] *= 2; variants.append(bad)
        bad = deepcopy(attempt); bad['clause'][0] *= -1; variants.append(bad)
        for candidate in variants:
            with self.assertRaises(ValueError): recover_premise_model(s, SOURCE, candidate)
        self.assertEqual(s.archive_storage()[0], 0)

    def test_residual_counter_is_not_trusted(self):
        source = [[1, 2], [-1, -2], [1, 3, 4], [-1, -3, -4]]
        s = self.solver(); screen = screen_branch(s, source + [[-1]], Counter())
        screen['residual_literals'] = 0
        with self.assertRaises(ValueError):
            recover_premise_model(s, source, dict(clause=[-1], screen=screen))

    def test_existing_choices_and_candidate_filter_scope(self):
        sources = ([], [[]], [[1]], [[1], [-1]],
            [[1, 2], [1, -2], [-1, 3], [-3, 4], [1, 5, 6], [1, -5, -6]],
            [[1, 2, 3], [1, -2, -3]])
        for raw in sources:
            s = self.solver(); old = self.solver()
            self.assertEqual(select(s, raw), previous_select(old, raw))
        # This is positive under x=1, but negative-probe filtering omits it.
        # The optional policy makes no claim to recover every positive premise.
        s = self.solver(); raw = sources[-1]
        self.assertIsNone(select(s, raw)[0])
        attempt = dict(clause=[1], screen=screen_branch(s, raw + [[1]], Counter()))
        self.assertTrue(holds(raw, dict(recover_premise_model(s, raw, attempt)['model'])))

    def test_persistence_and_known_target_bypass(self):
        with TemporaryDirectory() as td:
            path = Path(td) / 'proofs'
            s = ResidualSolver(path)
            try: choice, _ = select(s, SOURCE); answer = publish_model(s, SOURCE, choice)
            finally: s.close()
            s = ResidualSolver(path)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s, '_expand', side_effect=AssertionError('Cold search')), patch.object(s, '_store', side_effect=AssertionError('Cold publication')):
                    self.assertEqual(s.solve(SOURCE)['model'], answer['model'])
                    self.assertEqual(select(s, SOURCE)[1]['reason'], 'known-target')
                    self.assertEqual(select(s, SOURCE, 0)[1]['reason'], 'disabled')
            finally: s.close()

    def test_exhaustive_small_clause_sets_and_transports(self):
        pool = [[1, 2], [-1, -2], [1, 2, 3], [-1, -2, -3],
                [-1, 3], [1, -3], [2, -3], [-2, 3], [1], [-1]]
        recovered = 0
        for mask in range(1024):
            source = [c for i, c in enumerate(pool) if mask >> i & 1]
            expected = any(holds(source, dict(zip((1, 2, 3), bits))) for bits in product((False, True), repeat=3))
            for raw in (source, [[-7*l for l in c[::-1]] for c in source[::-1]]):
                s = ResidualSolver(); old = ResidualSolver()
                try:
                    choice, trace = select(s, raw)
                    if trace['reason'] != 'positive-premise-model':
                        self.assertEqual((choice, trace), previous_select(old, raw)); continue
                    recovered += 1; self.assertTrue(expected)
                    self.assertTrue(holds(raw, publish_model(s, raw, choice)['model']))
                finally: s.close(); old.close()
        self.assertGreater(recovered, 0)


if __name__ == '__main__': unittest.main()
