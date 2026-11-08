#!/usr/bin/env python3
"""Matched affine residency/reconstruction/restart and checked-CDCL study.

Fresh process/database per run; sequential rotated repetitions. Every mode sees
the same original equation histories and retains completed results. Full Gaussian
elimination is an independent correctness oracle, not a certified timing rival.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.affine_reference import equation,flattened_sat
from experiments.run_expanded import encode_dimacs,dimacs
from solver.persistent import PersistentSolver,DEFAULT_ENGINE,find_cadical

MODES=('resident','replay_each','restart_each','checked_cdcl')


def stream(width,pattern,steps=16):
    rng=random.Random(3200+width);values=[bool(i%2) for i in range(width)]
    batches=[];events=[]
    for step in range(steps):
        if step==0:rows=[equation(width,(width+i,),values[i]) for i in range(width)]
        else:
            order=list(range(width))
            if pattern=='novel':rng.shuffle(order)
            new=[False]*width;rows=[]
            for i in range(width):
                old=[i] if pattern=='repeated' else list(dict.fromkeys([i,rng.randrange(width)]))
                rhs=False if pattern=='repeated' else bool(rng.getrandbits(1))
                new[order[i]]=bool(sum(values[j] for j in old)%2)^rhs
                row=equation(width,old+[width+order[i]],rhs)
                rows.append(row)
                if pattern=='repeated':rows.append(row.copy())
            values=new
        batches=batches+[rows]
        events.append(dict(parent=len(events)-1,rows=rows,batches=batches,expected=True))
    parent=len(events)-1
    contradiction=[equation(width,(0,),not values[0])]
    events.append(dict(parent=parent,rows=contradiction,batches=batches+[contradiction],expected=False))
    events.append(dict(parent=parent,rows=[],batches=batches+[[]],expected=True))
    return events


def source_cnf(width,batches):
    """Linear Tseitin XOR encoding; auxiliary variables follow all source ones."""
    clauses=[];next_variable=width*(len(batches)+1)
    for step,batch in enumerate(batches):
        for row in batch:
            terms=[step*width+i+1 for i,value in enumerate(row['coefficients']) if value]
            if not terms:
                if row['rhs']:clauses.append([])
            elif len(terms)==1:clauses.append([terms[0] if row['rhs'] else -terms[0]])
            elif len(terms)==2:
                x,y=terms
                clauses.extend([[x,y],[-x,-y]] if row['rhs'] else [[-x,y],[x,-y]])
            else:
                x=terms[0]
                for y in terms[1:]:
                    next_variable+=1;z=next_variable
                    clauses.extend([[x,y,-z],[x,-y,z],[-x,y,z],[-x,-y,-z]])
                    x=z
                clauses.append([x if row['rhs'] else -x])
    return clauses,next_variable


def worker(config,path):
    width,mode=config['width'],config['mode'];events=stream(width,config['pattern'])
    cache_dir=Path(config['cache_dir']);cache_dir.mkdir(parents=True,exist_ok=True)
    cache=cache_dir/(path.stem+'.sqlite3');records=[];states=[]
    if cache.exists():raise ValueError('Refusing to overwrite a retained run database')
    def start():
        return PersistentSolver(cache,backend='cadical' if mode=='checked_cdcl' else 'lean',
              reuse_exact=False,native_affine_versions=4,query_timeout=30)
    began=time.perf_counter_ns();service=start();setup=time.perf_counter_ns()-began
    for index,event in enumerate(events):
        assert flattened_sat(width,event['batches'])==event['expected']
        began=time.perf_counter_ns();converted=0
        try:
            if service is None:service=start()
            if mode=='checked_cdcl':
                cnf_start=time.perf_counter_ns()
                clauses,n=source_cnf(width,event['batches'])
                bits=encode_dimacs(dimacs(clauses,n))
                converted=time.perf_counter_ns()-cnf_start
                result=service.solve(bits,learn=False)
            else:
                if mode=='replay_each' and hasattr(service,'affine_growth'):service.affine_growth.invalidate()
                base=None if event['parent']<0 else states[event['parent']]
                result=service.affine_grow(width if base is None else None,event['rows'],base=base)
                states.append(result['state'])
            assert result['answer']==event['expected']
            if mode=='restart_each':service.close();service=None
            elapsed=time.perf_counter_ns()-began
            records.append(dict(index=index,answer=result['answer'],expected=event['expected'],wall_ns=elapsed,
                conversion_ns=converted,service_wall_ns=result['wall_ns'],phase_ns=result['phase_ns'],
                service_events=result['service_events'],affine_updates=result.get('affine_updates'),
                reference_cell_charge=result.get('reference_cell_charge'),source=result.get('source'),backend=result.get('backend'),storage=result['storage'],error=None))
        except Exception as error:
            records.append(dict(index=index,expected=event['expected'],wall_ns=time.perf_counter_ns()-began,
                                error=type(error).__name__+': '+str(error)))
            break
    began=time.perf_counter_ns()
    if service is not None:service.close()
    shutdown=time.perf_counter_ns()-began
    record=dict(**config,setup_ns=setup,shutdown_ns=shutdown,records=records,
                total_ns=setup+shutdown+sum(r['wall_ns'] for r in records),
                complete=len(records)==len(events) and all(r['error'] is None for r in records),
                retained_database=str(cache),database_bytes=cache.stat().st_size)
    path.write_text(json.dumps(record,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repetitions',type=int,default=3)
    parser.add_argument('--cache-root',type=Path)
    parser.add_argument('--worker',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:
        worker(json.loads(args.worker),args.output);return
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    if (out/'comparison.json').exists():raise ValueError('Preserve earlier evidence; choose a new output')
    cases=[(width,pattern) for width in (2,8,16) for pattern in ('repeated','novel')]
    inputs={f'{w}-{p}':stream(w,p) for w,p in cases}
    packed=gzip.compress(json.dumps(inputs,separators=(',',':')).encode(),mtime=0)
    (out/'comparison-inputs.json.gz').write_bytes(packed)
    records=[]
    cache_dir=(args.cache_root or ROOT/'solver/.cache'/('affine-comparison-'+str(time.time_ns()))).resolve()
    for rep in range(args.repetitions):
        for width,pattern in cases:
            order=MODES[rep%len(MODES):]+MODES[:rep%len(MODES)]
            for mode in order:
                config=dict(width=width,pattern=pattern,mode=mode,repetition=rep,cache_dir=str(cache_dir))
                path=out/f'{width}-{pattern}-{mode}-{rep}.json'
                if path.exists():raise ValueError('Existing worker output: '+str(path))
                before=time.perf_counter_ns()
                subprocess.run([sys.executable,str(Path(__file__).resolve()),'--output',str(path),'--worker',json.dumps(config)],check=True,timeout=300)
                row=json.loads(path.read_text());row['worker_total_ns']=time.perf_counter_ns()-before
                records.append(row)
                print(json.dumps(dict(run=len(records),**config,complete=row['complete'])),flush=True)
    summary=[]
    for width,pattern in cases:
        for mode in MODES:
            selected=[r for r in records if (r['width'],r['pattern'],r['mode'])==(width,pattern,mode)]
            complete=[r['total_ns'] for r in selected if r['complete']]
            summary.append(dict(width=width,pattern=pattern,mode=mode,runs=len(selected),completed=len(complete),
                                median_total_ns=statistics.median(complete) if complete else None))
    fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
                  [Path(__file__).resolve(),ROOT/'experiments/affine_reference.py',ROOT/'experiments/run_expanded.py',
                   ROOT/'solver/affine_growth.py',ROOT/'solver/persistent.py',DEFAULT_ENGINE]}
    cadical=find_cadical()
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                platform=platform.platform(),python=sys.version,repetitions=args.repetitions,
                fingerprints=fingerprints,cadical_path=str(cadical),
                cadical_sha256=hashlib.sha256(cadical.read_bytes()).hexdigest(),
                input_sha256=hashlib.sha256(packed).hexdigest(),summary=summary,runs=records,
                protocol='Fresh process/database per run; sequential rotated modes; identical original histories; all results retained; setup/conversion/replay/shutdown charged',
                limitations=['Synthetic affine families only','No theorem about hardware time or total memory',
                    'Python CNF conversion is tested, not Lean-refined',
                    'Checked-CDCL comparison includes different encoding and certification costs',
                    'replay_each uses the same delta input and archive but reconstructs its full parent'])
    (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
