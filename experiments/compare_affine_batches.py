#!/usr/bin/env python3
"""Matched ablation of certified duplicate removal and adaptive batch sharing."""
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
from experiments.compare_affine_growth import stream
from experiments.affine_reference import flattened_sat
from solver.persistent import PersistentSolver,DEFAULT_ENGINE

MODES=('baseline','normalize','share','combined')


def workload(width,pattern):
    steps=32 if width==32 and pattern!='multiplicity' else 16
    events=stream(width,'repeated' if pattern=='multiplicity' else pattern,steps)
    if pattern=='multiplicity':
        batches=[]
        for i,event in enumerate(events):
            parent=event['parent']
            rows=event['rows']*(i+1) if 0<i<steps else event['rows']
            history=[] if parent<0 else batches[parent]
            batches.append(history+[rows])
            event['rows']=rows;event['batches']=batches[-1]
    return events


def worker(config,path):
    events=workload(config['width'],config['pattern'])
    for event in events:assert flattened_sat(config['width'],event['batches'])==event['expected']
    cache=Path(config['cache_dir'])/(path.stem+'.sqlite3');cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.exists():raise ValueError('Refusing to overwrite a run database')
    normalize=config['mode'] in ('normalize','combined');share=config['mode'] in ('share','combined')
    began=time.perf_counter_ns()
    service=PersistentSolver(cache,native_affine_versions=4,affine_kernel_slots=64,query_timeout=60,
                             affine_deduplicate=normalize,affine_share_batches=share)
    setup=time.perf_counter_ns()-began;states=[];records=[]
    try:
        for i,event in enumerate(events):
            began=time.perf_counter_ns()
            parent=event['parent'];base=None if parent<0 else states[parent]
            result=service.affine_grow(config['width'] if base is None else None,event['rows'],base=base)
            elapsed=time.perf_counter_ns()-began
            assert result['answer']==event['expected'] and result['steps']==len(event['batches'])
            assert result['affine_updates']['resident_versions']<=4
            states.append(result['state'])
            records.append(dict(index=i,state=result['state'],answer=result['answer'],steps=result['steps'],
                wall_ns=elapsed,phase_ns=result['phase_ns'],service_events=result['service_events'],
                updates=result['affine_updates'],storage=result['storage'],
                service_peak_rss_bytes=result['service_peak_rss_bytes']))
        began=time.perf_counter_ns()
        native=service._request(dict(mode='affine_stats'))
        objects=[dict(kind=k,objects=n,raw_bytes=r,packed_bytes=p) for k,n,r,p in service.db.execute(
                 'SELECT kind,count(*),sum(raw_bytes),sum(length(payload)) FROM knowledge_objects GROUP BY kind')]
        codecs=dict(service.db.execute("SELECT codec,count(*) FROM knowledge_objects WHERE kind='affine_version' GROUP BY codec"))
        count=service.db.execute('SELECT count(*) FROM affine_states').fetchone()[0];assert count==len(events)
        # Original ordered source is recovered byte-for-byte at the value level,
        # including every duplicate, even when the stored encoding is a reference.
        for event,state in zip(events,states):
            original=service.affine_growth.store.get(state,'affine_version')
            assert original['equations']==event['rows']
        audit=time.perf_counter_ns()-began
    finally:
        began=time.perf_counter_ns();service.close();shutdown=time.perf_counter_ns()-began
    keys=('kernel_hits','kernel_misses','executed_reference_cells','uncached_reference_cells',
          'batch_preparation_hits','input_rows','normalized_rows','preparation_key_cells',
          'preparation_compare_cell_bound','normalization_input_cells','kernel_key_cells',
          'kernel_compare_cell_bound','batch_admissions','batch_references','inline_versions')
    totals={k:sum(r['updates'][k] for r in records) for k in keys}
    report=dict(**config,setup_ns=setup,shutdown_ns=shutdown,audit_ns=audit,
                total_ns=setup+shutdown+sum(r['wall_ns'] for r in records),records=records,
                totals=totals,native_final=native,objects=objects,version_codecs=codecs,
                archive_rows=count,retained_database=str(cache),database_bytes=cache.stat().st_size)
    path.write_text(json.dumps(report,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--repetitions',type=int,default=5)
    parser.add_argument('--worker',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:worker(json.loads(args.worker),args.output);return
    if args.repetitions<1:raise ValueError('Repetitions must be positive')
    out=args.output;out.mkdir(parents=True,exist_ok=True)
    if (out/'comparison.json').exists():raise ValueError('Preserve existing evidence; choose a new directory')
    cases=[(w,p) for w in (16,32) for p in ('repeated','novel','multiplicity')]
    inputs={f'{w}-{p}':workload(w,p) for w,p in cases}
    packed=gzip.compress(json.dumps(inputs,separators=(',',':')).encode(),mtime=0)
    (out/'inputs.json.gz').write_bytes(packed)
    cache_dir=ROOT/'solver/.cache'/('affine-batches-'+str(time.time_ns()));runs=[]
    for rep in range(args.repetitions):
        for width,pattern in cases:
            order=MODES[rep%4:]+MODES[:rep%4]
            for mode in order:
                config=dict(width=width,pattern=pattern,mode=mode,repetition=rep,cache_dir=str(cache_dir))
                path=out/f'{width}-{pattern}-{mode}-{rep}.json'
                if path.exists():raise ValueError('Existing run: '+str(path))
                subprocess.run([sys.executable,str(Path(__file__).resolve()),'--output',str(path),
                                '--worker',json.dumps(config)],check=True,timeout=300)
                row=json.loads(path.read_text());runs.append(row)
                print(json.dumps(dict(run=len(runs),**config,total_ms=row['total_ns']/1e6)),flush=True)
    summary=[]
    for width,pattern in cases:
        item=dict(width=width,pattern=pattern,expansions=len(inputs[f'{width}-{pattern}']),modes={})
        for mode in MODES:
            chosen=[r for r in runs if (r['width'],r['pattern'],r['mode'])==(width,pattern,mode)]
            assert all(r['totals']==chosen[0]['totals'] for r in chosen)
            times=[r['total_ns'] for r in chosen]
            source_bytes=[sum(x['packed_bytes'] for x in r['objects'] if x['kind'] in ('affine_version','affine_batch')) for r in chosen]
            item['modes'][mode]=dict(median_total_ns=statistics.median(times),min_total_ns=min(times),max_total_ns=max(times),
                 median_source_payload_bytes=statistics.median(source_bytes),median_database_bytes=statistics.median(r['database_bytes'] for r in chosen),
                 totals=chosen[0]['totals'])
        summary.append(item)
    paths=[Path(__file__).resolve(),ROOT/'experiments/compare_affine_growth.py',ROOT/'experiments/affine_reference.py',
           ROOT/'solver/affine_archive.py',ROOT/'solver/affine_growth.py',ROOT/'solver/knowledge_store.py',ROOT/'solver/persistent.py',DEFAULT_ENGINE]
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                platform=platform.platform(),python=sys.version,repetitions=args.repetitions,summary=summary,runs=runs,
                fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                input_sha256=hashlib.sha256(packed).hexdigest(),
                protocol='Same binary; sequential rotated modes; fresh process/database; four resident versions; service setup, requests and persistence, and shutdown charged. Independent oracle and final source/archive audit excluded.',
                limitations=['Synthetic affine families; descriptive medians, no universal speedup',
                    'RSS is cumulative service observation, not a proved bound or isolated allocation profile',
                    'Source payload excludes indexes and pages; database sizes are reported separately',
                    'Duplicate normalization is separate from full row-space equivalence',
                    'Original histories remain; no durable native prepared-kernel certificate is trusted'])
    (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
