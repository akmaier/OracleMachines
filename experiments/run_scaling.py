#!/usr/bin/env python3
"""Sequential structural/public follow-up with equal logical archive caps.

Caps concern SQLite pages, not total RAM or WAL bytes. Every error remains in
the report. Historical studies and the user's live archive are never overwritten.
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
from experiments.run_interfaces import stream, storage
from experiments.run_structural import xor, var, neg, join
from experiments.run_expanded import workloads, encode_dimacs
from solver.persistent import PersistentSolver, DEFAULT_ENGINE
from solver.incremental import DEFAULT_INCREMENTAL
from solver.symbolic import BDD

MODES = ['checked', 'indexed_full', 'indexed_delta', 'symbolic_delta', 'adaptive', 'proof_live', 'proof_restart']


def cases_from_changes(changes):
    active, out = {}, []
    for i, (add, remove, expected) in enumerate(changes):
        for key in remove:del active[key]
        active.update(add)
        out.append(dict(stage=i, add=add, remove=remove, expected=expected,
                        bits=join([active[k] for k in sorted(active)])))
    return out


def inputs(archives):
    groups = {name:stream(name) for name in ['local_edits','width_shift','proof_reuse']}
    changes, old = [], 0
    for n in [8,16,32,48,64,96,128]:
        changes.append(({f'e{i}':xor(i-1,i) for i in range(old+1,n+1)},[],True))
        old=n
    groups['chain128'] = cases_from_changes(changes)
    base = {f'e{i}':xor(i-1,i) for i in range(1,65)}
    changes = [(base,[],True)]
    for i in range(8):
        changes.append(({'bridge':xor(i,64-i)},[],False))
        changes.append(({},['bridge'],True))
    groups['distant_edits'] = cases_from_changes(changes)
    source, public = workloads(archives)
    selected = []
    for name in ['satlib_uf50-218','satlib_uuf50-218','satlib_flat30-60','satlib_aim']:
        group = next(g for g in public if g['name']==name)
        chosen = group['cases'][:3] if name!='satlib_aim' else [group['cases'][0],group['cases'][-1]]
        for case in chosen:
            bits = encode_dimacs(case['dimacs'])
            selected.append(dict(stage=len(selected),add={'instance':bits},remove=[],bits=bits,
                                 expected=case['expected'],name=case['name'],sha256=case['file_sha256']))
    groups['public_satlib'] = selected
    # Shift within one chronological worker, including repeated cores and wide inputs.
    shift = [stream('proof_reuse')[0]]*3 + selected[:3] + selected[3:6] + [stream('proof_reuse')[0]]*3
    groups['distribution_shift'] = [dict(stage=i,add={'instance':c['bits']},remove=[],bits=c['bits'],expected=c['expected'])
                                    for i,c in enumerate(shift)]
    return groups,source


def worker(mode, cases, cap, timeout):
    with tempfile.TemporaryDirectory(prefix='oracle-scaling-') as directory:
        path=Path(directory)/'results.sqlite3'
        service=None;state=None;blocked=False
        options=dict(backend='cadical',reuse_exact=False,query_timeout=timeout,timeout=timeout,
            interfaces=mode.startswith('indexed'),symbolic=mode=='symbolic_delta',
            adaptive=mode=='adaptive',incremental_proofs=mode.startswith('proof'),max_archive_bytes=cap)
        try:
            for case in cases:
                start=time.perf_counter_ns()
                row=dict(event='query',stage=case['stage'],expected=case['expected'])
                try:
                    if blocked:raise RuntimeError('Previous delta failed; dependent snapshot not executed')
                    if service is None:service=PersistentSolver(path,**options)
                    if mode.endswith('delta'):
                        result=service.expand(state,add=case['add'],remove=case['remove']);state=result['state']
                    else:result=service.solve(case['bits'],learn=False)
                    if sum(result['phase_ns'].values())!=result['wall_ns']:raise AssertionError('Unpartitioned ledger')
                    row.update(result=result,status='ok' if result['answer']==case['expected'] else 'wrong')
                except Exception as error:
                    row.update(status='error',error=type(error).__name__+': '+str(error))
                    if mode.endswith('delta'):blocked=True
                finally:
                    if mode.endswith('restart') and service is not None:service.close();service=None
                    row['elapsed_ns']=time.perf_counter_ns()-start
                    print(json.dumps(row),flush=True)
            if service is None:service=PersistentSolver(path,**options)
            summary=storage(service);summary['usage']=service.archive_usage()
            service.close();service=None
            summary['closed_database_bytes']=path.stat().st_size
            print(json.dumps(summary),flush=True)
        finally:
            if service is not None:service.close()


def symbolic_scaling():
    results=[]
    for width in [8,16,32,64,128]:
        manager=BDD();start=time.perf_counter_ns();root=0
        for v in range(width):
            atom=manager.node(v,0,1)
            root=manager.apply('or',manager.apply('and',root,manager.negate(atom)),
                manager.apply('and',manager.negate(root),atom))
        payload=manager.dump(root)
        assert manager.exists(root,width//2)==1
        assert manager.evaluate(root,{v:v==0 for v in range(width)})
        results.append(dict(width=width,implicit_table_rows=2**width,
            retained_nodes=len(payload['nodes']),allocated_nodes=len(manager.nodes),operations=manager.work,
            serialized_bytes=len(json.dumps(payload,separators=(',',':')).encode()),
            construction_and_projection_ns=time.perf_counter_ns()-start))
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker',choices=MODES)
    p.add_argument('--archives',type=Path)
    p.add_argument('--output',type=Path,default=ROOT/'experiments/results/scaling')
    p.add_argument('--repeats',type=int,default=3)
    p.add_argument('--archive-cap',type=int,default=8*1024**2)
    p.add_argument('--timeout',type=float,default=5)
    args=p.parse_args()
    if args.worker:worker(args.worker,json.load(sys.stdin),args.archive_cap,args.timeout);return
    if args.archives is None or args.repeats<1:p.error('Supply archives and positive repetitions')
    args.output.mkdir(parents=True,exist_ok=False)
    groups,sources=inputs(args.archives)
    (args.output/'inputs.json').write_text(json.dumps(groups,separators=(',',':'))+'\n')
    all_runs=[]
    with (args.output/'runs.jsonl').open('w') as log:
        for name,cases in groups.items():
            for repeat in range(args.repeats):
                for mode in MODES[repeat%len(MODES):]+MODES[:repeat%len(MODES)]:
                    start=time.perf_counter_ns()
                    command=[sys.executable,__file__,'--worker',mode,'--archive-cap',str(args.archive_cap),'--timeout',str(args.timeout)]
                    try:
                        completed=subprocess.run(command,input=json.dumps(cases),capture_output=True,text=True,
                            timeout=args.timeout*len(cases)+30)
                        row=dict(exit=completed.returncode,records=[json.loads(l) for l in completed.stdout.splitlines()],stderr=completed.stderr)
                    except subprocess.TimeoutExpired as error:
                        output=error.stdout or b''
                        if isinstance(output,bytes):output=output.decode(errors='replace')
                        row=dict(exit=None,records=[json.loads(l) for l in output.splitlines() if l.endswith('}')],stderr='Worker timeout')
                    row.update(stream=name,mode=mode,repeat=repeat,planned=len(cases),elapsed_ns=time.perf_counter_ns()-start)
                    log.write(json.dumps(row)+'\n');log.flush();all_runs.append(row)
                print(name,repeat,'complete',flush=True)
    summary=[]
    for name in groups:
        for mode in MODES:
            runs=[r for r in all_runs if r['stream']==name and r['mode']==mode]
            queries=[q for r in runs for q in r['records'] if q['event']=='query']
            times=[q['elapsed_ns']/1e6 for q in queries]
            summary.append(dict(stream=name,mode=mode,planned=len(groups[name])*args.repeats,
                statuses=dict(Counter(q['status'] for q in queries)),
                missing=len(groups[name])*args.repeats-len(queries),
                median_stream_ms=statistics.median(sum(q['elapsed_ns'] for q in r['records'] if q['event']=='query')/1e6 for r in runs),
                median_query_ms=statistics.median(times) if times else None,
                min_stream_ms=min(sum(q['elapsed_ns'] for q in r['records'] if q['event']=='query')/1e6 for r in runs),
                max_stream_ms=max(sum(q['elapsed_ns'] for q in r['records'] if q['event']=='query')/1e6 for r in runs),
                storage=[r['records'][-1] for r in runs if r['records'] and r['records'][-1]['event']=='storage']))
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (args.output/'symbolic.json').write_text(json.dumps(symbolic_scaling(),indent=2)+'\n')
    files=[DEFAULT_ENGINE,DEFAULT_INCREMENTAL,Path(__file__)]+list((ROOT/'solver').glob('*.py'))+[ROOT/'formal/Solver.lean',ROOT/'formal/OracleMachines/Scaling.lean']
    metadata=dict(host=platform.platform(),python=sys.version,sources=sources,archive_page_cap=args.archive_cap,
        query_timeout=args.timeout,repeats=args.repeats,whole_process_memory_bound=False,
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip(),
        fingerprints={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files})
    (args.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps([dict(stream=s['stream'],mode=s['mode'],ms=round(s['median_stream_ms'],2),statuses=s['statuses']) for s in summary],indent=2))


if __name__=='__main__':main()
