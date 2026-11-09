#!/usr/bin/env python3
"""Profile a retained-history query from cold caches, separate from timings."""
import cProfile
import gzip
import hashlib
import json
from pathlib import Path
import pstats
import shutil
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_retained_plans import RetainedPlanInventory


def main(directory):
    target=directory/'profile.json'
    if target.exists():raise FileExistsError(target)
    report_path=directory/'report.json';report=json.loads(report_path.read_text())
    worst=max((r for r in report['records'] if r['mode']=='retained'),key=lambda r:r['discovery']['seconds'])
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'history.db'
        with gzip.open(report['seed']['path'],'rb') as src,path.open('wb') as dst:shutil.copyfileobj(src,dst)
        with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==report['seed']['database_sha256']
        h=RetainedPlanInventory(path,**report['options']);profile=cProfile.Profile();profile.enable()
        result=h.inspect(report['cases'][worst['case']]['source']);profile.disable();h.close()
        # ResidualSolver.solve performs this complete storage census on every
        # query, even when its decision is already cached. Isolate that metadata
        # work without changing the decision path or published acquisition run.
        db=sqlite3.connect(f'file:{path}?mode=ro',uri=True);samples=[];census=None
        for _ in range(12):
            started=time.perf_counter()
            census=db.execute('SELECT count(*), coalesce(sum(length(payload)+length(id)),0) FROM cnf_residual_v1').fetchone()
            samples.append(time.perf_counter()-started)
        db.close()
    functions=[]
    for (file,line,name),(primitive,calls,own,cumulative,_) in pstats.Stats(profile).stats.items():
        if '/experiments/' in file:
            functions.append(dict(file=file,line=line,function=name,calls=calls,own_seconds=own,cumulative_seconds=cumulative))
    data=dict(report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),case=worst['case'],
        original_discovery_seconds=worst['discovery']['seconds'],instrumented_seconds=result['seconds'],
        metrics=result['metrics'],prepared_metrics=result['prepared_metrics'],
        solver_storage_census=dict(repeats=len(samples),seconds=samples,
            mean_seconds=sum(samples)/len(samples),rows=census[0],payload_units=census[1],
            scope='Exact metadata aggregate from ResidualSolver.solve; excludes decision/verification'),
        functions=sorted(functions,key=lambda r:-r['own_seconds'])[:25],
        limitations=['Single query starts from the original seed with empty verifier caches, not the full comparison preceding-query state',
                     'Profiler overhead is included; this is a bottleneck diagnostic, not another performance ratio',
                     'Cumulative times overlap and must not be summed; seed restore and construction precede profiling',
                     'Repeated solver storage census is measured separately; it is metadata work, not SAT search. Multiplying its mean by query count is only an estimate'])
    target.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(case=data['case'],functions=data['functions'][:6])),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
