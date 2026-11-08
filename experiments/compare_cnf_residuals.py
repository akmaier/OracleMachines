#!/usr/bin/env python3
"""Matched ablations, warm reuse, and checked cold replay for the CNF candidate."""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_residual_dag import ResidualSolver, holds


def pigeonhole(holes):
    pigeons = holes + 1
    cnf = [tuple(p * holes + j + 1 for j in range(holes)) for p in range(pigeons)]
    cnf += [(-(p * holes + j + 1), -(q * holes + j + 1))
            for j in range(holes) for p, q in itertools.combinations(range(pigeons), 2)]
    return cnf


def odd_cycle(n):
    return [c for v in range(1, n + 1) for c in ((v, v % n + 1), (-v, -(v % n + 1)))]


def planted(seed):
    rng = random.Random(seed)
    clauses = set()
    while len(clauses) < 14:
        clause = [v * rng.choice((-1, 1)) for v in rng.sample(range(1, 7), 3)]
        if all(lit > 0 for lit in clause):
            clause[0] *= -1
        clauses.add(tuple(sorted(clause)))
    return sorted(clauses)


def workload():
    cases = []
    for family in ("repeated_components", "novel_components"):
        for size in (4, 8, 16, 32):
            cnf = [tuple((abs(lit) + 6 * i) * (1 if lit > 0 else -1) for lit in clause)
                   for i in range(size)
                   for clause in planted(100 if family == "repeated_components" else 100 + i)]
            cases.append(dict(family=family, size=size, cnf=cnf, expected=True))
    for n in (25, 51, 101, 201):
        cases.append(dict(family="odd_cycle_2cnf", size=n, cnf=odd_cycle(n), expected=False))
    for holes in range(2, 7):
        cases.append(dict(family="pigeonhole", size=holes, cnf=pigeonhole(holes), expected=False))
    rng = random.Random(20261108)
    for n in (8, 12, 16):
        for sample in range(3):
            cnf = [tuple(v * rng.choice((-1, 1)) for v in rng.sample(range(1, n + 1), 3))
                   for _ in range(round(4.3 * n))]
            expected = any(holds(cnf, dict(enumerate(bits, 1)))
                           for bits in itertools.product((False, True), repeat=n))
            cases.append(dict(family="seeded_3cnf", size=n, sample=sample, cnf=cnf, expected=expected))
    return cases


def archive_digest(solver):
    digest = hashlib.sha256()
    rows = solver.db.execute("SELECT id,payload FROM cnf_residual_v1 ORDER BY id")
    for key, payload in rows:
        digest.update(json.dumps([key, payload], separators=(",", ":")).encode())
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cases = workload()
    modes = {"full": {}, "no_search_reuse": {"reuse": False},
             "no_classes": {"leaves": False}, "no_components": {"decompose": False}}
    records, archives = [], []
    for mode, options in modes.items():
        for case_id, case in enumerate(cases):
            # Matched independent acquisitions, not a hidden warm cache from
            # preceding sizes. Within a case every completed residual is retained.
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "residuals.sqlite3"
                init = time.perf_counter()
                solver = ResidualSolver(path, **options)
                initialization_seconds = time.perf_counter() - init
                original = solver.solve(case["cnf"])
                assert original["answer"] == case["expected"]
                before = archive_digest(solver)
                phases = [("acquisition", original, initialization_seconds)]
                # Warm reuse and cold reconstruction are examined for the full
                # candidate. Ablations are acquisition-only comparisons.
                if mode == "full":
                    warm = solver.solve(case["cnf"])
                    assert archive_digest(solver) == before
                    phases.append(("warm", warm, 0))
                    solver.close()
                    init = time.perf_counter()
                    solver = ResidualSolver(path, **options)
                    cold_init = time.perf_counter() - init
                    cold = solver.solve(case["cnf"])
                    assert cold["answer"] == case["expected"]
                    assert archive_digest(solver) == before
                    phases.append(("cold", cold, cold_init))
                bytes_on_disk = path.stat().st_size
                for phase, result, init_seconds in phases:
                    root = result.pop("root")
                    result.pop("model")
                    records.append(dict(mode=mode, case=case_id, phase=phase,
                                        initialization_seconds=init_seconds,
                                        database_bytes=bytes_on_disk,
                                        root_sha256=hashlib.sha256(root.encode()).hexdigest(), **result))
                integrity = solver.db.execute("PRAGMA integrity_check").fetchone()[0]
                assert integrity == "ok"
                solver.close()
                destination = args.output / f"archive-{mode}-{case_id:02d}.sqlite3.gz"
                raw = path.read_bytes()
                destination.write_bytes(gzip.compress(raw, mtime=0))
                archives.append(dict(mode=mode, case=case_id, path=destination.name,
                                     raw_bytes=len(raw), compressed_bytes=destination.stat().st_size,
                                     database_sha256=hashlib.sha256(raw).hexdigest(),
                                     row_digest=before, integrity=integrity))
        print(mode, "completed", flush=True)
    report = dict(source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  candidate_sha256=hashlib.sha256(Path(__file__).with_name("cnf_residual_dag.py").read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  seed=20261108, cases=cases, records=records, archives=archives,
                  limitations=["Research implementation; not a Lean-verified native solver path",
                               "No polynomial bound on distinct residuals; no P=NP claim",
                               "Single timing observation per phase; mechanism counts are the primary evidence",
                               "Ablations compare this candidate, not a competitive external SAT solver",
                               "Seconds include query reporting SQL scan; initialization is separate",
                               "Diagnostic counters are named payload/visit counts, not all instructions",
                               "Proof checking, normalization, full-key copying, SQL and serialization are timed",
                               "Archive snapshots and their integrity/digest checks are offline and not included",
                               "Physical process peak RSS is not measured; database and logical payload are recorded"])
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(cases=len(cases), records=len(records), archives=len(archives),
                          compressed_archive_bytes=sum(a["compressed_bytes"] for a in archives))))


if __name__ == "__main__":
    main()
