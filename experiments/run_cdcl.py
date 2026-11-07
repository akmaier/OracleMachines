#!/usr/bin/env python3
"""Checked CDCL and persistent-service comparison, with retained timeout records.

Each run gets a fresh process and database. Initialization is measured separately
from warm query service and included in total time. No query answer is preloaded.
This is a small, deterministic mechanism study, not a SAT competition benchmark.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import signal
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from solver.persistent import DEFAULT_ENGINE, PersistentSolver, find_cadical
from solver.test_fast import cnf_bits, conj, disj, neg, var

MODES = ["lean", "cadical", "auto", "exact_auto", "persistent_auto"]


def pigeonhole(pigeons, holes):
    clauses = [[(p * holes + h, True) for h in range(holes)] for p in range(pigeons)]
    clauses += [[(p * holes + h, False), (q * holes + h, False)]
                for h in range(holes) for p in range(pigeons) for q in range(p + 1, pigeons)]
    return cnf_bits(clauses)


def streams(queries):
    mixed = cnf_bits([[(i, i % 2 == 0)] for i in range(12)])
    late = "0010"
    for i in range(16):
        late = conj(late, disj(var(i), neg(var(i))))
    late = conj(late, conj(var(16), neg(var(16))))
    chain = cnf_bits([[(0, True)], [(23, False)]] +
                     [[(i, False), (i + 1, True)] for i in range(23)])
    rng = random.Random(20261107)
    planted = [bool(rng.randrange(2)) for _ in range(20)]
    clauses = []
    for _ in range(86):
        clause = [(i, bool(rng.randrange(2))) for i in rng.sample(range(20), 3)]
        if not any(planted[i] == sign for i, sign in clause):
            i, _ = clause[0]
            clause[0] = (i, planted[i])
        clauses.append(clause)
    planted_formula = cnf_bits(clauses)
    families = [("mixed_units_12", mixed, True), ("late_conflict_17", late, False),
                ("implication_chain_24", chain, False),
                ("planted_3sat_20", planted_formula, True)]
    families += [(f"pigeonhole_{p}_{p-1}", pigeonhole(p, p - 1), False) for p in (3, 4, 5, 6)]
    families += [("pigeonhole_sat_5_5", pigeonhole(5, 5), True)]
    for name, formula, expected in families:
        yield {"workload": name, "bits": [formula + "1010" * i for i in range(queries)],
               "expected": [expected] * queries}
    yield {"workload": "repeated_planted_3sat_20", "bits": [planted_formula] * queries,
           "expected": [True] * queries}


def worker(mode, stream):
    backend = mode if mode in ("lean", "cadical", "auto") else "auto"
    with tempfile.TemporaryDirectory(prefix="oracle-cdcl-study-") as scratch:
        path = Path(scratch) / "results.sqlite3"
        with PersistentSolver(path, backend=backend, timeout=5) as solver:
            warm_start = time.perf_counter_ns()
            # Only start the interpreter; no answers, witnesses, or clauses retained.
            solver._request({"bits": "00", "mode": "verify_witness", "witness": ""})
            warmup_ns = time.perf_counter_ns() - warm_start
            results = []
            service_start = time.perf_counter_ns()
            for bits, expected in zip(stream["bits"], stream["expected"]):
                start = time.perf_counter_ns()
                if mode == "lean":
                    r = solver._live(bits, mode="baseline")
                    r.update(backend="lean", source="fallback", counted_complete=True)
                elif mode in ("cadical", "auto"):
                    r = solver._fast_live(bits)
                    r["source"] = "fallback"
                else:
                    r = solver.solve(bits, learn=(mode == "persistent_auto"))
                elapsed = time.perf_counter_ns() - start
                if r["answer"] != expected:
                    raise AssertionError(f"Incorrect answer for {stream['workload']}/{mode}")
                results.append({k: v for k, v in r.items() if k not in
                                ("certificate", "witness", "original_measurements")})
                results[-1]["latency_ns"] = elapsed
            service_ns = time.perf_counter_ns() - service_start
            row = dict(status="ok", engine=solver.engine_id, setup_ns=solver.setup_ns,
                       warmup_ns=warmup_ns, service_ns=service_ns, results=results,
                       stats=solver.stats())
            row["certificate_bytes"] = solver.db.execute(
                "SELECT coalesce(sum(length(certificate)),0) FROM proofs").fetchone()[0]
            closing = time.perf_counter_ns()
        row["shutdown_ns"] = time.perf_counter_ns() - closing
        row["total_ns"] = sum(row[k] for k in ("setup_ns", "warmup_ns", "service_ns", "shutdown_ns"))
        row["database_bytes"] = path.stat().st_size
        return row


def isolated_run(mode, stream, timeout):
    start = time.perf_counter_ns()
    process = subprocess.Popen([sys.executable, __file__, "--worker", mode],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    try:
        out, err = process.communicate(json.dumps(stream), timeout=timeout)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        return dict(status="timeout", timeout_seconds=timeout,
                    worker_elapsed_ns=time.perf_counter_ns() - start)
    if process.returncode:
        raise RuntimeError(f"Benchmark worker failed for {stream['workload']}/{mode}: {err}")
    return json.loads(out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=MODES)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/results/cdcl")
    parser.add_argument("--queries", type=int, default=8)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--run-timeout", type=float, default=8)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker, json.load(sys.stdin))))
        return
    if args.queries < 2 or args.repeats < 1 or args.run_timeout <= 0:
        parser.error("Use at least two queries, one repeat, and a positive timeout")
    if not find_cadical():
        parser.error("Build with solver/build.sh first")
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error("Choose an empty output directory to preserve existing evidence")
    inputs = list(streams(args.queries))
    for stream in inputs:
        stream["sha256"] = hashlib.sha256(json.dumps(stream, sort_keys=True).encode()).hexdigest()
    (args.output / "inputs.json").write_text(json.dumps(inputs, indent=2) + "\n")
    rows = []
    with (args.output / "workloads.jsonl").open("w") as output:
        for stream in inputs:
            for repeat in range(args.repeats):
                order = MODES[repeat % len(MODES):] + MODES[:repeat % len(MODES)]
                for mode in order:
                    row = isolated_run(mode, stream, args.run_timeout)
                    row.update(mode=mode, workload=stream["workload"], repeat=repeat,
                               queries=args.queries, input_sha256=stream["sha256"])
                    rows.append(row)
                    output.write(json.dumps(row, sort_keys=True) + "\n")
                    output.flush()
            print(f"checked {stream['workload']}", file=sys.stderr, flush=True)
    summaries = []
    for stream in inputs:
        for mode in MODES:
            group = [r for r in rows if r["workload"] == stream["workload"] and r["mode"] == mode]
            completed = [r for r in group if r["status"] == "ok"]
            row = dict(workload=stream["workload"], mode=mode, completed=len(completed),
                       timeouts=len(group) - len(completed))
            for field in ("total", "service", "setup", "warmup", "shutdown"):
                row[field + "_ms_median"] = (statistics.median(r[field + "_ns"] for r in completed) / 1e6
                                             if completed else None)
            for source in ("cache", "verified_witness", "verified_refutation"):
                row[source + "_hits_median"] = (statistics.median(sum(x["source"] == source for x in r["results"])
                                                                  for r in completed) if completed else None)
            row["external_calls_median"] = (statistics.median(sum(x.get("backend") == "cadical" for x in r["results"])
                                                             for r in completed) if completed else None)
            summaries.append(row)
    (args.output / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    raw = (args.output / "workloads.jsonl").read_bytes()
    cadical = find_cadical()
    metadata = dict(seed=20261107, platform=platform.platform(), python=sys.version,
                    queries=args.queries, repeats=args.repeats, run_timeout_seconds=args.run_timeout,
                    completed_runs=sum(r["status"] == "ok" for r in rows),
                    timed_out_runs=sum(r["status"] == "timeout" for r in rows),
                    checked_answers=sum(len(r.get("results", [])) for r in rows),
                    engine_sha256=hashlib.sha256(DEFAULT_ENGINE.read_bytes()).hexdigest(),
                    cadical_sha256=hashlib.sha256(cadical.read_bytes()).hexdigest(),
                    cadical_version=subprocess.check_output([str(cadical), "--version"], text=True).strip(),
                    cadical_flags=["--lrat", "--no-binary", "--quiet"],
                    raw_sha256=hashlib.sha256(raw).hexdigest(),
                    limits="Synthetic mechanism study. No peak memory, energy, or complete modern operation ledger. "
                    "Totals include engine fingerprinting, DB setup, native startup, warmup, service, and shutdown. "
                    "Python startup and observer statistics excluded. Timed-out runs are retained without inferred answers. "
                    "Every mode uses a new process and empty DB. Exact-auto disables cross-formula reuse; "
                    "persistent-auto checks stored proposals. All acquisition occurs inside the stream.")
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")


if __name__ == "__main__":
    main()
