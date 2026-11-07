import itertools
from pathlib import Path
import random
import tempfile
import unittest
from experiments.run_expanded import parse_dimacs, encode_dimacs, dimacs
from solver.persistent import PersistentSolver
from solver.resources import BudgetExceeded


class BenchmarkEncodingTests(unittest.TestCase):
    def test_dimacs_roundtrip_matches_independent_semantics(self):
        rng = random.Random(717)
        with tempfile.TemporaryDirectory() as directory, PersistentSolver(Path(directory)/"results.sqlite3") as s:
            for _ in range(30):
                clauses = [[rng.choice([-1, 1])*rng.randrange(1, 5) for _ in range(rng.randrange(4))]
                           for _ in range(rng.randrange(10))]
                text = dimacs(clauses, 4)
                self.assertEqual(parse_dimacs(text), (4, clauses))
                expected = any(all(any(a[abs(v)-1] == (v > 0) for v in c) for c in clauses)
                               for a in itertools.product((False, True), repeat=4))
                self.assertEqual(s.solve(encode_dimacs(text))["answer"], expected)

    def test_malformed_dimacs_and_oversized_conversion_are_rejected(self):
        for text in ["p cnf 1 1\n1", "p cnf 1 1\n2 0", "p cnf 1 2\n1 0", "1 0", "p cnf -1 0"]:
            with self.assertRaises(ValueError):
                parse_dimacs(text)
        with self.assertRaises(BudgetExceeded):
            encode_dimacs("p cnf 1000000 1\n1000000 0", maximum=100)

    def test_baseline_can_bypass_reuse_without_deleting_results(self):
        with tempfile.TemporaryDirectory() as directory, PersistentSolver(Path(directory)/"results.sqlite3", reuse_exact=False) as s:
            bits = encode_dimacs("p cnf 2 2\n1 0\n-2 0")
            s.solve(bits, learn=False)
            self.assertEqual(s.solve(bits, learn=False)["source"], "fallback")
            self.assertEqual(s.stats()["entries"], 1)
