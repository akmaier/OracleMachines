#!/usr/bin/env python3
"""Alternate exact subset kernels on the retained trace and adverse controls."""
from collections import Counter
import gzip
import itertools
import json
from pathlib import Path
import sys
import time
import tracemalloc
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_anchored_subsets import anchored_certificate
from experiments.cnf_implied_subsumption import indexed_certificate
from experiments.compare_cnf_retained_plans import sha


def main(out):
    out.mkdir(exist_ok=False);trace_path=Path('experiments/results/cnf-subset-reuse-trace/calls.json.gz')
    with gzip.open(trace_path,'rt') as f:trace=json.load(f)
    cases=[dict(group='trace',source=trace['sources'][r['source']],phase=r['phase'],certificate=r['certificate']) for r in trace['calls']]
    controls=[list(itertools.combinations(range(1,14),3)),
        [tuple(range(1,w))+(i,) for w in range(2,9) for i in range(20,40)],
        [(i,) for i in range(1,60)]+[tuple(range(i,i+5)) for i in range(1,60)],
        [(1,1),(1,2),(1,)], [(),(1,),(-1,2)]]
    for i,cnf in enumerate(controls):cases.append(dict(group='control_'+str(i),source=cnf,phase='discovery',certificate=indexed_certificate(cnf,Counter())))
    rows=[];modes=dict(baseline=indexed_certificate,anchored=anchored_certificate)
    for repeat in range(5):
        order=list(modes) if repeat%2==0 else list(reversed(modes))
        for mode in order:
            for group in dict.fromkeys(r['group'] for r in cases):
                chosen=[r for r in cases if r['group']==group];counts=Counter();started=time.perf_counter()
                for r in chosen:assert modes[mode](r['source'],counts,phase=r['phase'])==r['certificate']
                rows.append(dict(repeat=repeat,mode=mode,group=group,seconds=time.perf_counter()-started,counts=dict(counts)))
    allocation=[]
    for mode,fn in modes.items():
        tracemalloc.start();counts=Counter()
        for r in cases:fn(r['source'],counts,phase=r['phase'])
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
        allocation.append(dict(mode=mode,current_python_bytes=current,peak_python_bytes=peak))
    report=dict(script_sha256=sha(Path(__file__)),trace_sha256=sha(trace_path),controls=controls,rows=rows,allocation=allocation,
        source_fingerprints={p:sha(p) for p in ('experiments/cnf_anchored_subsets.py','experiments/cnf_implied_subsumption.py')},
        limitations=['Isolated kernel replay, not end-to-end discovery; equality assertions and counters are timed.',
        'Trace inputs were selected from one previous costly source. Controls include equal widths, shared literals, units, repeated literals and an empty clause.',
        'Five alternating-order repetitions on one host; allocation excludes native memory and full application state.'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(allocation))


if __name__=='__main__':main(Path(sys.argv[1]))
