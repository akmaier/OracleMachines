#!/usr/bin/env python3
"""Test matching recognition against the preceding residual portfolio."""
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
from experiments.compare_cnf_residuals import archive_digest, pigeonhole, workload


def domain_cnf(domains):
    variables, by_resource, cnf = 0, {}, []
    for domain in domains:
        clause = []
        for resource in domain:
            variables += 1
            clause.append(variables)
            by_resource.setdefault(resource, []).append(variables)
        cnf.append(clause)
    for group in by_resource.values():
        cnf.extend([[-a, -b] for a, b in itertools.combinations(group, 2)])
    return cnf


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cases = workload()
    for holes in (7, 8, 12, 24, 48):
        cases.append(dict(family="pigeonhole", size=holes, cnf=pigeonhole(holes),
                          expected=False, matching_only=holes > 8))
    for size in (4, 8, 16, 32):
        cases.append(dict(family="satisfiable_matching", size=size,
                          cnf=domain_cnf([sorted({i, (i + 1) % size, (i + 2) % size}) for i in range(size)]),
                          expected=True))
    for holes in (3, 4, 5):
        cnf = pigeonhole(holes)
        cnf.remove((-1, -(holes + 1)))
        cases.append(dict(family="missing_conflict_edge", size=holes, cnf=cnf, expected=True))
    cases.append(dict(family="overlapping_choices", size=5,
                      cnf=[(1, 2, 3), (3, 4, 5)] + [(-a, -b) for a, b in itertools.combinations(range(1, 6), 2)],
                      expected=True))
    records, archives = [], []
    for case_id, case in enumerate(cases):
        for mode, use_matching in (("matching", True), ("previous_portfolio", False)):
            if not use_matching and case.get("matching_only"):
                continue
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "residuals.sqlite3"
                init = time.perf_counter()
                solver = ResidualSolver(path, matching=use_matching)
                init_seconds = time.perf_counter() - init
                acquired = solver.solve(case["cnf"])
                assert acquired["answer"] == case["expected"]
                digest = archive_digest(solver)
                phases = [("acquisition", acquired, init_seconds)]
                if use_matching:
                    warm = solver.solve(case["cnf"])
                    assert archive_digest(solver) == digest
                    phases.append(("warm", warm, 0))
                    solver.close()
                    init = time.perf_counter()
                    solver = ResidualSolver(path)
                    cold_init = time.perf_counter() - init
                    cold = solver.solve(case["cnf"])
                    assert cold["answer"] == case["expected"]
                    assert archive_digest(solver) == digest
                    phases.append(("cold", cold, cold_init))
                for phase, result, seconds in phases:
                    root = result.pop("root")
                    result.pop("model")
                    records.append(dict(case=case_id, mode=mode, phase=phase,
                                        initialization_seconds=seconds, database_bytes=path.stat().st_size,
                                        root_sha256=hashlib.sha256(root.encode()).hexdigest(), **result))
                assert solver.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                solver.close()
                raw = path.read_bytes()
                destination = args.output / f"archive-{mode}-{case_id:02d}.sqlite3.gz"
                destination.write_bytes(gzip.compress(raw, mtime=0))
                archives.append(dict(mode=mode, case=case_id, path=destination.name,
                                     raw_bytes=len(raw), compressed_bytes=destination.stat().st_size,
                                     database_sha256=hashlib.sha256(raw).hexdigest(), row_digest=digest))
        print(case_id, case["family"], case["size"], "checked", flush=True)
    # The added certificate type is additive: every original snapshot is still
    # readable, all original answers still check, and loading changes no row.
    previous = Path(__file__).parent / "results/cnf-residual-dag"
    old_report = json.loads((previous / "report.json").read_text())
    old_checks = []
    for archived in old_report["archives"]:
        compressed = previous / archived["path"]
        raw = gzip.decompress(compressed.read_bytes())
        assert hashlib.sha256(raw).hexdigest() == archived["database_sha256"]
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "old.sqlite3"
            path.write_bytes(raw)
            solver = ResidualSolver(path)
            result = solver.solve(old_report["cases"][archived["case"]]["cnf"])
            assert result["answer"] == old_report["cases"][archived["case"]]["expected"]
            assert result["metrics"].get("expanded_nodes", 0) == 0
            assert archive_digest(solver) == archived["row_digest"]
            solver.close()
        old_checks.append(archived["path"])
    report = dict(source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  candidate_sha256=hashlib.sha256(Path(__file__).with_name("cnf_residual_dag.py").read_bytes()).hexdigest(),
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  cases=cases, records=records, archives=archives,
                  old_archives_rechecked_without_changes=old_checks,
                  limitations=["Matching recognition is a restricted class, not arbitrary SAT",
                               "No search-reuse theorem bounds all residual counts polynomially",
                               "Python certificate checker not connected to the native Lean trust boundary",
                               "Single timing samples; no competitive CDCL or peak-RSS comparison",
                               "Sizes 12/24/48 holes test matching only; no exponential baseline was run",
                               "Reported seconds include solve, verification, serialization and final SQL size scan",
                               "Database initialization is separate; offline snapshot/compression/report time excluded"])
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(cases=len(cases), records=len(records), archives=len(archives),
                          old_archives_rechecked=len(old_checks))))


if __name__ == "__main__":
    main()
