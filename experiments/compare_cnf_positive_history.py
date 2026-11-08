#!/usr/bin/env python3
"""Compare full-source core reuse with checked append-only source deltas."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_positive_history import PositiveHistory, UnsupportedExpansion
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_matching import domain_cnf
from experiments.compare_cnf_residuals import archive_digest, pigeonhole


def scenarios():
    cases = []
    for sat in (False, True):
        for size in (4, 8, 16):
            for steps in ((8, 32, 128, 512) if size == 4 else (8, 32, 128)):
                base = domain_cnf([range(size)] * size) if sat else pigeonhole(size)
                largest = max(abs(lit) for c in base for lit in c)
                additions = [tuple(base[i % size]) + (largest + i + 1,) for i in range(steps)]
                cases.append(dict(family="redundant_sat" if sat else "redundant_unsat", size=size,
                                  base=base, additions=additions, expected=sat))
    base = domain_cnf([range(4)] * 4)
    for family, steps in (("repeated_clause", 128), ("repeated_operation", 128),
                          ("novel_units", 32), ("mixed_redundant_novel", 32)):
        additions = []
        for i in range(steps):
            if family in ("repeated_clause", "repeated_operation"):
                additions.append(tuple(base[0]) + (100,))
            elif family == "novel_units" or i % 2:
                additions.append((100 + i,))
            else:
                additions.append(tuple(base[i % 4]) + (100 + i,))
        cases.append(dict(family=family, size=4, base=base, additions=additions,
                          expected=True, same_parent=family == "repeated_operation"))
    return cases


def all_rows(db):
    return {name: list(db.execute("SELECT * FROM " + name + " ORDER BY id")) for name in
            ("cnf_residual_v1", "cnf_positive_bases_v1", "cnf_positive_versions_v1")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cases, records, archives = scenarios(), [], []
    for case_id, case in enumerate(cases):
        for mode in ("full_source", "delta_history"):
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "history.sqlite3"
                started = time.perf_counter()
                engine = PositiveHistory(path) if mode == "delta_history" else ResidualSolver(path)
                initialization = time.perf_counter() - started
                source = tuple(map(tuple, case["base"]))
                initial_version = version = None
                for step, clause in enumerate([None] + case["additions"]):
                    if clause is not None:
                        if case.get("same_parent"):
                            source = tuple(map(tuple, case["base"])) + (tuple(clause),)
                            version = initial_version
                        else:
                            source = source + (tuple(clause),)
                    operation_start = time.perf_counter()
                    fallback = None
                    if mode == "full_source":
                        result = engine.solve(source)
                        result.pop("root")
                        result.pop("model")
                    elif clause is None:
                        result = engine.prepare(source)
                    else:
                        try:
                            result = engine.append(version, clause)
                        except UnsupportedExpansion:
                            rejected = dict(metrics=dict(engine.counts), solver_metrics=dict(engine.solver.counts))
                            materialized = engine.materialize(version)
                            expanded = materialized.pop("cnf") + (tuple(clause),)
                            result = engine.prepare(expanded)
                            fallback = dict(rejected=rejected, materialization=materialized)
                    operation_seconds = time.perf_counter() - operation_start
                    assert result["answer"] == case["expected"]
                    if mode == "delta_history":
                        version = result.pop("version")
                        if initial_version is None:
                            initial_version = version
                    records.append(dict(case=case_id, mode=mode, phase="acquisition", step=step,
                                        operation_seconds=operation_seconds, fallback=fallback,
                                        initialization_seconds=initialization if step == 0 else 0, **result))
                # These optional full scans and exports are timed explicitly;
                # they are not silently treated as delta-only operations.
                validation_start = time.perf_counter()
                if mode == "delta_history":
                    materialized = engine.materialize(version)
                    assert materialized["cnf"] == source
                    witness = engine.witness(version)
                    if case["expected"]:
                        assert holds(source, witness["model"])
                    storage = engine.storage()
                    saved_rows = all_rows(engine.db)
                    row_digest = hashlib.sha256(json.dumps(saved_rows, sort_keys=True).encode()).hexdigest()
                else:
                    materialized = witness = None
                    row_digest = archive_digest(engine)
                    storage = dict(residual_nodes=result["archive_nodes"], logical_bytes=result["archive_payload_bytes"])
                validation_seconds = time.perf_counter() - validation_start
                replay_records = []
                for phase in ("warm", "cold"):
                    if phase == "cold":
                        engine.close()
                        started = time.perf_counter()
                        engine = PositiveHistory(path) if mode == "delta_history" else ResidualSolver(path)
                        replay_initialization = time.perf_counter() - started
                    else:
                        replay_initialization = 0
                    replay = engine.query(version) if mode == "delta_history" else engine.solve(source)
                    assert replay["answer"] == case["expected"]
                    if mode == "delta_history":
                        replay.pop("version")
                        assert replay["solver_metrics"].get("expanded_nodes", 0) == 0
                        assert all_rows(engine.db) == saved_rows
                    else:
                        replay.pop("root")
                        replay.pop("model")
                        assert replay["metrics"].get("expanded_nodes", 0) == 0
                        assert archive_digest(engine) == row_digest
                    replay_records.append(dict(case=case_id, mode=mode, phase=phase,
                                               initialization_seconds=replay_initialization, **replay))
                records.extend(replay_records)
                assert engine.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
                engine.close()
                raw = path.read_bytes()
                destination = args.output / f"archive-{case_id:02d}-{mode}.sqlite3.gz"
                destination.write_bytes(gzip.compress(raw, mtime=0))
                if materialized is not None:
                    materialized.pop("cnf")
                    witness.pop("model")
                archives.append(dict(case=case_id, mode=mode, path=destination.name,
                                     database_bytes=len(raw), compressed_bytes=destination.stat().st_size,
                                     database_sha256=hashlib.sha256(raw).hexdigest(), row_digest=row_digest,
                                     storage=storage, final_materialization=materialized,
                                     final_witness=witness, export_and_validation_seconds=validation_seconds))
        print(case_id, case["family"], case["size"], len(case["additions"]), "checked", flush=True)

    # Replay all preceding archives without changing their old residual rows.
    old_checks = []
    for name in ("cnf-residual-dag", "cnf-matching", "cnf-subsumption"):
        previous = Path(__file__).parent / "results" / name
        report = json.loads((previous / "report.json").read_text())
        for archived in report["archives"]:
            raw = gzip.decompress((previous / archived["path"]).read_bytes())
            assert hashlib.sha256(raw).hexdigest() == archived["database_sha256"]
            if archived.get("kind") == "stream":
                case = report["streams"][archived["case"]]["history"][-1]
            else:
                case = report["cases"][archived["case"]]
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / "old.sqlite3"
                path.write_bytes(raw)
                solver = ResidualSolver(path)
                result = solver.solve(case["cnf"])
                assert result["answer"] == case["expected"]
                assert result["metrics"].get("expanded_nodes", 0) == 0
                assert archive_digest(solver) == archived["row_digest"]
                solver.close()
            old_checks.append(f"{name}/{archived['path']}")
    report = dict(source_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
                  fingerprints={"experiments/" + p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                                (Path(__file__), Path(__file__).with_name("cnf_positive_history.py"),
                                 Path(__file__).with_name("cnf_residual_dag.py"))},
                  cases=cases, records=records, archives=archives,
                  old_archives_rechecked_without_changes=old_checks,
                  limitations=["Delta API requires a version from this immutable archive; it is not an arbitrary full-CNF identity test",
                               "Uncovered additions explicitly materialize and acquire a new base in this driver",
                               "Cold history verification is linear in required deltas plus base proof work and SQL lookup costs",
                               "Exact duplicate clauses on successive parents remain distinct events; global semantic deduplication is absent",
                               "Repeated-operation mode instead repeats the same parent and payload and reuses its version",
                               "SQL metadata scans and final exports are separately charged; full-source solve includes its existing per-query SQL size scan",
                               "Common benchmark input assembly, gzip snapshots, digests and compatibility audit are not online solving costs",
                               "Single samples, no competitive CDCL or process peak-RSS evaluation",
                               "Python code and SQLite implementation are not verified by Lean"])
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(dict(cases=len(cases), decisions=len(records), archives=len(archives), old_archives=len(old_checks))))


if __name__ == "__main__":
    main()
