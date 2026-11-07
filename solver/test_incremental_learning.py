import itertools
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

from solver.incremental import DEFAULT_INCREMENTAL
from solver.learning import Predictor
from solver.persistent import PersistentSolver
from solver.test_fast import cnf_bits, MIXED, HARD_UNSAT, neg


class LearningTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "results.sqlite3"

    def test_learned_rule_transfers_to_new_witness_and_survives_restart(self):
        training = cnf_bits([[(i, i % 2 == 0)] for i in range(12)])
        held_out = cnf_bits([[(i, i % 3 == 0)] for i in range(20)])
        with PersistentSolver(self.path, learned=True) as s:
            first = s.solve(training)
            self.assertFalse(first["learned_proposed"])
            self.assertGreater(first["phase_ns"]["training"], 0)
        with PersistentSolver(self.path, learned=True) as s:
            r = s.solve(held_out)
            self.assertEqual(r["source"], "learned_witness")
            self.assertEqual(r["witness"], "".join("1" if i % 3 == 0 else "0" for i in range(20)))
            self.assertNotEqual(first["witness"], r["witness"])
            self.assertLess(r["model_bytes"], 256)
            self.assertEqual(s.stats()["entries"], 2)

    def test_wrong_prediction_requires_fallback(self):
        with PersistentSolver(self.path, learned=True) as s:
            s.solve(MIXED)
            with patch.object(Predictor, "predict", return_value="0" * 100):
                result = s.solve(HARD_UNSAT)
            self.assertFalse(result["answer"])
            self.assertFalse(result["learned_accepted"])

    def test_model_size_is_bounded_and_training_respects_no_learn(self):
        with PersistentSolver(self.path, learned=True) as s:
            s.solve(MIXED, learn=False)
            self.assertEqual(s.db.execute("SELECT count(*) FROM models").fetchone()[0], 0)
        p = Predictor({"weights": [10000] * 5, "examples": 2**63 - 1, "updates": 2**63 - 1})
        from solver.resources import Deadline
        p.update({0: (1, 32, 32, 1, 1)}, "0", Deadline(2))
        self.assertLess(len(p.dump()), 256)

    def test_concurrent_acquisitions_preserve_both_model_updates(self):
        import concurrent.futures
        import threading
        barrier = threading.Barrier(2)
        with PersistentSolver(self.path):
            pass
        def acquire(width):
            with PersistentSolver(self.path, learned=True) as s:
                original = s._fast_live
                def synchronized(*args):
                    barrier.wait(timeout=5)
                    return original(*args)
                with patch.object(s, "_fast_live", side_effect=synchronized):
                    s.solve(cnf_bits([[(i, i % 2 == 0)] for i in range(width)]))
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(acquire, [12, 20]))
        with PersistentSolver(self.path, learned=True) as s:
            state = json.loads(s.db.execute("SELECT state FROM models").fetchone()[0])
            self.assertEqual(state["examples"], 32)
            self.assertEqual(s.stats()["entries"], 2)


@unittest.skipUnless(DEFAULT_INCREMENTAL.is_file(), "Build the incremental bridge first")
class IncrementalTests(unittest.TestCase):
    setUp = LearningTests.setUp
    def test_state_survives_and_assumptions_do_not_leak(self):
        with PersistentSolver(self.path, backend="cadical", incremental=True) as s:
            a = s.solve(MIXED, learn=False)
            b = s.solve(HARD_UNSAT, learn=False)
            c = s.solve(neg(HARD_UNSAT), learn=False)
            d = s.solve(neg(neg(MIXED)), learn=False)
            self.assertEqual([a["answer"], b["answer"], c["answer"], d["answer"]], [True, False, True, True])
            self.assertEqual(a["backend"], "incremental")
            self.assertEqual(b["backend"], "cadical")  # independent negative proof
            self.assertEqual(d["incremental"]["queries"], 3)  # negation may be solved by a phase witness
            self.assertGreaterEqual(d["incremental"]["learned_clauses_total"], b["incremental"]["learned_clauses_total"])
            self.assertEqual(d["incremental"]["new_definition_clauses"], 0)

    def test_forged_incremental_results_cannot_bypass_checks(self):
        with PersistentSolver(self.path, backend="cadical", incremental=True) as s:
            with patch.object(s.incremental, "propose", return_value={"verdict": 10, "witness": "00"}):
                with self.assertRaisesRegex(ValueError, "witness rejected"):
                    s.solve(MIXED)
            with patch.object(s.incremental, "propose", return_value={"verdict": 20}):
                self.assertTrue(s.solve(MIXED)["answer"])
            self.assertEqual(s.stats()["entries"], 1)

    def test_random_queries_match_truth_tables_with_shared_state(self):
        rng = random.Random(707)
        with PersistentSolver(self.path, backend="cadical", incremental=True) as s:
            used = 0
            for _ in range(80):
                clauses = [[(i, bool(rng.randrange(2))) for i in rng.sample(range(5), 3)] for _ in range(22)]
                expected = any(all(any(a[i] == b for i, b in c) for c in clauses)
                               for a in itertools.product((False, True), repeat=5))
                result = s.solve(cnf_bits(clauses), learn=False)
                self.assertEqual(result["answer"], expected)
                used += result.get("incremental") is not None
            self.assertGreater(used, 30)


if __name__ == "__main__":
    unittest.main()
