#!/usr/bin/env python3
"""Compare fixed, globally raised and targeted equivalence-retry budgets."""
import argparse
import gc
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_budgeted_history import BudgetedRepairHistory
from experiments.cnf_matching_history import MatchingRepairHistory
from experiments.cnf_equivalence_history import EquivalenceRepairHistory
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.cnf_residual_dag import holds
from experiments.compare_cnf_affected_history import digest_rows, scenarios as affected_scenarios
from experiments.probe_structured_repair_gaps import source_for, supplied_move
from experiments.compare_cnf_matching import domain_cnf

RESULTS = Path(__file__).parent / 'results'
MODES = dict(fixed=MatchingRepairHistory, raised=MatchingRepairHistory, targeted=BudgetedRepairHistory)


def scenarios():
    cases = []
    for width in (256, 512, 1024, 2048, 4096):
        cases.append(dict(family='large_block', width=width, base=source_for('equivalence', width, 1),
                          additions=[(1,)], expected=[True, True]))
    cases.append(dict(family='two_large_blocks', width=1024,
                      base=source_for('equivalence', 1024, 2), additions=[(1,), (1025,)], expected=[True]*3))
    for width, copies in ((2, 8192), (1024, 8192)):
        cases.append(dict(family='high_degree', width=width, copies=copies,
                          base=source_for('equivalence', width, 1) + ((1, -1),)*copies,
                          additions=[(1,)], expected=[True, True]))
    for width in (1024, 2048):
        cases.append(dict(family='late_conflict', width=width,
                          base=source_for('equivalence', width, 1) + ((-1,),),
                          additions=[(1,)], expected=[True, False]))
    cases.append(dict(family='history_conflict', width=1024,
                      base=source_for('equivalence', 1024, 1), additions=[(1,), (-1,)],
                      expected=[True, True, False]))
    cases.append(dict(family='size_cap', width=1024, max_block_variables=512,
                      base=source_for('equivalence', 1024, 1), additions=[(1,)], expected=[True, True]))
    huge = 1 << 1024
    cases.append(dict(family='identifier_cap', repair_budget=1,
                      base=[(-huge, huge+1), (huge, -huge-1)], additions=[(huge,)], expected=[True, True]))
    old = json.loads((RESULTS/'cnf-matching-history/report.json').read_text())
    cases.extend(old['cases'][i] for i in (3, 7, 12, 13, 14, 15, 16, 17, 20, 21, 24, 31, 32, 35))
    return cases


def engine(path, mode, case):
    options = dict(repair_budget=32768 if mode == 'raised' else case.get('repair_budget', 4096))
    if mode == 'targeted':
        options.update({key: case[key] for key in
                        ('escalation_budget', 'max_block_variables', 'max_variable_bits') if key in case})
    return MODES[mode](path, **options)


def step(h, version, clause, base):
    fallback = None
    if version is None:
        result = h.prepare(base)
    else:
        try:
            result = h.append_repair(version, clause)
        except UnsupportedExpansion as error:
            fallback = dict(reason=str(error), rejected_metrics=dict(h.counts),
                            rejected_solver_metrics=dict(h.solver.counts))
            materialization = h.materialize(version)
            expanded = materialization.pop('cnf') + (tuple(clause),)
            fallback['materialization'] = materialization
            result = h.prepare(expanded)
    return result, fallback


def memory_profile(case, mode):
    gc.collect()
    with tempfile.TemporaryDirectory() as tmp:
        tracemalloc.start()
        h = engine(Path(tmp)/'memory.sqlite3', mode, case)
        version = None
        for i, clause in enumerate([None]+case['additions']):
            result, _ = step(h, version, clause, case['base'])
            assert result['answer'] == case['expected'][i]
            version = result['version']
        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        h.close()
    return dict(current_traced_bytes=current, peak_traced_bytes=peak)


def audit_archive(path, raw, expected_hash):
    assert hashlib.sha256(raw).hexdigest() == expected_hash
    path.write_bytes(raw)
    h = MatchingRepairHistory(path, repair_budget=0)
    versions = [v for v, in h.db.execute('SELECT id FROM cnf_positive_versions_v1')]
    for version in versions:
        result = h.query(version)
        assert result['solver_metrics'].get('expanded_nodes', 0) == 0
        source = h.materialize(version)['cnf']
        model = h.witness(version)['model']
        assert model is None or holds(source, model)
    residuals = list(h.db.execute('SELECT id FROM cnf_residual_v1'))
    for key, in residuals:
        assert h.solver._read(key, purpose='matching_audit') is not None
    assert h.solver.counts.get('expanded_nodes', 0) == 0
    assert h.db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    h.close()
    assert path.read_bytes() == raw
    return dict(versions=len(versions), residuals=len(residuals), bytes_unchanged=True, new_expansions=0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=False)
    cases, records, archives = scenarios(), [], []
    for case_id, case in enumerate(cases):
        for mode in MODES:
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'history.sqlite3'
                start = time.perf_counter()
                h = engine(path, mode, case)
                initialization = time.perf_counter()-start
                source, versions, version = tuple(map(tuple, case['base'])), [], None
                for i, clause in enumerate([None]+case['additions']):
                    if clause is not None:
                        source += (tuple(clause),)
                        if case['family'] == 'signed_equivalence':
                            assert not holds([clause], h.witness(version)['model'])
                    start = time.perf_counter()
                    result, fallback = step(h, version, clause, case['base'])
                    elapsed = time.perf_counter()-start
                    assert result['answer'] == case['expected'][i]
                    version = result.pop('version')
                    versions.append(version)
                    records.append(dict(case=case_id, mode=mode, phase='acquisition', step=i,
                                        operation_seconds=elapsed, fallback=fallback,
                                        initialization_seconds=initialization if i == 0 else 0, **result))
                    assert h.materialize(version)['cnf'] == source
                    assert not result['answer'] or holds(source, h.witness(version)['model'])
                start = time.perf_counter()
                storage, digest = h.storage(), digest_rows(h)
                export = h.witness(version)
                export.pop('model')
                inspection = time.perf_counter()-start
                for phase in ('warm', 'cold'):
                    restart = 0
                    if phase == 'cold':
                        h.close()
                        start = time.perf_counter()
                        h = engine(path, mode, case)
                        restart = time.perf_counter()-start
                    result = h.query(version)
                    assert result['answer'] == case['expected'][-1]
                    assert result['solver_metrics'].get('expanded_nodes', 0) == 0
                    assert digest_rows(h) == digest
                    result.pop('version')
                    records.append(dict(case=case_id, mode=mode, phase=phase,
                                        initialization_seconds=restart, **result))
                h.close()
                # Resume a known last update from its parent in a fresh process
                # state. This charges cold recognition, not just final query.
                start = time.perf_counter()
                h = engine(path, mode, case)
                restart = time.perf_counter()-start
                start = time.perf_counter()
                result, fallback = step(h, versions[-2], case['additions'][-1], case['base'])
                elapsed = time.perf_counter()-start
                assert result.pop('version') == version
                assert result['solver_metrics'].get('expanded_nodes', 0) == 0
                assert digest_rows(h) == digest
                records.append(dict(case=case_id, mode=mode, phase='cold_resume', operation_seconds=elapsed,
                                    initialization_seconds=restart, fallback=fallback, **result))
                h.close()
                raw = path.read_bytes()
                sha = hashlib.sha256(raw).hexdigest()
                name = f'archive-{case_id:02d}-{mode}.sqlite3.gz'
                (out/name).write_bytes(gzip.compress(raw, mtime=0))
                audit = audit_archive(Path(tmp)/'audit.sqlite3', raw, sha)
                archives.append(dict(case=case_id, mode=mode, path=name, final_version=version, versions=versions,
                                     database_bytes=len(raw), compressed_bytes=(out/name).stat().st_size,
                                     database_sha256=sha, row_digest=digest, storage=storage,
                                     final_witness=export, storage_digest_export_seconds=inspection, audit=audit))
        print(case_id, case['family'], 'checked', flush=True)
    profiles = [dict(case=i, mode=mode, **memory_profile(cases[i], mode))
                for i in (2, 8, 23) for mode in MODES]
    old_checks = []
    for directory in ('cnf-matching-history',):
        report = json.loads((RESULTS/directory/'report.json').read_text())
        entries = report['cases'] if directory == 'structured-repair-gaps' else report['archives']
        for entry in entries:
            name = entry.get('archive', entry.get('path'))
            raw = gzip.decompress((RESULTS/directory/name).read_bytes())
            with tempfile.TemporaryDirectory() as tmp:
                audit = audit_archive(Path(tmp)/'old.sqlite3', raw, entry['database_sha256'])
            old_checks.append(dict(archive=directory+'/'+name, **audit))
    files = [Path(__file__), Path('experiments/cnf_budgeted_history.py'), Path('experiments/cnf_matching_history.py'), Path('experiments/cnf_equivalence_history.py'), Path('experiments/cnf_affected_history.py'),
             Path('experiments/cnf_repair_history.py'), Path('experiments/cnf_positive_history.py'),
             Path('experiments/cnf_residual_dag.py'), Path('experiments/probe_structured_repair_gaps.py'),
             Path('experiments/compare_cnf_affected_history.py'), Path('experiments/compare_cnf_matching.py')]
    report = dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
                  fingerprints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  cases=cases, records=records, archives=archives, allocation_profiles=profiles,
                  prior_archive_checks=old_checks, limitations=[
                      'Single sequential timings; no representative SAT workload distribution or significance claim',
                      'Timed acquisition includes lazy recognition, candidate checking, state maintenance, serialization, persistence and rejected fallback',
                      'DB initialization, witness export/storage scans, warm/cold queries and cold resumption are separately reported',
                      'Cold resumption repeats the last recorded update from its parent; the archive already contains its result',
                      'Input assembly, validation between operations, offline compression and archive audits excluded from acquisition timing',
                      'Tracemalloc is a separate rerun; excludes native SQLite allocations and process RSS',
                      'Fixed mode uses the previous matching engine and case budget (default 4096); raised mode always uses 32768',
                      'Targeted mode retries only the first exhausted recognized base-equivalence block, after ordinary search fails',
                      'Retry gets min(32768, 8*q) variable/posting visits, at most 8192 variables and 64-bit IDs by default',
                      'No attempt to predict optimal fallback cost: high-degree and conflict controls can lose',
                      'Recognition, checking, trie paths, arithmetic and SQL are additional to the visit budget; prior failed work stays charged',
                      'Joint record format and independent checker are unchanged; every older addition is checked',
                      'Python budget policy and indexes are outside Lean; existing joint semantic lemmas still apply',
                      'Unsupported proposals give no verdict; unrestricted fallback remains potentially exponential'])
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases), archives=len(archives), prior_archives=len(old_checks))), flush=True)


if __name__ == '__main__':
    main()
