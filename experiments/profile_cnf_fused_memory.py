#!/usr/bin/env python3
"""Separate targeted allocation diagnostic; never overlap the timed benchmark."""
import gc
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import tracemalloc

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_fused_conditioning import MODES
from experiments.cnf_residual_dag import ResidualSolver


def run(directory):
    source=directory/'report.json';report=json.loads(source.read_text())
    indices=[777,790,819,850,885,889]
    results=[]
    for mode,(cls,options) in MODES.items():
        if options is None:continue
        gc.collect()
        with tempfile.TemporaryDirectory() as tmp:
            tracemalloc.start()
            path=Path(tmp)/'memory.db';h=cls(path,**options);solver=ResidualSolver(path)
            for i in indices:
                h.inspect(report['cases'][i]['source']);solver.solve(report['cases'][i]['source'])
            gc.collect();current,peak=tracemalloc.get_traced_memory();tracemalloc.stop()
            results.append(dict(mode=mode,current_traced_bytes=current,peak_traced_bytes=peak,storage=h.storage()))
            h.close();solver.close()
        print(mode,'allocation checked',flush=True)
    return dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                report_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),case_indices=indices,results=results,
                limitations=['Separate six-case reruns chosen to exercise fused branches, not full-corpus peak memory',
                             'Traced Python allocations exclude native SQLite memory and RSS',
                             'No timings from this instrumented diagnostic enter benchmark operation times'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'targeted-allocation.json'
    if out.exists():raise ValueError('Preserve the earlier allocation diagnostic')
    out.write_text(json.dumps(run(directory),indent=2)+'\n')
