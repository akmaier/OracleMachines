#!/usr/bin/env python3
"""Sequential, isolated local-interface and incremental-proof mechanism study.

Every mode sees the same logical snapshots. Delta transport is compared with
full input separately; all archived database categories and failures are retained.
This is not an equal-memory or SAT-competition comparison.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from solver.persistent import PersistentSolver,DEFAULT_ENGINE
from solver.incremental import DEFAULT_INCREMENTAL
from solver.relations import pack,dense_pack,unpack
from experiments.run_structural import var,neg,conj,disj,xor,join

MODES=['checked','interfaces_full','interfaces_delta','interfaces_restart','proof_live','proof_restart']
STREAMS=['chain_append','tree_append','hub_append','local_edits','width_shift','proof_reuse']


def stream(name):
    changes=[]
    if name.endswith('_append'):
        old=0
        for n in [4,8,12,16,24,32,48]:
            parent=lambda i:i-1 if name=='chain_append' else (i-1)//2 if name=='tree_append' else 0
            changes.append(({f'edge{i}':xor(parent(i),i) for i in range(old+1,n+1)},[],True))
            old=n
    elif name=='local_edits':
        changes=[({**{f'edge{i}':xor(i-1,i) for i in range(1,33)},'start':var(0),'end':var(32)},[],True),
            ({'end':neg(var(32))},[],False),({},['end'],True),({'bridge':xor(0,32)},[],False),
            ({},['edge1'],True),({'bridge':neg(xor(0,32))},[],True),({'edge1':xor(0,1)},[],True),
            ({'edge16':neg(xor(15,16))},[],False),({},['bridge'],True)]
    elif name=='width_shift':
        base={f'e{i}':xor(i-1,i) for i in range(1,9)}
        clique=join([xor(i,j) for i in range(10,15) for j in range(10,i)])
        changes=[(base,[],True),({'wide':clique},[],False),({},['wide'],True),
                 ({'e9':xor(8,9)},[],True),({'wide':clique},[],False),({},['wide'],True),
                 ({'large_leaf':join([disj(var(i),var(i+1)) for i in range(15,20)])},[],True)]
    elif name=='proof_reuse':
        from solver.test_fast import cnf_bits
        core=cnf_bits([[(i,bool(mask&(1<<i))) for i in range(3)] for mask in range(8)])
        changes=[({'core':core},[],False)]+[({f'new{i}':xor(i,i+1)},[],False) for i in range(3,7)]
        changes += [({},['core'],True),({'core':neg(neg(core))},[],False)]
    else:raise ValueError(name)
    active={};cases=[]
    for i,(add,remove,expected) in enumerate(changes):
        for k in remove:del active[k]
        active.update(add)
        bits=join([active[k] for k in sorted(active)])
        cases.append(dict(stage=i,add=add,remove=remove,bits=bits,expected=expected))
    return cases


def storage(s):
    counts={t:s.db.execute('SELECT count(*) FROM '+t).fetchone()[0] for t in
        ['results','proofs','interface_nodes','interface_rows','expansion_states','knowledge_objects']}
    kinds=[dict(kind=r[0],objects=r[1],raw_bytes=r[2],payload_bytes=r[3]) for r in s.db.execute(
        'SELECT kind,count(*),sum(raw_bytes),sum(length(payload)) FROM knowledge_objects GROUP BY kind')]
    return dict(event='storage',counts=counts,kinds=kinds,
        input_archive_bytes=s.db.execute('SELECT coalesce(sum(length(bits)),0) FROM results').fetchone()[0],
        proof_archive_bytes=s.db.execute('SELECT coalesce(sum(length(certificate)),0) FROM proofs').fetchone()[0])


def worker(mode,name):
    with tempfile.TemporaryDirectory(prefix='oracle-interface-study-') as tmp:
        path=Path(tmp)/'results.sqlite3';s=None;state=None;blocked=False
        options=dict(backend='cadical',reuse_exact=False,query_timeout=3,timeout=3,
            interfaces=mode.startswith('interfaces'),incremental_proofs=mode.startswith('proof'))
        try:
            for case in stream(name):
                started=time.perf_counter_ns()
                row=dict(event='query',stage=case['stage'],expected=case['expected'],full_input_bytes=len(case['bits']))
                try:
                    if blocked:raise RuntimeError('Previous delta failed; dependent snapshot not executed')
                    setup=time.perf_counter_ns()
                    if s is None:s=PersistentSolver(path,**options)
                    row['setup_ns']=time.perf_counter_ns()-setup
                    if mode in ('interfaces_delta','interfaces_restart'):
                        row['input_bytes']=len(json.dumps(dict(base=state,add=case['add'],remove=case['remove']),separators=(',',':')).encode())
                        result=s.expand(state,add=case['add'],remove=case['remove']);state=result['state']
                    else:
                        row['input_bytes']=len(json.dumps(dict(bits=case['bits']),separators=(',',':')).encode())
                        result=s.solve(case['bits'],learn=False)
                    row.update(result=result,status='ok' if result['answer']==case['expected'] else 'wrong')
                    if sum(result['phase_ns'].values())!=result['wall_ns']:raise AssertionError('Nonpartitioned phase ledger')
                except Exception as error:
                    row.update(status='error',error=type(error).__name__+': '+str(error))
                    if mode in ('interfaces_delta','interfaces_restart'):blocked=True
                finally:
                    if mode.endswith('restart') and s is not None:s.close();s=None
                    row['elapsed_ns']=time.perf_counter_ns()-started
                    print(json.dumps(row),flush=True)
            if s is None:s=PersistentSolver(path,**options)
            record=storage(s)
            started=time.perf_counter_ns();s.close();s=None
            record['shutdown_ns']=time.perf_counter_ns()-started;record['database_bytes']=path.stat().st_size
            print(json.dumps(record),flush=True)
        finally:
            if s is not None:s.close()


def representation_study():
    rng=random.Random(1701);records=[]
    for width in [2,4,6,8,10,12]:
        for family in ['constant','parity','sparse','random']:
            rows=[False]*(1<<width)
            if family=='parity':rows=[bool(i.bit_count()%2) for i in range(1<<width)]
            if family=='sparse':rows[-1]=True
            if family=='random':rows=[bool(rng.randrange(2)) for _ in rows]
            started=time.perf_counter_ns();encoded=pack(rows);elapsed=time.perf_counter_ns()-started
            assert unpack(encoded,width)==rows
            size=lambda x:len(json.dumps(x,sort_keys=True,separators=(',',':')).encode())
            records.append(dict(width=width,family=family,rows=len(rows),encoding=encoded.get('encoding','dense'),
                payload_bytes=size(encoded),dense_bytes=size(dense_pack(rows)),construction_ns=elapsed))
    return records


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--worker',nargs=2)
    parser.add_argument('--output',type=Path,default=ROOT/'experiments/results/interfaces')
    args=parser.parse_args()
    if args.worker:worker(*args.worker);return
    args.output.mkdir(parents=True,exist_ok=False)
    inputs={name:stream(name) for name in STREAMS}
    (args.output/'inputs.json').write_text(json.dumps(inputs,indent=2)+'\n')
    runs=[]
    with (args.output/'runs.jsonl').open('w') as out:
        for name in STREAMS:
            for repeat in range(3):
                # Rotate mode order; one timed worker at a time.
                for mode in MODES[repeat:]+MODES[:repeat]:
                    started=time.perf_counter_ns()
                    try:
                        run=subprocess.run([sys.executable,__file__,'--worker',mode,name],capture_output=True,text=True,timeout=120)
                        row=dict(exit=run.returncode,records=[json.loads(l) for l in run.stdout.splitlines()],stderr=run.stderr)
                    except subprocess.TimeoutExpired as error:
                        output=error.stdout or b''
                        if isinstance(output,bytes):output=output.decode(errors='replace')
                        row=dict(exit=None,timeout=True,records=[json.loads(l) for l in output.splitlines() if l.endswith('}')],stderr=str(error))
                    row.update(stream=name,mode=mode,repeat=repeat,elapsed_ns=time.perf_counter_ns()-started)
                    runs.append(row);out.write(json.dumps(row)+'\n');out.flush()
                print(name,repeat,'complete',flush=True)
    summary=[]
    for name in STREAMS:
        for mode in MODES:
            group=[r for r in runs if r['stream']==name and r['mode']==mode]
            qs=[q for r in group for q in r['records'] if q['event']=='query']
            summary.append(dict(stream=name,mode=mode,queries=len(qs),statuses=dict(Counter(q['status'] for q in qs)),
                median_total_ms=statistics.median(sum(q['elapsed_ns'] for q in r['records'] if q['event']=='query')/1e6 for r in group),
                median_worker_ms=statistics.median(r['elapsed_ns']/1e6 for r in group),
                total_input_bytes=[sum(q['input_bytes'] for q in r['records'] if q['event']=='query' and 'input_bytes' in q) for r in group],
                storage=[r['records'][-1] for r in group if r['records'] and r['records'][-1]['event']=='storage']))
    (args.output/'summary.json').write_text(json.dumps(dict(runs=len(runs),summary=summary),indent=2)+'\n')
    (args.output/'representations.json').write_text(json.dumps(representation_study(),indent=2)+'\n')
    files=[DEFAULT_ENGINE,DEFAULT_INCREMENTAL,Path(__file__)]+list((ROOT/'solver').glob('*.py'))+list((ROOT/'formal/OracleMachines').glob('*Interface*.lean'))+[ROOT/'formal/OracleMachines/IncrementalProof.lean',ROOT/'formal/Solver.lean']
    fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    (args.output/'metadata.json').write_text(json.dumps(dict(host=platform.platform(),python=sys.version,
        query_timeout_seconds=3,interface_cap=3,mode_order='rotated by repetition; sequential workers',
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),fingerprints=fingerprints),indent=2)+'\n')
    print(json.dumps([dict(stream=s['stream'],mode=s['mode'],ms=round(s['median_total_ms'],2),statuses=s['statuses']) for s in summary],indent=2))

if __name__=='__main__':main()
