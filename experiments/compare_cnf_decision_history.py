#!/usr/bin/env python3
"""Compare subset histories with UNSAT monotonicity and fixed-model reuse."""
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
from experiments.compare_cnf_positive_history import all_rows
from experiments.compare_cnf_residuals import archive_digest, pigeonhole


def digest_rows(engine):
    return hashlib.sha256(json.dumps(all_rows(engine.db), sort_keys=True).encode()).hexdigest()


def scenarios():
    cases = []
    for family in ("unsat_arbitrary_additions", "sat_model_compatible"):
        for size in (4, 8, 16):
            for steps in (8, 32, 128):
                sat = family.startswith("sat_")
                base = domain_cnf([range(size)] * size) if sat else pigeonhole(size)
                additions = []
                for i in range(steps):
                    fresh = 10000 + 2 * i
                    # Fresh variables default false. These signed clauses need
                    # not contain any positive base clause or be implied by it.
                    if sat:
                        clause = (-fresh, fresh + 1) if i % 2 else (-fresh,)
                    else:
                        clause = ((fresh,), (-fresh,), (fresh, -fresh), ())[i % 4]
                    additions.append(clause)
                cases.append(dict(family=family, size=size, base=base, additions=additions,
                                  expected=[sat] * (steps + 1)))
    base = domain_cnf([range(4)] * 4)
    cases.append(dict(family="sat_repeated_clause", size=4, base=base,
                      additions=[(-10000,)] * 128, expected=[True] * 129))
    cases.append(dict(family="sat_novel_positive_units", size=4, base=base,
                      additions=[(10000 + i,) for i in range(32)], expected=[True] * 33))
    # The first incompatible clause really makes the source UNSAT; following
    # arbitrary additions must then transfer that checked result, not guess it.
    cases.append(dict(family="sat_to_unsat", size=1, base=[(1,)],
                      additions=[(-1,)] + [(10000 + i,) for i in range(31)],
                      expected=[True] + [False] * 32))
    # A failed stored model also occurs when the expanded formula remains SAT.
    # Symmetric two-choice base: first select the complement of its fixed model.
    solver = ResidualSolver()
    model = solver.solve([(1, 2)])['model']
    solver.close()
    chosen = next(v for v in (1, 2) if model[v])
    cases.append(dict(family="sat_model_change", size=2, base=[(1, 2)],
                      additions=[(-chosen,)] + [(-10000 - i,) for i in range(31)],
                      expected=[True] * 33))
    return cases


def source_for(case):
    return tuple(map(tuple, case['base'] + case['additions']))


def audit_previous():
    checks = []
    for name in ('cnf-residual-dag', 'cnf-matching', 'cnf-subsumption', 'cnf-positive-history'):
        directory = Path(__file__).parent / 'results' / name
        report = json.loads((directory / 'report.json').read_text())
        handles = ({a['archive']: a['final_version'] for a in json.loads(
            (directory / 'history-replay.json').read_text())['archives']}
                   if name == 'cnf-positive-history' else {})
        for archive in report['archives']:
            raw = gzip.decompress((directory / archive['path']).read_bytes())
            assert hashlib.sha256(raw).hexdigest() == archive['database_sha256']
            if archive.get('kind') == 'stream':
                case = report['streams'][archive['case']]['history'][-1]
            else:
                case = report['cases'][archive['case']]
            if name == 'cnf-positive-history':
                additions = case['additions'][-1:] if case.get('same_parent') else case['additions']
                source = tuple(map(tuple, case['base'] + additions))
            else:
                source = case['cnf']
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'previous.sqlite3'
                path.write_bytes(raw)
                if archive['path'] in handles:
                    engine = PositiveHistory(path)
                    version = handles[archive['path']]
                    result = engine.query(version)
                    assert engine.materialize(version)['cnf'] == source
                    if result['answer']:
                        assert holds(source, engine.witness(version)['model'])
                    assert digest_rows(engine) == archive['row_digest']
                    metrics = result['solver_metrics']
                else:
                    engine = ResidualSolver(path)
                    result = engine.solve(source)
                    assert archive_digest(engine) == archive['row_digest']
                    metrics = result['metrics']
                assert result['answer'] == case['expected']
                assert metrics.get('expanded_nodes', 0) == 0
                engine.close()
            checks.append(f"{name}/{archive['path']}")
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    cases, records, archives = scenarios(), [], []
    for case_id, case in enumerate(cases):
        for mode in ('full_source', 'positive_history', 'decision_history'):
            is_history = mode != 'full_source'
            with tempfile.TemporaryDirectory() as temporary:
                path = Path(temporary) / 'history.sqlite3'
                started = time.perf_counter()
                engine = PositiveHistory(path) if is_history else ResidualSolver(path)
                initialization = time.perf_counter() - started
                source, version = tuple(map(tuple, case['base'])), None
                for step, clause in enumerate([None] + case['additions']):
                    if clause is not None:
                        source += (tuple(clause),)
                    started = time.perf_counter()
                    fallback = None
                    if not is_history:
                        result = engine.solve(source)
                        result.pop('root')
                        result.pop('model')
                    elif clause is None:
                        result = engine.prepare(source)
                    else:
                        try:
                            if mode == 'positive_history' and (not clause or any(lit < 0 for lit in clause)):
                                # This is an input-interface rejection, not a
                                # claim that a signed/empty clause is invalid CNF.
                                engine._begin()
                                raise UnsupportedExpansion('Outside positive-append interface')
                            append = engine.append_decision if mode == 'decision_history' else engine.append
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
                    if is_history:
                        version = result.pop('version')
                    records.append(dict(case=case_id, mode=mode, phase='acquisition', step=step,
                                        operation_seconds=elapsed, fallback=fallback,
                                        initialization_seconds=initialization if step == 0 else 0, **result))
                started = time.perf_counter()
                if is_history:
                    materialization = engine.materialize(version)
                    assert materialization.pop('cnf') == source
                    witness = engine.witness(version)
                    model = witness.pop('model')
                    if result['answer']:
                        assert holds(source, model)
                    storage, row_digest = engine.storage(), digest_rows(engine)
                else:
                    materialization = witness = None
                    storage = dict(logical_bytes=result['archive_payload_bytes'],
                                   residual_nodes=result['archive_nodes'])
                    row_digest = archive_digest(engine)
                export_seconds = time.perf_counter() - started
                for phase in ('warm', 'cold'):
                    replay_init = 0
                    if phase == 'cold':
                        engine.close()
                        started = time.perf_counter()
                        engine = PositiveHistory(path) if is_history else ResidualSolver(path)
                        replay_init = time.perf_counter() - started
                    replay = engine.query(version) if is_history else engine.solve(source)
                    assert replay['answer'] == case['expected'][-1]
                    if is_history:
                        replay.pop('version')
                        assert digest_rows(engine) == row_digest
                        metrics = replay['solver_metrics']
                    else:
                        replay.pop('root')
                        replay.pop('model')
                        assert archive_digest(engine) == row_digest
                        metrics = replay['metrics']
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
    old_checks = audit_previous()
    files = [Path(__file__), Path(__file__).with_name('cnf_positive_history.py'),
             Path(__file__).with_name('cnf_residual_dag.py'),
             Path(__file__).with_name('compare_cnf_positive_history.py')]
    report = dict(source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  fingerprints={str(p.relative_to(Path(__file__).resolve().parents[1])):
                                hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  cases=cases, records=records, archives=archives,
                  old_archives_rechecked_without_changes=old_checks,
                  limitations=['Single sequential samples on synthetic streams; no peak-RSS or competitive-CDCL claim',
                               'Base acquisition, rejected attempts and materialized fresh-base fallback are timed',
                               'DB initialization and optional final full export/storage scans are separately timed',
                               'Full-source solve includes its existing archive-size scan and model output each time',
                               'Both history modes have the same verdict and optional model-export interface',
                               'Inputs assembled outside timed operations; offline gzip, audit and digests excluded',
                               'Cold query checks the base and all required ancestors; no constant restart bound',
                               'SAT rule retains one total assignment, not all models; missing variables are false',
                               'Acquisition and successful-model frequency have no unrestricted polynomial bound',
                               'Exact event duplicates and copied fresh bases remain; Python/SQL are outside Lean'])
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(cases=len(cases), decisions=len(records), archives=len(archives),
                          old_archives=len(old_checks))))


if __name__ == '__main__':
    main()
