#!/usr/bin/env python3
"""Preserve affine append evidence, independent full-system checks and restart.
This validates the restricted mechanism; it is not a solver speed comparison.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.affine_reference import equation,flattened_sat
from solver.persistent import PersistentSolver,DEFAULT_CACHE


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache',type=Path,default=DEFAULT_CACHE)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    report_path=args.output/'growth.json'
    if report_path.exists():raise ValueError('Choose a new output; existing evidence is immutable')
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                engine_sha256=hashlib.sha256((ROOT/'formal/.lake/build/bin/oracleSolver').read_bytes()).hexdigest(),
                seed=2403,comparative_speed_claim=False,records=[],restarts=[])
    inputs={};finals=[];rng=random.Random(report['seed'])
    def record(kind,result,width,batches):
        expected=flattened_sat(width,batches)
        assert result['answer']==expected,(width,len(batches),kind)
        assert result['summary_rows']<=width+1
        assert result['reference_cell_charge']<=result['reference_cell_budget']
        assert result['steps']==len(batches)
        keys=('state','answer','width','steps','summary_rows','summary_cells','summary_cell_bound',
              'reference_cell_charge','reference_cell_budget','counted_complete','wall_ns','phase_ns',
              'service_events','affine_updates','service_cpu_ns','service_peak_rss_bytes')
        report['records'].append(dict(kind=kind,expected=expected,**{key:result[key] for key in keys}))
        inputs[result['state']]=s.affine_growth.store.get(result['state'],'affine_version')
    with PersistentSolver(args.cache,query_timeout=60) as s:
        report['archive_before']=s.archive_usage()
        for width in (2,8,32,64):
            state=s.affine_grow(width);batches=[]
            record('initial',state,width,batches)
            values=[bool(i%2) for i in range(width)]
            for step in range(64):
                if step==0:rows=[equation(width,(width+i,),values[i]) for i in range(width)]
                else:
                    permutation=list(range(width));rng.shuffle(permutation)
                    rhs=[bool(rng.getrandbits(1)) for _ in range(width)]
                    rows=[equation(width,(i,width+permutation[i]),rhs[i]) for i in range(width)]
                    successor=[False]*width
                    for i in range(width):successor[permutation[i]]=values[i]^rhs[i]
                    values=successor
                batches=batches+[rows]
                state=s.affine_grow(base=state['state'],equations=rows)
                record('append',state,width,batches)
            finals.append((state['state'],width,batches,True))
            negative_rows=[equation(width,(0,),not values[0])]
            negative=s.affine_grow(base=state['state'],equations=negative_rows)
            record('contradict_previous_boundary',negative,width,batches+[negative_rows])
            finals.append((negative['state'],width,batches+[negative_rows],False))
            branch=s.affine_grow(base=state['state'],equations=[])
            record('unconstrained_fresh_branch',branch,width,batches+[[]])
            finals.append((branch['state'],width,batches+[[]],True))
            record('retained_parent',s.affine_grow(base=state['state']),width,batches)
        report['archive_after']=s.archive_usage()
        report['affine_state_rows']=s.db.execute('SELECT count(*) FROM affine_states').fetchone()[0]
    with PersistentSolver(args.cache,query_timeout=60) as s:
        for token,width,batches,expected in finals:
            result=s.affine_grow(base=token)
            assert result['answer']==expected==flattened_sat(width,batches)
            report['restarts'].append(dict(state=token,answer=result['answer'],steps=result['steps'],
                                           wall_ns=result['wall_ns'],updates=result['affine_updates'],
                                           service_events=result['service_events']))
    raw=json.dumps(inputs,separators=(',',':')).encode()
    packed=gzip.compress(raw,mtime=0)
    (args.output/'inputs.json.gz').write_bytes(packed)
    report['inputs']=dict(file='inputs.json.gz',raw_bytes=len(raw),packed_bytes=len(packed),
                          sha256=hashlib.sha256(packed).hexdigest())
    report['completed_ns']=time.time_ns()
    report['independently_checked']=len(report['records'])+len(report['restarts'])
    report_path.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(records=len(report['records']),restarts=len(report['restarts']),
                         checked=report['independently_checked'],affine_state_rows=report['affine_state_rows'],
                         input_packed_bytes=len(packed))))


if __name__=='__main__':main()
