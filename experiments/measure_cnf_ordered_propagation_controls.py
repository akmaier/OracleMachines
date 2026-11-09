#!/usr/bin/env python3
"""Ordered propagation controls, including short-conflict preparation regressions."""
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
from experiments.cnf_ordered_propagation import propagate_ordered
from experiments.cnf_residual_dag import propagate
from experiments.cnf_simplification import check_simplification


def sources(n):
    chain = [(-i, i+1) for i in range(1, n)]
    tail = [(3*i+1, -3*i-2, 3*i+3) for i in range(n, 2*n)]
    return dict(forward_chain=[(1,)]+chain,
                reverse_chain=list(reversed(chain))+[(1,)],
                unit_free=chain,
                sparse_cascade=[(1,), (-1, 2)]+tail,
                early_conflict=[(1,), (-1,)]+tail,
                early_empty=[()]+tail,
                long_identifiers=[tuple((1 if lit > 0 else -1)*(abs(lit)+(1 << 1024))
                                        for lit in c) for c in list(reversed(chain))+[(1,)]])


def main(directory):
    target = directory/'controls.json'
    if target.exists(): raise FileExistsError(target)
    rows = []
    for n in (16, 64, 256, 1024):
        for family, source in sources(n).items():
            engines = dict(baseline=propagate, ordered=propagate_ordered)
            reference = propagate(source, Counter())
            traces = {}; times = {mode: [] for mode in engines}; metrics = {}
            for mode in ('baseline','ordered','ordered','baseline','ordered','baseline','baseline','ordered'):
                gc.collect(); counts = Counter(); started = time.perf_counter()
                result = engines[mode](source, counts)
                elapsed = time.perf_counter()-started
                assert result == reference
                certificate = dict(units=result[1], conflict=result[2], pure_rounds=[])
                check_simplification(source, certificate, Counter(), pure=False)
                if mode in metrics: assert metrics[mode] == dict(counts)
                metrics[mode] = dict(counts); times[mode].append(elapsed)
                traces[mode] = hashlib.sha256(json.dumps(result, separators=(',', ':')).encode()).hexdigest()
            allocation = {}
            for mode, engine in engines.items():
                gc.collect(); tracemalloc.start()
                result = engine(source, Counter())
                current, peak = tracemalloc.get_traced_memory(); tracemalloc.stop()
                assert result == reference
                allocation[mode] = dict(current_bytes=current, peak_bytes=peak)
            rows.append(dict(n=n,family=family,clauses=len(source),literals=sum(map(len,source)),
                source_sha256=hashlib.sha256(json.dumps(source,separators=(',',':')).encode()).hexdigest(),
                trace_sha256=traces,metrics=metrics,seconds=times,
                mean_seconds={m:statistics.mean(t) for m,t in times.items()},allocation=allocation))
    output=dict(rows=rows,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        fingerprints={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
            ('experiments/cnf_ordered_propagation.py','experiments/cnf_residual_dag.py','experiments/cnf_simplification.py')},
        limitations=['Standalone single closures, not end-to-end SAT or cross-assumption index reuse',
            'Four alternating trials per mode; allocation measured separately; no significance claim',
            'First-time index preparation is charged, including the early-conflict regression',
            'Large integer labels test arithmetic overhead; unit-cost bounds do not erase bit costs',
            'Ordered and scan modes must return identical complete traces, assignments and conflict indices'])
    target.write_text(json.dumps(output,indent=2)+'\n')
    print('Recorded',len(rows),'controls',flush=True)


if __name__ == '__main__':main(Path(sys.argv[1]))
