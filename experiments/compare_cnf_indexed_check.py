#!/usr/bin/env python3
"""Matched checker-owned occurrence reconstruction on prepared and fresh inputs."""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_accounted_residuals import AccountedResidualSolver, CENSUS, TABLE
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_retained_plans import RetainedPlanInventory
from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_indexed_check import IndexedCheckInventory
from experiments.compare_cnf_binary_paths import fresh_cases, root_lift
from experiments.compare_cnf_retained_plans import audit, check_old_rows, sha

MODES = dict(scan=PreparedProbeInventory, indexed=IndexedCheckInventory)
TABLES = ('cnf_patterns_v1', 'cnf_pattern_sources_v1', 'cnf_residual_v1')


def table_digest(db, table):
    digest = hashlib.sha256(); rows = 0
    for key, payload in db.execute(f'SELECT id,payload FROM {table} ORDER BY id'):
        for value in (key, payload):
            raw = value.encode(); digest.update(len(raw).to_bytes(8, 'big')); digest.update(raw)
        rows += 1
    return dict(rows=rows, sha256=digest.hexdigest())


def query(history, solver, source):
    started = time.perf_counter()
    found = history.inspect(source); solved = solver.solve(source)
    root = history._load(found['root']['key'])
    if solved['answer']:
        assert holds(source, solved['model'])
        if root['kind'] == 'retained_plan':
            model = {i: solved['model'][v] for i, v in enumerate(found['root']['names'], 1)}
            assert holds(root['cnf'], history.lift(found['root']['key'], model))
        else:
            root_lift(history, found, solved['model'])
    elapsed = time.perf_counter() - started
    return dict(total_seconds=elapsed, discovery_seconds=found['seconds'],
                solver_seconds=solved['seconds'], answer=solved['answer'],
                root_sha256=hashlib.sha256(found['root']['key'].encode()).hexdigest(),
                profile=found['profile'], summary=found['summary'],
                solver_root_sha256=hashlib.sha256(solved['root'].encode()).hexdigest(),
                archive_nodes=solved['archive_nodes'], archive_payload_units=solved['archive_payload_bytes'],
                discovery_metrics=found['metrics'], prepared_metrics=found['prepared_metrics'],
                solver_metrics=solved['metrics'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--suite', choices=('full', 'fresh', 'empty'), default='full')
    parser.add_argument('--reverse', action='store_true')
    args = parser.parse_args(); out = args.output; out.mkdir(parents=True, exist_ok=False)
    prior_path = Path('experiments/results/cnf-prepared-probes-full/report.json')
    prior = json.loads(prior_path.read_text()); options = prior['options']
    cases = prior['cases'] if args.suite == 'full' else fresh_cases()
    modes = dict(reversed(list(MODES.items()))) if args.reverse else MODES
    report = dict(source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  suite=args.suite, input_report_sha256=sha(prior_path), options=options,
                  seed=prior['seed'] if args.suite != 'empty' else None,
                  execution_order=list(modes), cases=cases, results=[])
    files = sorted(set(prior['fingerprints']) | {
        'experiments/compare_cnf_indexed_check.py', 'experiments/cnf_indexed_check.py',
        'solver/test_cnf_indexed_check.py', 'experiments/cnf_single_pass_inventory.py',
        'experiments/compare_cnf_prepared_probes.py', 'experiments/cnf_prepared_probes.py',
        'solver/test_cnf_prepared_probes.py', 'experiments/cnf_retained_plans.py', 'experiments/cnf_accounted_residuals.py',
        'solver/test_cnf_accounted_residuals.py', 'experiments/cnf_residual_dag.py'})
    report['fingerprints'] = {p: sha(p) for p in files}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); seed = tmp / 'seed.db'; started = time.perf_counter()
        if args.suite == 'empty':
            h = RetainedPlanInventory(seed, **options); h.close()
            s = ResidualSolver(seed); s.close()
        else:
            with gzip.open(prior['seed']['path'], 'rb') as src, seed.open('wb') as dst:
                shutil.copyfileobj(src, dst)
            assert sha(seed) == prior['seed']['database_sha256']
        report['seed_restore_seconds'] = time.perf_counter() - started
        report['seed_bytes'] = seed.stat().st_size
        for mode, cls in modes.items():
            path = tmp / f'{mode}.db'; started = time.perf_counter(); shutil.copyfile(seed, path)
            clone_seconds = time.perf_counter() - started
            gc.collect(); started = time.perf_counter()
            h = cls(path, **options); s = AccountedResidualSolver(path)
            init = time.perf_counter() - started; records = []
            for i, case in enumerate(cases):
                if i % 200 == 0: print(mode, 'query', i, flush=True)
                records.append(dict(case=i, **query(h, s, case['source'])))
            assert s.archive_storage() == s.db.execute(CENSUS).fetchone()
            censuses = getattr(s, 'accounting_censuses', None)
            # Warm replay includes the solver and its metadata, unlike earlier
            # discovery-only warm diagnostics. Preserve each phase separately.
            started = time.perf_counter()
            for i, case in enumerate(cases):
                r = query(h, s, case['source'])
                assert r['answer'] == records[i]['answer']
                assert not r['solver_metrics'].get('expanded_nodes', 0)
                assert not r['discovery_metrics'].get('inserted_nodes', 0)
                assert not r['discovery_metrics'].get('inserted_sources', 0)
            warm = time.perf_counter() - started
            digests = {table: table_digest(s.db, table) for table in TABLES}
            accounting = None
            if isinstance(s, AccountedResidualSolver):
                accounting = dict(initialization_seconds=s.accounting_initialization_seconds,
                                  censuses_after_acquisition=censuses,
                                  censuses_after_warm=s.accounting_censuses,
                                  singleton=s.db.execute(f'SELECT * FROM {TABLE}').fetchall())
            reconstruction_cache = h.reconstruction_state() if isinstance(h, IndexedCheckInventory) else None
            h.close(); s.close()
            started = time.perf_counter(); preserved = check_old_rows(seed, path)
            preservation_seconds = time.perf_counter() - started
            archive = out / f'archive-{mode}.sqlite3.gz'; started = time.perf_counter()
            with path.open('rb') as src, archive.open('wb') as raw:
                with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as dst:
                    shutil.copyfileobj(src, dst)
            result = dict(mode=mode, records=records, clone_seconds=clone_seconds,
                          initialization_seconds=init, warm_combined_seconds=warm,
                          database_bytes=path.stat().st_size, database_sha256=sha(path),
                          archive_path=str(archive), archive_sha256=sha(archive),
                          compression_seconds=time.perf_counter() - started,
                          old_rows_preserved=preserved, preservation_seconds=preservation_seconds,
                          table_digests=digests, accounting=accounting, reconstruction_cache=reconstruction_cache)
            (out / f'checkpoint-{mode}.json').write_text(json.dumps(result, separators=(',', ':')) + '\n')
            print(mode, 'acquired; cold audit', flush=True)
            result['audit'] = audit(path, cls, options)
            before = sha(path); started = time.perf_counter(); s = AccountedResidualSolver(path)
            result['cold_accounting_open_seconds'] = time.perf_counter() - started
            assert s.archive_storage() == s.db.execute(CENSUS).fetchone(); s.close()
            assert sha(path) == before
            # Isolated small-prefix allocation diagnostic, after all timings.
            memory_path = tmp / f'memory-{mode}.db'; shutil.copyfile(seed, memory_path)
            indices = [858, 875, 907, 970, 1042, 1061] if args.suite == 'full' else [0, 1, 2, 3]
            gc.collect(); tracemalloc.start(); h = cls(memory_path, **options); s = AccountedResidualSolver(memory_path)
            for i in indices: query(h, s, cases[i]['source'])
            current, peak = tracemalloc.get_traced_memory(); tracemalloc.stop(); h.close(); s.close()
            result['allocation'] = dict(indices=indices, current_python_bytes=current, peak_python_bytes=peak)
            report['results'].append(result)
            (out / f'checkpoint-{mode}.json').write_text(json.dumps(result, separators=(',', ':')) + '\n')
            print(mode, 'verified', flush=True)
    paired = {r['mode']: r for r in report['results']}
    assert paired['scan']['table_digests'] == paired['indexed']['table_digests']
    for a, b in zip(paired['scan']['records'], paired['indexed']['records'], strict=True):
        for field in ('case', 'answer', 'root_sha256', 'solver_root_sha256', 'profile', 'summary',
                      'archive_nodes', 'archive_payload_units'):
            assert encode(a[field]) == encode(b[field]), (a['case'], field)
        assert a['solver_metrics'] == b['solver_metrics']
    summary = []
    for result in report['results']:
        records = result['records']
        summary.append(dict(mode=result['mode'], cases=len(records),
            closed=sum(r['summary']['closed'] for r in records),
            non_tiny_closed=sum(r['summary']['closed'] for r in records[512:]) if args.suite == 'full' else None,
            total_seconds=sum(r['total_seconds'] for r in records),
            discovery_seconds=sum(r['discovery_seconds'] for r in records),
            solver_seconds=sum(r['solver_seconds'] for r in records),
            discovery_metrics=dict(sum((Counter(r['discovery_metrics']) for r in records), Counter())),
            prepared_metrics=dict(sum((Counter(r['prepared_metrics']) for r in records), Counter())),
            **{k: v for k, v in result.items() if k not in ('records', 'mode')}))
    report['limitations'] = [
        'Prepared history is charged as prior acquisition and storage; restoring/cloning/opening are separately timed.',
        'Acquisition includes discovery, verification, solving, metadata, commits and source/model lifts.',
        'Cold audit, preservation checks, compression and small-prefix allocation are separate from acquisition.',
        'Warm combined replay includes both discovery and solver; it is not comparable to old discovery-only warm timings.',
        'Both modes charge a full census at every accounted open and after conflicting writes; these are not constant-time.',
        'SQL length units match the historical census; ASCII generated keys/payloads make those units equal bytes.',
        'Direct writes to the private accounting schema during a live connection are outside the contract.',
        'Python tracing excludes native SQLite, process RSS and full-history peak.',
        'Single ordered comparisons on synthetic workloads; fresh inputs are the prior published controls, not an independent holdout.',
        'Only independent reconstruction changes; every proof reason and fixed-point obligation remains checked.',
        'The new index holds source representation facts only; it is separate from discovery state and bounded in logical slots, not RSS.',
        'Matching stored evidence establishes the measured policy equivalence, not broader SAT coverage or a uniform polynomial bound.']
    (out / 'report.json').write_text(json.dumps(report, separators=(',', ':')) + '\n')
    (out / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    for mode in modes: (out / f'checkpoint-{mode}.json').unlink()
    print(json.dumps([{k: s[k] for k in ('mode', 'cases', 'closed', 'total_seconds', 'solver_seconds', 'database_bytes')} for s in summary]), flush=True)


if __name__ == '__main__':
    main()
