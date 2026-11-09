#!/usr/bin/env python3
"""Matched restriction streams, including lost identity and dense updates."""
from collections import Counter
import gc
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_indexed_restriction import IndexedRestriction
from experiments.cnf_residual_dag import restrict_scan


def streams(n):
    base=tuple((3*i+1,-3*i-2,3*i+3) for i in range(n))
    assumptions=[{3*(i%n)+1:bool(i%2)} for i in range(32)]
    equal=[tuple(tuple(list(c)) for c in base) for _ in assumptions]
    mutable=[list(c) for c in base]
    overlap=tuple((1,i+2,-i-3) for i in range(n))
    return dict(
        warm_sparse=(32768,list(zip([base]*32,assumptions))),
        equal_new_objects=(32768,list(zip(equal,assumptions))),
        novel_append=(32768,[(base+((3*n+i+1,),),a) for i,a in enumerate(assumptions)]),
        dense_updates=(32768,[(overlap,{1:False}) for _ in assumptions]),
        mutable_fallback=(32768,list(zip([mutable]*32,assumptions))),
        oversize_fallback=(32,list(zip([base]*32,assumptions))),
        absent_variable=(32768,[(base,{3*n+1:True}) for _ in assumptions]),
        empty_assignment=(32768,[(base,{}) for _ in assumptions]))


def main(directory):
    target=directory/'controls.json'
    if target.exists():raise FileExistsError(target)
    rows=[]
    for n in (16,64,256,1024):
        for family,(limit,queries) in streams(n).items():
            expected=[restrict_scan(cnf,a) for cnf,a in queries]
            checked=IndexedRestriction(limit)
            for (cnf,a),answer in zip(queries,expected):assert checked(cnf,a)==answer
            del checked
            times={m:[] for m in ('baseline','indexed')};metrics={};states={}
            for mode in ('baseline','indexed','indexed','baseline','indexed','baseline','baseline','indexed'):
                gc.collect();engine=IndexedRestriction(limit) if mode=='indexed' else restrict_scan
                counts=Counter();started=time.perf_counter()
                for cnf,a in queries:result=engine(cnf,a,counts)
                elapsed=time.perf_counter()-started
                assert result==expected[-1]
                if mode in metrics:assert metrics[mode]==dict(counts)
                metrics[mode]=dict(counts);times[mode].append(elapsed)
                states[mode]=engine.state() if mode=='indexed' else None
                del engine,result
            allocation={}
            for mode in ('baseline','indexed'):
                gc.collect();tracemalloc.start()
                engine=IndexedRestriction(limit) if mode=='indexed' else restrict_scan
                counts=Counter()
                for cnf,a in queries:result=engine(cnf,a,counts)
                current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
                assert result==expected[-1]
                allocation[mode]=dict(current_bytes=current,peak_bytes=peak)
                del engine,result
            rows.append(dict(n=n,family=family,queries=len(queries),limit_units=limit,
                input_sha256=hashlib.sha256(json.dumps(queries,separators=(',',':')).encode()).hexdigest(),
                seconds=times,mean_seconds={m:statistics.mean(t) for m,t in times.items()},
                metrics=metrics,cache=states,allocation=allocation))
    report=dict(rows=rows,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        fingerprints={p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in
            ('experiments/cnf_indexed_restriction.py','experiments/cnf_residual_dag.py')},
        limitations=['32-query streams; each trial starts with an empty index; four alternating trials per mode',
            'All outputs validated separately; timed stream retains only its last result and checks it after stopping the clock',
            'Source/assignment construction and expected outputs are outside timing/allocation; cache construction is included',
            'Allocator controls retain the index and last output, exclude original source storage and are not RSS bounds',
            'Identity locality, mutable and oversized fallbacks, dense edits and equal reallocation are deliberately separated',
            'This is restriction helper work, not full expansion, checking or SAT runtime'])
    target.write_text(json.dumps(report,indent=2)+'\n')
    print('Recorded',len(rows),'restriction controls',flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
