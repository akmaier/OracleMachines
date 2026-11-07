#!/usr/bin/env python3
"""Persistent results for the Lean-verified SAT core. Standard library only.

The local database is a trusted store of this engine's previous results. Row
checksums detect accidental corruption; they are not authentication against an
attacker. `audit` re-solves stored instances. No result is evicted automatically.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENGINE = ROOT / "formal/.lake/build/bin/oracleSolver"
DEFAULT_CACHE = ROOT / "solver/.cache/results.sqlite3"


def checksum(engine: str, bits: str, answer: bool, witness: str | None) -> str:
    payload = json.dumps([engine, bits, answer, witness], separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def check_bits(bits: str) -> None:
    if not isinstance(bits, str) or any(c not in "01" for c in bits):
        raise ValueError("An encoding must be a string containing only 0 and 1")


class PersistentSolver:
    def __init__(self, cache: Path = DEFAULT_CACHE, engine: Path = DEFAULT_ENGINE):
        start = time.perf_counter_ns()
        self.engine = Path(engine).resolve()
        if not self.engine.is_file():
            raise FileNotFoundError("Build the engine first: cd formal && lake build oracleSolver")
        self.engine_id = hashlib.sha256(self.engine.read_bytes()).hexdigest()
        self.cache = Path(cache)
        self.cache.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.cache, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            self.db.close()
            raise ValueError(f"Unsupported cache schema {version}; database left unchanged")
        with self.db:
            self.db.execute("""CREATE TABLE IF NOT EXISTS results (
                engine TEXT NOT NULL, bits TEXT NOT NULL, answer INTEGER NOT NULL,
                witness TEXT, acquisition_core_work INTEGER NOT NULL,
                created_ns INTEGER NOT NULL, checksum TEXT NOT NULL,
                PRIMARY KEY (engine, bits), CHECK (answer IN (0, 1)))""")
            self.db.execute("""CREATE TABLE IF NOT EXISTS active_witness (
                engine TEXT PRIMARY KEY, bits TEXT NOT NULL)""")
            self.db.execute("PRAGMA user_version=1")
        self.process: subprocess.Popen | None = None
        self.setup_ns = time.perf_counter_ns() - start

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        if self.process is not None:
            self.process.stdin.close()
            self.process.wait(timeout=30)
            self.process.stdout.close()
            self.process = None
        self.db.close()

    def _validate(self, row: sqlite3.Row) -> None:
        check_bits(row["bits"])
        if row["answer"] not in (0, 1):
            raise ValueError("Corrupt cache answer")
        if bool(row["answer"]):
            check_bits(row["witness"])
        elif row["witness"] is not None:
            raise ValueError("An UNSAT record cannot have a satisfying witness")
        expected = checksum(row["engine"], row["bits"], bool(row["answer"]), row["witness"])
        if row["checksum"] != expected:
            raise ValueError("Cache integrity check failed; refusing to reuse this record")

    def _candidate(self) -> str | None:
        row = self.db.execute("""SELECT r.* FROM active_witness a JOIN results r
            ON r.engine=a.engine AND r.bits=a.bits WHERE a.engine=?""",
            (self.engine_id,)).fetchone()
        if row is None:
            return None
        self._validate(row)
        if not row["answer"]:
            raise ValueError("The active witness refers to an UNSAT result")
        return row["witness"]

    def _activate(self, bits: str) -> None:
        self.db.execute("""INSERT INTO active_witness(engine,bits) VALUES (?,?)
            ON CONFLICT(engine) DO UPDATE SET bits=excluded.bits""", (self.engine_id, bits))

    def _live(self, bits: str, candidate: str | None = None, *, mode: str = "hybrid") -> dict:
        if self.process is None:
            self.process = subprocess.Popen(
                [str(self.engine)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                text=True, bufsize=1,
            )
        self.process.stdin.write(json.dumps({"bits": bits, "candidate": candidate, "mode": mode}) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("Lean solver exited without a result; no answer was cached")
        response = json.loads(line)
        if "error" in response:
            raise ValueError(response["error"])
        if type(response.get("answer")) is not bool or type(response.get("core_work")) is not int:
            raise ValueError("Invalid engine response; no answer was cached")
        if response["answer"]:
            check_bits(response.get("witness"))
        elif response.get("witness") is not None:
            raise ValueError("Invalid UNSAT engine response")
        return response

    def solve(self, bits: str, *, learn: bool = True) -> dict:
        start = time.perf_counter_ns()
        check_bits(bits)
        row = self.db.execute("SELECT * FROM results WHERE engine=? AND bits=?",
                              (self.engine_id, bits)).fetchone()
        if row is not None:
            self._validate(row)
            if row["answer"] and learn:
                with self.db:
                    self._activate(bits)
            return {"answer": bool(row["answer"]), "witness": row["witness"],
                    "source": "cache", "core_work": 0,
                    "original_acquisition_core_work": row["acquisition_core_work"],
                    "wall_ns": time.perf_counter_ns() - start}
        result = self._live(bits, self._candidate() if learn else None)
        answer, witness = result["answer"], result["witness"]
        with self.db:
            self.db.execute("""INSERT OR IGNORE INTO results
                (engine,bits,answer,witness,acquisition_core_work,created_ns,checksum)
                VALUES (?,?,?,?,?,?,?)""", (self.engine_id, bits, int(answer), witness,
                result["core_work"], time.time_ns(), checksum(self.engine_id, bits, answer, witness)))
            stored = self.db.execute("SELECT * FROM results WHERE engine=? AND bits=?",
                                     (self.engine_id, bits)).fetchone()
            self._validate(stored)
            if bool(stored["answer"]) != answer:
                raise ValueError("Conflicting exact results; transaction rolled back")
            if answer and learn:
                self._activate(bits)
        return {"answer": answer, "witness": witness,
                "source": "verified_witness" if result["fast"] else "fallback",
                "core_work": result["core_work"], "wall_ns": time.perf_counter_ns() - start}

    def stats(self) -> dict:
        row = self.db.execute("""SELECT count(*) AS entries, coalesce(sum(answer),0) AS sat
            FROM results WHERE engine=?""", (self.engine_id,)).fetchone()
        total = self.db.execute("SELECT count(*) FROM results").fetchone()[0]
        return {"engine": self.engine_id, "entries": row["entries"], "sat": row["sat"],
                "unsat": row["entries"] - row["sat"], "all_engine_entries": total}

    def audit(self) -> dict:
        rows = self.db.execute("SELECT * FROM results WHERE engine=? ORDER BY bits",
                               (self.engine_id,)).fetchall()
        for row in rows:
            self._validate(row)
            result = self._live(row["bits"])
            if result["answer"] != bool(row["answer"]):
                raise ValueError("Cache semantic audit failed")
            if row["answer"] and not self._live(row["bits"], row["witness"])["fast"]:
                raise ValueError("Cached witness does not satisfy its formula")
        return {"checked": len(rows), "valid": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--engine", type=Path, default=DEFAULT_ENGINE)
    sub = parser.add_subparsers(dest="command", required=True)
    solve = sub.add_parser("solve")
    solve.add_argument("bits")
    solve.add_argument("--no-learn", action="store_true")
    sub.add_parser("stats")
    sub.add_parser("audit")
    args = parser.parse_args()
    try:
        with PersistentSolver(args.cache, args.engine) as solver:
            if args.command == "solve":
                result = solver.solve(args.bits, learn=not args.no_learn)
            elif args.command == "stats":
                result = solver.stats()
            else:
                result = solver.audit()
            result["setup_ns"] = solver.setup_ns
            print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
