from collections import Counter
from itertools import combinations, product
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy
import unittest

from experiments.cnf_binary_subset import BinarySubsetSolver, refute_binary_subset
from experiments.cnf_residual_dag import ResidualSolver, holds, normalize
from experiments.cnf_cross_family import generate, truth_table


class BinarySubsetTests(unittest.TestCase):
    def test_mixed_refutation_uses_source_clause_indices(self):
        source = [[1, 2], [-1, 2], [1, -2], [-1, -2], [1, 3, 4]]
        s = BinarySubsetSolver(); self.addCleanup(s.close)
        r = s.solve(source)
        self.assertFalse(r['answer'])
        self.assertEqual(r['metrics']['inserted_nodes'], 1)
        self.assertEqual(r['metrics']['binary_subset_refutations'], 1)
        node = s.checked[r['root']]
        self.assertEqual(node['proof']['kind'], 'implications')
        # This is checked by the original authority, with unrelated wide clauses.
        old = ResidualSolver(); self.addCleanup(old.close)
        old._verify(r['root'], node)
        bad = copy.deepcopy(node)
        wide = next(i for i, c in enumerate(node['cnf']) if len(c) > 2)
        bad['proof']['forward'][0][1] = wide
        with self.assertRaises(ValueError): old._verify(r['root'], bad)

    def test_satisfiable_binary_core_never_decides_whole_source(self):
        # All eight ternary clauses refute three variables, but the binary
        # subset over disjoint variables has both polarities and is satisfiable.
        source = [list(c) for c in product((1, -1), (2, -2), (3, -3))]
        source += [[4, 5], [-4, -5]]
        cnf, _ = normalize(source); counts = Counter()
        self.assertIsNone(refute_binary_subset(cnf, counts))
        self.assertEqual(counts['binary_subset_satisfiable_misses'], 1)
        s = BinarySubsetSolver(); self.addCleanup(s.close)
        self.assertFalse(s.solve(source)['answer'])

    def test_skip_conditions_preserve_fallback(self):
        for source in ([], [[1]], [[1], [-1]], [[1, 2], [-1, -2]],
                       [[1, 2, 3]], [[-1, -2], [1, 2, 3]], [[1, 2], [-1, -2, -3]]):
            counts = Counter(); cnf, _ = normalize(source)
            with patch('experiments.cnf_binary_subset.two_cnf', side_effect=AssertionError('Unnecessary SCC')):
                self.assertIsNone(refute_binary_subset(cnf, counts))
            s = BinarySubsetSolver(); self.addCleanup(s.close)
            self.assertEqual(s.solve(source)['answer'], truth_table(source)['answer'])

    def test_exhaustive_binary_subsets_with_wide_clause(self):
        binary = [c for vs in combinations((1, 2, 3), 2)
                  for c in product(*[(v, -v) for v in vs])]
        # All 4096 binary subsets, with alternating signed wide clauses.
        s = BinarySubsetSolver(); self.addCleanup(s.close)
        for mask in range(1 << len(binary)):
            source = [c for i, c in enumerate(binary) if mask >> i & 1]
            source += [(1 if mask & 1 else -1, 2, -3)]
            actual = s.solve(source)
            expected = any(holds(source, dict(zip((1, 2, 3), bits)))
                           for bits in product((False, True), repeat=3))
            self.assertEqual(actual['answer'], expected, source)

    def test_signed_renaming_and_original_cold_reader(self):
        source = [[-90, 17], [90, 17], [-90, -17], [90, -17], [-90, 810, 500]]
        with TemporaryDirectory() as td:
            path = Path(td) / 'archive'; s = BinarySubsetSolver(path)
            try:
                r = s.solve(source)
                before = dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
            finally: s.close()
            s = ResidualSolver(path)
            try:
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s, '_expand', side_effect=AssertionError('Cold search')), patch.object(s, '_store', side_effect=AssertionError('Cold write')):
                    self.assertFalse(s.solve(source)['answer'])
                self.assertEqual(before, dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            finally: s.close()

    def test_existing_proofs_and_disabled_leaves_keep_priority(self):
        source = [[1, 2], [-1, 2], [1, -2], [-1, -2], [1, 3, 4]]
        with TemporaryDirectory() as td:
            path = Path(td) / 'archive'; s = ResidualSolver(path)
            try:
                s.solve(source); before = dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1'))
            finally: s.close()
            s = BinarySubsetSolver(path)
            try:
                with patch.object(s, '_expand', side_effect=AssertionError('Known root')):
                    s.solve(source)
                self.assertEqual(before, dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1')))
            finally: s.close()
        s = BinarySubsetSolver(leaves=False); self.addCleanup(s.close)
        with patch('experiments.cnf_binary_subset.refute_binary_subset', side_effect=AssertionError('Disabled leaves')):
            self.assertFalse(s.solve(source)['answer'])

    def test_cross_family_truth(self):
        for family in ('random-three', 'coupled-parity', 'gated-horn', 'graph-colouring'):
            for sample in range(4):
                source = generate(family, 12, sample, 34)
                s = BinarySubsetSolver()
                try: self.assertEqual(s.solve(source)['answer'], truth_table(source)['answer'])
                finally: s.close()


if __name__ == '__main__': unittest.main()
