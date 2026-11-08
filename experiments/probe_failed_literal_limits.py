#!/usr/bin/env python3
"""Separate, post-study budget diagnostic on all remaining misses; no holdout claim."""
from collections import Counter
import cProfile
import gzip
import hashlib
import json
from pathlib import Path
import pstats
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_failed_literal import FailedLiteralInventory
from experiments.cnf_residual_dag import ResidualSolver
from experiments.compare_cnf_failed_literal import node_summary
from experiments.compare_cnf_pattern_inventory import audit


def run(directory):
    report=json.loads((directory/'report.json').read_text())
    mechanisms=json.loads((directory/'mechanisms.json').read_text())
    indices=[r['case'] for r in mechanisms['changes']['probe4']['misses']]
    assert max(len({abs(l) for c in report['cases'][i]['source'] for l in c}) for i in indices)<=64
    runs=[]
    for cap in (4,64):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'inventory.sqlite3'
            # The shared audit also opens the ordinary solver. Initialize its
            # empty tables before snapshotting, so replay is strictly read-only.
            ResidualSolver(path).close()
            h=FailedLiteralInventory(path,max_depth=2,probe_limit=cap)
            rows=[]
            for i in indices:
                r=h.inspect(report['cases'][i]['source'])
                rows.append(dict(case=i,seconds=r['seconds'],metrics=r['metrics'],summary=r['summary'],
                                 dag=node_summary(h,r['root']['key'])))
            remaining=[]
            for n in h.checked.values():
                if n['kind']!='unresolved':continue
                binary={abs(l) for c in n['cnf'] if len(c)==2 for l in c}
                tried={a['variable'] for a in n['profile']['probing'].get('attempts',[])}
                if cap==64:assert tried==binary
                remaining.append(dict(shape=n['profile']['shape'],binary_variables=len(binary),attempted_variables=len(tried)))
            storage=h.storage();h.close();raw=path.read_bytes();name=f'limits-cap{cap}.sqlite3.gz'
            (directory/name).write_bytes(gzip.compress(raw,mtime=0))
            cold=audit(Path(tmp)/'cold.sqlite3',raw,dict(max_depth=2,probe_limit=cap),FailedLiteralInventory)
            runs.append(dict(cap=cap,records=rows,seconds=sum(r['seconds'] for r in rows),
                closed=sum(r['summary']['closed'] for r in rows),storage=storage,database_bytes=len(raw),
                archive=name,database_sha256=hashlib.sha256(raw).hexdigest(),audit=cold,unresolved=remaining))
        print('cap',cap,'checked',flush=True)
    # Profile the most expensive remaining discovery in the main probe4 run.
    worst=max((r for r in report['records'] if r['mode']=='probe4' and not r['discovery']['summary']['closed']),
              key=lambda r:r['discovery']['seconds'])['case']
    with tempfile.TemporaryDirectory() as tmp:
        h=FailedLiteralInventory(Path(tmp)/'profile.sqlite3',max_depth=2,probe_limit=4)
        profiler=cProfile.Profile();profiler.enable();r=h.inspect(report['cases'][worst]['source']);profiler.disable();h.close()
        stats=pstats.Stats(profiler);functions=[]
        for (file,line,name),(primitive,calls,own,cumulative,_) in stats.stats.items():
            functions.append(dict(file=file,line=line,name=name,primitive_calls=primitive,calls=calls,
                                  own_seconds=own,cumulative_seconds=cumulative))
    return dict(source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),case_indices=indices,runs=runs,
        profile=dict(case=worst,seconds=r['seconds'],metrics=r['metrics'],
                     functions=sorted(functions,key=lambda f:-f['own_seconds'])[:45]),
        limitations=['Diagnostic chosen after results, not independent holdout; only 29 previously unresolved inputs',
                     'Inventory-only times exclude ordinary solving and model lifting; cold audit separately reported',
                     'Cap64 covers every binary variable in these sources, not all variables of arbitrary SAT inputs',
                     'Profiler is a separate instrumented run; its time is not an uninstrumented comparison'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'limits.json'
    if out.exists():raise ValueError('Preserve earlier diagnostic')
    out.write_text(json.dumps(run(directory),indent=2)+'\n')
