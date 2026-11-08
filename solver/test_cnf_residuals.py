"""Research-candidate checks; no access to the production result archive."""
import itertools
import json
from collections import Counter
from pathlib import Path
import random
import tempfile
import unittest

from experiments.cnf_residual_dag import (ResidualSolver, check_positive_core, holds,
                                          matching_structure, normalize, positive_core, solve_matching)


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

    def test_every_three_by_three_matching_domain(self):
        for mask in range(1 << 9):
            domains = [[3 * p + h + 1 for h in range(3) if mask >> (3 * p + h) & 1]
                       for p in range(3)]
            cnf = list(domains)
            for h in range(3):
                members = [3 * p + h + 1 for p in range(3) if mask >> (3 * p + h) & 1]
                cnf += [(-a, -b) for a, b in itertools.combinations(members, 2)]
            canonical, _ = normalize(cnf)
            structure = matching_structure(canonical, Counter())
            if () in canonical:
                self.assertIsNone(structure)
                continue
            self.assertIsNotNone(structure)
            model, proof = solve_matching(structure, Counter())
            self.assertEqual(model is not None, brute(canonical))
            if model is not None:
                self.assertTrue(holds(canonical, model))
            else:
                selected = proof["groups"]
                neighbors = {r for p in selected for r in structure[p]}
                self.assertLess(len(neighbors), len(selected))

    def test_matching_recognizer_rejects_unsound_near_misses(self):
        # Shared positive literal can serve two clauses: treating these as two
        # exclusive choice groups would give a false Hall contradiction.
        overlap = [(1, 2), (2, 3), (-1, -2), (-1, -3), (-2, -3)]
        # A path is not an exclusion clique: endpoints may both be selected.
        missing_edge = [(1,), (3,), (-1, -2), (-2, -3)]
        for cnf in (overlap, missing_edge):
            canonical, _ = normalize(cnf)
            self.assertIsNone(matching_structure(canonical, Counter()))
            solver = ResidualSolver()
            try:
                self.assertTrue(solver.solve(cnf)["answer"])
            finally:
                solver.close()

    def test_hall_certificate_cold_replay_and_tampering(self):
        from experiments.compare_cnf_residuals import pigeonhole
        cnf = pigeonhole(4)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "research.sqlite3"
            solver = ResidualSolver(path)
            result = solver.solve(cnf)
            self.assertFalse(result["answer"])
            self.assertEqual(result["metrics"].get("expanded_nodes"), 1)
            self.assertEqual(result["metrics"].get("matching_leaves"), 1)
            solver.close()
            solver = ResidualSolver(path)
            cold = solver.solve(cnf)
            self.assertEqual(cold["metrics"].get("verified_nodes"), 1)
            node = solver.checked[result["root"]]
            node["proof"]["groups"] = node["proof"]["groups"][:1]
            with solver.db:
                solver.db.execute("UPDATE cnf_residual_v1 SET payload=? WHERE id=?",
                                  (json.dumps(node), result["root"]))
            solver.close()
            solver = ResidualSolver(path)
            with self.assertRaisesRegex(ValueError, "not deficient"):
                solver.solve(cnf)
            solver.close()

    def test_positive_core_preserves_all_models_on_small_families(self):
        clauses = [c for size in (2, 3, 4)
                   for c in itertools.combinations(range(1, 5), size)]
        assignments = [dict(zip(range(1, 5), bits))
                       for bits in itertools.product((False, True), repeat=4)]
        for mask in range(1 << len(clauses)):
            cnf = tuple(c for i, c in enumerate(clauses) if mask >> i & 1)
            core, removed = positive_core(cnf, Counter())
            self.assertEqual(core, positive_core(core, Counter())[0])
            if removed:
                self.assertEqual(core, check_positive_core(cnf, removed, Counter()))
            for assignment in assignments:
                self.assertEqual(holds(cnf, assignment), holds(core, assignment), cnf)
            # Every retained positive clause is minimal, and input order does
            # not change the resulting set (source certificate IDs may differ).
            self.assertFalse(any(set(c) < set(d) for c in core for d in core))
            self.assertEqual(set(core), set(positive_core(tuple(reversed(cnf)), Counter())[0]))

    def test_subsumption_reuses_prepared_core_and_preserves_old_rows(self):
        from experiments.compare_cnf_residuals import pigeonhole
        from experiments.compare_cnf_matching import domain_cnf
        for core, expected in ((pigeonhole(4), False),
                               (domain_cnf([range(4)] * 4), True)):
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "research.sqlite3"
                solver = ResidualSolver(path)
                first = solver.solve(core)
                old_rows = solver.db.execute("SELECT * FROM cnf_residual_v1").fetchall()
                # New variables occur only in redundant clauses. They vanish
                # from the core and must be reconstructed safely in SAT models.
                variants = [core + [tuple(core[0]) + tuple(range(100, 101 + i))]
                            for i in range(3)]
                for cnf in variants:
                    result = solver.solve(cnf)
                    self.assertEqual(result["answer"], expected)
                    self.assertEqual(result["metrics"].get("expanded_nodes"), 1)
                    self.assertEqual(result["metrics"].get("matching_leaves", 0), 0)
                    self.assertEqual(result["metrics"].get("search_memory_hits"), 1)
                    if expected:
                        self.assertTrue(holds(cnf, result["model"]))
                    else:
                        self.assertEqual(solver.checked[result["root"]]["proof"]["child"], first["root"])
                for key, payload in old_rows:
                    self.assertEqual(payload, solver.db.execute(
                        "SELECT payload FROM cnf_residual_v1 WHERE id=?", (key,)).fetchone()[0])
                solver.close()
                solver = ResidualSolver(path)
                cold = solver.solve(variants[-1])
                self.assertEqual(cold["answer"], expected)
                self.assertEqual(cold["metrics"].get("expanded_nodes", 0), 0)
                self.assertEqual(cold["metrics"]["verified_nodes"], 1 if expected else 2)
                solver.close()

    def test_subsumption_witness_tampering_and_dependency_changes(self):
        from experiments.compare_cnf_residuals import pigeonhole
        cnf = pigeonhole(3)
        cnf += [tuple(cnf[0]) + (4,)]
        solver = ResidualSolver()
        result = solver.solve(cnf)
        original = solver.checked[result["root"]]
        self.assertEqual(original["proof"]["kind"], "positive-subsumption-v1")
        cid, kept = original["proof"]["removed"][0]
        mutations = [dict(removed=[]), dict(removed=[[cid, cid]]),
                     dict(removed=[[cid, kept], [cid, kept]]),
                     dict(removed=[[cid, kept], [kept, cid]]),
                     dict(removed=[[cid, 0]]), dict(removed=[[cid, True]]),
                     dict(child="not the core")]
        for mutation in mutations:
            node = json.loads(json.dumps(original))
            node["proof"].update(mutation)
            with self.assertRaises(ValueError):
                solver._verify(result["root"], node)
        solver.close()
        # Removing the stronger choice invalidates the old equivalence. The
        # weakened formula is SAT: the fourth pigeon can share a true variable.
        weakened = cnf[1:]
        solver = ResidualSolver()
        self.assertFalse(solver.solve(cnf)["answer"])
        self.assertTrue(solver.solve(weakened)["answer"])
        solver.close()

    def test_minimal_overlap_is_not_erased(self):
        choices = [(1, 2, 3), (3, 4, 5)]
        cnf = choices + [(-a, -b) for a, b in itertools.combinations(range(1, 6), 2)]
        canonical, _ = normalize(cnf)
        core, removed = positive_core(canonical, Counter())
        self.assertEqual(removed, [])
        self.assertIsNone(matching_structure(core, Counter()))
        solver = ResidualSolver()
        self.assertTrue(solver.solve(cnf)["answer"])
        solver.close()


if __name__ == "__main__":
    unittest.main()
