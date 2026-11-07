"""Checks of the native CNF/LRAT boundary and durable accelerated service."""
from pathlib import Path
import itertools
import json
import random
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from solver.persistent import DEFAULT_ENGINE, PersistentSolver, find_cadical


def var(i):
    return "01" + "1" * i + "0"


def neg(f):
    return f + "10"


def conj(f, g):
    return f + g + "11"


def disj(f, g):
    return neg(conj(neg(f), neg(g)))


def cnf_bits(clauses):
    formula = "0010"
    for clause in clauses:
        term = "00"
        for i, sign in clause:
            term = disj(term, var(i) if sign else neg(var(i)))
        formula = conj(formula, term)
    return formula


MIXED = conj(var(0), neg(var(1)))
HARD_UNSAT = cnf_bits([[(0, a), (1, b)] for a in (False, True) for b in (False, True)])


@unittest.skipUnless(DEFAULT_ENGINE.is_file() and find_cadical(), "Build with solver/build.sh first")
class FastTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "results.sqlite3"

    def test_external_results_require_checked_model_or_lrat(self):
        with PersistentSolver(self.path, backend="cadical") as s:
            sat = s.solve(MIXED)
            unsat = s.solve(HARD_UNSAT, learn=False)
            self.assertEqual(sat["witness"], "10")
            self.assertFalse(unsat["answer"])
            self.assertEqual(sat["backend"], "cadical")
            self.assertEqual(unsat["backend"], "cadical")
            self.assertIsNone(unsat["counted_work"])
            self.assertIsNone(unsat["nodes"])
            self.assertFalse(unsat["counted_complete"])
            self.assertGreater(unsat["verification_ns"], 0)
            self.assertEqual(s.audit()["checked"], 2)

    def test_lrat_archive_and_transfer_survive_restart(self):
        with PersistentSolver(self.path, backend="cadical") as s:
            s.solve(HARD_UNSAT)
        with PersistentSolver(self.path, backend="cadical") as s:
            hit = s.solve(HARD_UNSAT)
            self.assertEqual(hit["source"], "cache")
            self.assertIsNone(hit["original_acquisition_core_work"])
            self.assertFalse(hit["original_measurements"]["counted_complete"])
            self.assertIsNone(s.process)
            transferred = s.solve(neg(neg(HARD_UNSAT)))
            self.assertEqual(transferred["source"], "verified_refutation")
            self.assertEqual(s.audit()["checked"], 2)

    def test_false_circuit_certificate_is_checked_on_new_formula(self):
        with PersistentSolver(self.path, backend="cadical") as s:
            f = conj(var(0), neg(var(0)))
            self.assertFalse(s.solve(f)["answer"])
            self.assertEqual(s.solve(conj(f, var(100)))["source"], "verified_refutation")
            self.assertTrue(s.solve(neg(f))["answer"])
            self.assertFalse(s._verify_certificate(MIXED, {"format": "aig_false"}))

    def test_mutated_or_wrong_formula_lrat_is_rejected(self):
        with PersistentSolver(self.path, backend="cadical") as s:
            s.solve(HARD_UNSAT)
            certificate = json.loads(s.db.execute("SELECT certificate FROM proofs").fetchone()[0])
            self.assertFalse(s._verify_certificate(MIXED, certificate))
            self.assertFalse(s._verify_certificate(HARD_UNSAT, {"format": "lrat", "text": "99 0 0\n"}))
            with self.assertRaises(ValueError):
                s._verify_certificate(HARD_UNSAT, {"format": "lrat", "text": "garbage"})

    def test_external_solver_cannot_inject_negative_answer(self):
        def fake(args, *_pos, **_):
            Path(args[-1]).write_text("99 0 0\n")
            return subprocess.CompletedProcess(args, 20, "s UNSATISFIABLE\n", "")
        with PersistentSolver(self.path, backend="cadical") as s:
            with patch("solver.persistent.bounded_run", side_effect=fake):
                with self.assertRaisesRegex(ValueError, "UNSAT proof rejected"):
                    s.solve(MIXED)
            self.assertEqual(s.stats()["entries"], 0)

    def test_external_solver_cannot_inject_positive_answer(self):
        with PersistentSolver(self.path, backend="cadical") as s:
            with patch("solver.persistent.bounded_run", return_value=subprocess.CompletedProcess([], 10, "s SATISFIABLE\nv 0\n", "")):
                with self.assertRaisesRegex(ValueError, "SAT witness rejected"):
                    s.solve(HARD_UNSAT)
            self.assertEqual(s.stats()["entries"], 0)

    def test_timeout_has_no_negative_cache_entry(self):
        with PersistentSolver(self.path, backend="cadical") as s:
            with patch("solver.persistent.bounded_run", side_effect=subprocess.TimeoutExpired("cadical", 0.01)):
                with self.assertRaisesRegex(RuntimeError, "timed out"):
                    s.solve(MIXED)
            self.assertEqual(s.stats()["entries"], 0)

    def test_missing_external_solver_uses_verified_fallback(self):
        with PersistentSolver(self.path, backend="cadical") as s:
            s.cadical = None
            r = s.solve(MIXED)
            self.assertTrue(r["answer"])
            self.assertEqual(r["backend"], "lean_fallback")
            self.assertIsNone(r["nodes"])

    def test_bounded_attempt_exhaustion_does_not_mean_unsat(self):
        with PersistentSolver(self.path, backend="auto") as s:
            limited = s._request({"bits": MIXED, "mode": "prepare", "search_budget": 1})
            self.assertTrue(limited["pending"])
            self.assertNotIn("answer", limited)
            with patch("solver.persistent.bounded_run", side_effect=AssertionError("Should fit the local budget")):
                r = s.solve(MIXED)
            self.assertTrue(r["answer"])
            self.assertEqual(r["backend"], "preprocess")

    def test_shared_circuit_and_sparse_model_mapping(self):
        with PersistentSolver(self.path, backend="cadical") as s:
            first = s._request({"bits": MIXED, "mode": "prepare"})
            repeated = s._request({"bits": conj(MIXED, MIXED), "mode": "prepare"})
            self.assertEqual(first["dimacs"], repeated["dimacs"])
            r = s.solve(conj(var(100), neg(var(0))))
            self.assertEqual(len(r["witness"]), 101)
            self.assertEqual(r["witness"][0], "0")
            self.assertEqual(r["witness"][100], "1")

    def test_candidate_selection_does_not_scan_duplicate_archive(self):
        with PersistentSolver(self.path, backend="cadical") as s:
            for i in range(100):
                s.solve(var(0) + "1010" * i)
            with patch.object(s, "_validate", wraps=s._validate) as validate:
                self.assertEqual(s._candidates(), ["1"])
                self.assertLessEqual(validate.call_count, 5)
            changes = s.db.total_changes
            s.solve(var(0) + "1010" * 99)
            self.assertEqual(s.db.total_changes, changes)

    def test_random_cnf_matches_independent_truth_tables(self):
        rng = random.Random(20261108)
        external = 0
        with PersistentSolver(self.path, backend="cadical") as s:
            for _ in range(120):
                clauses = [[(i, bool(rng.randrange(2))) for i in rng.sample(range(5), 3)]
                           for _ in range(rng.randrange(15, 30))]
                expected = any(all(any(a[i] == sign for i, sign in c) for c in clauses)
                               for a in itertools.product((False, True), repeat=5))
                r = s.solve(cnf_bits(clauses), learn=False)
                self.assertEqual(r["answer"], expected)
                external += r.get("backend") == "cadical"
                if expected:
                    values = [b == "1" for b in r["witness"]]
                    self.assertTrue(all(any(values[i] == sign for i, sign in c) for c in clauses))
            self.assertGreater(external, 40)

    def test_warm_json_lines_service_keeps_all_results(self):
        requests = [{"bits": MIXED}, {"bits": HARD_UNSAT}, {"bits": MIXED}, {"bits": "invalid"}]
        r = subprocess.run(["python3", str(Path(__file__).with_name("persistent.py")),
                            "--cache", str(self.path), "serve"],
                           input="".join(json.dumps(x) + "\n" for x in requests),
                           text=True, capture_output=True, check=True)
        answers = [json.loads(line) for line in r.stdout.splitlines()]
        self.assertEqual([a["answer"] for a in answers[:3]], [True, False, True])
        self.assertEqual(answers[2]["source"], "cache")
        self.assertIn("error", answers[3])
        with PersistentSolver(self.path, backend="cadical") as s:
            self.assertEqual(s.stats()["entries"], 2)


if __name__ == "__main__":
    unittest.main()
