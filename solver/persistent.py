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
from solver.chain import ChainSolver
from solver.layered import LayeredSolver
from solver.source_updates import SourceSolver
from copy import deepcopy
from solver.routing import Router
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
                 symbolic: bool = False, adaptive: bool = False,
                 max_archive_bytes: int | None = None, active_cache_bytes: int = 2*1024**2,
                 symbolic_node_limit: int = 50000, wal_checkpoint_bytes: int = 4*1024**2,
                 native_layer_cells: int = 1024**2,
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
        if any(type(v) is not int or v<=0 for v in (active_cache_bytes,symbolic_node_limit,wal_checkpoint_bytes,native_layer_cells)):
            raise ValueError('Active payload, symbolic node and WAL thresholds must be positive integers')
        self.active_cache_bytes,self.symbolic_node_limit,self.wal_checkpoint_bytes=active_cache_bytes,symbolic_node_limit,wal_checkpoint_bytes
        self.native_layer_cells=native_layer_cells
        self.backend, self.timeout = backend, timeout
        self.query_timeout, self.verify_cache = query_timeout, verify_cache
        self.max_input_bytes, self.max_message_bytes, self.max_proof_bytes = max_input_bytes, max_message_bytes, max_proof_bytes
        self._deadline = self._ledger = None
        self._route_decision = None
        self.max_archive_bytes = max_archive_bytes
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
        if max_archive_bytes is not None:
            page_size = self.db.execute("PRAGMA page_size").fetchone()[0]
            page_count = self.db.execute("PRAGMA page_count").fetchone()[0]
            if type(max_archive_bytes) is not int or max_archive_bytes < page_size * max(1, page_count):
                self.db.close()
                raise ValueError("Archive cap is smaller than the existing database; history was retained")
            self.db.execute("PRAGMA max_page_count=" + str(max_archive_bytes // page_size))
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
                Router.create(self.db)
                ChainSolver.create(self.db)
                LayeredSolver.create(self.db)
                SourceSolver.create(self.db)
                self.db.execute("PRAGMA user_version=8")
        except Exception:
            self.db.close()
            raise
        self.process: subprocess.Popen | None = None
        self.chains = ChainSolver(self)
        self.layers = None
        self.source_layers = None
        self.interfaces = InterfaceSolver(self, max_interface, symbolic=symbolic) if interfaces or symbolic or adaptive else None
        routing_namespace = self.engine_id + ":routes-v3:" + json.dumps(
            [backend, symbolic, max_interface, components, incremental, incremental_proofs], separators=(",", ":"))
        self.router = Router(self.db, routing_namespace, self.engine_id) if adaptive and backend != "lean" else None
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
            if self._ledger is not None:self._ledger.count('native_worker_starts')
            self.process = subprocess.Popen(
                [str(self.engine)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                text=True, bufsize=1,
            )
        try:
            with self._phase("serialization"):
                payload = (json.dumps(request) + "\n").encode()
                if self._ledger is not None:
                    self._ledger.count('native_requests');self._ledger.count('native_request_bytes',len(payload))
            with self._phase("native_" + request.get("mode", "hybrid")):
                line = exchange(self.process, payload, self._deadline or Deadline(self.query_timeout),
                                self.max_message_bytes)
            with self._phase("serialization"):
                response = json.loads(line)
                if self._ledger is not None:self._ledger.count('native_response_bytes',len(line.encode()))
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

    def _try_proposals(self,bits,candidates,proofs):
        """Charge each checked proposal; reserve at least 90% for fallback.

        A timed-out native worker is reaped by _request. Its volatile caches
        are replayed on demand, and immutable historical evidence is retained.
        """
        original=self._deadline
        remaining=original.remaining() if original else self.query_timeout
        budget=min(0.25,remaining*0.1)
        local=Deadline(budget);attempts=[]
        self._proposal_metrics=dict(budget_seconds=budget,attempts=attempts)
        try:
            self._deadline=local
            for kind,values in [('witness',candidates or []),('proof',proofs or [])]:
                for value in values:
                    start=time.perf_counter_ns();record=dict(kind=kind)
                    attempts.append(record)
                    try:
                        local.check()
                        result=self._request(dict(mode='propose',bits=bits,
                            candidates=[value] if kind=='witness' else [],proofs=[value] if kind=='proof' else []))
                        record['outcome']='miss' if result.get('pending') else 'accepted'
                        if not result.get('pending'):return result
                    except BudgetExceeded:
                        record['outcome']='budget';return None
                    finally:record['elapsed_ns']=time.perf_counter_ns()-start
        finally:self._deadline=original
        return None

    def _fast_live(self, bits: str, candidates=None, proofs=None, *, allow_components=True,
                   allow_incremental=True, allow_interfaces=True) -> dict:
        interface_fallback = None
        if self.interfaces is not None and allow_interfaces and (self._route_decision is None or self._route_decision["route"] == "interfaces"):
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
        r = self._try_proposals(bits,candidates,proofs) if candidates or proofs else None
        if r is None:
            r = self._request({"bits": bits, "mode": "prepare", "candidates": [], "proofs": [],
                               "search_budget": 64 if self.backend == "auto" else 0})
        r.update(backend="preprocess", core_work=None, counted_work=None, counted_complete=False)
        if interface_fallback is not None:
            r["interface_fallback"] = interface_fallback
        if not r.get("pending"):
            return r
        incremental_metrics = None
        if self.incremental is not None and allow_incremental:
            if isinstance(self.incremental, ProofIncremental):
                with self._phase("incremental_core_reuse"):
                    reused=self.incremental.reuse_checked(bits)
                if reused is not None:
                    reused["parse_work"]+=r["parse_work"]
                    return reused
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
                        checked=self.incremental.verify_live(bits,certificate) if isinstance(self.incremental, ProofIncremental) else self._request(dict(bits=bits,mode="verify_certificate",certificate=certificate))
                    incremental_metrics["proof_accepted"]=checked["valid"]
                    incremental_metrics["history_recompiled"]=checked.get("history_recompiled")
                    incremental_metrics["checked_fragment_reuse"]=checked.get("checked_fragment_reuse",False)
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
        self._route_decision = None
        observation_attempted = False
        self._proposal_metrics = None
        try:
            self._database_budget()
            self.db.set_progress_handler(lambda: int(time.monotonic() >= self._deadline.end), 1000)
            result = self._solve_impl(bits, learn=learn)
            with self._phase("storage_accounting"):
                result["storage"] = self.archive_usage()
            if self._route_decision is not None:
                elapsed = time.perf_counter_ns() - self._ledger.start
                result["routing"] = dict(self._route_decision, observed_ns=elapsed)
                observation_attempted = True
                try:
                    with self._phase("routing_observation"):
                        self.router.observe(self._route_decision, elapsed, True)
                except Exception as error:
                    # Telemetry is best effort. Do not turn a completed checked
                    # response into a second, contradictory route observation.
                    result["routing"]["observation_error"] = str(error)
            self.last_metrics = self._ledger.finish()
            result.update(self.last_metrics)
            return result
        except BaseException as error:
            if self._route_decision is not None and not observation_attempted:
                try:
                    with self._phase("routing_observation"):
                        self.router.observe(self._route_decision, time.perf_counter_ns()-self._ledger.start, False)
                except Exception:
                    pass
            self.last_metrics = self._ledger.finish()
            if isinstance(error, sqlite3.Error) and getattr(error,"sqlite_errorcode",None)==sqlite3.SQLITE_FULL:
                raise BudgetExceeded("Archive page cap reached; committed history retained; no new verdict returned") from error
            raise
        finally:
            self.db.set_progress_handler(None, 0)
            self._deadline = self._ledger = None
            self._route_decision = None

    def archive_usage(self):
        # A safe-point checkpoint is charged, may be blocked by another reader,
        # and supplies no hard physical-disk bound.
        wal=Path(str(self.cache)+'-wal');checkpoint=None
        if not self.db.in_transaction and wal.exists() and wal.stat().st_size>self.wal_checkpoint_bytes:
            with self._phase('archive_checkpoint'):
                self.db.execute('PRAGMA busy_timeout=0')
                try:checkpoint=list(self.db.execute('PRAGMA wal_checkpoint(TRUNCATE)').fetchone())
                finally:self._database_budget()
        caches={name:obj.cache.report() for name,obj in [('chain',self.chains),('layered',self.layers),('source',self.source_layers),('interfaces',self.interfaces)] if obj is not None}
        pages=self.db.execute("PRAGMA page_count").fetchone()[0]
        size=self.db.execute("PRAGMA page_size").fetchone()[0]
        free=self.db.execute("PRAGMA freelist_count").fetchone()[0]
        wal=Path(str(self.cache)+"-wal")
        return dict(database_pages=pages,page_bytes=size,logical_database_bytes=pages*size,
            free_pages=free,configured_page_cap_bytes=None if self.max_archive_bytes is None else self.max_archive_bytes//size*size,
            database_file_bytes=self.cache.stat().st_size,wal_bytes=wal.stat().st_size if wal.exists() else 0,
            physical_storage_hard_bound=False,whole_process_memory_bound=False,
            active_caches=caches,symbolic_node_limit=self.symbolic_node_limit,
            native_layer_cells_cap=self.native_layer_cells,
            native_layer_cells=0 if self.layers is None else len(self.layers.verified)*self.layers.states**2,
            native_source_cells=0 if self.source_layers is None else len(self.source_layers.verified)*self.source_layers.states**2,
            wal_checkpoint_threshold=self.wal_checkpoint_bytes,checkpoint_result=checkpoint)

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
        if self.router is not None:
            with self._phase("routing_selection"):
                self._route_decision = self.router.choose(bits,self._deadline,self.interfaces.max_interface)
        if self.backend == "lean":
            result = self._live(bits, candidates=candidates, proofs=[p for p in proofs if not isinstance(p, dict)],
                                mode="hybrid" if learn else "baseline")
            result.update(backend="lean", counted_complete=True)
        else:
            result = self._fast_live(bits, candidates, proofs)
        if self._proposal_metrics is not None:result['proposals']=self._proposal_metrics
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
            details = {k: result[k] for k in ("backend", "counted_complete", "external_ns", "verification_ns", "cnf_clauses", "proof_bytes", "incremental", "components", "interfaces", "interface_fallback", "learned_proposed", "learned_accepted", "model_bytes", "proposals") if k in result}
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
            with self._phase("storage_accounting"):
                result["storage"] = self.archive_usage()
            self.last_metrics = self._ledger.finish()
            result.update(self.last_metrics)
            return result
        except BaseException as error:
            self.last_metrics = self._ledger.finish()
            if isinstance(error, sqlite3.Error) and getattr(error,"sqlite_errorcode",None)==sqlite3.SQLITE_FULL:
                raise BudgetExceeded("Archive page cap reached; committed history retained; no new verdict returned") from error
            raise
        finally:
            self.db.set_progress_handler(None, 0)
            self._ledger = self._deadline = None

    def chain(self, base=None, *, replace=None, append=None, left=3, right=3, witness=False):
        """Explicit binary-relation chain API; old versions remain archived."""
        if self._ledger is not None:raise RuntimeError("Concurrent query")
        self._ledger,self._deadline=Ledger(),Deadline(self.query_timeout)
        try:
            self._database_budget()
            self.db.set_progress_handler(lambda:int(time.monotonic()>=self._deadline.end),1000)
            result=self.chains.run(base,{} if replace is None else replace,[] if append is None else append,left,right,witness)
            with self._phase("storage_accounting"):result["storage"]=self.archive_usage()
            self.last_metrics=self._ledger.finish();result.update(self.last_metrics)
            return result
        except BaseException as error:
            self.last_metrics=self._ledger.finish()
            if isinstance(error,sqlite3.Error) and getattr(error,"sqlite_errorcode",None)==sqlite3.SQLITE_FULL:
                raise BudgetExceeded("Chain archive cap reached; previous versions retained") from error
            raise
        finally:
            self.db.set_progress_handler(None,0)
            self._ledger=self._deadline=None

    def source_cnf(self,width=None,clauses=None,layers=None,*,base=None,replace=None,witness=False):
        """Checked adjacent-block source versions; replace an edge's entire CNF.

        Initial requests supply width, clauses and a disjoint ordered partition.
        Updates supply base and a map from edge indices to replacement clauses;
        [] deletes those clauses. Decisions omit full witnesses by default.
        """
        if self._ledger is not None:raise RuntimeError('Concurrent query')
        self._ledger,self._deadline=Ledger(),Deadline(self.query_timeout)
        try:
            self._database_budget()
            self.db.set_progress_handler(lambda:int(time.monotonic()>=self._deadline.end),1000)
            with self._phase('source_input'):
                payload=dict(width=width,clauses=clauses,layers=layers,base=base,replace=replace,witness=witness)
                input_bytes=len(json.dumps(payload).encode())
                if input_bytes>self.max_input_bytes:raise BudgetExceeded('Source request exceeds input cap')
                # Cached source nodes must not retain caller-owned mutable lists.
                width,clauses,layers,base,replace,witness=deepcopy((width,clauses,layers,base,replace,witness))
                store=KnowledgeStore(self.db,self.engine_id)
                if base is None:
                    if type(width) is not int or not 1<=width<=4:raise ValueError('Source width must be 1 to 4')
                    if not isinstance(clauses,list) or not isinstance(layers,list) or len(layers)<2:
                        raise ValueError('Supply CNF clauses and at least two variable blocks')
                    layout=dict(width=width,layers=layers)
                    with self.db:layout_id=store.put('source_layout',layout)[0]
                else:
                    if width is not None or clauses is not None or layers is not None:
                        raise ValueError('Source edits keep the saved partition; supply only base and replacements')
                    if self.db.execute('SELECT 1 FROM source_states WHERE engine=? AND id=?',(self.engine_id,base)).fetchone() is None:
                        raise ValueError('Unknown source version in this checker namespace')
                    layout_id=store.get(base,'source_version')['layout']
                    if self.source_layers is not None and self.source_layers.layout_id==layout_id:
                        layout=self.source_layers.layout
                    else:layout=store.get(layout_id,'source_layout')
                if self.source_layers is None or self.source_layers.layout_id!=layout_id:
                    self.source_layers=SourceSolver(self,layout_id,layout)
            result=self.source_layers.run(base,clauses,{} if replace is None else replace,witness)
            result['source_updates']['input_bytes']=input_bytes
            result['source_updates']['input_store']={field:getattr(store,field) for field in SourceSolver.storage_fields}
            with self._phase('storage_accounting'):result['storage']=self.archive_usage()
            self.last_metrics=self._ledger.finish();result.update(self.last_metrics)
            return result
        except BaseException as error:
            self.last_metrics=self._ledger.finish()
            if isinstance(error,sqlite3.Error) and getattr(error,'sqlite_errorcode',None)==sqlite3.SQLITE_FULL:
                raise BudgetExceeded('Source archive cap reached; previous versions retained') from error
            raise
        finally:
            self.db.set_progress_handler(None,0);self._ledger=self._deadline=None

    def layered_cnf(self,width,clauses,layers,*,witness=False):
        """Compile CNF whose supplied disjoint variable blocks are adjacent.

        IDs are positive DIMACS variable numbers, literals are signed integers.
        Compilation and a second independent source/root binding pass are charged.
        """
        return self.layered(width,witness=witness,_source=dict(clauses=clauses,layers=layers))

    def layered(self, width, base=None, *, replace=None, append=None, left=None, right=None, witness=False,_source=None):
        """Supplied bounded-width layer relations; no automatic SAT decomposition."""
        if type(width) is not int or not 1<=width<=4:raise ValueError('Layer width must be 1 to 4')
        if self._ledger is not None:raise RuntimeError('Concurrent query')
        self._ledger,self._deadline=Ledger(),Deadline(self.query_timeout)
        try:
            self._database_budget()
            self.db.set_progress_handler(lambda:int(time.monotonic()>=self._deadline.end),1000)
            source_request=None
            if _source is not None:
                if base is not None or replace or append or left is not None or right is not None:
                    raise ValueError('Source compilation requires a fresh full source request')
                source_request=dict(width=width,**_source)
                with self._phase('source_encoding'):
                    source_bytes=len(json.dumps(source_request).encode())
                if source_bytes>self.max_input_bytes:raise BudgetExceeded('CNF source exceeds input cap')
                compiled=self._request(dict(mode='layered_compile',**source_request))
                append=compiled['masks']
            if self.layers is None or self.layers.width!=width:
                if self.layers is not None:self._request(dict(mode='layered_reset'))
                self.layers=LayeredSolver(self,width)
            any_state=(1<<(1<<width))-1
            result=self.layers.run(base,{} if replace is None else replace,[] if append is None else append,
                any_state if left is None else left,any_state if right is None else right,witness)
            if source_request is not None:
                checked=self._request(dict(mode='layered_source_query',root=result['root'],witness=witness,**source_request))
                if checked['answer'] is not result['answer'] or checked['witness']!=result['witness']:
                    raise ValueError('Source binding disagrees with layered result')
                with self._phase('source_storage'),self.db:
                    binding=self.layers.store.put('layered_source',dict(**source_request,state=result['state'],
                        root=result['root'],answer=result['answer']))[0]
                result.update(source='compiled_adjacent_cnf',source_binding=binding,
                    compilation=dict(input_bytes=source_bytes,relation_cells=compiled['relation_cells'],
                                     passes=2,source_edges=len(append)))
            with self._phase('storage_accounting'):result['storage']=self.archive_usage()
            self.last_metrics=self._ledger.finish();result.update(self.last_metrics)
            return result
        except BaseException as error:
            self.last_metrics=self._ledger.finish()
            if isinstance(error,sqlite3.Error) and getattr(error,'sqlite_errorcode',None)==sqlite3.SQLITE_FULL:
                raise BudgetExceeded('Layer archive cap reached; previous versions retained') from error
            raise
        finally:
            self.db.set_progress_handler(None,0);self._ledger=self._deadline=None

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
    parser.add_argument("--adaptive", action="store_true", help="Select checked or interface solving from measured complete-query times")
    parser.add_argument("--max-archive-bytes", type=int, help="Bound logical SQLite pages; stop acquisition at capacity and preserve all history")
    parser.add_argument('--active-cache-bytes',type=int,default=2*1024**2,help='Per-cache retained JSON payload cap; not a process memory cap')
    parser.add_argument('--native-layer-cells',type=int,default=1024**2,help='Retained native relation cells; not an RSS limit')
    parser.add_argument('--symbolic-node-limit',type=int,default=50000)
    parser.add_argument('--wal-checkpoint-bytes',type=int,default=4*1024**2)
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
                              incremental=args.incremental, incremental_proofs=args.incremental_proofs, learned=args.learned, components=args.components, interfaces=args.interfaces, max_interface=args.max_interface, symbolic=args.symbolic, adaptive=args.adaptive, max_archive_bytes=args.max_archive_bytes, active_cache_bytes=args.active_cache_bytes,
                              symbolic_node_limit=args.symbolic_node_limit,wal_checkpoint_bytes=args.wal_checkpoint_bytes,
                              native_layer_cells=args.native_layer_cells) as solver:
            if args.command == "serve":
                for line in sys.stdin:
                    try:
                        request = json.loads(line)
                        if not isinstance(request, dict):
                            raise ValueError("A request must be a JSON object")
                        if request.get("op") == "expand":
                            result = solver.expand(request.get("base"), add=request.get("add", {}), remove=request.get("remove", []))
                        elif request.get("op") == "layered":
                            result = solver.layered(request['width'],request.get('base'),replace=request.get('replace',{}),
                                append=request.get('append',[]),left=request.get('left'),right=request.get('right'),
                                witness=request.get('witness',False))
                        elif request.get("op") == "layered_cnf":
                            result=solver.layered_cnf(request['width'],request['clauses'],request['layers'],
                                witness=request.get('witness',False))
                        elif request.get('op')=='source_cnf':
                            result=solver.source_cnf(request.get('width'),request.get('clauses'),request.get('layers'),
                                base=request.get('base'),replace=request.get('replace'),witness=request.get('witness',False))
                        elif request.get("op") == "chain":
                            result = solver.chain(request.get("base"), replace=request.get("replace", {}),
                                append=request.get("append", []), left=request.get("left", 3),
                                right=request.get("right", 3), witness=request.get("witness", False))
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
