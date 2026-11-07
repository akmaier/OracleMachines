#!/usr/bin/env python3
"""Persistent results for the Lean-verified SAT core. Standard library only.

The local database is a trusted store of this engine's previous results. Row
checksums detect accidental corruption; they are not authentication against an
attacker. `audit` re-solves stored instances. No result is evicted automatically.
"""

from __future__ import annotations

import argparse
from contextlib import nullcontext
import functools
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from solver.resources import BudgetExceeded, Deadline, Ledger, exchange, stop_process, bounded_run
from solver.incremental import DEFAULT_INCREMENTAL, Incremental
from solver.incremental_proof import ProofIncremental
from solver.learning import Predictor, features
from solver.knowledge_store import KnowledgeStore
from solver.components import ComponentSolver
from solver.interfaces import InterfaceSolver
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
                 backend: str = "auto", cadical: Path | None = None, timeout: float = 30,
                 query_timeout: float = 30, verify_cache: bool = False,
                 incremental: bool = False, incremental_proofs: bool = False, learned: bool = False, reuse_exact: bool = True,
                 components: bool = False, interfaces: bool = False, max_interface: int = 3,
                 symbolic: bool = False,
                 max_input_bytes: int = 8 * 1024**2, max_message_bytes: int = 64 * 1024**2,
                 max_proof_bytes: int = 16 * 1024**2):
        start = time.perf_counter_ns()
        self.engine = Path(engine).resolve()
        if not self.engine.is_file():
            raise FileNotFoundError("Build the engine first: cd formal && lake build oracleSolver")
        if backend not in ("auto", "lean", "cadical"):
            raise ValueError("Unknown solver backend")
        if not all(math.isfinite(t) and t > 0 for t in (timeout, query_timeout)):
            raise ValueError("Solver and query timeouts must be finite and positive")
        if min(max_input_bytes, max_message_bytes, max_proof_bytes) <= 0:
            raise ValueError("Resource byte limits must be positive")
        self.backend, self.timeout = backend, timeout
        self.query_timeout, self.verify_cache = query_timeout, verify_cache
        self.max_input_bytes, self.max_message_bytes, self.max_proof_bytes = max_input_bytes, max_message_bytes, max_proof_bytes
        self._deadline = self._ledger = None
        self.last_metrics = {}
        self.use_learning = learned
        self.reuse_exact = reuse_exact
        if (incremental or incremental_proofs) and not DEFAULT_INCREMENTAL.is_file():
            raise FileNotFoundError("Build the incremental bridge with solver/build_incremental.sh first")
        self.incremental = ProofIncremental(self,max_bytes=max_message_bytes) if incremental_proofs else Incremental(max_bytes=max_message_bytes) if incremental else None
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
                if version not in (0, 1, 2, 3, 4, 5, 6, 7, 8):
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
                self.db.execute("""CREATE TABLE IF NOT EXISTS models (
                    engine TEXT PRIMARY KEY, state TEXT NOT NULL, checksum TEXT NOT NULL)""")
                if version < 4:
                    # An index of distinct proposals; the archive remains intact.
                    for row in self.db.execute("SELECT engine,bits,witness,created_ns FROM results WHERE answer=1").fetchall():
                        self._index_candidate(row["engine"], "witness", row["bits"], row["witness"], row["created_ns"])
                    for row in self.db.execute("""SELECT p.*,r.created_ns FROM proofs p JOIN results r
                            ON p.engine=r.engine AND p.bits=r.bits WHERE r.answer=0""").fetchall():
                        self._index_candidate(row["engine"], "proof", row["bits"], row["certificate"], row["created_ns"])
                KnowledgeStore.create(self.db)
                self.db.execute("PRAGMA user_version=8")
        except Exception:
            self.db.close()
            raise
        self.process: subprocess.Popen | None = None
        self.interfaces = InterfaceSolver(self, max_interface, symbolic=symbolic) if interfaces or symbolic else None
        self.components = ComponentSolver(self.db, self.engine_id) if components else None
        if self.incremental:
            bridge = hashlib.sha256(DEFAULT_INCREMENTAL.read_bytes()).hexdigest()
            self.incremental.store = KnowledgeStore(self.db, self.engine_id + ":" + bridge + (":proof-dag-v1" if incremental_proofs else ":dag-v1"))
        self.setup_ns = time.perf_counter_ns() - start

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def close(self):
        if self.incremental:
            self.incremental.close()
        if self.process is not None:
            stop_process(self.process)
            self.process = None
        self.db.close()

    def _phase(self, name):
        return self._ledger.phase(name) if self._ledger else nullcontext()

    def _check_deadline(self):
        if self._deadline:
            self._deadline.check()

    def _remaining(self):
        return self._deadline.remaining() if self._deadline else self.query_timeout

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
        try:
            with self._phase("serialization"):
                payload = (json.dumps(request) + "\n").encode()
            with self._phase("native_" + request.get("mode", "hybrid")):
                line = exchange(self.process, payload, self._deadline or Deadline(self.query_timeout),
                                self.max_message_bytes)
            with self._phase("serialization"):
                response = json.loads(line)
        except (BudgetExceeded, RuntimeError, OSError, ValueError):
            stop_process(self.process)
            self.process = None
            raise
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

    def _fast_live(self, bits: str, candidates=None, proofs=None, *, allow_components=True,
                   allow_incremental=True, allow_interfaces=True) -> dict:
        interface_fallback = None
        if self.interfaces is not None and allow_interfaces:
            result, reason, metrics = self.interfaces.solve(bits)
            if result is not None:
                return result
            fallback = self._fast_live(bits, candidates, proofs, allow_components=allow_components,
                                       allow_incremental=allow_incremental, allow_interfaces=False)
            fallback["interface_fallback"] = dict(reason=reason, metrics=metrics)
            return fallback
        if self.components is not None and allow_components:
            result = self.components.solve(self, bits)
            if result is not None:
                return result
        r = self._request({"bits": bits, "mode": "prepare",
                           "candidates": candidates or [], "proofs": proofs or [],
                           "search_budget": 64 if self.backend == "auto" else 0})
        r.update(backend="preprocess", core_work=None, counted_work=None, counted_complete=False)
        if interface_fallback is not None:
            r["interface_fallback"] = interface_fallback
        if not r.get("pending"):
            return r
        incremental_metrics = None
        if self.incremental is not None and allow_incremental:
            with self._phase("incremental_solver"):
                proposal = self.incremental.propose(bits, self._deadline or Deadline(self.query_timeout))
            incremental_metrics = {k: v for k, v in proposal.items() if k not in ("witness", "values", "certificate", "proof_events")}
            if proposal["verdict"] == 10:
                checked = self._request({"bits": bits, "mode": "verify_witness", "witness": proposal["witness"]})
                if not checked["valid"]:
                    self.incremental.close()
                    raise ValueError("Incremental SAT witness rejected; no answer was cached")
                return dict(answer=True, witness=proposal["witness"], certificate=None, fast=False,
                            reuse_kind="none", backend="incremental", nodes=None, core_work=None,
                            parse_work=r["parse_work"] + checked["parse_work"], counted_work=None,
                            counted_complete=False, incremental=incremental_metrics)
            if proposal["verdict"] == 20 and proposal.get("certificate"):
                certificate=proposal["certificate"]
                if len(json.dumps(certificate).encode())<=self.max_proof_bytes:
                    with self._phase("incremental_proof_verification"):
                        checked=self._request(dict(bits=bits,mode="verify_certificate",certificate=certificate))
                    incremental_metrics["proof_accepted"]=checked["valid"]
                    if checked["valid"]:
                        return dict(answer=False,witness=None,certificate=certificate,fast=False,
                            reuse_kind="none",backend="incremental_lrat",nodes=None,core_work=None,
                            parse_work=r["parse_work"]+checked["parse_work"],counted_work=None,
                            counted_complete=False,incremental=incremental_metrics)
            # Negative or inconclusive proposals do not decide UNSAT. A fresh,
            # independently checked proof is required on the original formula.
        if self.cadical is None:
            # Availability changes performance, never the decision semantics.
            fallback = self._live(bits, mode="baseline")
            fallback["parse_work"] += r["parse_work"]
            fallback.update(backend="lean_fallback", counted_complete=False,
                            core_work=None, counted_work=None, nodes=None, incremental=incremental_metrics)
            return fallback
        with tempfile.TemporaryDirectory(prefix="oracle-cdcl-") as directory:
            cnf = Path(directory) / "query.cnf"
            proof = Path(directory) / "query.lrat"
            cnf.write_text(r["dimacs"])
            started = time.perf_counter_ns()
            try:
                with self._phase("external_solver"):
                    run = bounded_run([str(self.cadical), "--lrat", "--no-binary", "--quiet",
                                       str(cnf), str(proof)], Path(directory),
                                      self._deadline or Deadline(self.query_timeout), self.timeout,
                                      self.max_message_bytes, proof, self.max_proof_bytes)
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
                if proof.stat().st_size > self.max_proof_bytes:
                    raise BudgetExceeded("LRAT proof exceeds the configured byte limit")
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
                        cnf_clauses=r["clauses"], proof_bytes=proof.stat().st_size if proof.exists() else 0,
                        incremental=incremental_metrics)

    def solve(self, bits: str, *, learn: bool = True) -> dict:
        """Deadline covers lookup, preprocessing, subprocesses, and checking.

        Python/SQLite checkpoints are cooperative; this is not a hard real-time
        scheduling guarantee. A completed atomic commit retains a valid result
        even if the caller subsequently disconnects.
        """
        if self._ledger is not None:
            raise RuntimeError("Concurrent requests need separate PersistentSolver instances")
        self._ledger, self._deadline = Ledger(), Deadline(self.query_timeout)
        try:
            self._database_budget()
            self.db.set_progress_handler(lambda: int(time.monotonic() >= self._deadline.end), 1000)
            result = self._solve_impl(bits, learn=learn)
            self.last_metrics = self._ledger.finish()
            result.update(self.last_metrics)
            return result
        except BaseException:
            self.last_metrics = self._ledger.finish()
            raise
        finally:
            self.db.set_progress_handler(None, 0)
            self._deadline = self._ledger = None

    def _database_budget(self):
        self.db.execute("PRAGMA busy_timeout=" + str(max(1, int(self._remaining() * 1000))))

    def _solve_impl(self, bits: str, *, learn: bool = True) -> dict:
        start = time.perf_counter_ns()
        with self._phase("input"):
            if isinstance(bits, str) and len(bits) > self.max_input_bytes:
                raise BudgetExceeded("Input exceeds the configured byte limit")
            check_bits(bits)
        self._check_deadline()
        with self._phase("lookup"):
            row = self.db.execute("SELECT * FROM results WHERE engine=? AND bits=?",
                                  (self.engine_id, bits)).fetchone() if self.reuse_exact else None
        if row is not None:
            self._validate(row)
            check_parse_work = 0
            if self.verify_cache:
                if row["answer"]:
                    checked = self._request({"bits": bits, "mode": "verify_witness", "witness": row["witness"]})
                else:
                    proof = self.db.execute("SELECT * FROM proofs WHERE engine=? AND bits=?",
                                            (self.engine_id, bits)).fetchone()
                    if proof is None:
                        fresh = self._fast_live(bits)
                        checked = dict(valid=not fresh["answer"], parse_work=fresh["parse_work"])
                    else:
                        checked = self._request({"bits": bits, "mode": "verify_certificate",
                                                 "certificate": self._validate_proof(proof)})
                if not checked["valid"]:
                    raise ValueError("Cached certificate rejected; no answer was accepted")
                check_parse_work = checked["parse_work"]
            measurement = self.db.execute("SELECT details FROM measurements WHERE engine=? AND bits=?",
                                          (self.engine_id, bits)).fetchone()
            measured = json.loads(measurement[0]) if measurement else {"counted_complete": True}
            if row["answer"] and learn:
                self._database_budget()
                with self.db:
                    self._activate(bits)
            return {"answer": bool(row["answer"]), "witness": row["witness"],
                    "source": "cache", "core_work": None if self.verify_cache else 0,
                    "parse_work": check_parse_work, "counted_work": None if self.verify_cache else 0,
                    "nodes": None if self.verify_cache else 0,
                    "counted_complete": not self.verify_cache, "cache_verified": self.verify_cache,
                    "original_acquisition_core_work": row["acquisition_core_work"] if measured["counted_complete"] else None,
                    "original_acquisition_parse_work": row["acquisition_parse_work"],
                    "original_measurements": measured,
                    "wall_ns": time.perf_counter_ns() - start}
        with self._phase("retrieval"):
            candidates, proofs = (self._candidates(), self._proofs()) if learn else ([], [])
        predictor = observed = predicted = None
        if self.use_learning and learn and self.backend != "lean":
            with self._phase("prediction"):
                model = self.db.execute("SELECT * FROM models WHERE engine=?", (self.engine_id,)).fetchone()
                if model and model["checksum"] != hashlib.sha256(model["state"].encode()).hexdigest():
                    raise ValueError("Predictor integrity check failed")
                predictor = Predictor(json.loads(model["state"]) if model else None)
                observed = features(bits, self._deadline)
                if predictor.state["examples"]:
                    predicted = predictor.predict(observed)
                    candidates = [predicted] + [c for c in candidates if c != predicted][:PORTFOLIO_SIZE - 1]
        self._check_deadline()
        if self.backend == "lean":
            result = self._live(bits, candidates=candidates, proofs=[p for p in proofs if not isinstance(p, dict)],
                                mode="hybrid" if learn else "baseline")
            result.update(backend="lean", counted_complete=True)
        else:
            result = self._fast_live(bits, candidates, proofs)
        answer, witness = result["answer"], result["witness"]
        learned_hit = (predicted is not None and result["reuse_kind"] == "witness"
                       and result.get("backend") not in ("components", "interfaces") and witness == predicted)
        result.update(learned_proposed=predicted is not None, learned_accepted=learned_hit,
                      model_bytes=0)
        self._check_deadline()
        self._database_budget()
        with self._phase("persistence"), self.db:
            inserted = self.db.execute("""INSERT OR IGNORE INTO results
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
            if predictor is not None and answer:
                # Read/update under the acquired write transaction so concurrent
                # acquisitions do not overwrite each other's training progress.
                with self._phase("training"):
                    current = self.db.execute("SELECT * FROM models WHERE engine=?", (self.engine_id,)).fetchone()
                    if current and current["checksum"] != hashlib.sha256(current["state"].encode()).hexdigest():
                        raise ValueError("Predictor integrity check failed")
                    latest = Predictor(json.loads(current["state"]) if current else None)
                    if inserted.rowcount:
                        latest.update(observed, stored["witness"], self._deadline)
                    model_text = latest.dump()
                    self.db.execute("INSERT INTO models VALUES (?,?,?) ON CONFLICT(engine) DO UPDATE SET state=excluded.state,checksum=excluded.checksum",
                                    (self.engine_id, model_text, hashlib.sha256(model_text.encode()).hexdigest()))
                    result["model_bytes"] = len(model_text.encode())
            details = {k: result[k] for k in ("backend", "counted_complete", "external_ns", "verification_ns", "cnf_clauses", "proof_bytes", "incremental", "components", "interfaces", "interface_fallback", "learned_proposed", "learned_accepted", "model_bytes") if k in result}
            self.db.execute("INSERT OR IGNORE INTO measurements VALUES (?,?,?)",
                            (self.engine_id, bits, json.dumps(details, sort_keys=True)))
            if answer and learn:
                self._activate(bits)
        return {"answer": answer, "witness": witness,
                "source": ("interface_witness" if answer else "interface_refutation") if result.get("backend") == "interfaces" else ("component_witness" if answer else "component_refutation") if result.get("backend") == "components" else "learned_witness" if learned_hit else {"witness": "verified_witness", "refutation": "verified_refutation",
                           "none": "fallback"}[result["reuse_kind"]],
                "nodes": result["nodes"],
                **details,
                "core_work": result["core_work"], "parse_work": result["parse_work"],
                "counted_work": result["counted_work"], "wall_ns": time.perf_counter_ns() - start}

    def expand(self, base=None, *, add=None, remove=None):
        if self.interfaces is None:
            raise ValueError("Enable --interfaces for expansion requests")
        if self._ledger is not None:
            raise RuntimeError("Concurrent requests need separate solver instances")
        self._ledger, self._deadline = Ledger(), Deadline(self.query_timeout)
        try:
            self._database_budget()
            self.db.set_progress_handler(lambda: int(time.monotonic() >= self._deadline.end), 1000)
            result = self.interfaces.expand(base, {} if add is None else add, [] if remove is None else remove)
            self.last_metrics = self._ledger.finish()
            result.update(self.last_metrics)
            return result
        except BaseException:
            self.last_metrics = self._ledger.finish()
            raise
        finally:
            self.db.set_progress_handler(None, 0)
            self._ledger = self._deadline = None

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
            result = self._fast_live(row["bits"], allow_components=False, allow_incremental=False, allow_interfaces=False)
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
    parser.add_argument("--query-timeout", type=float, default=30)
    parser.add_argument("--verify-cache", action="store_true", help="Recheck stored certificates before accepting exact hits")
    parser.add_argument("--max-proof-bytes", type=int, default=16 * 1024**2)
    parser.add_argument("--incremental-proofs", action="store_true", help="Use persistent circuit definitions and independently checked incremental LRAT traces")
    parser.add_argument("--incremental", action="store_true", help="Use the persistent CDCL proposal engine")
    parser.add_argument("--learned", action="store_true", help="Learn a bounded shared witness predictor")
    parser.add_argument("--components", action="store_true", help="Reuse renamed disjoint components and checked conjunct refutations")
    parser.add_argument("--interfaces", action="store_true", help="Use checked local-interface elimination and delta expansion")
    parser.add_argument("--max-interface", type=int, default=3)
    parser.add_argument("--symbolic", action="store_true", help="Build bounded BDD proposals directly from syntax and projections; implies interfaces")
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
                              timeout=args.timeout, query_timeout=args.query_timeout,
                              verify_cache=args.verify_cache, max_proof_bytes=args.max_proof_bytes,
                              incremental=args.incremental, incremental_proofs=args.incremental_proofs, learned=args.learned, components=args.components, interfaces=args.interfaces, max_interface=args.max_interface, symbolic=args.symbolic) as solver:
            if args.command == "serve":
                for line in sys.stdin:
                    try:
                        request = json.loads(line)
                        if not isinstance(request, dict):
                            raise ValueError("A request must be a JSON object")
                        if request.get("op") == "expand":
                            result = solver.expand(request.get("base"), add=request.get("add", {}), remove=request.get("remove", []))
                        else:
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
