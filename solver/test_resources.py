from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from solver.persistent import PersistentSolver, checksum
from solver.resources import BudgetExceeded, Deadline, bounded_run, stop_process
from solver.test_fast import MIXED, HARD_UNSAT


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "results.sqlite3"

    def stalled(self):
        return subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"],
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def test_native_deadline_reaps_worker_and_recovers(self):
        with PersistentSolver(self.path, query_timeout=0.1) as s:
            s.process = self.stalled()
            child = s.process
            start = time.monotonic()
            with self.assertRaises(BudgetExceeded):
                s.solve(MIXED)
            self.assertLess(time.monotonic() - start, 2)
            self.assertIsNotNone(child.poll())
            self.assertIsNone(s.process)
            self.assertEqual(s.stats()["entries"], 0)
            s.query_timeout = 5
            self.assertTrue(s.solve(MIXED)["answer"])

    def test_blocked_write_is_also_bounded(self):
        with PersistentSolver(self.path, query_timeout=0.05) as s:
            s.process = self.stalled()
            with self.assertRaises(BudgetExceeded):
                s._request({"mode": "prepare", "bits": "0010" + "1010" * 50000})
            self.assertIsNone(s.process)

    def test_oversized_response_is_rejected(self):
        with PersistentSolver(self.path, max_message_bytes=4096) as s:
            s.process = subprocess.Popen([sys.executable, "-c", "print('x'*10000, flush=True)"],
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            with self.assertRaisesRegex(BudgetExceeded, "response"):
                s.solve(MIXED)
            self.assertEqual(s.stats()["entries"], 0)

    def test_input_and_proof_limits_do_not_create_false_answers(self):
        with PersistentSolver(self.path, max_input_bytes=2) as s:
            with self.assertRaisesRegex(BudgetExceeded, "Input"):
                s.solve(MIXED)
            self.assertEqual(s.stats()["entries"], 0)
        with PersistentSolver(self.path, backend="cadical", max_proof_bytes=1) as s:
            with self.assertRaisesRegex(BudgetExceeded, "LRAT"):
                s.solve(HARD_UNSAT)
            self.assertEqual(s.stats()["entries"], 0)

    def test_strict_cache_rejects_semantically_forged_rows(self):
        with PersistentSolver(self.path, verify_cache=True) as s:
            s.solve(MIXED)
            with s.db:
                s.db.execute("UPDATE results SET witness=?,checksum=?", ("00", checksum(s.engine_id, MIXED, True, "00")))
            with self.assertRaisesRegex(ValueError, "Cached certificate"):
                s.solve(MIXED)
            with s.db:
                s.db.execute("UPDATE results SET answer=0,witness=NULL,checksum=?", (checksum(s.engine_id, MIXED, False, None),))
            with self.assertRaisesRegex(ValueError, "Cached certificate"):
                s.solve(MIXED)
            self.assertEqual(s.stats()["entries"], 1)  # Do not silently delete evidence.

    def test_strict_cache_checks_sat_and_unsat_across_restart(self):
        with PersistentSolver(self.path) as s:
            s.solve(MIXED)
            s.solve(HARD_UNSAT)
        with PersistentSolver(self.path, verify_cache=True) as s:
            for bits, expected in [(MIXED, True), (HARD_UNSAT, False)]:
                r = s.solve(bits)
                self.assertEqual(r["answer"], expected)
                self.assertTrue(r["cache_verified"])
                self.assertIsNone(r["counted_work"])
                self.assertGreater(r["parse_work"], 0)

    def test_disjoint_phases_cover_measured_query(self):
        with PersistentSolver(self.path) as s:
            for _ in range(2):
                r = s.solve(MIXED)
                self.assertEqual(sum(r["phase_ns"].values()), r["wall_ns"])
                self.assertTrue(all(v >= 0 for v in r["phase_ns"].values()))
                self.assertGreater(r["service_peak_rss_bytes"], 0)

    def test_deadline_also_covers_certificate_verification(self):
        with PersistentSolver(self.path, backend="cadical", query_timeout=0.3) as s:
            request = s._request
            def stall_verification(payload):
                if payload["mode"] == "verify_certificate":
                    stop_process(s.process)
                    s.process = self.stalled()
                return request(payload)
            with patch.object(s, "_request", side_effect=stall_verification):
                with self.assertRaises(BudgetExceeded):
                    s.solve(HARD_UNSAT)
            self.assertIsNone(s.process)
            self.assertEqual(s.stats()["entries"], 0)

    def test_external_output_and_runtime_are_bounded(self):
        directory = Path(self.temp.name)
        for script, seconds, pattern in [("print('x'*10000)", 2, "output"),
                                          ("import time; time.sleep(30)", 0.1, "deadline")]:
            with self.assertRaisesRegex(BudgetExceeded, pattern):
                bounded_run([sys.executable, "-c", script], directory, Deadline(3),
                            seconds, 1024, directory / "proof", 1024)

    def test_write_lock_timeout_rolls_back_and_service_recovers(self):
        import sqlite3
        with PersistentSolver(self.path, query_timeout=0.1) as s:
            other = sqlite3.connect(self.path)
            try:
                other.execute("BEGIN IMMEDIATE")
                start = time.monotonic()
                with self.assertRaises(sqlite3.OperationalError):
                    s.solve(MIXED)
                self.assertLess(time.monotonic() - start, 1)
                self.assertEqual(s.stats()["entries"], 0)
            finally:
                other.rollback()
                other.close()
            s.query_timeout = 2
            self.assertTrue(s.solve(MIXED)["answer"])

    def test_invalid_deadlines(self):
        for value in (0, -1, float("inf"), float("nan")):
            with self.assertRaises(ValueError):
                PersistentSolver(self.path, query_timeout=value)

    def test_restricted_coverage_is_explicit(self):
        with PersistentSolver(self.path) as s:
            self.assertTrue(s._request({"bits": "010", "mode": "restricted"})["answer"])
            self.assertFalse(s._request({"bits": "00", "mode": "restricted"})["answer"])
            for bits, stage in [("010", 2), ("01" + "1" * 20 + "0", 100)]:
                result = s._request({"bits": bits, "mode": "restricted", "stage": stage})
                self.assertFalse(result["covered"])
                self.assertIsNone(result["answer"])


if __name__ == "__main__":
    unittest.main()
