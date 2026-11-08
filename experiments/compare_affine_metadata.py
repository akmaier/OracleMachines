#!/usr/bin/env python3
"""Matched parent-width reuse study, including warm appends and cold replay.

Both modes keep normalization and batch sharing enabled. Only reuse of checked
resident parent widths changes. Fresh databases are retained, never overwritten.
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
from solver.affine_archive import AffineArchive
from solver.persistent import PersistentSolver,DEFAULT_ENGINE

MODES=('reread','metadata')
STEPS=32


def worker(config,path):
    events=stream(config['width'],config['pattern'],STEPS)
    for event in events:assert flattened_sat(config['width'],event['batches'])==event['expected']
    cache=Path(config['cache_dir'])/(path.stem+'.sqlite3');cache.parent.mkdir(parents=True,exist_ok=True)
    if cache.exists():raise ValueError('Refusing to overwrite an experiment database')
    def start():
        return PersistentSolver(cache,native_affine_versions=4,affine_kernel_slots=64,
            affine_reuse_metadata=config['mode']=='metadata',query_timeout=60)
    def record(result,elapsed):
        return dict(state=result['state'],answer=result['answer'],steps=result['steps'],wall_ns=elapsed,
            phase_ns=result['phase_ns'],service_events=result['service_events'],updates=result['affine_updates'])
    began=time.perf_counter_ns();service=start();setup=time.perf_counter_ns()-began
    records=[];states=[];cold=[]
    try:
        for event in events:
            parent=event['parent'];base=None if parent<0 else states[parent]
            began=time.perf_counter_ns()
            result=service.affine_grow(config['width'] if base is None else None,event['rows'],base=base)
            elapsed=time.perf_counter_ns()-began
            assert result['answer']==event['expected'] and result['steps']==len(event['batches'])
            assert result['affine_updates']['resident_versions']<=4
            states.append(result['state']);records.append(record(result,elapsed))
        began=time.perf_counter_ns();service.close();shutdown=time.perf_counter_ns()-began
        # Each branch query starts with a new Python service and native worker;
        # neither warm width metadata nor native kernels survive the restart.
        for index in (STEPS,STEPS+1):
            began=time.perf_counter_ns();service=start();cold_setup=time.perf_counter_ns()-began
            began=time.perf_counter_ns();result=service.affine_grow(base=states[index])
            elapsed=time.perf_counter_ns()-began
            assert result['answer']==events[index]['expected']
            assert result['affine_updates']['replayed_versions']==len(events[index]['batches'])+1
            row=record(result,elapsed)
            began=time.perf_counter_ns();service.close();cold_shutdown=time.perf_counter_ns()-began
            cold.append(dict(index=index,setup_ns=cold_setup,shutdown_ns=cold_shutdown,**row))
        began=time.perf_counter_ns();service=start()
        archive=AffineArchive(service.db,service.engine_id)
        for event,state in zip(events,states):
            original=archive.get(state,'affine_version')
            assert original['equations']==event['rows'] and original['width']==config['width']
            expected_parent=None if event['parent']<0 else states[event['parent']]
            if expected_parent is not None:assert original['base']==expected_parent
        objects=[dict(kind=k,count=n,packed_bytes=p) for k,n,p in service.db.execute(
            'SELECT kind,count(*),sum(length(payload)) FROM knowledge_objects GROUP BY kind')]
        assert service.db.execute('SELECT count(*) FROM affine_states').fetchone()[0]==len(events)
        service.close();audit=time.perf_counter_ns()-began
    finally:service.close()
    report=dict(**config,setup_ns=setup,shutdown_ns=shutdown,audit_ns=audit,records=records,cold=cold,
        total_stream_ns=setup+shutdown+sum(r['wall_ns'] for r in records),
        # Exclude initial fill, final contradiction and branching empty append.
        warm_append_ns=sum(r['wall_ns'] for r in records[4:STEPS]),
        total_cold_ns=sum(r['setup_ns']+r['wall_ns']+r['shutdown_ns'] for r in cold),
        objects=objects,retained_database=str(cache),database_bytes=cache.stat().st_size)
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
    if any(out.iterdir()):raise ValueError('Choose a new empty evidence directory')
    cases=[(w,p) for w in (16,32,64) for p in ('repeated','novel')]
    inputs={f'{w}-{p}':stream(w,p,STEPS) for w,p in cases}
    packed=gzip.compress(json.dumps(inputs,separators=(',',':')).encode(),mtime=0)
    (out/'inputs.json.gz').write_bytes(packed)
    cache_dir=ROOT/'solver/.cache'/('affine-metadata-'+str(time.time_ns()));runs=[]
    for rep in range(args.repetitions):
        for width,pattern in cases:
            for mode in MODES[rep%2:]+MODES[:rep%2]:
                config=dict(width=width,pattern=pattern,mode=mode,repetition=rep,cache_dir=str(cache_dir))
                path=out/f'{width}-{pattern}-{mode}-{rep}.json'
                subprocess.run([sys.executable,str(Path(__file__).resolve()),'--output',str(path),
                    '--worker',json.dumps(config)],check=True,timeout=300)
                row=json.loads(path.read_text());runs.append(row)
                print(json.dumps(dict(run=len(runs),**config,stream_ms=row['total_stream_ns']/1e6)),flush=True)
    summary=[]
    for width,pattern in cases:
        item=dict(width=width,pattern=pattern,modes={})
        selected=[r for r in runs if (r['width'],r['pattern'])==(width,pattern)]
        identities=[v['state'] for v in selected[0]['records']]
        for run in selected:assert [v['state'] for v in run['records']]==identities
        for mode in MODES:
            chosen=[r for r in selected if r['mode']==mode]
            medians={k:statistics.median(r[k] for r in chosen)
                     for k in ('total_stream_ns','warm_append_ns','total_cold_ns','database_bytes')}
            counts={}
            for segment in ('records','cold'):
                counts[segment]={k:sum(x['updates'][k] for x in chosen[0][segment]) for k in
                    ('object_reads','read_packed_bytes','parent_metadata_hits','parent_archive_reads',
                     'executed_reference_cells','kernel_hits','kernel_misses')}
                for run in chosen:
                    for key,value in counts[segment].items():
                        assert sum(x['updates'][key] for x in run[segment])==value
            item['modes'][mode]=dict(medians=medians,counts=counts,
                ranges_ns={k:[min(r[k] for r in chosen),max(r[k] for r in chosen)] for k in
                           ('total_stream_ns','warm_append_ns','total_cold_ns')})
        for segment in ('records','cold'):
            for field in ('executed_reference_cells','kernel_hits','kernel_misses'):
                assert item['modes']['reread']['counts'][segment][field]==item['modes']['metadata']['counts'][segment][field]
        summary.append(item)
    paths=[Path(__file__).resolve(),ROOT/'experiments/compare_affine_growth.py',ROOT/'experiments/affine_reference.py',
           ROOT/'solver/affine_growth.py',ROOT/'solver/affine_archive.py',ROOT/'solver/knowledge_store.py',
           ROOT/'solver/persistent.py',DEFAULT_ENGINE]
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        platform=platform.platform(),python=sys.version,repetitions=args.repetitions,steps=STEPS,summary=summary,runs=runs,
        fingerprints={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        input_sha256=hashlib.sha256(packed).hexdigest(),
        protocol='Sequential rotated paired modes, fresh database per run, 4 resident versions, 64 kernel slots; normalization and sharing enabled. Independent oracle before timing. Setup, requests with persistence and shutdown charged; two cold service/worker restarts per run. Final source audit, interpreter/import and orchestration excluded.',
        limitations=['Synthetic affine streams; descriptive medians, not a universal timing improvement',
            'Cold means new service/worker; operating-system file caches are not flushed',
            'Source payload and persisted decisions are unchanged; metrics may affect database pages',
            'One bounded integer per resident entry; no whole-process memory measurement or proof',
            'No native batch handle, compact definition response, durable kernel checkpoint or general SAT claim'])
    (out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
