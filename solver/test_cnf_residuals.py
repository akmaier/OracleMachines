"""Research-candidate checks; no access to the production result archive."""
import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_residual_dag import ResidualSolver, holds


def brute(cnf):
    names = sorted({abs(lit) for c in cnf for lit in c})
    return any(holds(cnf, dict(zip(names, a)))
               for a in itertools.product((False, True), repeat=len(names)))


class ResidualTests(unittest.TestCase):
    def test_complete_two_variable_formulas_and_all_modes(self):
        clauses = [tuple(s * (i + 1) for i, s in enumerate(p) if s)
                   for p in itertools.product((-1, 0, 1), repeat=2)]
        for options in ({}, {"reuse": False}, {"leaves": False}, {"decompose": False}):
            solver = ResidualSolver(**options)
            try:
                for mask in range(1 << len(clauses)):
                    cnf = [c for i, c in enumerate(clauses) if mask >> i & 1]
                    result = solver.solve(cnf)
                    self.assertEqual(result["answer"], brute(cnf), (cnf, options))
            finally:
                solver.close()

    def test_seeded_general_formulas(self):
        rng = random.Random(20261108)
        solver = ResidualSolver()
        try:
            for _ in range(400):
                n = rng.randrange(3, 8)
                cnf = [tuple(v * rng.choice((-1, 1)) for v in rng.sample(range(1, n + 1), rng.randrange(1, n + 1)))
                       for _ in range(rng.randrange(1, 35))]
                self.assertEqual(solver.solve(cnf)["answer"], brute(cnf), cnf)
        finally:
            solver.close()

    def test_repeated_components_and_renamed_cold_reuse(self):
        base = [(1, 2, 3), (-1, -2, -3)]
        cnf = [tuple((abs(lit) + 3 * i) * (1 if lit > 0 else -1) for lit in c)
               for i in range(8) for c in base]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "research.sqlite3"
            solver = ResidualSolver(path)
            first = solver.solve(cnf)
            self.assertTrue(first["answer"])
            self.assertGreaterEqual(first["metrics"].get("search_memory_hits", 0), 7)
            old_rows = solver.db.execute("SELECT * FROM cnf_residual_v1 ORDER BY id").fetchall()
            solver.close()
            solver = ResidualSolver(path)
            renamed = [tuple((abs(lit) + 1000) * (1 if lit > 0 else -1) for lit in c) for c in cnf]
            cold = solver.solve(renamed)
            self.assertTrue(cold["answer"])
            self.assertEqual(cold["metrics"].get("expanded_nodes", 0), 0)
            self.assertEqual(cold["metrics"].get("search_disk_hits", 0), 1)
            self.assertEqual(old_rows, solver.db.execute("SELECT * FROM cnf_residual_v1 ORDER BY id").fetchall())
            changed = solver.solve(cnf + [(1,), (-1,)])
            self.assertFalse(changed["answer"])
            for row in old_rows:
                self.assertEqual(row[1], solver.db.execute("SELECT payload FROM cnf_residual_v1 WHERE id=?", (row[0],)).fetchone()[0])
            solver.close()

    def test_leaf_certificates_and_cold_negative_replay(self):
        examples = [([(1,), (-1, 2), (-2,)], "units"),
                    ([(1, 2), (1, -2), (-1, 2), (-1, -2)], "implications"),
                    ([tuple((i + 1) * sign for i, sign in enumerate(p))
                      for p in itertools.product((-1, 1), repeat=3)], "split")]
        for cnf, kind in examples:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "research.sqlite3"
                solver = ResidualSolver(path)
                result = solver.solve(cnf)
                self.assertFalse(result["answer"])
                self.assertEqual(solver.checked[result["root"]]["proof"]["kind"], kind)
                solver.close()
                solver = ResidualSolver(path)
                cold = solver.solve(cnf)
                self.assertFalse(cold["answer"])
                self.assertEqual(cold["metrics"].get("expanded_nodes", 0), 0)
                self.assertGreater(cold["metrics"].get("verified_nodes", 0), 0)
                solver.close()

    def test_mutated_certificates_are_rejected(self):
        cases = [([(1,)], lambda n: n.update(model=[False])),
                 ([(1,), (-1,)], lambda n: n["proof"].update(trace=[])),
                 ([(1, 2), (1, -2), (-1, 2), (-1, -2)],
                  lambda n: n["proof"].update(forward=[])),
                 ([tuple((i + 1) * sign for i, sign in enumerate(p))
                   for p in itertools.product((-1, 1), repeat=3)],
                  lambda n: n["proof"].update(low="0" * 64))]
        for cnf, mutate in cases:
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "research.sqlite3"
                solver = ResidualSolver(path)
                result = solver.solve(cnf)
                node = dict(solver.checked[result["root"]])
                mutate(node)
                with solver.db:
                    solver.db.execute("UPDATE cnf_residual_v1 SET payload=? WHERE id=?",
                                      (json.dumps(node), result["root"]))
                solver.close()
                solver = ResidualSolver(path)
                with self.assertRaises(ValueError):
                    solver.solve(cnf)
                solver.close()

    def test_budget_exhaustion_never_becomes_unsat(self):
        solver = ResidualSolver(node_limit=1, leaves=False)
        try:
            with self.assertRaisesRegex(RuntimeError, "no verdict"):
                solver.solve([(1, 2, 3), (-1, -2, -3)])
        finally:
            solver.close()

    def test_tautologies_duplicates_sparse_ids_and_invalid_literals(self):
        solver = ResidualSolver()
        try:
            for cnf in ([], [[]], [[9000, -9000]], [[9000, 9000]], [[3, -3], [8], [-8]]):
                self.assertEqual(solver.solve(cnf)["answer"], brute(cnf))
            for cnf in ([[0]], [[True]], [[1.0]]):
                with self.assertRaises(ValueError):
                    solver.solve(cnf)
        finally:
            solver.close()


if __name__ == "__main__":
    unittest.main()
