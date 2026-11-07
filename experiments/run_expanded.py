#!/usr/bin/env python3
"""Chronological public/structural workloads; preserve every failure and timeout.

Archives stay outside Git. Selection is fixed before timing, by sorted filename.
Each stream/mode/repetition has a fresh process and database. Direct CaDiCaL
uses original DIMACS and is an unverified performance reference. All other modes
use the same checked service and include conversion, acquisition and updates.
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
import tarfile
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from solver.persistent import PersistentSolver, DEFAULT_ENGINE, find_cadical
from solver.resources import BudgetExceeded, Deadline, bounded_run, peak_rss
from solver.incremental import DEFAULT_INCREMENTAL
import resource

BASE = "https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/"
ARCHIVES = {"uf50-218": "RND3SAT/uf50-218.tar.gz", "uuf50-218": "RND3SAT/uuf50-218.tar.gz",
            "flat30-60": "GCP/flat30-60.tar.gz", "aim": "DIMACS/AIM/aim.tar.gz",
            "ssa": "DIMACS/SSA/ssa.tar.gz"}
MODES = ["direct", "checked", "exact", "portfolio", "incremental", "learned"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_dimacs(text):
    header, clauses, current = None, [], []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("c"):
            continue
        if line.startswith("%"):
            break
        if line.startswith("p"):
            fields = line.split()
            if header is not None or clauses or current or len(fields) != 4 or fields[:2] != ["p", "cnf"]:
                raise ValueError("Invalid DIMACS header")
            header = tuple(map(int, fields[2:]))
            if min(header) < 0:
                raise ValueError("Negative DIMACS size")
            continue
        if header is None:
            raise ValueError("Missing DIMACS header")
        for token in line.split():
            literal = int(token)
            if abs(literal) > header[0]:
                raise ValueError("DIMACS variable outside header")
            if literal:
                current.append(literal)
            else:
                clauses.append(current)
                current = []
    if header is None or current or len(clauses) != header[1]:
        raise ValueError("Unterminated clause or incorrect DIMACS clause count")
    return header[0], clauses


def balanced(parts, combine, empty):
    if not parts:
        return empty
    while len(parts) > 1:
        parts = [combine(parts[i], parts[i+1]) if i+1 < len(parts) else parts[i]
                 for i in range(0, len(parts), 2)]
    return parts[0]


def encode_dimacs(text, maximum=8 * 1024**2):
    _, clauses = parse_dimacs(text)
    # Conservative preflight before allocating the unary-index expansion.
    size = 4 + sum(4 + sum(abs(v) + 12 for v in c) for c in clauses)
    if size > maximum:
        raise BudgetExceeded("DIMACS unary conversion exceeds input budget")
    terms = []
    for clause in clauses:
        literals = ["01" + "1" * (abs(v)-1) + "0" + ("10" if v < 0 else "") for v in clause]
        terms.append(balanced(literals, lambda a, b: a + "10" + b + "10" + "1110", "00"))
    return balanced(terms, lambda a, b: a + b + "11", "0010")


def dimacs(clauses, variables=None):
    n = variables if variables is not None else max((abs(v) for c in clauses for v in c), default=0)
    return f"p cnf {n} {len(clauses)}\n" + "".join(" ".join(map(str, c)) + " 0\n" for c in clauses)


def workloads(directory):
    manifest, groups = {}, []
    for archive, relative in ARCHIVES.items():
        path = directory / (archive + ".tar.gz")
        manifest[archive] = dict(url=BASE + relative, sha256=digest(path.read_bytes()))
        with tarfile.open(path) as bundle:
            members = sorted((m for m in bundle.getmembers() if m.isfile() and m.name.endswith(".cnf")), key=lambda m: m.name)
            if archive == "aim":
                members = [m for m in members if "-no-" in m.name][:3] + [m for m in members if "-yes1-" in m.name][:3]
            elif archive == "ssa":
                # First two UNSAT and first two SAT filenames, fixed by source labels.
                names = {"ssa0432-003.cnf", "ssa2670-130.cnf", "ssa7552-038.cnf", "ssa7552-158.cnf"}
                members = [m for m in members if m.name in names]
            else:
                members = members[:6]
            cases = []
            for member in members:
                raw = bundle.extractfile(member).read()  # never extract untrusted paths
                expected = (archive in ("uf50-218", "flat30-60") or
                            archive == "aim" and "-yes1-" in member.name or
                            archive == "ssa" and "ssa7552" in member.name)
                cases.append(dict(name=member.name, dimacs=raw.decode(), expected=expected,
                                  file_sha256=digest(raw), phase="public"))
            groups.append(dict(name="satlib_" + archive, cases=cases))
    units = []
    for t in range(10):
        n = 12 + 2*t
        clauses = [[(i+1) * (1 if (i+t) % (2 + t % 3) == 0 else -1)] for i in range(n)]
        units.append(dict(name=f"signed_units_{t}", dimacs=dimacs(clauses), expected=True,
                          phase="train" if t < 2 else "held_out"))
    groups.append(dict(name="learned_transfer", cases=units))
    graph = next(g for g in groups if g["name"] == "satlib_flat30-60")["cases"]
    groups.append(dict(name="distribution_shift", cases=units[:2] +
                       [dict(c, phase="shift") for c in graph] + units[6:]))
    rng = random.Random(707)
    planted = [rng.choice([-1, 1]) for _ in range(20)]
    base = []
    for _ in range(86):
        clause = [(i+1)*rng.choice([-1, 1]) for i in rng.sample(range(20), 3)]
        if not any((v > 0) == (planted[abs(v)-1] > 0) for v in clause):
            clause[0] *= -1
        base.append(clause)
    structural = [dict(name=f"root_extension_{i}", dimacs=dimacs(base + [[(21+i) * (-1 if i % 2 else 1)]]),
                       expected=True, phase="structural") for i in range(10)]
    groups.append(dict(name="shared_definitions", cases=structural))
    groups.append(dict(name="exact_repetition", cases=[structural[0]] * 10))
    for group in groups:
        for case in group["cases"]:
            case.setdefault("file_sha256", digest(case["dimacs"].encode()))
    return manifest, groups


def worker(mode, group, seconds):
    with tempfile.TemporaryDirectory(prefix="oracle-expanded-") as tmp:
        directory = Path(tmp)
        started = time.perf_counter_ns()
        solver = None if mode == "direct" else PersistentSolver(
            directory / "results.sqlite3", backend="cadical", query_timeout=seconds, timeout=seconds,
            incremental=mode in ("incremental", "learned"), learned=mode == "learned", reuse_exact=mode != "checked")
        print(json.dumps(dict(event="setup", ns=time.perf_counter_ns()-started,
                              engine=solver.engine_id if solver else None)), flush=True)
        try:
            for index, case in enumerate(group["cases"]):
                start = time.perf_counter_ns()
                row = dict(event="query", index=index, name=case["name"], phase=case["phase"], expected=case["expected"])
                try:
                    if mode == "direct":
                        cnf = directory / "query.cnf"
                        cnf.write_text(case["dimacs"])
                        run = bounded_run([str(find_cadical()), "--quiet", str(cnf)], directory,
                                          Deadline(seconds), seconds, 64*1024**2, directory/"unused.proof", 16*1024**2)
                        if run.returncode not in (10, 20):
                            raise RuntimeError(f"CaDiCaL exit {run.returncode}")
                        result = dict(answer=run.returncode == 10, source="direct", counted_complete=False)
                    else:
                        bits = encode_dimacs(case["dimacs"])
                        row.update(conversion_ns=time.perf_counter_ns()-start, input_bytes=len(bits))
                        result = solver.solve(bits, learn=mode in ("portfolio", "learned"))
                    row.update({k:v for k,v in result.items() if k not in ("witness", "certificate", "original_measurements")})
                    row["status"] = "ok" if result["answer"] == case["expected"] else "wrong_answer"
                except Exception as exc:
                    row.update(status="timeout_or_limit" if isinstance(exc, BudgetExceeded) else "error",
                               error=type(exc).__name__ + ": " + str(exc))
                    if solver and solver.last_metrics:
                        row["failure_metrics"] = solver.last_metrics
                row["latency_ns"] = time.perf_counter_ns()-start
                print(json.dumps(row, sort_keys=True), flush=True)
        finally:
            if solver:
                storage = dict(stats=solver.stats(), model_bytes=solver.db.execute("SELECT coalesce(sum(length(state)),0) FROM models").fetchone()[0],
                               proof_bytes=solver.db.execute("SELECT coalesce(sum(length(certificate)),0) FROM proofs").fetchone()[0])
                solver.close()
                storage["database_bytes"] = (directory/"results.sqlite3").stat().st_size
            else:
                storage = {}
            print(json.dumps(dict(event="end", service_peak_rss_bytes=peak_rss(resource.RUSAGE_SELF),
                                  reaped_children_peak_rss_bytes=peak_rss(resource.RUSAGE_CHILDREN), **storage)), flush=True)


def isolated(mode, group, seconds):
    start = time.perf_counter_ns()
    process = subprocess.Popen([sys.executable, __file__, "--worker", mode, "--query-timeout", str(seconds)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    status = "ok"
    try:
        out, err = process.communicate(json.dumps(group), timeout=seconds*len(group["cases"])+15)
    except subprocess.TimeoutExpired:
        status = "worker_timeout"
        os.killpg(process.pid, signal.SIGKILL)
        out, err = process.communicate()
    if process.returncode and status == "ok":
        status = "worker_error"
    events = []
    for line in out.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            status = "worker_error"
    return dict(status=status, events=events, stderr=err[-4000:], worker_ns=time.perf_counter_ns()-start)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=MODES)
    parser.add_argument("--archives", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT/"experiments/results/expanded")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--query-timeout", type=float, default=3)
    args = parser.parse_args()
    if args.worker:
        worker(args.worker, json.load(sys.stdin), args.query_timeout)
        return
    if not args.archives or args.repeats < 1 or args.query_timeout <= 0:
        parser.error("Supply archives, positive repeats and timeout")
    if not DEFAULT_INCREMENTAL.is_file() or not find_cadical():
        parser.error("Build both solver binaries first")
    args.output.mkdir(parents=True, exist_ok=True)
    if any(args.output.iterdir()):
        parser.error("Choose an empty output directory")
    archives, groups = workloads(args.archives)
    manifest = dict(archives=archives, groups=[dict(name=g["name"], cases=[{k:v for k,v in c.items() if k != "dimacs"} for c in g["cases"]]) for g in groups])
    (args.output/"manifest.json").write_text(json.dumps(manifest, indent=2)+"\n")
    rows = []
    with (args.output/"runs.jsonl").open("w") as log:
        for group in groups:
            for repeat in range(args.repeats):
                for mode in MODES[repeat % len(MODES):] + MODES[:repeat % len(MODES)]:
                    row = isolated(mode, group, args.query_timeout)
                    row.update(mode=mode, workload=group["name"], repeat=repeat, planned_queries=len(group["cases"]))
                    rows.append(row)
                    log.write(json.dumps(row, sort_keys=True)+"\n")
                    log.flush()
            print("finished " + group["name"], file=sys.stderr, flush=True)
    summary = []
    for group in groups:
        for mode in MODES:
            selected = [r for r in rows if r["workload"] == group["name"] and r["mode"] == mode]
            queries = [e for r in selected for e in r["events"] if e["event"] == "query"]
            ok = [e for e in queries if e["status"] == "ok"]
            latencies = sorted(e["latency_ns"]/1e6 for e in ok)
            summary.append(dict(workload=group["name"], mode=mode, planned=len(group["cases"])*args.repeats,
                                completed=len(ok), failed=len(queries)-len(ok), missing=len(group["cases"])*args.repeats-len(queries),
                                median_ms=statistics.median(latencies) if latencies else None,
                                p95_ms=latencies[min(len(latencies)-1, int(0.95*len(latencies)))] if latencies else None,
                                worker_ms_median=statistics.median(r["worker_ns"] for r in selected)/1e6,
                                learned_hits=sum(e.get("source") == "learned_witness" for e in ok),
                                cache_hits=sum(e.get("source") == "cache" for e in ok)))
    (args.output/"summary.json").write_text(json.dumps(summary, indent=2)+"\n")
    metadata = dict(platform=platform.platform(), python=sys.version, seed=707, repeats=args.repeats,
                    query_timeout=args.query_timeout, runs=len(rows),
                    native_sha256=digest(DEFAULT_ENGINE.read_bytes()), incremental_sha256=digest(DEFAULT_INCREMENTAL.read_bytes()),
                    cadical_sha256=digest(find_cadical().read_bytes()),
                    source_sha256={str(p.relative_to(ROOT)):digest(p.read_bytes()) for p in [Path(__file__), *sorted((ROOT/"solver").glob("*.py")), ROOT/"solver/incremental.cpp"]},
                    raw_sha256=digest((args.output/"runs.jsonl").read_bytes()))
    (args.output/"metadata.json").write_text(json.dumps(metadata, indent=2)+"\n")
    if any(e.get("status") == "wrong_answer" for r in rows for e in r["events"]):
        raise SystemExit("WRONG ANSWER: retained in results")


if __name__ == "__main__":
    main()
