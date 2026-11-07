"""Integration tests against the actual compiled Lean engine."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import itertools
import json
import random
import sqlite3
import time
import unittest

from solver.persistent import DEFAULT_ENGINE, PersistentSolver, checksum, proof_checksum

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

    def test_parser_cost_is_retained_after_restart(self):
        with PersistentSolver(self.path) as s:
            first = s.solve(DOUBLE_NOT_VAR0)
            self.assertGreater(first["parse_work"], 0)
            self.assertLessEqual(first["parse_work"], 8 * len(DOUBLE_NOT_VAR0) + 7)
            self.assertEqual(first["counted_work"], first["core_work"] + first["parse_work"])
        with PersistentSolver(self.path) as s:
            hit = s.solve(DOUBLE_NOT_VAR0)
            self.assertEqual(hit["counted_work"], 0)
            self.assertEqual(hit["original_acquisition_parse_work"], first["parse_work"])
            self.assertIsNone(s.process)

    def test_v1_migration_retains_answers_and_marks_unknown_cost(self):
        # Real legacy schema, not a mock of the migration implementation.
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE results (
                engine TEXT NOT NULL, bits TEXT NOT NULL, answer INTEGER NOT NULL,
                witness TEXT, acquisition_core_work INTEGER NOT NULL,
                created_ns INTEGER NOT NULL, checksum TEXT NOT NULL,
                PRIMARY KEY (engine,bits), CHECK (answer IN (0,1)))""")
            db.execute("CREATE TABLE active_witness (engine TEXT PRIMARY KEY, bits TEXT NOT NULL)")
            db.execute("INSERT INTO results VALUES (?,?,?,?,?,?,?)",
                       ("legacy", UNSAT, 0, None, 46, time.time_ns(), checksum("legacy", UNSAT, False, None)))
            db.execute("PRAGMA user_version=1")
        with PersistentSolver(self.path) as s:
            old = s.db.execute("SELECT * FROM results WHERE engine='legacy'").fetchone()
            self.assertEqual(old["answer"], 0)
            self.assertIsNone(old["acquisition_parse_work"])
            self.assertEqual(s.db.execute("PRAGMA user_version").fetchone()[0], 3)
            self.assertEqual(s.revalidate(), {"previous_inputs": 1, "revalidated": 1, "already_current": 0})
            self.assertEqual(s.stats()["all_engine_entries"], 2)
            self.assertFalse(s.solve(UNSAT)["answer"])
            self.assertEqual(s.revalidate()["already_current"], 1)
            self.assertEqual(s.audit()["checked"], 1)

    def test_revalidation_recomputes_instead_of_trusting_old_answers(self):
        with PersistentSolver(self.path) as s:
            with s.db:
                s.db.execute("""INSERT INTO results
                    (engine,bits,answer,witness,acquisition_core_work,created_ns,checksum)
                    VALUES (?,?,?,?,?,?,?)""", ("old", VAR0, 0, None, 0,
                    time.time_ns(), checksum("old", VAR0, False, None)))
            self.assertEqual(s.revalidate()["revalidated"], 1)
            self.assertTrue(s.solve(VAR0)["answer"])
            self.assertEqual(s.db.execute("SELECT answer FROM results WHERE engine='old'").fetchone()[0], 0)
            self.assertEqual(s.audit()["checked"], 1)

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

    def test_sparse_variable_does_not_enumerate_unused_indices(self):
        with PersistentSolver(self.path) as s:
            r = s._live("01" + "1" * 100 + "0", mode="baseline")
            self.assertEqual(r["witness"], "0" * 100 + "1")
            self.assertEqual(r["nodes"], 3)
            self.assertLess(r["core_work"], 100000)

    def test_root_conflict_prunes_all_assignments(self):
        formula = VAR0
        for i in range(1, 30):
            formula += "01" + "1" * i + "0" + "11"
        with PersistentSolver(self.path) as s:
            r = s._live("00" + formula + "11", mode="baseline")
            self.assertFalse(r["answer"])
            self.assertEqual(r["nodes"], 1)
            self.assertEqual(r["certificate"], "conflict")

    def test_portfolio_retains_alternating_witnesses(self):
        with PersistentSolver(self.path) as s:
            s.solve(VAR0)
            s.solve(NOT_VAR0)
        with PersistentSolver(self.path) as s:
            for bits in (DOUBLE_NOT_VAR0, NOT_VAR0 + "1010", VAR0 + "10101010"):
                self.assertEqual(s.solve(bits)["source"], "verified_witness")

    def test_refutation_transfers_to_conjunction_after_restart(self):
        with PersistentSolver(self.path) as s:
            s.solve(UNSAT)
        with PersistentSolver(self.path) as s:
            extension = UNSAT + "01" + "1" * 100 + "0" + "11"
            r = s.solve(extension)
            self.assertFalse(r["answer"])
            self.assertEqual(r["source"], "verified_refutation")
            self.assertEqual(r["nodes"], 0)
            self.assertEqual(s.stats()["refutations"], 2)
            self.assertEqual(s.audit()["checked"], 2)

    def test_refutation_does_not_transfer_under_negation_or_renaming(self):
        with PersistentSolver(self.path) as s:
            s.solve(UNSAT)
            self.assertTrue(s.solve(UNSAT + "10")["answer"])
            var1 = "0110"
            r = s.solve(var1 + var1 + "1011")
            self.assertFalse(r["answer"])
            self.assertEqual(r["source"], "fallback")

    def test_invalid_refutations_cannot_reject_satisfiable_formula(self):
        with PersistentSolver(self.path) as s:
            for p in ("conflict", [0, "conflict", "conflict"],
                      [0, "conflict", [0, "conflict", "conflict"]]):
                r = s._live(VAR0, proofs=[p])
                self.assertTrue(r["answer"])
                self.assertEqual(r["reuse_kind"], "none")
            for p in ([], [0, "conflict"], [-1, "conflict", "conflict"], "wrong"):
                with self.assertRaises(ValueError):
                    s._live(VAR0, proofs=[p])

    def test_refutation_corruption_and_semantic_audit(self):
        with PersistentSolver(self.path) as s:
            s.solve(UNSAT)
            certificate = json.dumps("conflict")
            with s.db:
                s.db.execute("UPDATE proofs SET certificate=?", (certificate,))
            with self.assertRaisesRegex(ValueError, "integrity"):
                s.solve(UNSAT + "1010")
            with s.db:
                s.db.execute("UPDATE proofs SET checksum=?",
                             (proof_checksum(s.engine_id, UNSAT, certificate),))
            with self.assertRaisesRegex(ValueError, "does not establish"):
                s.audit()
            # A bad certificate is a rejected proposal, not a negative answer.
            self.assertEqual(s.solve(UNSAT + "1010")["source"], "fallback")

    def test_v2_migration_preserves_records_without_inventing_proofs(self):
        with PersistentSolver(self.path) as s:
            s.solve(UNSAT)
            old_rows = [tuple(r) for r in s.db.execute("SELECT * FROM results")]
            with s.db:
                s.db.execute("DROP TABLE proofs")
                s.db.execute("PRAGMA user_version=2")
        with PersistentSolver(self.path) as s:
            self.assertEqual([tuple(r) for r in s.db.execute("SELECT * FROM results")], old_rows)
            self.assertEqual(s.stats()["refutations"], 0)
            self.assertEqual(s.audit()["checked"], 1)

    def test_search_matches_independent_truth_tables(self):
        rng = random.Random(20261107)

        def generate(depth):
            if depth == 0 or rng.randrange(4) == 0:
                return ("var", rng.randrange(4)) if rng.randrange(5) else ("false",)
            if rng.randrange(3) == 0:
                return ("not", generate(depth - 1))
            return ("and", generate(depth - 1), generate(depth - 1))

        def encode(f):
            if f[0] == "false":
                return "00"
            if f[0] == "var":
                return "01" + "1" * f[1] + "0"
            if f[0] == "not":
                return encode(f[1]) + "10"
            return encode(f[1]) + encode(f[2]) + "11"

        def evaluate(f, assignment):
            if f[0] == "false":
                return False
            if f[0] == "var":
                return assignment[f[1]]
            if f[0] == "not":
                return not evaluate(f[1], assignment)
            return evaluate(f[1], assignment) and evaluate(f[2], assignment)

        with PersistentSolver(self.path) as s:
            for _ in range(400):
                f = generate(5)
                expected = any(evaluate(f, a) for a in itertools.product((False, True), repeat=4))
                r = s._live(encode(f), mode="baseline")
                self.assertEqual(r["answer"], expected, repr(f))
                self.assertEqual(s._live(encode(f), mode="exhaustive")["answer"], expected)
                self.assertLessEqual(r["nodes"], 31)
                if expected:
                    self.assertTrue(evaluate(f, [c == "1" for c in r["witness"]] + [False] * 4))
                else:
                    checked = s._live(encode(f), proofs=[r["certificate"]])
                    self.assertEqual(checked["reuse_kind"], "refutation")


if __name__ == "__main__":
    unittest.main()
