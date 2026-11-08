#!/usr/bin/env python3
"""Matched positive-core reduction, growing histories and old-archive replay."""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_residual_dag import ResidualSolver
from experiments.compare_cnf_matching import domain_cnf
from experiments.compare_cnf_residuals import archive_digest, pigeonhole, workload


def laminar_supersets(cnf, choices):
    return cnf + [tuple(v for c in cnf[:k] for v in c) for k in range(2, choices + 1)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cases = workload()
    for holes in range(3, 9):
        cases.append(dict(family="laminar_pigeonhole", size=holes,
                          cnf=laminar_supersets(pigeonhole(holes), holes + 1), expected=False))
    for size in (4, 8, 12, 16):
        cases.append(dict(family="laminar_satisfiable_matching", size=size,
                          cnf=laminar_supersets(domain_cnf([range(size)] * size), size), expected=True))
    for size in (4, 8):
        cnf = pigeonhole(size)
        cases.append(dict(family="crossing_redundant_supersets", size=size,
                          cnf=cnf + [tuple(cnf[0]) + (cnf[1][i],) for i in range(size)], expected=False))
    cases.append(dict(family="irreducible_positive_overlap", size=5,
                      cnf=[(1, 2, 3), (3, 4, 5)] +
                          [(-a, -b) for a, b in itertools.combinations(range(1, 6), 2)], expected=True))

    streams = []
    for sat in (False, True):
        for size in (4, 8):
            core = domain_cnf([range(size)] * size) if sat else pigeonhole(size)
            history = [dict(cnf=core, expected=sat)]
            accumulated = list(core)
            max_var = max(abs(lit) for c in core for lit in c)
            for step in range(1, 9):
                # A new variable makes the source grow, but it occurs only in
                # an entailed clause. All eight additions have the same core.
                added = tuple(core[(step - 1) % size]) + (max_var + step,)
                accumulated = accumulated + [added]
                history.append(dict(cnf=accumulated, expected=sat, added=added))
            streams.append(dict(family="sat_growth" if sat else "unsat_growth",
                                size=size, history=history))

    records, archives = [], []

    def evaluate(kind, case_id, history):
        for mode, enabled in (("positive_core", True), ("previous_matching", False)):
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "residuals.sqlite3"
                started = time.perf_counter()
                solver = ResidualSolver(path, positive_subsumption=enabled)
                initialization = time.perf_counter() - started
                old_rows = {}
                for step, item in enumerate(history):
                    acquired = solver.solve(item["cnf"])
                    assert acquired["answer"] == item["expected"]
                    current = dict(solver.db.execute("SELECT * FROM cnf_residual_v1"))
                    assert all(current[key] == payload for key, payload in old_rows.items())
                    old_rows = current
                    digest = archive_digest(solver)
                    warm = solver.solve(item["cnf"])
                    assert warm["answer"] == item["expected"]
                    assert warm["metrics"].get("expanded_nodes", 0) == 0
                    assert archive_digest(solver) == digest
                    cold_start = time.perf_counter()
                    cold_solver = ResidualSolver(path, positive_subsumption=enabled)
                    cold_init = time.perf_counter() - cold_start
                    cold = cold_solver.solve(item["cnf"])
                    assert cold["answer"] == item["expected"]
                    assert cold["metrics"].get("expanded_nodes", 0) == 0
                    assert archive_digest(cold_solver) == digest
                    cold_solver.close()
                    for phase, result, init in (("acquisition", acquired, initialization if step == 0 else 0),
                                                ("warm", warm, 0), ("cold", cold, cold_init)):
                        root = result.pop("root")
                        result.pop("model")
                        records.append(dict(kind=kind, case=case_id, step=step, mode=mode, phase=phase,
                                            initialization_seconds=init, database_bytes=path.stat().st_size,
                                            root_sha256=hashlib.sha256(root.encode()).hexdigest(), **result))
                assert solver.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                solver.close()
                raw = path.read_bytes()
                destination = args.output / f"archive-{kind}-{case_id:02d}-{mode}.sqlite3.gz"
                destination.write_bytes(gzip.compress(raw, mtime=0))
                archives.append(dict(kind=kind, case=case_id, mode=mode, path=destination.name,
                                     raw_bytes=len(raw), compressed_bytes=destination.stat().st_size,
                                     database_sha256=hashlib.sha256(raw).hexdigest(), row_digest=digest))
        print(kind, case_id, "checked", flush=True)

    for case_id, case in enumerate(cases):
        evaluate("static", case_id, [case])
    for case_id, stream in enumerate(streams):
        evaluate("stream", case_id, stream["history"])

    old_checks = []
    for name in ("cnf-residual-dag", "cnf-matching"):
        previous = Path(__file__).parent / "results" / name
        report = json.loads((previous / "report.json").read_text())
        for archived in report["archives"]:
            raw = gzip.decompress((previous / archived["path"]).read_bytes())
            assert hashlib.sha256(raw).hexdigest() == archived["database_sha256"]
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "old.sqlite3"
                path.write_bytes(raw)
                solver = ResidualSolver(path)
                case = report["cases"][archived["case"]]
                result = solver.solve(case["cnf"])
                assert result["answer"] == case["expected"]
                assert result["metrics"].get("expanded_nodes", 0) == 0
                assert archive_digest(solver) == archived["row_digest"]
                solver.close()
            old_checks.append(f"{name}/{archived['path']}")

    report = dict(source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  candidate_sha256=hashlib.sha256(Path(__file__).with_name("cnf_residual_dag.py").read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  cases=cases, streams=streams, records=records, archives=archives,
                  old_archives_rechecked_without_changes=old_checks,
                  limitations=["Positive subsumption is established preprocessing, not a novel SAT algorithm",
                               "Minimal positive overlap can still encode arbitrary SAT",
                               "Every distinct source retains its full key and checked record; cores alone are shared",
                               "Recognition is rerun from the source, not yet a delta-only update",
                               "Single timing samples, no competitive CDCL or process peak-RSS comparison",
                               "Solve time includes recognition, checking, serialization, SQL writes and full archive size scan",
                               "Initialization is separate; offline replay audit, digests, compression and reporting excluded",
                               "Python program is not linked to the native Lean trust boundary"])
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(cases=len(cases), streams=len(streams), decisions=len(records),
                          archives=len(archives), previous_archives=len(old_checks))))


if __name__ == "__main__":
    main()
