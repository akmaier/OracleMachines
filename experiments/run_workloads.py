#!/usr/bin/env python3
"""Deterministic mechanism study using the actual Lean engine and SQLite adapter.

All variants use the same wrapper setup and parsed-input service. Baseline calls
the lazy core on every query; exhaustive retains the earlier eager reference.
Witness reuse has one witness and no exact-result cache; exact_cache has no
cross-formula transfer; persistent_hybrid also reuses witness/refutation portfolios.
Elapsed times include RPC, parsing, cache access, writes, and process shutdown. Core and parsing operation
counts are reported separately; RPC and persistence remain elapsed-time costs.
"""

import argparse
import hashlib
import json
import platform
from pathlib import Path
import statistics
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from solver.persistent import DEFAULT_ENGINE, PersistentSolver  # noqa: E402


def var(i):
    return "01" + "1" * i + "0"


def neg(f):
    return f + "10"


def conj(f, g):
    return f + g + "11"


def forcing(n, truth):
    f = "0010"  # true, encoded as NOT false
    for i in range(n):
        f = conj(f, var(i) if truth else neg(var(i)))
    return f


def wrap(f, repetitions):
    return f + "1010" * repetitions


def workloads(n, queries, extended=False):
    yes, opposite = forcing(n, True), forcing(n, False)
    no = conj(yes, neg(var(0)))
    streams = {
        "repeated_sat": ([yes] * queries, [True] * queries),
        "distinct_same_witness": ([wrap(yes, i) for i in range(queries)], [True] * queries),
        "distribution_shift": ([wrap(yes if i < queries // 2 else opposite, i)
                                for i in range(queries)], [True] * queries),
        "alternating_witness": ([wrap(yes if i % 2 == 0 else opposite, i)
                                 for i in range(queries)], [True] * queries),
        "distinct_unsat": ([wrap(no, i) for i in range(queries)], [False] * queries),
        "mixed_sat_unsat": ([wrap(yes if i % 2 == 0 else no, i) for i in range(queries)],
                             [i % 2 == 0 for i in range(queries)]),
    }
    if extended:
        contradiction = conj(var(0), neg(var(0)))
        streams.update({
            "sparse_index": ([wrap(var(n - 1), i) for i in range(queries)], [True] * queries),
            "root_conflict": ([conj("00", wrap(yes, i)) for i in range(queries)], [False] * queries),
            "unsat_extension": ([conj(contradiction, wrap(yes, i)) for i in range(queries)], [False] * queries),
        })
    return streams


MODES = ["baseline", "exhaustive", "witness", "exact_cache", "persistent_hybrid"]


def run_one(mode, bits, expected, path, engine):
    with PersistentSolver(path, engine, backend="lean") as solver:
        start = time.perf_counter_ns()
        state = None
        core_work = parse_work = hits = transferred = refuted = fallbacks = nodes = 0
        answers, latency_ns = [], []
        for query in bits:
            query_start = time.perf_counter_ns()
            if mode in ("baseline", "exhaustive"):
                r = solver._live(query, mode=mode)
                source = "fallback"
            elif mode == "witness":
                r = solver._live(query, state)
                source = "verified_witness" if r["fast"] else "fallback"
                if r["answer"]:
                    state = r["witness"]
            else:
                r = solver.solve(query, learn=(mode == "persistent_hybrid"))
                source = r["source"]
            latency_ns.append(time.perf_counter_ns() - query_start)
            answers.append(r["answer"])
            core_work += r["core_work"]
            parse_work += r["parse_work"]
            if r["counted_work"] != r["core_work"] + r["parse_work"]:
                raise AssertionError("Inconsistent parser/core accounting")
            hits += source == "cache"
            transferred += source == "verified_witness"
            fallbacks += source == "fallback"
            refuted += source == "verified_refutation"
            nodes += r["nodes"]
        service_ns = time.perf_counter_ns() - start
        if answers != expected:
            raise AssertionError(f"Incorrect answers for {mode}")
        stats = solver.stats()
        payload = solver.db.execute("SELECT coalesce(sum(length(bits) + coalesce(length(witness),0)),0) "
                                    "FROM results WHERE engine=?", (solver.engine_id,)).fetchone()[0]
        proof_bytes = solver.db.execute("SELECT coalesce(sum(length(certificate)),0) FROM proofs WHERE engine=?",
                                        (solver.engine_id,)).fetchone()[0]
        row = dict(mode=mode, core_work=core_work, parse_work=parse_work,
                   counted_work=core_work + parse_work, cache_hits=hits,
                   witness_hits=transferred, refutation_hits=refuted, fallbacks=fallbacks, search_nodes=nodes,
                   service_ns=service_ns, setup_ns=solver.setup_ns, latency_ns=latency_ns,
                   stored_entries=stats["entries"], input_witness_bytes=payload, certificate_bytes=proof_bytes,
                   engine=solver.engine_id)
        closing = time.perf_counter_ns()
    row["shutdown_ns"] = time.perf_counter_ns() - closing
    row["total_ns"] = row["setup_ns"] + service_ns + row["shutdown_ns"]
    row["database_bytes"] = path.stat().st_size
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/results/lazy-search")
    parser.add_argument("--engine", type=Path, default=DEFAULT_ENGINE)
    parser.add_argument("--queries", type=int, default=32)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--extended", action="store_true", help="Also test sparse indices, root conflicts, and UNSAT extensions")
    args = parser.parse_args()
    if args.queries < 2 or args.repeats < 1:
        parser.error("Use at least two queries and one repeat")
    if any((args.output / name).exists() for name in
           ("inputs.json", "workloads.jsonl", "summary.json", "metadata.json")):
        parser.error("Results already exist; choose a new --output directory to retain earlier runs")
    args.output.mkdir(parents=True, exist_ok=True)
    rows, streams = [], []
    with tempfile.TemporaryDirectory(prefix="oracle-workloads-") as scratch:
        for width in (2, 4, 8, 12):
            for name, (bits, expected) in workloads(width, args.queries, args.extended).items():
                stream = dict(width=width, workload=name, bits=bits, expected=expected)
                stream_hash = hashlib.sha256(json.dumps(stream, sort_keys=True).encode()).hexdigest()
                stream["sha256"] = stream_hash
                streams.append(stream)
                for repeat in range(args.repeats):
                    order = MODES[repeat % len(MODES):] + MODES[:repeat % len(MODES)]
                    for mode in order:
                        cache = Path(scratch) / f"{width}-{name}-{repeat}-{mode}.sqlite3"
                        row = run_one(mode, bits, expected, cache, args.engine)
                        row.update(width=width, workload=name, repeat=repeat,
                                   queries=len(bits), distinct=len(set(bits)), input_sha256=stream_hash)
                        rows.append(row)
                print(f"checked width={width} workload={name}", file=sys.stderr, flush=True)
    raw = "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows)
    (args.output / "workloads.jsonl").write_text(raw)
    (args.output / "inputs.json").write_text(json.dumps(streams, indent=2) + "\n")
    summaries = []
    for stream in streams:
        selected = [r for r in rows if r["width"] == stream["width"] and r["workload"] == stream["workload"]]
        baseline = next(r["core_work"] for r in selected if r["mode"] == "baseline")
        total_baseline = next(r["counted_work"] for r in selected if r["mode"] == "baseline")
        for mode in MODES:
            group = [r for r in selected if r["mode"] == mode]
            if len({(r["core_work"], r["parse_work"]) for r in group}) != 1:
                raise AssertionError("Operation counts changed across identical runs")
            row = dict(width=stream["width"], workload=stream["workload"], mode=mode,
                       core_work=group[0]["core_work"],
                       core_ratio=group[0]["core_work"] / baseline,
                       parse_work=group[0]["parse_work"], counted_work=group[0]["counted_work"],
                       counted_ratio=group[0]["counted_work"] / total_baseline,
                       service_ms_median=statistics.median(r["service_ns"] for r in group) / 1e6,
                       total_ms_median=statistics.median(r["total_ns"] for r in group) / 1e6,
                       setup_ms_median=statistics.median(r["setup_ns"] for r in group) / 1e6,
                       shutdown_ms_median=statistics.median(r["shutdown_ns"] for r in group) / 1e6,
                       database_bytes=group[0]["database_bytes"],
                       input_witness_bytes=group[0]["input_witness_bytes"],
                       certificate_bytes=group[0]["certificate_bytes"], search_nodes=group[0]["search_nodes"],
                       cache_hits=group[0]["cache_hits"], witness_hits=group[0]["witness_hits"],
                       refutation_hits=group[0]["refutation_hits"], fallbacks=group[0]["fallbacks"])
            summaries.append(row)
    (args.output / "summary.json").write_text(json.dumps(summaries, indent=2) + "\n")
    metadata = dict(cost_model="parser-lazy-search-v3", platform=platform.platform(), machine=platform.machine(), python=sys.version,
                    engine_sha256=rows[0]["engine"], queries=args.queries, repeats=args.repeats,
                    runs=len(rows), checked_answers=len(rows) * args.queries, extended=args.extended,
                    raw_sha256=hashlib.sha256(raw.encode()).hexdigest(),
                    limitations="Synthetic exact-core mechanism study; not a neural or competitive SAT benchmark. "
                                 "Counted work includes parser and core operations; RPC and persistence appear only in elapsed times, which include shutdown. "
                                 "All modes pay the same wrapper setup; setup is also reported separately. Observer statistics and the experiment runner are excluded. Database bytes are measured after close; process peak memory is not measured.")
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
