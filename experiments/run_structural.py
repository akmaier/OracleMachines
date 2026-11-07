#!/usr/bin/env python3
"""Fixed structural expansion streams; restart, acquisition and storage costs included.

Synthetic families diagnose mechanisms, not representative general-SAT speed.
Every mode/repetition runs in a fresh process/database. All failures are retained.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from solver.persistent import PersistentSolver, DEFAULT_ENGINE
from solver.incremental import DEFAULT_INCREMENTAL
from experiments.run_expanded import balanced

MODES = ['checked', 'incremental_live', 'incremental_restart', 'components_live', 'components_restart']

def var(i):
    return '01' + '1'*i + '0'
def neg(f):
    return f+'10'
def conj(a,b):
    return a+b+'11'
def disj(a,b):
    return neg(conj(neg(a),neg(b)))
def xor(i,j):
    return conj(disj(var(i),var(j)),disj(neg(var(i)),neg(var(j))))
def join(parts):
    return balanced(parts,conj,'0010')
def stream(name):
    counts=[1,2,4,8,16,32,64]
    if name=='independent_copies':
        return [dict(stage=n,bits=join([xor(2*i,2*i+1) for i in range(n)]),expected=True) for n in counts]
    if name=='connected_chain':
        # This chain has small separators, but the implemented zero-interface
        # decomposition cannot exploit them: a deliberate negative control.
        return [dict(stage=n,bits=join([xor(i,i+1) for i in range(n)]),expected=True) for n in counts]
    if name=='negative_core':
        core=join([disj(a,b) for a in [var(0),neg(var(0))] for b in [var(1),neg(var(1))]])
        return [dict(stage=n,bits=join([core]+[disj(var(1),var(i+2)) for i in range(n-1)]),expected=False) for n in counts]
    if name=='shared_definitions':
        return [dict(stage=n,bits=conj(join([xor(i,i+1) for i in range(12)]),var(n+20)),expected=True) for n in counts]
    raise ValueError(name)

STREAMS=['independent_copies','connected_chain','negative_core','shared_definitions']

def worker(mode,name):
    with tempfile.TemporaryDirectory(prefix='oracle-structure-') as tmp:
        path=Path(tmp)/'results.sqlite3'
        solver=None
        setup_total=0
        try:
            for case in stream(name):
                started=time.perf_counter_ns()
                row=dict(stage=case['stage'],expected=case['expected'],input_bytes=len(case['bits']),
                         input_sha256=hashlib.sha256(case['bits'].encode()).hexdigest())
                try:
                    setup=time.perf_counter_ns()
                    if solver is None:
                        solver=PersistentSolver(path,backend='cadical',reuse_exact=False,
                            incremental=mode.startswith('incremental'), components=mode.startswith('components'))
                    row['setup_ns']=time.perf_counter_ns()-setup
                    setup_total+=row['setup_ns']
                    row['result']=solver.solve(case['bits'],learn=False)
                    row['correct']=row['result']['answer']==case['expected']
                    row['status']='ok' if row['correct'] else 'wrong'
                except Exception as error:
                    row.update(status='error',error=type(error).__name__+': '+str(error))
                finally:
                    if mode.endswith('restart') and solver is not None:
                        solver.close(); solver=None
                    row['elapsed_ns']=time.perf_counter_ns()-started
                    print(json.dumps(dict(event='query',**row)),flush=True)
            if solver is None:
                solver=PersistentSolver(path)
            kinds=[dict(kind=r[0],objects=r[1],raw_bytes=r[2],compressed_bytes=r[3]) for r in solver.db.execute(
                'SELECT kind,count(*),sum(raw_bytes),sum(length(payload)) FROM knowledge_objects GROUP BY kind')]
            totals=dict(event='storage',kinds=kinds,setup_ns=setup_total,
                        input_archive_bytes=solver.db.execute('SELECT sum(length(bits)) FROM results').fetchone()[0],
                        proof_archive_bytes=solver.db.execute('SELECT coalesce(sum(length(certificate)),0) FROM proofs').fetchone()[0],
                        result_count=solver.stats()['entries'])
            solver.close();solver=None
            totals['database_bytes']=path.stat().st_size
            print(json.dumps(totals),flush=True)
        finally:
            if solver is not None:solver.close()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--worker',nargs=2)
    parser.add_argument('--output',type=Path,default=ROOT/'experiments/results/structural')
    args=parser.parse_args()
    if args.worker:
        worker(*args.worker);return
    args.output.mkdir(parents=True,exist_ok=False)
    runs=[]
    with (args.output/'runs.jsonl').open('w') as out:
        for name in STREAMS:
            for mode in MODES:
                for repeat in range(3):
                    start=time.perf_counter_ns()
                    run=subprocess.run([sys.executable,__file__,'--worker',mode,name],text=True,capture_output=True,timeout=300)
                    row=dict(stream=name,mode=mode,repeat=repeat,exit=run.returncode,elapsed_ns=time.perf_counter_ns()-start,
                             records=[json.loads(line) for line in run.stdout.splitlines()],stderr=run.stderr)
                    runs.append(row);out.write(json.dumps(row)+'\n');out.flush()
    summary=[]
    for name in STREAMS:
        for mode in MODES:
            group=[r for r in runs if r['stream']==name and r['mode']==mode]
            queries=[q for r in group for q in r['records'] if q['event']=='query']
            summary.append(dict(stream=name,mode=mode,queries=len(queries),statuses=dict(Counter(q['status'] for q in queries)),
                median_total_ms=statistics.median(sum(q['elapsed_ns'] for q in r['records'] if q['event']=='query')/1e6 for r in group),
                median_process_ms=statistics.median(r['elapsed_ns']/1e6 for r in group),
                acquisitions=[sum(q.get('result',{}).get('components',{}).get('acquisitions',0) for q in r['records']) for r in group],
                last_storage=[r['records'][-1] for r in group]))
    fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                  [DEFAULT_ENGINE,DEFAULT_INCREMENTAL,ROOT/'solver/components.py',ROOT/'solver/knowledge_store.py',ROOT/'solver/incremental.py',ROOT/'solver/incremental.cpp',ROOT/'solver/persistent.py',Path(__file__)]}
    (args.output/'summary.json').write_text(json.dumps(dict(host=platform.platform(),python=sys.version,
        fingerprints=fingerprints,runs=len(runs),summary=summary),indent=2)+'\n')
    print(json.dumps([dict((k,v) for k,v in s.items() if k!='last_storage') for s in summary],indent=2))

if __name__=='__main__':main()
