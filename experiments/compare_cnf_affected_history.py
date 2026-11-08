#!/usr/bin/env python3
"""Compare pure-literal repair with checked affected-clause model repair."""
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
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.cnf_repair_history import RepairHistory
from experiments.cnf_affected_history import AffectedRepairHistory
from experiments.compare_cnf_repair_history import audit_previous as audit_earlier, scenarios as earlier_scenarios
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_matching import domain_cnf
from experiments.compare_cnf_positive_history import all_rows
from experiments.compare_cnf_residuals import archive_digest


def digest_rows(engine):
    return hashlib.sha256(json.dumps(all_rows(engine.db), sort_keys=True).encode()).hexdigest()


def scenarios():
    cases = earlier_scenarios()
    for steps in (8, 128, 512):
        additions = [c for i in range(steps) for c in ((-10000-i, 1), (10000+i,))]
        cases.append(dict(family='protected_flips', size=steps, base=[(1,)],
                          additions=additions, expected=[True]*(len(additions)+1)))
    for size in (4, 8, 16):
        for steps in (32, 128):
            additions = [c for i in range(steps) for c in ((-10000-i, 999), (10000+i,))]
            cases.append(dict(family='protected_matching', size=size,
                              base=domain_cnf([range(size)]*size)+[(999,)],
                              additions=additions, expected=[True]*(len(additions)+1)))
    for degree in (1, 16, 256, 4096):
        cases.append(dict(family='high_occurrence_degree', size=degree,
                          base=[(1,)]+[(-2, 1, 10000+i) for i in range(degree)],
                          additions=[(2,)], expected=[True, True]))
    cases.append(dict(family='bounded_repair_rejection', size=64, repair_budget=32,
                      base=[(1,)]+[(-2, 1, 10000+i) for i in range(64)],
                      additions=[(2,)], expected=[True, True]))
    cases.append(dict(family='joint_change_needed', size=2,
                      base=[(-1, 2), (1, -2)], additions=[(1,)], expected=[True, True]))
    return cases


def make_engine(path, mode, case):
    return (AffectedRepairHistory(path, repair_budget=case.get('repair_budget', 4096))
            if mode == 'affected_history' else RepairHistory(path))


def audit_previous():
    checked = audit_earlier()
    directory = Path(__file__).parent / 'results' / 'cnf-repair-history'
    report = json.loads((directory/'report.json').read_text())
    for archive in report['archives']:
        raw = gzip.decompress((directory/archive['path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == archive['database_sha256']
        case = report['cases'][archive['case']]
        source = tuple(map(tuple, case['base']+case['additions']))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'previous.sqlite3'
            path.write_bytes(raw)
            if archive['final_version'] is not None:
                engine = AffectedRepairHistory(path)
                result = engine.query(archive['final_version'])
                assert engine.materialize(archive['final_version'])['cnf'] == source
                if result['answer']:
                    assert holds(source, engine.witness(archive['final_version'])['model'])
                digest, metrics = digest_rows(engine), result['solver_metrics']
            else:
                engine = ResidualSolver(path)
                result = engine.solve(source)
                digest, metrics = archive_digest(engine), result['metrics']
            assert result['answer'] == case['expected'][-1]
            assert digest == archive['row_digest']
            assert metrics.get('expanded_nodes',0) == 0
            engine.close()
        checked.append('cnf-repair-history/'+archive['path'])
    return checked


def allocation_profile(case, mode):
    # Separate untimed rerun: tracemalloc perturbs performance and excludes
    # SQLite/native allocations. Input assembly is included equally here.
    import gc
    import tracemalloc
    gc.collect()
    with tempfile.TemporaryDirectory() as temporary:
        tracemalloc.start()
        path = Path(temporary)/'profile.sqlite3'
        engine = make_engine(path, mode, case)
        source = tuple(map(tuple, case['base']))
        version = None
        for step, clause in enumerate([None]+case['additions']):
            if clause is not None:
                source += (tuple(clause),)
            if clause is None:
                result = engine.prepare(source)
            else:
                try:
                    append = engine.append_repair
                    result = append(version, clause)
                except UnsupportedExpansion:
                    expanded = engine.materialize(version)['cnf']+(tuple(clause),)
                    result = engine.prepare(expanded)
            assert result['answer'] == case['expected'][step]
            version = result['version']
        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        engine.close()
    return dict(current_traced_bytes=current, peak_traced_bytes=peak,
                scope='Python allocations during a separate run; excludes native SQLite and process RSS')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cases, records, archives = scenarios(), [], []
    for case_id, case in enumerate(cases):
        for mode in ('repair_history', 'affected_history'):
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'history.sqlite3'
                started = time.perf_counter()
                engine = make_engine(path, mode, case)
                initialization = time.perf_counter() - started
                source, version = tuple(map(tuple, case['base'])), None
                for step, clause in enumerate([None] + case['additions']):
                    if clause is not None:
                        source += (tuple(clause),)
                    started = time.perf_counter()
                    fallback = None
                    if clause is None:
                        result = engine.prepare(source)
                    else:
                        try:
                            append = engine.append_repair
                            result = append(version, clause)
                        except UnsupportedExpansion as error:
                            rejected = dict(reason=str(error), metrics=dict(engine.counts),
                                            solver_metrics=dict(engine.solver.counts))
                            materialized = engine.materialize(version)
                            expanded = materialized.pop('cnf') + (tuple(clause),)
                            result = engine.prepare(expanded)
                            fallback = dict(rejected=rejected, materialization=materialized)
                    elapsed = time.perf_counter() - started
                    assert result['answer'] == case['expected'][step]
                    version = result.pop('version')
                    records.append(dict(case=case_id, mode=mode, phase='acquisition', step=step,
                                        operation_seconds=elapsed, fallback=fallback,
                                        initialization_seconds=initialization if step == 0 else 0, **result))
                started = time.perf_counter()
                materialization = engine.materialize(version)
                assert materialization.pop('cnf') == source
                witness = engine.witness(version)
                model = witness.pop('model')
                if result['answer']:
                    assert holds(source, model)
                storage, row_digest = engine.storage(), digest_rows(engine)
                export_seconds = time.perf_counter() - started
                for phase in ('warm', 'cold'):
                    replay_init = 0
                    if phase == 'cold':
                        engine.close()
                        started = time.perf_counter()
                        engine = make_engine(path, mode, case)
                        replay_init = time.perf_counter() - started
                    replay = engine.query(version)
                    assert replay['answer'] == case['expected'][-1]
                    replay.pop('version')
                    assert digest_rows(engine) == row_digest
                    metrics = replay['solver_metrics']
                    assert metrics.get('expanded_nodes', 0) == 0
                    records.append(dict(case=case_id, mode=mode, phase=phase,
                                        initialization_seconds=replay_init, **replay))
                assert engine.db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
                engine.close()
                raw = path.read_bytes()
                destination = args.output / f'archive-{case_id:02d}-{mode}.sqlite3.gz'
                destination.write_bytes(gzip.compress(raw, mtime=0))
                archives.append(dict(case=case_id, mode=mode, path=destination.name,
                                     final_version=version, database_bytes=len(raw),
                                     compressed_bytes=destination.stat().st_size,
                                     database_sha256=hashlib.sha256(raw).hexdigest(), row_digest=row_digest,
                                     storage=storage, final_materialization=materialization,
                                     final_witness=witness, export_and_validation_seconds=export_seconds))
        print(case_id, case['family'], case['size'], len(case['additions']), 'checked', flush=True)
    profiles = [dict(case=i, mode=mode, **allocation_profile(cases[i], mode))
                for i in (13, 15, 18, 28) for mode in ('repair_history', 'affected_history')]
    old_checks = audit_previous()
    files = [Path(__file__), Path(__file__).with_name('cnf_repair_history.py'), Path(__file__).with_name('cnf_affected_history.py'),
             Path(__file__).with_name('compare_cnf_repair_history.py'),
             Path(__file__).with_name('compare_cnf_decision_history.py'), Path(__file__).with_name('cnf_positive_history.py'),
             Path(__file__).with_name('cnf_residual_dag.py'),
             Path(__file__).with_name('compare_cnf_positive_history.py')]
    report = dict(source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  fingerprints={str(p.relative_to(Path(__file__).resolve().parents[1])):
                                hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  cases=cases, records=records, archives=archives, allocation_profiles=profiles,
                  old_archives_rechecked_without_changes=old_checks,
                  limitations=['Single sequential timings; separate tracemalloc runs exclude native SQLite and process peak RSS',
                               'Base acquisition, rejected attempts and materialized fresh-base fallback are timed',
                               'DB initialization and optional final full export/storage scans are separately timed',
                               'Both histories return verdicts and export a sparse model separately; model export traverses shared maps',
                               'Inputs assembled outside timed operations; offline gzip, audit and digests excluded',
                               'Cold query checks the base and all required ancestors; no constant restart bound',
                               'Affected repairs change one variable only if exact affected-clause counts stay positive; candidate visits are budgeted',
                               'Acquisition and successful-model frequency have no unrestricted polynomial bound',
                               'Exact event duplicates and copied fresh bases remain; Python/SQL are outside Lean'])
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=len(cases), decisions=len(records), archives=len(archives),
                          old_archives=len(old_checks))))


if __name__ == '__main__':
    main()
