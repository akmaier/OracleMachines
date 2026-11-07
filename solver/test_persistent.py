"""Integration tests against the actual compiled Lean engine."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

from solver.persistent import DEFAULT_ENGINE, PersistentSolver, checksum

VAR0 = "010"
NOT_VAR0 = VAR0 + "10"
UNSAT = VAR0 + NOT_VAR0 + "11"
DOUBLE_NOT_VAR0 = VAR0 + "1010"
TRUE = "0010"


@unittest.skipUnless(DEFAULT_ENGINE.is_file(), "Build oracleSolver first")
class PersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "results.sqlite3"

    def test_results_survive_restart_without_starting_solver(self):
        with PersistentSolver(self.path) as s:
            self.assertTrue(s.solve(VAR0)["answer"])
            self.assertFalse(s.solve(UNSAT)["answer"])
        with PersistentSolver(self.path) as s:
            self.assertEqual(s.solve(VAR0)["source"], "cache")
            self.assertEqual(s.solve(UNSAT)["source"], "cache")
            self.assertIsNone(s.process)
            self.assertEqual(s.stats()["entries"], 2)

    def test_learned_witness_transfers_after_restart(self):
        with PersistentSolver(self.path) as s:
            self.assertEqual(s.solve(VAR0)["source"], "fallback")
        with PersistentSolver(self.path) as s:
            r = s.solve(DOUBLE_NOT_VAR0)
            self.assertTrue(r["answer"])
            self.assertEqual(r["source"], "verified_witness")
            self.assertEqual(s.stats()["entries"], 2)

    def test_new_learning_retains_old_answers(self):
        with PersistentSolver(self.path) as s:
            s.solve(VAR0)
            self.assertTrue(s.solve(NOT_VAR0)["answer"])
            self.assertEqual(s.solve(VAR0)["source"], "cache")
            self.assertFalse(s.solve(UNSAT)["answer"])
            self.assertEqual(s.stats()["entries"], 3)
            self.assertEqual(s.audit(), {"checked": 3, "valid": True})

    def test_empty_witness_is_retained(self):
        with PersistentSolver(self.path) as s:
            self.assertEqual(s.solve(TRUE)["witness"], "")
        with PersistentSolver(self.path) as s:
            self.assertEqual(s.solve(TRUE)["source"], "cache")
            self.assertEqual(s.audit()["checked"], 1)

    def test_bad_or_incomplete_inputs_are_not_cached(self):
        with PersistentSolver(self.path) as s:
            for bits in ("x", "0", "", "11", "0111"):
                with self.assertRaises(ValueError):
                    s.solve(bits)
            self.assertEqual(s.stats()["entries"], 0)
            self.assertTrue(s.solve(VAR0)["answer"])

    def test_corruption_is_rejected(self):
        with PersistentSolver(self.path) as s:
            s.solve(VAR0)
            with s.db:
                s.db.execute("UPDATE results SET answer=0, witness=NULL")
            with self.assertRaisesRegex(ValueError, "integrity"):
                s.solve(VAR0)

    def test_semantic_audit_rejects_forged_negative_record(self):
        with PersistentSolver(self.path) as s:
            s.solve(VAR0)
            forged = checksum(s.engine_id, VAR0, False, None)
            with s.db:
                s.db.execute("UPDATE results SET answer=0, witness=NULL, checksum=?", (forged,))
            with self.assertRaisesRegex(ValueError, "semantic audit"):
                s.audit()

    def test_engine_namespaces_preserve_old_records(self):
        with PersistentSolver(self.path) as s:
            r = s.solve(VAR0)
            old = "previous-engine"
            with s.db:
                s.db.execute("UPDATE results SET engine=?, checksum=?",
                             (old, checksum(old, VAR0, True, r["witness"])))
                s.db.execute("DELETE FROM active_witness")
        with PersistentSolver(self.path) as s:
            self.assertEqual(s.solve(VAR0)["source"], "fallback")
            self.assertEqual(s.stats()["entries"], 1)
            self.assertEqual(s.stats()["all_engine_entries"], 2)

    def test_concurrent_writers_keep_exact_results(self):
        with PersistentSolver(self.path):
            pass

        def run(bits):
            with PersistentSolver(self.path) as s:
                return s.solve(bits)["answer"]

        with ThreadPoolExecutor(max_workers=2) as pool:
            answers = list(pool.map(run, [VAR0, UNSAT, VAR0, NOT_VAR0]))
        self.assertEqual(answers, [True, False, True, True])
        with PersistentSolver(self.path) as s:
            self.assertEqual(s.stats()["entries"], 3)
            self.assertEqual(s.audit()["checked"], 3)


if __name__ == "__main__":
    unittest.main()
