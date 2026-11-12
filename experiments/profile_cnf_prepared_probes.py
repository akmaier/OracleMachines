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
from experiments.cnf_prepared_probes import PreparedProbeInventory


def main(directory):
    target=directory/'profile.json'
    if target.exists():raise FileExistsError(target)
    directory.mkdir(parents=True,exist_ok=True)
    report_path=Path('experiments/results/cnf-prepared-probes-full/report.json');report=json.loads(report_path.read_text())
    worst=max((r for mode in report['results'] if mode['mode']=='reuse' for r in mode['records'] if not r['summary']['closed']),key=lambda r:r['discovery_seconds'])
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'history.db'
        with gzip.open(report['seed']['path'],'rb') as src,path.open('wb') as dst:shutil.copyfileobj(src,dst)
        with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==report['seed']['database_sha256']
        h=PreparedProbeInventory(path,**report['options']);profile=cProfile.Profile();profile.enable()
        result=h.inspect(report['cases'][worst['case']]['source']);profile.disable();h.close()
    functions=[]
    for (file,line,name),(primitive,calls,own,cumulative,_) in pstats.Stats(profile).stats.items():
        if '/experiments/' in file:
            functions.append(dict(file=file,line=line,function=name,calls=calls,own_seconds=own,cumulative_seconds=cumulative))
    data=dict(report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),case=worst['case'],
        original_discovery_seconds=worst['discovery_seconds'],instrumented_seconds=result['seconds'],
        metrics=result['metrics'],prepared_metrics=result['prepared_metrics'],
        functions=sorted(functions,key=lambda r:-r['own_seconds'])[:25],
        limitations=['Single query starts from the original seed with empty verifier caches, not the full comparison preceding-query state',
                     'Profiler overhead is included; this is a bottleneck diagnostic, not another performance ratio',
                     'Cumulative times overlap and must not be summed; seed restore and construction precede profiling'])
    target.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(dict(case=data['case'],functions=data['functions'][:6])),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
