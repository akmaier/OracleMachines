#!/usr/bin/env python3
"""Observe exact expansion-input repetition without installing a result cache.

The input is a previously frozen comparison stream. Summaries come from the
checked native solver, and original-system decisions are checked independently.
No timing or net-savings claim follows from counting identical kernel inputs.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.affine_reference import flattened_sat
from solver.persistent import PersistentSolver,DEFAULT_ENGINE


def token(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def normalized_batch(rows):
    # Preserve row contents; only exact duplicates and order are ignored.
    return sorted(set(tuple(row['coefficients'])+(row['rhs'],) for row in rows))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,default=ROOT/'experiments/results/history-retention/comparison-inputs.json.gz')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise ValueError('Preserve earlier evidence; choose a new output')
    cases=json.loads(gzip.decompress(args.inputs.read_bytes()))
    cache_dir=ROOT/'solver/.cache'/('affine-patterns-'+str(time.time_ns()));cache_dir.mkdir(parents=True)
    results=[]
    for name,events in cases.items():
        width=int(name.split('-')[0]);cache=cache_dir/(name+'.sqlite3')
        states=[];records=[];exact_seen={};normalized_seen={}
        with PersistentSolver(cache,native_affine_versions=4) as service:
            initial=service.affine_grow(width,summary=True)
            for index,event in enumerate(events):
                parent=initial if event['parent']<0 else states[event['parent']]
                original=dict(width=width,summary=parent['summary'],equations=event['rows'])
                normalized=dict(original,equations=normalized_batch(event['rows']))
                exact_key,normalized_key=token(original),token(normalized)
                result=service.affine_grow(base=parent['state'],equations=event['rows'],summary=True)
                assert result['answer']==event['expected']==flattened_sat(width,event['batches'])
                assert result['reference_cell_charge']<=result['reference_cell_budget']
                records.append(dict(index=index,parent=event['parent'],state=result['state'],parent_state=parent['state'],
                    parent_summary=parent['summary'],equations=event['rows'],summary=result['summary'],
                    answer=result['answer'],steps=result['steps'],exact_kernel_key=exact_key,
                    normalized_batch_key=normalized_key,exact_previous=exact_seen.get(exact_key),
                    normalized_previous=normalized_seen.get(normalized_key),
                    rows=len(event['rows']),unique_rows=len(normalized['equations']),
                    reference_cell_charge=result['reference_cell_charge'],reference_cell_budget=result['reference_cell_budget']))
                exact_seen.setdefault(exact_key,index);normalized_seen.setdefault(normalized_key,index)
                states.append(result)
        results.append(dict(case=name,width=width,events=len(records),
            distinct_versions=len(set(r['state'] for r in records)),
            exact_repeated_kernel_inputs=sum(r['exact_previous'] is not None for r in records),
            normalized_repeated_kernel_inputs=sum(r['normalized_previous'] is not None for r in records),
            duplicate_input_rows=sum(r['rows']-r['unique_rows'] for r in records),
            repeated_kernel_reference_charge=sum(r['reference_cell_charge'] for r in records if r['exact_previous'] is not None),
            total_reference_charge=sum(r['reference_cell_charge'] for r in records),
            retained_database=str(cache),database_bytes=cache.stat().st_size,records=records))
    report=dict(runtime_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        input_path=str(args.inputs),input_sha256=hashlib.sha256(args.inputs.read_bytes()).hexdigest(),
        fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [Path(__file__).resolve(),ROOT/'experiments/affine_reference.py',ROOT/'solver/affine_growth.py',DEFAULT_ENGINE]},
        cases=results,limitations=[
            'Observation only: no semantic-kernel cache is installed and no net speedup is measured',
            'Keys use exact ordered parent summaries; only batch duplicates/order are normalized in the second key',
            'Canonical row-space equivalence, renaming and low-rank changes are not detected',
            'A cache must rebind the cached relation to each new original history and preserve all source versions',
            'Lookup, canonicalization, checking, storage and eviction costs must be charged',
            'Synthetic affine streams do not establish general CNF compression'])
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps([{k:v for k,v in case.items() if k!='records'} for case in results]))


if __name__=='__main__':main()
