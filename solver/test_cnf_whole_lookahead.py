from collections import Counter
from itertools import product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import random
import unittest
from experiments import cnf_whole_lookahead as policy
from experiments.cnf_residual_dag import normalize, holds
from experiments.cnf_probed_partition import acquire
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot

# x=False propagates a,b and conflicts through a ternary clause. The binary
# implication graph alone cannot expose this contradiction.
SOURCE = [(1, 2), (1, 3), (1, -2, -3), (1, 4, 5), (-1, 6, 7)]


class WholeLookaheadTests(unittest.TestCase):
    def solver(self, **kwargs):
        s = policy.WholeLookaheadSolver(**kwargs)
        self.addCleanup(s.close)
        return s

    def test_wide_clause_failure_both_polarities(self):
        for sign in (1, -1):
            source = [[sign*l for l in c] for c in SOURCE]
            cnf, _ = normalize(source)
            s = self.solver()
            with patch.object(policy, 'probe_child', wraps=policy.probe_child) as probe:
                model, proof = policy.lookahead(s, cnf)
            self.assertIsNone(proof)
            self.assertTrue(holds(cnf, model))
            self.assertEqual(s.counts['whole_probe_selections'], 1)
            self.assertEqual([call.args[3] for call in probe.call_args_list if call.args[1] == cnf],
                             [False] if sign == 1 else [False, True])

    def test_misses_are_not_answers_or_publications(self):
        s = self.solver()
        cnf, _ = normalize([(1, 2, 3), (-1, -2, -3)])
        self.assertIsNone(policy.lookahead(s, cnf))
        self.assertEqual(s.archive_storage()[0], 0)
        self.assertEqual(s.counts['whole_probe_misses'], 1)

    def test_unit_and_size_guards(self):
        s = self.solver()
        with patch.object(policy, 'probe_child', side_effect=AssertionError('probe')):
            for src in ([], [()], [(1,)], [(i, i+1, i+2) for i in range(1, 300, 3)], [(1, 2, 3)]*4097):
                self.assertIsNone(policy.lookahead(s, src))

    def test_binary_evidence_keeps_existing_priority(self):
        s = self.solver()
        with patch.object(policy, 'lookahead', side_effect=AssertionError('unnecessary')):
            self.assertFalse(s.solve([(1, 2), (1, -2), (-1, 2), (-1, -2)])['answer'])

    def test_exhaustive_two_variable_cnf_truth(self):
        clauses = [tuple(s*v for v, s in enumerate(signs, 1) if s)
                   for signs in product((-1, 0, 1), repeat=2)]
        s = self.solver()
        for mask in range(1 << len(clauses)):
            src = [c for i, c in enumerate(clauses) if mask & (1 << i)]
            truth = any(holds(src, dict(zip((1, 2), b))) for b in product((False, True), repeat=2))
            self.assertEqual(s.solve(src)['answer'], truth)

    def test_random_wider_truth_and_sparse_labels(self):
        rng = random.Random(20261123)
        s = self.solver()
        labels = (13, 29, 103, 505, 812)
        for _ in range(192):
            src = [[rng.choice((-1, 1))*v for v in rng.sample(labels, rng.choice((2, 3, 4)))]
                   for _ in range(rng.randrange(4, 28))]
            truth = any(holds(src, dict(zip(labels, b))) for b in product((False, True), repeat=5))
            result = s.solve(src)
            self.assertEqual(result['answer'], truth)
            if truth:
                self.assertTrue(holds(src, result['model']))

    def test_budget_stop_keeps_only_checked_prefix(self):
        s = self.solver()
        cnf, _ = normalize(SOURCE)
        with self.assertRaisesRegex(RuntimeError, 'Residual expansion budget exhausted'):
            s.node_limit = 0
            policy.lookahead(s, cnf)
        self.assertGreater(s.archive_storage()[0], 0)
        self.assertIsNone(s._read(s._canonical(cnf)[2]))
        s.node_limit = 256
        self.assertTrue(s.solve(cnf)['answer'])

    def test_native_cold_readers_check_split_proofs(self):
        with TemporaryDirectory() as td:
            path = Path(td)/'db'
            s = policy.WholeLookaheadSolver(path)
            try:
                for sign in (1, -1):
                    s.solve([[sign*l for l in c] for c in SOURCE])
                hard = [tuple(v if b else -v for v, b in enumerate(bits, 1))
                        for bits in product((False, True), repeat=3)]
                self.assertFalse(s.solve(hard)['answer'])
                keys = [k for k, in s.db.execute('SELECT id FROM cnf_residual_v1')]
            finally:
                s.close()
            for cls in (SnapshotResidualSolver, CanonicalVerifySnapshot):
                reader = cls(path)
                try:
                    for key in keys:
                        self.assertIsNotNone(reader._read(key))
                finally:
                    reader.close()

    def test_single_pass_input_and_invalid_literals(self):
        s = self.solver()
        self.assertTrue(s.solve((iter(c) for c in SOURCE))['answer'])
        for bad in (0, True, 1.5):
            with self.assertRaises((ValueError, TypeError)):
                s.solve([[bad]])


if __name__ == '__main__':
    unittest.main()
