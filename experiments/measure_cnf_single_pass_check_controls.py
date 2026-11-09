#!/usr/bin/env python3
"""Matched reconstruction controls, retaining the slower support-cache idea."""
from collections import Counter
import gc
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_shared_clause_check import SharedClauseReconstruction
from experiments.cnf_single_pass_check import reconstruct_single_pass
from experiments.cnf_simplification import reconstruct_simplification_scan


def streams(n, width):
    base = tuple(tuple((width*i+j+1)*(-1 if j%3 == 1 else 1) for j in range(width)) for i in range(n))
    sparse = [{width*(i%n)+1: bool(i%2)} for i in range(32)]
    equal = [tuple(tuple(list(c)) for c in base) for _ in sparse]
    mutable = [list(c) for c in base]
    return dict(
        sparse_reuse=list(zip([base]*32, sparse)),
        equal_new_objects=list(zip(equal, sparse)),
        novel_append=[(base+((width*n+i+1,),), a) for i, a in enumerate(sparse)],
        all_clauses_affected=[(base, {width*i+1: False for i in range(n)}) for _ in sparse],
        early_satisfied=[(base, {width*i+1: True for i in range(n)}) for _ in sparse],
        mutable=list(zip([mutable]*32, sparse)),
        absent_variable=[(base, {width*n+1: True}) for _ in sparse],
        empty_assignment=[(base, {}) for _ in sparse])


def engine(mode):
    return (SharedClauseReconstruction(32768) if mode == 'cached' else
            reconstruct_single_pass if mode == 'single' else reconstruct_simplification_scan)


def main(directory):
    target = directory/'controls.json'
    if target.exists():raise FileExistsError(target)
    rows = []; order = ['baseline', 'single', 'cached', 'cached', 'single', 'baseline']
    for n in (16, 64, 256):
        for width in (3, 32):
            for family, queries in streams(n, width).items():
                expected = [reconstruct_simplification_scan(cnf, a, Counter(), units=False) for cnf, a in queries]
                for mode in ('single', 'cached'):
                    check = engine(mode)
                    for (cnf, a), result in zip(queries, expected):
                        assert check(cnf, a, Counter(), units=False) == result
                    del check
                times = {m: [] for m in ('baseline', 'single', 'cached')}; metrics = {}; states = {}
                for mode in order:
                    gc.collect(); selected = engine(mode); counts = Counter(); start = time.perf_counter()
                    for cnf, a in queries:result = selected(cnf, a, counts, units=False)
                    elapsed = time.perf_counter()-start
                    assert result == expected[-1]
                    if mode in metrics:assert metrics[mode] == dict(counts)
                    times[mode].append(elapsed); metrics[mode] = dict(counts)
                    states[mode] = selected.state() if mode == 'cached' else None
                    del selected, result
                allocation = {}
                for mode in ('baseline', 'single', 'cached'):
                    gc.collect(); tracemalloc.start(); selected = engine(mode); counts = Counter()
                    for cnf, a in queries:result = selected(cnf, a, counts, units=False)
                    current, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
                    assert result == expected[-1]
                    allocation[mode] = dict(current_bytes=current, peak_bytes=peak)
                    del selected, result
                rows.append(dict(n=n, width=width, family=family, queries=len(queries),
                    input_sha256=hashlib.sha256(json.dumps(queries, separators=(',', ':')).encode()).hexdigest(),
                    seconds=times, mean_seconds={m: statistics.mean(t) for m, t in times.items()},
                    metrics=metrics, cache=states, allocation=allocation))
    files = [str(Path(__file__)), 'experiments/cnf_single_pass_check.py',
             'experiments/cnf_shared_clause_check.py', 'experiments/cnf_simplification.py']
    report = dict(rows=rows, order=order, fingerprints={p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in files},
        limitations=['32-query streams, two reversed-order samples per mode, starting with empty optional cache',
            'All results validated separately; timed streams retain only the last output and validate it after timing',
            'Input and expected-result construction excluded; allocation excludes preconstructed source memory',
            'Cache construction and all loop work included; allocations are Python traced bytes, not RSS',
            'Reconstruction only with unit-fixed-point requirement disabled; full certificate replay is in the corpus study',
            'The support-cache variant is retained as a rejected alternative, not the selected implementation',
            'Input widths and locality are synthetic controls, not significance or unrestricted SAT bounds'])
    target.write_text(json.dumps(report, indent=2)+'\n')
    print('Recorded', len(rows), 'reconstruction controls', flush=True)


if __name__ == '__main__':main(Path(sys.argv[1]))
