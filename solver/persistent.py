#!/usr/bin/env python3
"""Persistent results for the Lean-verified SAT core. Standard library only.

The local database is a trusted store of this engine's previous results. Row
checksums detect accidental corruption; they are not authentication against an
attacker. `audit` re-solves stored instances. No result is evicted automatically.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENGINE = ROOT / "formal/.lake/build/bin/oracleSolver"
DEFAULT_CACHE = ROOT / "solver/.cache/results.sqlite3"
PORTFOLIO_SIZE = 4
MAX_PROPOSAL_BYTES = 65536


@functools.lru_cache(maxsize=8)
def _fingerprint(path: str, version: tuple) -> str:
    # The stat tuple invalidates this process-local cache after a binary change.
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def find_cadical() -> Path | None:
    configured = os.environ.get("ORACLE_CADICAL") or shutil.which("cadical")
    hint = ROOT / "formal/.lake/cadical-path"
    if not configured and hint.is_file():
        configured = hint.read_text().strip()
    if not configured:
        pinned = Path.home() / ".elan/toolchains/leanprover--lean4---v4.24.0/bin/cadical"
        if pinned.is_file():
            configured = str(pinned)
    return Path(configured).resolve() if configured and Path(configured).is_file() else None


def checksum(engine: str, bits: str, answer: bool, witness: str | None) -> str:
    payload = json.dumps([engine, bits, answer, witness], separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def proof_checksum(engine: str, bits: str, certificate: str) -> str:
    payload = json.dumps([engine, bits, certificate], separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def check_bits(bits: str) -> None:
    if not isinstance(bits, str) or any(c not in "01" for c in bits):
        raise ValueError("An encoding must be a string containing only 0 and 1")


class PersistentSolver:
    def __init__(self, cache: Path = DEFAULT_CACHE, engine: Path = DEFAULT_ENGINE, *,
                 backend: str = "auto", cadical: Path | None = None, timeout: float = 30):
        start = time.perf_counter_ns()
        self.engine = Path(engine).resolve()
        if not self.engine.is_file():
            raise FileNotFoundError("Build the engine first: cd formal && lake build oracleSolver")
        if backend not in ("auto", "lean", "cadical"):
            raise ValueError("Unknown solver backend")
        if timeout <= 0:
            raise ValueError("The external solver timeout must be positive")
        self.backend, self.timeout = backend, timeout
        self.cadical = Path(cadical).resolve() if cadical is not None else find_cadical()
        if backend == "cadical" and (self.cadical is None or not self.cadical.is_file()):
            raise FileNotFoundError("CaDiCaL is unavailable; run solver/build.sh or set ORACLE_CADICAL")
        st = self.engine.stat()
        self.engine_id = _fingerprint(str(self.engine), (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns, st.st_ctime_ns))
        self.cache = Path(cache)
        self.cache.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.cache, timeout=30)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        try:
            with self.db:
                # Serialize migrations as well as ordinary writes.
                self.db.execute("BEGIN IMMEDIATE")
                version = self.db.execute("PRAGMA user_version").fetchone()[0]
                if version not in (0, 1, 2, 3, 4):
                    raise ValueError(f"Unsupported cache schema {version}; records left unchanged")
                self.db.execute("""CREATE TABLE IF NOT EXISTS results (
                    engine TEXT NOT NULL, bits TEXT NOT NULL, answer INTEGER NOT NULL,
                    witness TEXT, acquisition_core_work INTEGER NOT NULL,
                    created_ns INTEGER NOT NULL, checksum TEXT NOT NULL,
                    acquisition_parse_work INTEGER,
                    PRIMARY KEY (engine, bits), CHECK (answer IN (0, 1)))""")
                self.db.execute("""CREATE TABLE IF NOT EXISTS active_witness (
                    engine TEXT PRIMARY KEY, bits TEXT NOT NULL)""")
                if version == 1:
                    # NULL means the historical parser cost was not measured.
                    self.db.execute("ALTER TABLE results ADD COLUMN acquisition_parse_work INTEGER")
                self.db.execute("""CREATE TABLE IF NOT EXISTS proofs (
                    engine TEXT NOT NULL, bits TEXT NOT NULL, certificate TEXT NOT NULL,
                    checksum TEXT NOT NULL, PRIMARY KEY (engine,bits))""")
                self.db.execute("""CREATE INDEX IF NOT EXISTS result_candidates
                    ON results(engine,answer,created_ns DESC)""")
                self.db.execute("""CREATE TABLE IF NOT EXISTS portfolio (
                    engine TEXT NOT NULL, kind TEXT NOT NULL, token TEXT NOT NULL,
                    bits TEXT NOT NULL, seen_ns INTEGER NOT NULL,
                    PRIMARY KEY(engine,kind,token))""")
                self.db.execute("""CREATE INDEX IF NOT EXISTS portfolio_recent
                    ON portfolio(engine,kind,seen_ns DESC)""")
                self.db.execute("""CREATE TABLE IF NOT EXISTS measurements (
                    engine TEXT NOT NULL, bits TEXT NOT NULL, details TEXT NOT NULL,
                    PRIMARY KEY(engine,bits))""")
                if version < 4:
                    # An index of distinct proposals; the archive remains intact.
                    for row in self.db.execute("SELECT engine,bits,witness,created_ns FROM results WHERE answer=1").fetchall():
                        self._index_candidate(row["engine"], "witness", row["bits"], row["witness"], row["created_ns"])
                    for row in self.db.execute("""SELECT p.*,r.created_ns FROM proofs p JOIN results r
                            ON p.engine=r.engine AND p.bits=r.bits WHERE r.answer=0""").fetchall():
                        self._index_candidate(row["engine"], "proof", row["bits"], row["certificate"], row["created_ns"])
                self.db.execute("PRAGMA user_version=4")
        except Exception:
            self.db.close()
            raise
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

    def _candidates(self) -> list[str]:
        active = self._candidate()
        candidates = [] if active is None else [active]
        for row in self.db.execute("""SELECT r.* FROM portfolio p JOIN results r
                ON r.engine=p.engine AND r.bits=p.bits
                WHERE p.engine=? AND p.kind='witness' ORDER BY p.seen_ns DESC LIMIT ?""",
                (self.engine_id, PORTFOLIO_SIZE)):
            self._validate(row)
            if row["witness"] not in candidates:
                candidates.append(row["witness"])
            if len(candidates) == PORTFOLIO_SIZE:
                break
        return candidates

    def _validate_proof(self, row: sqlite3.Row):
        if row["checksum"] != proof_checksum(row["engine"], row["bits"], row["certificate"]):
            raise ValueError("Refutation integrity check failed")
        return json.loads(row["certificate"])

    def _proofs(self) -> list:
        # Bound the active proposals, not the archive. SQL/JSON cost is measured
        # in elapsed time, outside the Lean operation ledger.
        proposals, seen = [], set()
        for row in self.db.execute("""SELECT p.* FROM portfolio k JOIN proofs p
                ON p.engine=k.engine AND p.bits=k.bits
                WHERE k.engine=? AND k.kind='proof' ORDER BY k.seen_ns DESC LIMIT ?""",
                (self.engine_id, PORTFOLIO_SIZE)):
            if row["certificate"] in seen:
                continue
            proposals.append(self._validate_proof(row))
            seen.add(row["certificate"])
            if len(proposals) == PORTFOLIO_SIZE:
                break
        return proposals

    def _index_candidate(self, engine, kind, bits, payload, timestamp):
        if kind == "proof" and len(payload.encode()) > MAX_PROPOSAL_BYTES:
            return
        token = hashlib.sha256(payload.encode()).hexdigest()
        self.db.execute("""INSERT INTO portfolio VALUES (?,?,?,?,?)
            ON CONFLICT(engine,kind,token) DO UPDATE SET bits=excluded.bits,seen_ns=excluded.seen_ns
            WHERE excluded.seen_ns >= portfolio.seen_ns""", (engine, kind, token, bits, timestamp))

    def _activate(self, bits: str) -> None:
        self.db.execute("""INSERT INTO active_witness(engine,bits) VALUES (?,?)
            ON CONFLICT(engine) DO UPDATE SET bits=excluded.bits
            WHERE active_witness.bits != excluded.bits""", (self.engine_id, bits))

    def _request(self, request: dict) -> dict:
        if self.process is None:
            self.process = subprocess.Popen(
                [str(self.engine)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                text=True, bufsize=1,
            )
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError("Lean solver exited without a result; no answer was cached")
        response = json.loads(line)
        if "error" in response:
            raise ValueError(response["error"])
        return response

    def _live(self, bits: str, candidate: str | None = None, *, mode: str = "hybrid",
              candidates: list[str] | None = None, proofs: list | None = None) -> dict:
        request = {"bits": bits, "candidate": candidate, "mode": mode}
        if candidates is not None:
            request["candidates"] = candidates
        if proofs is not None:
            request["proofs"] = proofs
        response = self._request(request)
        if type(response.get("answer")) is not bool or type(response.get("core_work")) is not int:
            raise ValueError("Invalid engine response; no answer was cached")
        if (type(response.get("parse_work")) is not int or response["parse_work"] < 0
                or response["core_work"] < 0
                or type(response.get("counted_work")) is not int
                or response["counted_work"] != response["core_work"] + response["parse_work"]):
            raise ValueError("Invalid engine accounting; no answer was cached")
        if response["answer"]:
            check_bits(response.get("witness"))
        elif response.get("witness") is not None:
            raise ValueError("Invalid UNSAT engine response")
        if not response["answer"] and mode != "exhaustive" and response.get("certificate") is None:
            raise ValueError("Missing UNSAT refutation; no answer was cached")
        return response

    def _verify_certificate(self, bits, certificate):
        return self._request({"bits": bits, "mode": "verify_certificate", "certificate": certificate})["valid"]

    def _fast_live(self, bits: str, candidates=None, proofs=None) -> dict:
        r = self._request({"bits": bits, "mode": "prepare",
                           "candidates": candidates or [], "proofs": proofs or [],
                           "search_budget": 64 if self.backend == "auto" else 0})
        r.update(backend="preprocess", core_work=None, counted_work=None, counted_complete=False)
        if not r.get("pending"):
            return r
        if self.cadical is None:
            # Availability changes performance, never the decision semantics.
            fallback = self._live(bits, mode="baseline")
            fallback["parse_work"] += r["parse_work"]
            fallback.update(backend="lean_fallback", counted_complete=False,
                            core_work=None, counted_work=None, nodes=None)
            return fallback
        with tempfile.TemporaryDirectory(prefix="oracle-cdcl-") as directory:
            cnf = Path(directory) / "query.cnf"
            proof = Path(directory) / "query.lrat"
            cnf.write_text(r["dimacs"])
            started = time.perf_counter_ns()
            try:
                run = subprocess.run([str(self.cadical), "--lrat", "--no-binary", "--quiet",
                                      str(cnf), str(proof)], capture_output=True, text=True,
                                     timeout=self.timeout)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("CaDiCaL timed out; no SAT/UNSAT answer was cached") from exc
            external_ns = time.perf_counter_ns() - started
            verification_start = time.perf_counter_ns()
            if run.returncode == 10:
                values = {}
                for line in run.stdout.splitlines():
                    if line.startswith("v "):
                        for token in line[2:].split():
                            lit = int(token)
                            if lit:
                                if abs(lit) in values and values[abs(lit)] != (lit > 0):
                                    raise ValueError("Inconsistent external model; no answer was cached")
                                values[abs(lit)] = lit > 0
                witness = "".join("1" if values.get(r["offset"] + i + 1, False) else "0"
                                  for i in range(r["width"]))
                checked = self._request({"bits": bits, "mode": "verify_witness", "witness": witness})
                if not checked["valid"]:
                    raise ValueError("External SAT witness rejected; no answer was cached")
                r["parse_work"] += checked["parse_work"]
                answer, certificate = True, None
            elif run.returncode == 20:
                certificate = {"format": "lrat", "text": proof.read_text()}
                checked = self._request({"bits": bits, "mode": "verify_certificate", "certificate": certificate})
                r["parse_work"] += checked["parse_work"]
                if not checked["valid"]:
                    raise ValueError("External UNSAT proof rejected; no answer was cached")
                answer, witness = False, None
            else:
                raise RuntimeError(f"CaDiCaL returned no checked answer (exit {run.returncode}); no answer was cached")
            return dict(answer=answer, witness=witness, certificate=certificate, fast=False,
                        reuse_kind="none", backend="cadical", nodes=None, core_work=None,
                        parse_work=r["parse_work"], counted_work=None, counted_complete=False,
                        external_ns=external_ns, verification_ns=time.perf_counter_ns() - verification_start,
                        cnf_clauses=r["clauses"], proof_bytes=proof.stat().st_size if proof.exists() else 0)

    def solve(self, bits: str, *, learn: bool = True) -> dict:
        start = time.perf_counter_ns()
        check_bits(bits)
        row = self.db.execute("SELECT * FROM results WHERE engine=? AND bits=?",
                              (self.engine_id, bits)).fetchone()
        if row is not None:
            self._validate(row)
            measurement = self.db.execute("SELECT details FROM measurements WHERE engine=? AND bits=?",
                                          (self.engine_id, bits)).fetchone()
            measured = json.loads(measurement[0]) if measurement else {"counted_complete": True}
            if row["answer"] and learn:
                with self.db:
                    self._activate(bits)
            return {"answer": bool(row["answer"]), "witness": row["witness"],
                    "source": "cache", "core_work": 0, "parse_work": 0, "counted_work": 0,
                    "nodes": 0,
                    "counted_complete": True,
                    "original_acquisition_core_work": row["acquisition_core_work"] if measured["counted_complete"] else None,
                    "original_acquisition_parse_work": row["acquisition_parse_work"],
                    "original_measurements": measured,
                    "wall_ns": time.perf_counter_ns() - start}
        candidates, proofs = (self._candidates(), self._proofs()) if learn else ([], [])
        if self.backend == "lean":
            result = self._live(bits, candidates=candidates, proofs=[p for p in proofs if not isinstance(p, dict)],
                                mode="hybrid" if learn else "baseline")
            result.update(backend="lean", counted_complete=True)
        else:
            result = self._fast_live(bits, candidates, proofs)
        answer, witness = result["answer"], result["witness"]
        with self.db:
            self.db.execute("""INSERT OR IGNORE INTO results
                (engine,bits,answer,witness,acquisition_core_work,created_ns,checksum,acquisition_parse_work)
                VALUES (?,?,?,?,?,?,?,?)""", (self.engine_id, bits, int(answer), witness,
                result["core_work"] if result["core_work"] is not None else 0,
                time.time_ns(), checksum(self.engine_id, bits, answer, witness),
                result["parse_work"]))
            stored = self.db.execute("SELECT * FROM results WHERE engine=? AND bits=?",
                                     (self.engine_id, bits)).fetchone()
            self._validate(stored)
            if bool(stored["answer"]) != answer:
                raise ValueError("Conflicting exact results; transaction rolled back")
            if not answer:
                certificate = json.dumps(result["certificate"], separators=(",", ":"))
                self.db.execute("""INSERT OR IGNORE INTO proofs VALUES (?,?,?,?)""",
                    (self.engine_id, bits, certificate, proof_checksum(self.engine_id, bits, certificate)))
                proof = self.db.execute("SELECT * FROM proofs WHERE engine=? AND bits=?",
                                        (self.engine_id, bits)).fetchone()
                self._validate_proof(proof)
                self._index_candidate(self.engine_id, "proof", bits, proof["certificate"], time.time_ns())
            else:
                self._index_candidate(self.engine_id, "witness", bits, stored["witness"], time.time_ns())
            details = {k: result[k] for k in ("backend", "counted_complete", "external_ns", "verification_ns", "cnf_clauses", "proof_bytes") if k in result}
            self.db.execute("INSERT OR IGNORE INTO measurements VALUES (?,?,?)",
                            (self.engine_id, bits, json.dumps(details, sort_keys=True)))
            if answer and learn:
                self._activate(bits)
        return {"answer": answer, "witness": witness,
                "source": {"witness": "verified_witness", "refutation": "verified_refutation",
                           "none": "fallback"}[result["reuse_kind"]],
                "nodes": result["nodes"],
                **details,
                "core_work": result["core_work"], "parse_work": result["parse_work"],
                "counted_work": result["counted_work"], "wall_ns": time.perf_counter_ns() - start}

    def stats(self) -> dict:
        row = self.db.execute("""SELECT count(*) AS entries, coalesce(sum(answer),0) AS sat
            FROM results WHERE engine=?""", (self.engine_id,)).fetchone()
        total = self.db.execute("SELECT count(*) FROM results").fetchone()[0]
        proofs = self.db.execute("SELECT count(*) FROM proofs WHERE engine=?", (self.engine_id,)).fetchone()[0]
        return {"engine": self.engine_id, "entries": row["entries"], "sat": row["sat"],
                "unsat": row["entries"] - row["sat"], "all_engine_entries": total,
                "refutations": proofs}

    def revalidate(self) -> dict:
        """Recompute older engines' inputs; keep their original records intact.

        Old answer bits are never imported as current-engine answers. Progress is
        committed per input, so an interrupted replay can safely be resumed.
        """
        bits = [row[0] for row in self.db.execute(
            "SELECT DISTINCT bits FROM results WHERE engine != ? ORDER BY bits",
            (self.engine_id,))]
        solved = cached = 0
        for encoded in bits:
            result = self.solve(encoded)
            cached += result["source"] == "cache"
            solved += result["source"] != "cache"
        return {"previous_inputs": len(bits), "revalidated": solved, "already_current": cached}

    def audit(self) -> dict:
        rows = self.db.execute("SELECT * FROM results WHERE engine=? ORDER BY bits",
                               (self.engine_id,)).fetchall()
        for row in rows:
            self._validate(row)
            result = self._fast_live(row["bits"])
            if result["answer"] != bool(row["answer"]):
                raise ValueError("Cache semantic audit failed")
            if row["answer"] and not self._live(row["bits"], row["witness"])["fast"]:
                raise ValueError("Cached witness does not satisfy its formula")
            if not row["answer"]:
                proof = self.db.execute("SELECT * FROM proofs WHERE engine=? AND bits=?",
                                        (self.engine_id, row["bits"])).fetchone()
                # Historical records may predate certificates; audit still
                # re-solves these independently and does not invent provenance.
                if proof is not None:
                    certificate = self._validate_proof(proof)
                    if not self._verify_certificate(row["bits"], certificate):
                        raise ValueError("Cached refutation does not establish its formula")
        return {"checked": len(rows), "valid": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--engine", type=Path, default=DEFAULT_ENGINE)
    parser.add_argument("--backend", choices=("auto", "lean", "cadical"), default="auto")
    parser.add_argument("--cadical", type=Path)
    parser.add_argument("--timeout", type=float, default=30)
    sub = parser.add_subparsers(dest="command", required=True)
    solve = sub.add_parser("solve")
    solve.add_argument("bits")
    solve.add_argument("--no-learn", action="store_true")
    sub.add_parser("stats")
    sub.add_parser("audit")
    sub.add_parser("revalidate")
    sub.add_parser("serve", help="Serve JSON-lines requests using one warm solver and database")
    args = parser.parse_args()
    try:
        with PersistentSolver(args.cache, args.engine, backend=args.backend, cadical=args.cadical,
                              timeout=args.timeout) as solver:
            if args.command == "serve":
                for line in sys.stdin:
                    try:
                        request = json.loads(line)
                        if not isinstance(request, dict):
                            raise ValueError("A request must be a JSON object")
                        result = solver.solve(request["bits"], learn=request.get("learn", True))
                    except (KeyError, ValueError, RuntimeError, OSError, sqlite3.Error) as exc:
                        result = {"error": str(exc)}
                    print(json.dumps(result, sort_keys=True), flush=True)
                return 0
            elif args.command == "solve":
                result = solver.solve(args.bits, learn=not args.no_learn)
            elif args.command == "stats":
                result = solver.stats()
            elif args.command == "revalidate":
                result = solver.revalidate()
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
