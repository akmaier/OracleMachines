#!/usr/bin/env python3
"""Matched source-CNF rebuild/update study; all inputs and failures are retained.

Each timed run has a fresh Python process and database. RSS observations cover
only that service process and its owned native checker; sampling is not a cap.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import subprocess
import sys
import tempfile
import threading
import time

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from solver.persistent import PersistentSolver,DEFAULT_ENGINE


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def make_case(width,size):
    rng=random.Random(1830+10000*width+size)
    layers=[list(range(i*width+1,(i+1)*width+1)) for i in range(size+1)]
    def relation(edge):
        order=list(range(width));rng.shuffle(order);out=[]
        for i,j in enumerate(order):
            x,y=layers[edge][i],layers[edge+1][j]
            # A bijection between the two Boolean blocks, hence extendable.
            out.extend([[x,y],[-x,-y]] if rng.getrandbits(1) else [[x,-y],[-x,y]])
        return out
    buckets=[relation(i) for i in range(size)]
    edits=[];current=list(buckets)
    for step in range(32):
        edge=(step*17)%size
        replacement=relation(edge)
        while replacement==current[edge]:replacement=relation(edge)
        current[edge]=replacement
        edits.append(dict(edge=edge,clauses=replacement))
    return dict(width=width,size=size,layers=layers,buckets=buckets,edits=edits)


class RssObserver:
    def __init__(self,holder):
        self.holder=holder;self.stop=threading.Event();self.samples=0;self.misses=0
        self.peak=None;self.native_peak=None;self.max_interval=0;self.last=None
        self.thread=threading.Thread(target=self.run,daemon=True)

    def run(self):
        while not self.stop.is_set():
            now=time.monotonic_ns()
            if self.last is not None:self.max_interval=max(self.max_interval,now-self.last)
            self.last=now
            service=self.holder[0];native=None if service is None else service.process
            pids=[os.getpid()]
            if native is not None and native.poll() is None:pids.append(native.pid)
            try:
                r=subprocess.run(['/bin/ps','-o','pid=,rss=','-p',','.join(map(str,pids))],
                                 text=True,capture_output=True,timeout=2)
                observed={int(p):int(rss)*1024 for p,rss in (line.split() for line in r.stdout.splitlines())}
                if r.returncode or any(pid not in observed for pid in pids):raise ValueError('Incomplete RSS sample')
                self.samples+=1;self.peak=max(self.peak or 0,sum(observed[p] for p in pids))
                if len(pids)==2:self.native_peak=max(self.native_peak or 0,observed[pids[1]])
            except (OSError,ValueError,subprocess.TimeoutExpired):self.misses+=1
            self.stop.wait(.02)

    def finish(self):
        self.stop.set();self.thread.join(timeout=3)
        return dict(valid_samples=self.samples,sampling_misses=self.misses,
                    sampled_service_and_native_peak_bytes=self.peak,sampled_native_peak_bytes=self.native_peak,
                    max_sample_interval_ns=self.max_interval,hard_memory_bound=False)


def worker(mode,case):
    holder=[None];observer=RssObserver(holder);observer.thread.start();records=[]
    with tempfile.TemporaryDirectory() as directory:
        path=Path(directory)/'s.db';width,size=case['width'],case['size']
        capacity=1<<(size-1).bit_length();cap=(2*capacity-1)*(1<<width)**2
        service=PersistentSolver(path,native_layer_cells=cap,query_timeout=30)
        holder[0]=service;buckets=[list(b) for b in case['buckets']];state=first=None
        def query(kind,changes=None,expected=True,restart=False,branch=False):
            nonlocal service,state,first,buckets
            if branch:buckets=[list(b) for b in case['buckets']]
            if changes:
                for edge,clauses in changes.items():buckets[edge]=clauses
            start=time.perf_counter_ns();row=dict(kind=kind,expected=expected)
            try:
                if restart:
                    holder[0]=None;service.close()
                    service=PersistentSolver(path,native_layer_cells=cap,query_timeout=30);holder[0]=service
                if mode=='source_full' or state is None:
                    # Full reconstruction is part of the baseline's elapsed time.
                    flat=[clause for bucket in buckets for clause in bucket]
                    result=service.source_cnf(width,flat,case['layers'])
                else:
                    result=service.source_cnf(base=first if branch else state,replace=changes or {})
                if result['answer']!=expected:raise AssertionError('Wrong source verdict')
                row.update(status='ok',result=result);state=result['state']
                if first is None:first=state
            except Exception as error:
                row.update(status='error',error=type(error).__name__+': '+str(error),failure_metrics=service.last_metrics)
            row['elapsed_ns']=time.perf_counter_ns()-start;records.append(row)
        try:
            query('initial')
            for edit in case['edits']:query('edit',{edit['edge']:edit['clauses']})
            query('unchanged')
            query('negative',{size//2:[[]]},False)
            query('deletion',{size//2:[]})
            query('old_branch',branch=True)
            query('restart',restart=True)
            storage=service.archive_usage()
        finally:
            resources=observer.finish();holder[0]=None;service.close()
    return dict(mode=mode,width=width,size=size,records=records,storage=storage,resources=resources)


def summarize(runs):
    table=[]
    for width in (1,4):
        for size in (16,64,256,1024):
            for mode in ('source_delta','source_full'):
                selected=[r for r in runs if (r['width'],r['size'],r['mode'])==(width,size,mode)]
                good=[q for r in selected for q in r['records'] if q['status']=='ok']
                edits=[q for q in good if q['kind']=='edit']
                def median(field):return statistics.median(q['result']['source_updates'][field] for q in edits)
                table.append(dict(width=width,size=size,mode=mode,completed=len(good),planned=38*len(selected),
                    median_stream_ms=statistics.median(sum(q['elapsed_ns'] for q in r['records'])/1e6 for r in selected),
                    median_edit_ms=statistics.median(q['elapsed_ns']/1e6 for q in edits),
                    median_node_reads=median('node_reads'),median_new_objects=median('inserted_objects'),
                    median_binding_visits=median('binding_visits'),median_patch_visits=median('patch_visits'),
                    median_new_packed_bytes=median('inserted_packed_bytes'),
                    median_request_bytes=statistics.median(q['result']['service_events']['native_request_bytes'] for q in edits)))
    return dict(table=table,planned=sum(len(r['records']) for r in runs),
        completed=sum(q['status']=='ok' for r in runs for q in r['records']),
        errors=[dict(mode=r['mode'],width=r['width'],size=r['size'],kind=q['kind'],error=q['error'])
                for r in runs for q in r['records'] if q['status']!='ok'],
        valid_rss_samples=sum(r['resources']['valid_samples'] for r in runs),
        rss_misses=sum(r['resources']['sampling_misses'] for r in runs))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--worker',choices=('source_delta','source_full'))
    args=parser.parse_args()
    if args.worker:
        print(json.dumps(worker(args.worker,json.load(sys.stdin))));return
    if args.output is None:parser.error('--output is required')
    args.output.mkdir(parents=True,exist_ok=False)
    cases=[make_case(w,n) for w in (1,4) for n in (16,64,256,1024)]
    (args.output/'inputs.json').write_text(json.dumps(cases,indent=2)+'\n')
    runs=[]
    with gzip.open(args.output/'runs.jsonl.gz','wt') as log:
        for repeat in range(3):
            for case in cases:
                for mode in (('source_delta','source_full') if repeat%2==0 else ('source_full','source_delta')):
                    child=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker',mode],
                        input=json.dumps(case),text=True,capture_output=True,timeout=180,check=True)
                    result=json.loads(child.stdout);result['repeat']=repeat
                    if child.stderr:result['stderr']=child.stderr
                    log.write(json.dumps(result)+'\n');log.flush();runs.append(result)
                    print(json.dumps(dict(run=len(runs),mode=mode,width=case['width'],size=case['size'])),flush=True)
    summary=summarize(runs)
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    files=[Path(__file__),DEFAULT_ENGINE,ROOT/'formal/Solver.lean',
           *sorted((ROOT/'solver').glob('*.py')),*sorted((ROOT/'formal/OracleMachines').glob('*.lean'))]
    metadata=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        inputs_sha256=digest(args.output/'inputs.json'),
        fingerprints={str(p.relative_to(ROOT)):digest(p) for p in files},
        scope='Synthetic supplied adjacent-block CNF; same native source checker; no claim about unrestricted SAT or learning',
        repetitions=3,queries_per_run=38,memory_observer='Sample only owned service and native checker PIDs; no hard RSS cap')
    (args.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='table'}))


if __name__=='__main__':main()
