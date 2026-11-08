#!/usr/bin/env python3
"""Matched exact-kernel cache ablation, preserving original histories and results.

Both modes use one binary. Zero slots bypass hashing and lookup. Sequential,
rotated repetitions use fresh processes/databases and include service startup,
all append calls, persistence, and shutdown in reported elapsed totals.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.affine_reference import flattened_sat
from experiments.compare_affine_growth import stream
from solver.persistent import PersistentSolver,DEFAULT_ENGINE

MODES=('disabled','cached')
METRICS=('kernel_hits','kernel_misses','kernel_evictions','kernel_key_cells',
         'kernel_compare_cell_bound','executed_reference_cells','uncached_reference_cells')


def worker(config,path):
    width=config['width'];events=stream(width,config['pattern'],config['steps'])
    cache_dir=Path(config['cache_dir']);cache_dir.mkdir(parents=True,exist_ok=True)
    cache=cache_dir/(path.stem+'.sqlite3')
    if cache.exists():raise ValueError('Refusing to overwrite a retained database')
    # The independent oracle is outside the service timing and runs before it.
    for event in events:assert flattened_sat(width,event['batches'])==event['expected']
    began=time.perf_counter_ns()
    service=PersistentSolver(cache,reuse_exact=False,native_affine_versions=4,
                             affine_kernel_slots=64 if config['mode']=='cached' else 0,query_timeout=60,
                             affine_deduplicate=False,affine_share_batches=False)
    setup=time.perf_counter_ns()-began
    states=[];records=[];totals=dict.fromkeys(METRICS,0)
    try:
        for index,event in enumerate(events):
            began=time.perf_counter_ns()
            base=None if event['parent']<0 else states[event['parent']]
            result=service.affine_grow(width if base is None else None,event['rows'],base=base)
            elapsed=time.perf_counter_ns()-began
            assert result['answer']==event['expected']
            assert result['steps']==len(event['batches'])
            assert result['affine_updates']['resident_versions']<=4
            states.append(result['state'])
            for metric in METRICS:totals[metric]+=result['affine_updates'][metric]
            records.append(dict(index=index,state=result['state'],steps=result['steps'],
                answer=result['answer'],expected=event['expected'],wall_ns=elapsed,
                service_wall_ns=result['wall_ns'],phase_ns=result['phase_ns'],
                service_events=result['service_events'],affine_updates=result['affine_updates'],
                creation_reference_cells=result['reference_cell_charge'],
                creation_uncached_cells=result['uncached_reference_cell_charge'],
                storage=result['storage']))
        began=time.perf_counter_ns()
        native=service._request(dict(mode='affine_stats'))
        archive_rows=service.db.execute('SELECT count(*) FROM affine_states').fetchone()[0]
        assert archive_rows==len(events)
        assert native['kernel_cache_entries']<=native['kernel_cache_slots']
        audit=time.perf_counter_ns()-began
    finally:
        began=time.perf_counter_ns();service.close();shutdown=time.perf_counter_ns()-began
    record=dict(**config,setup_ns=setup,shutdown_ns=shutdown,audit_ns=audit,records=records,
        total_ns=setup+shutdown+sum(r['wall_ns'] for r in records),kernel_totals=totals,
        complete=len(records)==len(events),native_final=native,archive_rows=archive_rows,
        retained_database=str(cache),database_bytes=cache.stat().st_size)
    path.write_text(json.dumps(record,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repetitions',type=int,default=5)
    parser.add_argument('--cache-root',type=Path)
    parser.add_argument('--worker',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:worker(json.loads(args.worker),args.output);return
    if args.repetitions<1:raise ValueError('At least one repetition required')
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    if (out/'comparison.json').exists():raise ValueError('Preserve earlier evidence; choose a new output')
    cases=[(w,p,32 if w==32 else 16) for w in (2,8,16,32) for p in ('repeated','novel')]
    inputs={f'{w}-{p}':stream(w,p,steps) for w,p,steps in cases}
    packed=gzip.compress(json.dumps(inputs,separators=(',',':')).encode(),mtime=0)
    (out/'inputs.json.gz').write_bytes(packed)
    cache_dir=(args.cache_root or ROOT/'solver/.cache'/('affine-kernels-'+str(time.time_ns()))).resolve()
    runs=[]
    for rep in range(args.repetitions):
        for width,pattern,steps in cases:
            order=MODES[rep%2:]+MODES[:rep%2]
            for mode in order:
                config=dict(width=width,pattern=pattern,steps=steps,mode=mode,repetition=rep,cache_dir=str(cache_dir))
                path=out/f'{width}-{pattern}-{mode}-{rep}.json'
                if path.exists():raise ValueError('Existing worker output: '+str(path))
                subprocess.run([sys.executable,str(Path(__file__).resolve()),'--output',str(path),
                                '--worker',json.dumps(config)],check=True,timeout=300)
                row=json.loads(path.read_text());runs.append(row)
                print(json.dumps(dict(run=len(runs),**config,total_ms=row['total_ns']/1e6)),flush=True)
    summary=[]
    for width,pattern,steps in cases:
        entry=dict(width=width,pattern=pattern,expansions=steps+2,modes={})
        for mode in MODES:
            chosen=[r for r in runs if (r['width'],r['pattern'],r['mode'])==(width,pattern,mode)]
            times=[r['total_ns'] for r in chosen]
            assert all(r['kernel_totals']==chosen[0]['kernel_totals'] for r in chosen)
            entry['modes'][mode]=dict(median_total_ns=statistics.median(times),min_total_ns=min(times),
                max_total_ns=max(times),kernel_totals=chosen[0]['kernel_totals'])
        off,on=[entry['modes'][m]['median_total_ns'] for m in MODES]
        entry['median_speedup']=off/on
        entry['median_reduction_fraction']=1-on/off
        summary.append(entry)
    paths=[Path(__file__).resolve(),ROOT/'experiments/compare_affine_growth.py',ROOT/'experiments/affine_reference.py',
           ROOT/'solver/affine_growth.py',ROOT/'solver/persistent.py',DEFAULT_ENGINE]
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        platform=platform.platform(),python=sys.version,repetitions=args.repetitions,
        fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        input_sha256=hashlib.sha256(packed).hexdigest(),summary=summary,runs=runs,
        protocol='Same binary; fresh process/database; sequential rotated modes; four resident versions; '
                 'setup, native configuration, decoding, hashing, comparison, elimination, archival and shutdown charged. '
                 'Independent correctness oracle and final inspection excluded, inspection reported separately.',
        limitations=['Synthetic affine families; five repetitions are descriptive, not a significance test',
                     'Reference coefficients and key scans are separate partial ledgers, not total machine work',
                     'Exact ordered equality only; no canonicalization, low-rank update or durable kernel certificate',
                     'Direct-mapped collisions can remove useful entries; no universal speedup or unrestricted SAT claim'])
    (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
