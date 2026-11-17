from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import tempfile, unittest
from unittest.mock import patch
from experiments.cnf_assumption_guard import probe, publish_guard
from experiments.cnf_guard_chain import make_record, check_record, GuardChainBank
from experiments.cnf_partition_screen import publish_screened_branch
from experiments.cnf_residual_dag import ResidualSolver, holds


class AssumptionGuardTests(unittest.TestCase):
    def solver(self):
        s = ResidualSolver()
        self.addCleanup(s.close)
        return s

    def test_failed_probe_and_bound(self):
        s = self.solver(); source = [[1, 2], [1, -2]]; counts = Counter()
        with patch.object(s, '_expand', side_effect=AssertionError('Probe search')), patch.object(s, '_store', side_effect=AssertionError('Probe publication')):
            choice, trace = probe(s, source, [[-2], [-1]], 1, counts)
            self.assertIsNone(choice); self.assertEqual(len(trace['attempts']), 1)
            choice, trace = probe(s, source, [[-2], [-1]], 2, counts)
            self.assertEqual(choice['clause'], [-1]); self.assertEqual(trace['selected'], 1)
        self.assertEqual(s.archive_storage()[0], 0)
        with patch.object(s, '_expand', side_effect=AssertionError('Premise search')):
            guard, fixed, target, premise = publish_guard(s, source, choice)
        self.assertEqual(fixed, {1: True}); self.assertEqual(premise['metrics']['screen_trace_publications'], 1)
        child = s.solve(target); record = make_record(s, source, [guard], child)
        self.assertTrue(record['answer']); self.assertTrue(holds(source, record['model']))

    def test_terminal_target_precedes_candidates(self):
        s = self.solver(); counts = Counter(); source = [[1], [-1]]
        choice, trace = probe(s, source, [[0]], counts=counts)
        self.assertEqual(choice['kind'], 'terminal'); self.assertEqual(trace['attempts'], [])
        self.assertEqual(counts['assumption_candidates_examined'], 0)
        with patch.object(s, '_expand', side_effect=AssertionError('Terminal search')):
            self.assertFalse(publish_screened_branch(s, source, choice['screen'])['answer'])

    def test_multiple_forced_values_and_persistence(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / 'proofs'; s = ResidualSolver(path)
            source = [[-10], [-20], [30, 40]]
            try:
                choice, _ = probe(s, source, [[10, 20]])
                guard, fixed, target, _ = publish_guard(s, source, choice)
                self.assertEqual(fixed, {10: False, 20: False})
                record = make_record(s, source, [guard], s.solve(target))
                self.assertTrue(record['answer'])
            finally:
                s.close()
            s = ResidualSolver(path)
            try:
                with patch.object(s, '_expand', side_effect=AssertionError('Warm search')), patch.object(s, '_store', side_effect=AssertionError('Warm publication')):
                    check_record(s, record); self.assertTrue(GuardChainBank(s, [record]).lookup(source)['answer'])
                    publish_guard(s, source, choice)
            finally:
                s.close()

    def test_skip_invalid_domain_and_disabled_budget(self):
        s = self.solver(); source = [[1, 2]]
        choice, trace = probe(s, source, [[], [3], [1, 2], [-1], [-1]], 5)
        self.assertIsNone(choice)
        self.assertEqual([r['skipped'] for r in trace['attempts']], ['empty', 'outside', 'contained', None, 'duplicate'])
        self.assertEqual(probe(s, source, [[0]], 0), (None, dict(baseline=None, attempts=[], selected=None)))
        for limit in (-1, True, 0.5):
            with self.assertRaises(ValueError): probe(s, source, [], limit)

    def test_tampered_conflict_cannot_publish(self):
        source = [[1, 2], [1, -2]]
        for mutation in ('root', 'trace', 'clause'):
            s = self.solver(); choice, _ = probe(s, source, [[-1]])
            bad = deepcopy(choice)
            if mutation == 'root': bad['screen']['root'] = 'bad'
            elif mutation == 'trace': bad['screen']['trace'] = []
            else: bad['clause'] = [-2]
            with self.assertRaises(ValueError): publish_guard(s, source, bad)
            self.assertEqual(s.archive_storage()[0], 0)

    def test_failed_probe_does_not_establish_a_guard(self):
        s = self.solver(); source = [[1, 2]]
        choice, trace = probe(s, source, [[-1]])
        self.assertIsNone(choice)
        with self.assertRaises(ValueError): publish_guard(s, source, dict(kind='guard', clause=[-1], screen=trace['attempts'][0]['screen']))
        self.assertEqual(s.archive_storage()[0], 0)

    def test_exhaustive_two_variable_truth_and_composition(self):
        clauses = [[i * sign for i, sign in enumerate(signs, 1) if sign] for signs in product((-1, 0, 1), repeat=2)]
        for mask in range(1 << len(clauses)):
            source = [c for i, c in enumerate(clauses) if mask >> i & 1]
            expected = any(holds(source, dict(zip((1, 2), bits))) for bits in product((False, True), repeat=2))
            s = ResidualSolver()
            try:
                choice, _ = probe(s, source, [[-1], [1], [-2], [2]], 4)
                guards = []
                if choice is None: child = s.solve(source)
                elif choice['kind'] == 'terminal': child = publish_screened_branch(s, source, choice['screen'])
                else:
                    guard, _, target, _ = publish_guard(s, source, choice)
                    guards.append(guard); child = s.solve(target)
                record = make_record(s, source, guards, child)
                self.assertEqual(record['answer'], expected); check_record(s, record)
                if expected: self.assertTrue(holds(source, record['model']))
            finally:
                s.close()


if __name__ == '__main__':
    unittest.main()
