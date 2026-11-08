#!/usr/bin/env python3
"""Diagnostic cube-substitution prototype; not a production or Lean-checked path.

A cube is a tuple of fixed bits / None (free coordinates). None as the entire
cube denotes the empty boundary. Reject rows involving free old coordinates or
more than one new coordinate; the accepted case needs no elimination. Exhaustive
small frontiers check every returned summary, including empty and free cases.
"""
import argparse
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.affine_reference import flattened_sat
from solver.affine_growth import AffineGrowth


class Unsupported(ValueError):
    pass


def advance_cube(width,cube,rows):
    AffineGrowth.validate_equations(width,rows)
    if cube is None:return None
    if len(cube)!=width or any(x is not None and type(x) is not bool for x in cube):
        raise ValueError('Invalid cube')
    fresh=[None]*width
    for row in rows:
        value=row['rhs'];new=[]
        for i,coefficient in enumerate(row['coefficients']):
            if not coefficient:continue
            if i<width:
                if cube[i] is None:raise Unsupported('Free old coordinate requires a richer summary')
                value^=cube[i]
            else:new.append(i-width)
        if len(new)>1:raise Unsupported('Coupled new coordinates require a richer summary')
        if not new:
            if value:return None
        else:
            i=new[0]
            if fresh[i] is not None and fresh[i]!=value:return None
            fresh[i]=value
    return tuple(fresh)


def members(width,cube):
    if cube is None:return set()
    return {v for v in itertools.product((False,True),repeat=width)
            if all(x is None or x==v[i] for i,x in enumerate(cube))}


def frontier(width,cube,rows):
    return {v for v in itertools.product((False,True),repeat=width)
            if any(all(sum(c and x for c,x in zip(r['coefficients'],u+v))%2==r['rhs'] for r in rows)
                   for u in members(width,cube))}


def validate_prototype():
    counts=dict(cases=0,accepted=0,declined=0)
    def check(width,cube,rows):
        counts['cases']+=1
        try:result=advance_cube(width,cube,rows)
        except Unsupported:counts['declined']+=1;return
        assert members(width,result)==frontier(width,cube,rows),(width,cube,rows,result)
        counts['accepted']+=1
    for width in (1,2):
        rows=[dict(coefficients=list(bits[:-1]),rhs=bits[-1])
              for bits in itertools.product((False,True),repeat=2*width+1)]
        batches=[[]]+[[r] for r in rows]+[[r,s] for r in rows for s in rows]
        for cube in [None,*itertools.product((None,False,True),repeat=width)]:
            for batch in batches:check(width,cube,batch)
    rng=random.Random(1108)
    for _ in range(1000):
        cube=None if rng.randrange(10)==0 else tuple(rng.choice((None,False,True)) for _ in range(3))
        rows=[dict(coefficients=[bool(rng.getrandbits(1)) for _ in range(6)],rhs=bool(rng.getrandbits(1)))
              for _ in range(rng.randrange(7))]
        check(3,cube,rows)
    return counts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Preserve the prior diagnostic')
    checks=validate_prototype()
    source=ROOT/'experiments/results/affine-resident-metadata/matched'
    packed=(source/'inputs.json.gz').read_bytes();inputs=json.loads(gzip.decompress(packed))
    benchmark=json.loads((source/'comparison.json').read_text());cases=[]
    for key,events in inputs.items():
        width=int(key.split('-')[0]);states=[];records=[]
        for index,event in enumerate(events):
            old=(None,)*width if event['parent']<0 else states[event['parent']]
            successor=advance_cube(width,old,event['rows']);states.append(successor)
            kind='empty' if successor is None else ('point' if all(x is not None for x in successor)
                                                  else 'free' if all(x is None for x in successor) else 'partial')
            expected=successor is not None
            assert expected==event['expected']==flattened_sat(width,event['batches'])
            records.append(dict(index=index,parent_kind='empty' if old is None else 'point' if all(x is not None for x in old) else 'cube',
                                successor_kind=kind,successor=successor,source_coefficient_cells=len(event['rows'])*(2*width+1)))
        prior=next(r for r in benchmark['runs'] if r['width']==width and r['pattern']==key.split('-')[1] and r['mode']=='metadata')
        cases.append(dict(case=key,accepted=len(records),point_successors=sum(r['successor_kind']=='point' for r in records),
            source_coefficient_cells=sum(r['source_coefficient_cells'] for r in records),
            current_executed_reference_cells=sum(r['updates']['executed_reference_cells'] for r in prior['records']),
            records=records))
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        validation=checks,cases=cases,input_sha256=hashlib.sha256(packed).hexdigest(),
        prototype_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limitations=['Diagnostic only; no native integration, recognizer theorem or matched runtime measurement',
            'All supported small cases have complete frontier checks; larger cases compare decision to independent full-history elimination',
            'Declining a case must dispatch to the general checked algorithm, never label it SAT or UNSAT',
            'Source coefficient payload is not a complete work counter and is not comparable to wall time',
            'Current repeated and novel streams have point frontiers on regular steps and do not cover general correlated affine boundaries'])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(validation=checks,cases=[{k:v for k,v in c.items() if k!='records'} for c in cases])))


if __name__=='__main__':main()
