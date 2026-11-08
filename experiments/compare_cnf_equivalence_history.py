#!/usr/bin/env python3
"""Matched single-variable versus simultaneous equivalence repair, all costs charged."""
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
from experiments.cnf_affected_history import AffectedRepairHistory
from experiments.cnf_equivalence_history import EquivalenceRepairHistory
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.cnf_residual_dag import holds
from experiments.compare_cnf_affected_history import digest_rows, scenarios as affected_scenarios
from experiments.probe_structured_repair_gaps import source_for

RESULTS = Path(__file__).parent / 'results'
MODES = dict(affected=AffectedRepairHistory, equivalence=EquivalenceRepairHistory)


def scenarios():
    old = json.loads((RESULTS/'structured-repair-gaps/report.json').read_text())
    cases = [dict(family=c['family'], width=c['width'], blocks=c['blocks'], base=c['base'],
                  additions=c['additions'], expected=[True]*(len(c['additions'])+1)) for c in old['cases']]
    signed = lambda lit: -lit if abs(lit) % 2 else lit
    cases.append(dict(family='signed_equivalence', width=8, blocks=32,
                      base=[[signed(lit) for lit in clause] for clause in cases[3]['base']],
                      # The acquired signed model has odd variables false;
                      # complementing the old additions made them compatible.
                      additions=[(1+8*i,) for i in range(32)],
                      expected=[True]*33))
    controls = [
        ('coupled_repeated', [(-1, 2), (1, -2), (-3, 4), (3, -4)], [(1, 3), (-1, 3), (-1,)], [True]*4),
        ('contradiction', [(-1, 2), (1, -2)], [(1,), (-1,)], [True, True, False]),
        ('new_equivalence', [], [(-1, 2), (1, -2), (1,)], [True]*4),
        ('nonpaired_cycle', [(-1, 2), (-2, 3), (-3, 1)], [(1,)], [True]*2),
        ('compatible', source_for('equivalence', 32, 8), [(-1-i*32,) for i in range(8)], [True]*9),
    ]
    for family, base, additions, expected in controls:
        cases.append(dict(family=family, base=base, additions=additions, expected=expected))
    for width in (256, 1024):
        cases.append(dict(family='large_block', width=width, blocks=1,
                          base=source_for('equivalence', width, 1), additions=[(1,)], expected=[True, True]))
    cases.append(dict(family='small_budget', repair_budget=8,
                      base=source_for('equivalence', 32, 1), additions=[(1,)], expected=[True, True]))
    huge = 1 << 1024
    cases.append(dict(family='sparse_ids', base=[(-huge, huge+1), (huge, -huge-1)],
                      additions=[(huge,)], expected=[True, True]))
    cases.append(next(c for c in affected_scenarios()
                      if c['family'] == 'protected_matching' and c['size'] == 16 and len(c['additions']) == 256))
    return cases


def engine(path, mode, case):
    return MODES[mode](path, repair_budget=case.get('repair_budget', 4096))


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
    h = EquivalenceRepairHistory(path, repair_budget=0)
    versions = [v for v, in h.db.execute('SELECT id FROM cnf_positive_versions_v1')]
    for version in versions:
        result = h.query(version)
        assert result['solver_metrics'].get('expanded_nodes', 0) == 0
        source = h.materialize(version)['cnf']
        model = h.witness(version)['model']
        assert model is None or holds(source, model)
    residuals = list(h.db.execute('SELECT id FROM cnf_residual_v1'))
    for key, in residuals:
        assert h.solver._read(key, purpose='equivalence_audit') is not None
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
                for i in (5, 11, 17, 22) for mode in MODES]
    old_checks = []
    for directory in ('structured-repair-gaps', 'cnf-affected-history'):
        report = json.loads((RESULTS/directory/'report.json').read_text())
        entries = report['cases'] if directory == 'structured-repair-gaps' else report['archives']
        for entry in entries:
            name = entry.get('archive', entry.get('path'))
            raw = gzip.decompress((RESULTS/directory/name).read_bytes())
            with tempfile.TemporaryDirectory() as tmp:
                audit = audit_archive(Path(tmp)/'old.sqlite3', raw, entry['database_sha256'])
            old_checks.append(dict(archive=directory+'/'+name, **audit))
    files = [Path(__file__), Path('experiments/cnf_equivalence_history.py'), Path('experiments/cnf_affected_history.py'),
             Path('experiments/cnf_repair_history.py'), Path('experiments/cnf_positive_history.py'),
             Path('experiments/cnf_residual_dag.py'), Path('experiments/probe_structured_repair_gaps.py'),
             Path('experiments/compare_cnf_affected_history.py')]
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
                      'Recognition scans a base once on its first failed single-variable repair; newly added equivalences and arbitrary implication SCCs are not discovered',
                      'Joint proposal budget charges variables plus postings; base recognition, arithmetic and trie paths are additional charged work',
                      'No compact assignment groups: every moved variable is still updated; internal affected clauses are still visited',
                      'Python, SQLite, binary-pair discovery and count indexes are outside Lean; only the semantic protection rule is formalized',
                      'Unsupported proposals give no verdict; unrestricted fallback remains potentially exponential'])
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases), archives=len(archives), prior_archives=len(old_checks))), flush=True)


if __name__ == '__main__':
    main()
