#!/usr/bin/env python3
"""Measure discovery coverage and overhead; the SAT decision engine is unchanged."""
import argparse
from collections import Counter
import gc
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
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_pattern_inventory import PatternInventory, FAMILIES
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_matching import domain_cnf
from solver.test_cnf_pattern_inventory import assignments, parity, check_pointwise

MODES = dict(solver_only=None,
             whole=dict(max_depth=0, decompose=False),
             components=dict(max_depth=0),
             conditioned=dict(max_depth=1),
             conditioned2=dict(max_depth=2))


def scenarios():
    clauses = [tuple(s*(i+1) for i, s in enumerate(signs) if s)
               for signs in itertools.product((-1, 0, 1), repeat=2)]
    cases = [dict(group='exhaustive2', source=[c for i, c in enumerate(clauses) if mask >> i & 1])
             for mask in range(1 << len(clauses))]
    rng = random.Random(2026110820)
    for n, count, low, high in ((6, 96, 6, 20), (8, 24, 20, 34)):
        for _ in range(count):
            source = [tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, n+1), rng.randrange(2, 5)))
                      for _ in range(rng.randrange(low, high))]
            cases.append(dict(group='random', source=source))
    structured = []
    for n in (4, 6, 8, 10):
        structured.append((f'parity_{n}', parity(range(1, n+1), 1)))
    for n in (4, 5, 6):
        structured.append((f'full_cube_unsat_{n}', parity(range(1, n+1), 0)+parity(range(1, n+1), 1)))
    p = parity((1, 2, 3, 4), 1)
    structured += [
        ('disjoint_parity', p+parity((5, 6, 7, 8), 1)),
        ('overlapping_parity', p+parity((3, 4, 5, 6), 1)),
        ('parity_bridge', p+parity((5, 6, 7, 8), 1)+[(1, 5)]),
        ('parity_unit', p+[(1,)]),
        ('mixed_matching', domain_cnf([range(3)]*3)+[(-100, 101), (100, -101)]),
        ('matching_parity', domain_cnf([range(3)]*3)+parity((10, 11, 12, 13), 1)),
        ('coupled_matching_parity', domain_cnf([range(3)]*3)+parity((10, 11, 12, 13), 1)+[(1, 10)]),
    ]
    hard = parity((1, 2, 3, 4), 0)+parity((1, 2, 3, 4), 1)
    guarded = [tuple(c)+(5,) for c in hard]
    structured += [('guarded', guarded), ('guard_activated', guarded+[(-5,)])]
    for label, source in structured:
        cases.append(dict(group='structured', label=label, source=source))
        names = sorted({abs(lit) for c in source for lit in c})
        shuffled = names[:];rng.shuffle(shuffled)
        rename = dict(zip(names, (v*17+100 for v in shuffled)))
        variant = [tuple(rename[abs(lit)]*(1 if lit > 0 else -1) for lit in reversed(c))
                   for c in reversed(source)]
        cases.append(dict(group='variant', label=label, source=variant+variant[:2]+[(9999, -9999)]))
    return cases


def node_summary(h, root):
    seen, stack, leaves = set(), [root], []
    while stack:
        key = stack.pop()
        if key in seen:
            continue
        seen.add(key);node = h._load(key)
        if node['kind'] == 'and':
            stack.extend(e['key'] for e in node['edges'])
        elif node['kind'] == 'or':
            stack.extend(e['key'] for e in node['alternatives'][node['selected']]['edges'])
        elif node['kind'] == 'unresolved':
            leaves.append(node['profile']['shape'])
    return dict(selected_distinct_nodes=len(seen), unresolved_distinct_leaves=len(leaves),
                unresolved_distinct_literals=sum(x['literals'] for x in leaves),
                unresolved_shapes=leaves)


def audit(path, raw, options):
    path.write_bytes(raw)
    started = time.perf_counter()
    h = PatternInventory(path, **options) if options is not None else None
    sources = nodes = 0
    if h:
        for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):
            h._load(key);nodes += 1
        for key, payload in h.db.execute('SELECT id,payload FROM cnf_pattern_sources_v1'):
            saved = json.loads(payload)
            result = h.inspect(saved['source'])
            assert result['source_id'] == key and result['root'] == saved['root']
            assert result['metrics'].get('inserted_nodes', 0) == 0 and result['metrics']['inserted_sources'] == 0
            sources += 1
        h.close()
    solver = ResidualSolver(path)
    residuals = 0
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
        assert solver._read(key) is not None
        residuals += 1
    assert solver.counts.get('expanded_nodes', 0) == 0
    assert solver.db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    solver.close()
    assert path.read_bytes() == raw
    return dict(nodes=nodes, sources=sources, residuals=residuals,
                seconds=time.perf_counter()-started, bytes_unchanged=True)


def memory_profile(cases, options):
    gc.collect()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)/'memory.sqlite3'
        tracemalloc.start()
        solver = ResidualSolver(path)
        h = PatternInventory(path, **options) if options is not None else None
        for case in cases:
            if h:
                h.inspect(case['source'])
            solver.solve(case['source'])
        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        if h:
            h.close()
        solver.close()
    return dict(current_traced_bytes=current, peak_traced_bytes=peak)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=False)
    cases, records, archives = scenarios(), [], []
    # This validation is outside the timing loop and never selects a route.
    expected = [any(holds(c['source'], a) for a in assignments(c['source']))
                if len({abs(lit) for clause in c['source'] for lit in clause}) <= 8 else None for c in cases]
    answers = None
    for mode, options in MODES.items():
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history.sqlite3'
            start = time.perf_counter()
            solver = ResidualSolver(path)
            h = PatternInventory(path, **options) if options is not None else None
            initialization = time.perf_counter()-start
            current_answers = []
            for i, case in enumerate(cases):
                start = time.perf_counter()
                discovery = h.inspect(case['source']) if h else None
                result = solver.solve(case['source'])
                elapsed = time.perf_counter()-start
                current_answers.append(result['answer'])
                assert expected[i] is None or result['answer'] == expected[i]
                if answers is not None:
                    assert result['answer'] == answers[i]
                if result['answer']:
                    assert holds(case['source'], result['model'])
                if discovery:
                    key = discovery['root']['key']
                    # Small pointwise checks cover every attempted alternative,
                    # not only the branch selected for the coverage summary.
                    if discovery['profile']['shape']['variables'] <= 8:
                        check_pointwise(h, key)
                    discovery['dag'] = node_summary(h, key)
                    discovery['root_hash'] = hashlib.sha256(key.encode()).hexdigest()
                    del discovery['root'], discovery['source_id']
                records.append(dict(case=i, mode=mode, total_seconds=elapsed, discovery=discovery,
                                    answer=result['answer'], solver_seconds=result['seconds'],
                                    solver_metrics=result['metrics'], solver_nodes=result['archive_nodes'],
                                    solver_payload_bytes=result['archive_payload_bytes']))
            if answers is None:
                answers = current_answers
            storage = h.storage() if h else {}
            warm_seconds = 0
            if h:
                start = time.perf_counter()
                for case in cases:
                    result = h.inspect(case['source'])
                    assert result['metrics'].get('inserted_nodes', 0) == 0
                    assert result['metrics']['inserted_sources'] == 0
                warm_seconds = time.perf_counter()-start
                assert storage == h.storage()
                h.close()
            solver.close()
            raw = path.read_bytes()
            name = f'archive-{mode}.sqlite3.gz'
            (out/name).write_bytes(gzip.compress(raw, mtime=0))
            verified = audit(Path(tmp)/'cold.sqlite3', raw, options)
            archives.append(dict(mode=mode, path=name, database_bytes=len(raw),
                                 compressed_bytes=(out/name).stat().st_size,
                                 database_sha256=hashlib.sha256(raw).hexdigest(),
                                 initialization_seconds=initialization, warm_inventory_seconds=warm_seconds,
                                 storage=storage, audit=verified))
        print(mode, 'checked', flush=True)
    selected = [c for c in cases if c.get('label') in ('overlapping_parity', 'guard_activated', 'mixed_matching')]
    profiles = [dict(mode=mode, **memory_profile(selected, options)) for mode, options in MODES.items()]
    files = [Path(__file__), Path('experiments/cnf_pattern_inventory.py'), Path('experiments/cnf_residual_dag.py'),
             Path('experiments/compare_cnf_matching.py'), Path('solver/test_cnf_pattern_inventory.py')]
    report = dict(source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  fingerprints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  modes=MODES, families=FAMILIES, cases=cases, records=records, archives=archives,
                  allocation_profiles=profiles, allocation_case_labels=[c['label'] for c in selected],
                  limitations=[
                      'Single sequential samples, not significance estimates or a representative SAT distribution',
                      'Analysis is additive: all modes use the same unchanged residual solver; no decision speedup claimed',
                      'Generator labels never enter classification or choose a solver method',
                      'Profiles classify normalized representations, retaining exact source bindings and name maps',
                      'Closed means all selected leaves have a recognized family, not SAT or a compact general-SAT guarantee',
                      'Parity recognizes one complete direct equation encoding only; above width cap it is unresolved',
                      'All candidate alternatives are retained; summary literal sums count tree occurrences and DAG fields count distinct selected residuals',
                      'Matched acquisition includes analysis checking and persistence plus ordinary solving; initialization and warm/cold replay are separate',
                      'Input generation, truth tables, inter-operation checks, storage inspection and offline compression excluded from timing',
                      'Cold audit includes row reads, JSON decoding, all alternative checking, source rebinding and residual-certificate checking',
                      'Tracemalloc reruns are separate, limited to the listed six cases; native SQLite and process RSS excluded',
                      'Warm cache assumes append-only single-writer archives; Python recognition and SQLite are outside Lean refinement'])
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases), archives=len(archives))), flush=True)


if __name__ == '__main__':
    main()
