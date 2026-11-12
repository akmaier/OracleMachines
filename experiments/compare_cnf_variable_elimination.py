#!/usr/bin/env python3
"""Matched terminal elimination, with pure-only control and charged persistence."""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_variable_elimination import VariableEliminationInventory
from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_accounted_residuals import AccountedResidualSolver, CENSUS
from experiments.compare_cnf_binary_paths import root_lift, fresh_cases
from experiments.compare_cnf_retained_plans import sha, selected, audit, check_old_rows

MODES = dict(baseline=(PreparedProbeInventory, {}),
             pure=(VariableEliminationInventory, dict(elimination_pair_limit=0)),
             bounded=(VariableEliminationInventory, dict(elimination_pair_limit=64)))


def query(h, solver, source):
    started = time.perf_counter(); found = h.inspect(source); solved = solver.solve(source)
    node = h._load(found['root']['key'])
    if solved['answer']:
        assert holds(source, solved['model'])
        names = found['root']['names']
        if node['kind'] == 'retained_plan':
            local = {i: solved['model'][v] for i, v in enumerate(names, 1)}
            assert holds(node['cnf'], h.lift(found['root']['key'], local))
        elif node['kind'] == 'eliminate':
            child = {i: solved['model'][names[v-1]] for i, v in enumerate(node['edge']['names'], 1)}
            assert holds(node['cnf'], h.lift(found['root']['key'], child))
        else:
            root_lift(h, found, solved['model'])
    elapsed = time.perf_counter() - started
    return found, dict(total_seconds=elapsed, discovery_seconds=found['seconds'],
        solver_seconds=solved['seconds'], answer=solved['answer'], profile=found['profile'],
        summary=found['summary'], root_sha256=hashlib.sha256(found['root']['key'].encode()).hexdigest(),
        root_kind=node['kind'], discovery_metrics=found['metrics'], prepared_metrics=found['prepared_metrics'],
        solver_metrics=solved['metrics'])


def edge_models(path, cls, options):
    started = time.perf_counter(); h = cls(path, **options); solver = ResidualSolver(); counts = Counter()
    for key, payload in h.db.execute('SELECT id,payload FROM cnf_patterns_v1'):
        if json.loads(payload)['kind'] != 'eliminate':
            continue
        node = h._load(key); child = h._load(node['edge']['key'])
        a, b = solver.solve(node['cnf']), solver.solve(child['cnf'])
        assert a['answer'] == b['answer']
        counts['edges'] += 1; counts['sat' if b['answer'] else 'unsat'] += 1
        if b['answer']:
            assert holds(node['cnf'], h.lift(key, b['model']))
    h.close(); solver.close()
    return dict(seconds=time.perf_counter()-started, **counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--suite', choices=('frontier', 'originals', 'fresh'), default='frontier')
    parser.add_argument('--reverse', action='store_true')
    args = parser.parse_args(); out = args.output; out.mkdir(parents=True, exist_ok=False)
    input_path = Path('experiments/results/cnf-prepared-probes-full/report.json')
    frontier_path = Path('experiments/results/cnf-variable-elimination-probe/raw-opportunity.json')
    prior = json.loads(input_path.read_text()); frontier = json.loads(frontier_path.read_text())
    options = dict(prior['options']); prepared = args.suite != 'frontier'
    if args.suite == 'frontier':
        cases = [dict(group='selected_unresolved_leaf', source=r['cnf'], prior_key_sha256=r['key_sha256']) for r in frontier['rows']]
        options['max_depth'] = 0
    elif args.suite == 'originals':
        cases = [dict(prior['cases'][i], original_case=i) for i in sorted(map(int, frontier['origins']))]
    else:
        cases = fresh_cases()
    modes = dict(reversed(list(MODES.items()))) if args.reverse else MODES
    files = set(prior['fingerprints']) | {'experiments/cnf_variable_elimination.py',
        'experiments/compare_cnf_variable_elimination.py', 'solver/test_cnf_variable_elimination.py'}
    report = dict(source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        input_report_sha256=sha(input_path), frontier_sha256=sha(frontier_path), options=options, suite=args.suite,
        seed=prior['seed'] if prepared else None, cases=cases, execution_order=list(modes),
        fingerprints={p: sha(p) for p in sorted(files)}, results=[])
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); seed = tmp / 'seed.db'; started = time.perf_counter()
        if prepared:
            with gzip.open(prior['seed']['path'], 'rb') as src, seed.open('wb') as dst:
                shutil.copyfileobj(src, dst)
            assert sha(seed) == prior['seed']['database_sha256']
        else:
            h = PolarityHornInventory(seed, **options); h.close(); s = ResidualSolver(seed); s.close()
        report['seed_restore_seconds'] = time.perf_counter()-started
        report['seed_bytes'] = seed.stat().st_size
        for mode, (cls, extra) in modes.items():
            configuration = dict(options, **extra); path = tmp / (mode + '.db')
            started = time.perf_counter(); shutil.copyfile(seed, path); clone = time.perf_counter()-started
            gc.collect(); started = time.perf_counter(); h = cls(path, **configuration); solver = AccountedResidualSolver(path)
            initialization = time.perf_counter()-started; records = []; leaves = {}
            for i, case in enumerate(cases):
                if i % 20 == 0: print(mode, 'query', i, flush=True)
                found, row = query(h, solver, case['source']); records.append(dict(case=i, **row))
                # This diagnostic walk is outside the acquisition timing.
                for key, node in selected(h, found['root']['key']):
                    if node['kind'] == 'unresolved': leaves[key] = node
            assert solver.archive_storage() == solver.db.execute(CENSUS).fetchone()
            storage = h.storage(); started = time.perf_counter()
            for i, case in enumerate(cases):
                _, row = query(h, solver, case['source'])
                assert row['answer'] == records[i]['answer']
                assert not row['discovery_metrics'].get('inserted_nodes', 0)
                assert not row['discovery_metrics'].get('inserted_sources', 0)
                assert not row['solver_metrics'].get('expanded_nodes', 0)
            warm = time.perf_counter()-started; h.close(); solver.close()
            started = time.perf_counter(); preserved = check_old_rows(seed, path); preservation = time.perf_counter()-started
            archive = out / ('archive-' + mode + '.sqlite3.gz'); started = time.perf_counter()
            with path.open('rb') as src, archive.open('wb') as raw:
                with gzip.GzipFile(fileobj=raw, mode='wb', mtime=0) as dst: shutil.copyfileobj(src, dst)
            result = dict(mode=mode, configuration=configuration, records=records,
                clone_seconds=clone, initialization_seconds=initialization, warm_combined_seconds=warm,
                compression_seconds=time.perf_counter()-started, preservation_seconds=preservation,
                old_rows_preserved=preserved, archive_path=str(archive), archive_sha256=sha(archive),
                database_bytes=path.stat().st_size, database_sha256=sha(path), storage=storage,
                frontier=[dict(key_sha256=hashlib.sha256(k.encode()).hexdigest(), cnf=n['cnf']) for k, n in leaves.items()])
            checkpoint = out / ('checkpoint-' + mode + '.json')
            checkpoint.write_text(json.dumps(result, separators=(',', ':'))+'\n')
            print(mode, 'acquired; cold audit', flush=True)
            result['audit'] = audit(path, cls, configuration)
            before = sha(path); result['edge_models'] = edge_models(path, cls, configuration); assert sha(path) == before
            memory_path = tmp / ('memory-' + mode + '.db'); shutil.copyfile(seed, memory_path)
            gc.collect(); tracemalloc.start(); h = cls(memory_path, **configuration); solver = AccountedResidualSolver(memory_path)
            for case in cases[:4]: query(h, solver, case['source'])
            current, peak = tracemalloc.get_traced_memory(); tracemalloc.stop(); h.close(); solver.close()
            result['allocation'] = dict(indices=list(range(min(4, len(cases)))), current_python_bytes=current, peak_python_bytes=peak)
            report['results'].append(result)
            checkpoint.write_text(json.dumps(result, separators=(',', ':'))+'\n')
            print(mode, 'verified', sum(r['summary']['closed'] for r in records), flush=True)
    by_mode = {r['mode']: r for r in report['results']}; summary = []
    for mode, result in by_mode.items():
        for previous, row in zip(by_mode['baseline']['records'], result['records'], strict=True):
            assert previous['answer'] == row['answer']
            assert encode(previous['profile']) == encode(row['profile'])
            assert previous['solver_metrics'] == row['solver_metrics']
            if previous['summary']['closed']: assert row['summary']['closed']
        rows = result['records']
        summary.append(dict(mode=mode, cases=len(rows), closed=sum(r['summary']['closed'] for r in rows),
            discovery_seconds=sum(r['discovery_seconds'] for r in rows), total_seconds=sum(r['total_seconds'] for r in rows),
            solver_seconds=sum(r['solver_seconds'] for r in rows), database_bytes=result['database_bytes'],
            selected_unresolved_leaves=len(result['frontier']),
            selected_unresolved_literals=sum(sum(map(len, r['cnf'])) for r in result['frontier']),
            metrics=dict(sum((Counter(r['discovery_metrics'])+Counter(r['prepared_metrics']) for r in rows), Counter())),
            gains=[r['case'] for r, a in zip(rows, by_mode['baseline']['records']) if r['summary']['closed'] and not a['summary']['closed']]))
    report['limitations'] = [
        'One ordered synthetic comparison; the frontier and original inputs were already selected for failure, not independent holdouts.',
        'Pure-only terminal elimination is separated from mixed-polarity resolution; neither rule is new SAT theory.',
        'Complete source reasoning and prior failed alternatives remain checked; selected proof compaction is not implemented.',
        'Cold audit, edge model checks, frontier walks, compression and four-case allocation are outside acquisition and separately reported.',
        'Prepared archive construction is prior paid work; clone, restore, opening and retained bytes are not free.',
        'The unchanged ordinary solver still decides original CNFs; structural closure is not a SAT verdict or a measured change to its search.',
        'Python allocation excludes native SQLite, RSS and full-history peak; storage can grow while residuals shrink.',
        'Leaf closure does not imply closure of every original root, or an efficient partition of arbitrary SAT.',
        'No Python-to-Lean refinement, universal elimination availability or polynomial arbitrary-SAT bound.']
    (out/'report.json').write_text(json.dumps(report, separators=(',', ':'))+'\n')
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    for mode in modes: (out/('checkpoint-'+mode+'.json')).unlink()
    print(json.dumps([{k: s[k] for k in ('mode', 'closed', 'total_seconds', 'database_bytes', 'selected_unresolved_literals')} for s in summary]), flush=True)


if __name__ == '__main__': main()
