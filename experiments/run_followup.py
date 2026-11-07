#!/usr/bin/env python3
"""Sequential held-out follow-up; sampled process-tree RSS is not a hard bound.

Selection: first twelve towers05 increments and the complete LIDRUP example
from the TACAS 2026 artifact, fixed before timing. All failures are retained.
Old streams come from the immutable scaling input artifact. Resource sampling
runs in the parent; short-lived processes and peaks between samples can be missed.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.run_scaling import worker, MODES, cases_from_changes
from experiments.run_expanded import dimacs,encode_dimacs,balanced
from solver.persistent import PersistentSolver,DEFAULT_ENGINE
from solver.incremental import DEFAULT_INCREMENTAL
from solver.symbolic import BDD


def incremental_cases(parts,expected):
    permanent=[];out=[];delta=[]
    for name,text in parts:
        for line in text.splitlines():
            tokens=line.split()
            if not tokens or tokens[0] in ('p','c'):continue
            assumptions=tokens[0]=='a'
            values=list(map(int,tokens[1:] if assumptions else tokens))
            if not values or values[-1]!=0 or 0 in values[:-1]:raise ValueError('Unterminated incremental clause')
            if not assumptions:delta.append(values[:-1]);continue
            permanent+=delta
            clauses=permanent+[[v] for v in values[:-1]]
            out.append(dict(stage=len(out),bits=encode_dimacs(dimacs(clauses)),expected=expected[len(out)],
                add={f'increment{len(out)}':encode_dimacs(dimacs(delta)),
                     'assumptions':encode_dimacs(dimacs([[v] for v in values[:-1]]))},remove=[],name=name))
            delta=[]
    if delta or len(out)!=len(expected):raise ValueError('Unexpected incremental query count')
    return out


def public_inputs(archive):
    with zipfile.ZipFile(archive) as z:
        prefix='mallob/instances/incremental/'
        names=[prefix+f'towers05-{i}.cnf' for i in range(12)]
        labels=z.read(prefix+'towers05').decode().splitlines()[:12]
        small=prefix+'lidrup-example.cnf'
        groups=dict(tacas26_towers_prefix=incremental_cases([(n,z.read(n).decode()) for n in names],[s=='sat' for s in labels]),
                    tacas26_lidrup=incremental_cases([(small,z.read(small).decode())],[False,True,False]))
        metadata=dict(url='https://zenodo.org/records/18330441',sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            md5=hashlib.md5(archive.read_bytes()).hexdigest(),selection='first 12 towers05 increments; entire lidrup example',
            members={n:hashlib.sha256(z.read(n)).hexdigest() for n in names+[small,prefix+'towers05']})
    return groups,metadata


def counter_stream():
    # A four-bit synchronous counter, checked against its arithmetic trajectory.
    width=4;active={'initial':encode_dimacs(dimacs([[-(i+1)] for i in range(width)]))}
    changes=[]
    for t in range(1,13):
        clauses=[]
        for j in range(width):
            inputs=[(t-1)*width+i+1 for i in range(j+1)];output=t*width+j+1
            for values in itertools.product((False,True),repeat=j+1):
                expected=values[j] ^ all(values[:j])
                # Exclude exactly the incorrect next-bit value.
                clauses.append([(-v if b else v) for v,b in zip(inputs,values)]+[output if expected else -output])
        add={f'step{t}':encode_dimacs(dimacs(clauses))}
        if t==1:add.update(active)
        target=t % (1<<width)
        add['target']=encode_dimacs(dimacs([[t*width+j+1 if target&(1<<j) else -(t*width+j+1)] for j in range(width)]))
        changes.append((add,[],True))
        bad=target^1
        changes.append(({'target':encode_dimacs(dimacs([[t*width+j+1 if bad&(1<<j) else -(t*width+j+1)] for j in range(width)]))},[],False))
    return cases_from_changes(changes)


def measured_worker(mode,cases,timeout,cap):
    import psutil
    with tempfile.TemporaryDirectory(prefix='oracle-followup-monitor-') as d:
        directory=Path(d);input_path=directory/'input.json';input_path.write_text(json.dumps(cases))
        output=directory/'stdout';errors=directory/'stderr';scratch=directory/'scratch';scratch.mkdir()
        command=[sys.executable,__file__,'--worker',mode,'--timeout',str(timeout),'--cap',str(cap)]
        peak=0;disk=0;wal=0;samples=0;misses=0;largest=0;max_interval=0;last=None
        started=time.perf_counter_ns()
        with input_path.open() as inp,output.open('w') as out,errors.open('w') as err:
            process=subprocess.Popen(command,stdin=inp,stdout=out,stderr=err,env=os.environ|{'TMPDIR':str(scratch)})
            root=psutil.Process(process.pid)
            limit=time.monotonic()+timeout*len(cases)+45
            while process.poll() is None:
                now=time.monotonic()
                if last is not None:max_interval=max(max_interval,now-last)
                last=now
                try:
                    members=[root]+root.children(recursive=True);rss=0
                    for p in members:
                        try:rss+=p.memory_info().rss
                        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):misses+=1
                    peak=max(peak,rss);largest=max(largest,len(members));samples+=1
                except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):misses+=1
                total=journals=0
                for path in scratch.rglob('*'):
                    try:
                        if path.is_file():
                            size=path.stat().st_size;total+=size
                            if path.name.endswith(('-wal','-shm')):journals+=size
                    except OSError:pass
                disk=max(disk,total);wal=max(wal,journals)
                if now>=limit:
                    try:children=root.children(recursive=True)
                    except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):children=[]
                    for p in children:
                        try:p.kill()
                        except psutil.NoSuchProcess:pass
                    process.kill();break
                time.sleep(0.02)
            process.wait()
        records=[]
        for line in output.read_text().splitlines():
            try:records.append(json.loads(line))
            except json.JSONDecodeError:pass
        return dict(exit=process.returncode,records=records,stderr=errors.read_text(),elapsed_ns=time.perf_counter_ns()-started,
            sampled_peak_process_tree_rss_bytes=peak,sampled_peak_scratch_bytes=disk,sampled_peak_wal_shm_bytes=wal,
            resource_samples=samples,sampling_misses=misses,max_observed_processes=largest,
            requested_sample_interval_ms=20,max_sample_interval_ms=max_interval*1000,hard_memory_bound=False)


def chain_study():
    out=[]
    for size in (16,64,256,1024):
        for want in (False,True):
            for repetition in range(3):
                with tempfile.TemporaryDirectory() as d, PersistentSolver(Path(d)/'s.db') as s:
                    first=s.chain(append=[6]*size,left=1,right=1,witness=want)
                    for i in (0,size//2,size-1):
                        changed=s.chain(first['state'],replace={i:9},left=1,right=1,witness=want)
                        assert not changed['answer']
                        positive=s.chain(first['state'],replace={i:9},left=1,right=2,witness=want)
                        assert positive['answer']
                        assert positive['chain']['compositions']==size.bit_length()-1
                        out.append(dict(size=size,witness=want,repeat=repetition,index=i,negative=changed,positive=positive))
    return out


def symbolic_study():
    out=[]
    for size in (8,16,32,64):
        for method in ('separate','fused'):
            m=BDD(max_nodes=200000,max_work=3000000);variables=[m.node(i,0,1) for i in range(size)]
            left=right=1
            for i in range(size-1):
                left=m.apply('and',left,m.apply('or',variables[i],variables[i+1]))
                right=m.apply('and',right,m.apply('or',m.negate(variables[i]),variables[i+1]))
            before=len(m.nodes);start=time.perf_counter_ns()
            root=m.apply('and',left,right) if method=='separate' else m.and_exists(left,right,range(0,size,2))
            if method=='separate':
                for v in range(0,size,2):root=m.exists(root,v)
            elapsed=time.perf_counter_ns()-start;allocated=len(m.nodes)
            payload=m.dump(root);roots=m.collect({'result':root})
            assert m.dump(roots['result'])==payload
            out.append(dict(size=size,method=method,build_nodes=before,allocated_nodes=allocated,
                retained_nodes=len(m.nodes),operations=m.work,projection_ns=elapsed,payload=payload))
    # Equality of a and b is sensitive to whether corresponding bits are adjacent.
    for width in (4,6,8):
        for name,order in [('grouped',tuple(range(2*width))),('interleaved',tuple(v for i in range(width) for v in (i,width+i)))]:
            m=BDD(order=order);root=1;start=time.perf_counter_ns()
            for i in range(width):
                a,b=m.node(i,0,1),m.node(width+i,0,1)
                equal=m.apply('or',m.apply('and',a,b),m.apply('and',m.negate(a),m.negate(b)))
                root=m.apply('and',root,equal)
            out.append(dict(order=name,width=width,allocated_nodes=len(m.nodes),retained_nodes=len(m.dump(root)['nodes']),
                            operations=m.work,build_ns=time.perf_counter_ns()-start))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--worker',choices=MODES);p.add_argument('--artifact',type=Path)
    p.add_argument('--output',type=Path);p.add_argument('--timeout',type=float,default=5)
    p.add_argument('--cap',type=int,default=8*1024**2);p.add_argument('--repeats',type=int,default=3)
    args=p.parse_args()
    if args.worker:worker(args.worker,json.load(sys.stdin),args.cap,args.timeout);return
    if args.output is None or args.artifact is None:p.error('Supply artifact and fresh output directory')
    args.output.mkdir(parents=True,exist_ok=False)
    groups=json.loads((ROOT/'experiments/results/scaling/inputs.json').read_text())
    public,source=public_inputs(args.artifact);groups.update(public);groups['heldout_counter4']=counter_stream()
    (args.output/'inputs.json').write_text(json.dumps(groups,separators=(',',':'))+'\n')
    rows=[]
    with (args.output/'runs.jsonl').open('w') as log:
        for name,cases in groups.items():
            for repeat in range(args.repeats):
                for mode in MODES[repeat%len(MODES):]+MODES[:repeat%len(MODES)]:
                    row=measured_worker(mode,cases,args.timeout,args.cap)
                    row.update(stream=name,mode=mode,repeat=repeat,planned=len(cases));rows.append(row)
                    log.write(json.dumps(row)+'\n');log.flush()
                print(name,repeat,'complete',flush=True)
    summary=[]
    for name in groups:
        for mode in MODES:
            selected=[r for r in rows if r['stream']==name and r['mode']==mode]
            queries=[q for r in selected for q in r['records'] if q['event']=='query']
            times=[sum(q['elapsed_ns'] for q in r['records'] if q['event']=='query')/1e6 for r in selected]
            summary.append(dict(stream=name,mode=mode,statuses=dict(Counter(q['status'] for q in queries)),
                planned=len(groups[name])*args.repeats,missing=len(groups[name])*args.repeats-len(queries),
                median_stream_ms=statistics.median(times),min_stream_ms=min(times),max_stream_ms=max(times),
                max_sampled_rss_bytes=max(r['sampled_peak_process_tree_rss_bytes'] for r in selected),
                max_sampled_scratch_bytes=max(r['sampled_peak_scratch_bytes'] for r in selected)))
    (args.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (args.output/'chain.json').write_text(json.dumps(chain_study(),separators=(',',':'))+'\n')
    (args.output/'symbolic.json').write_text(json.dumps(symbolic_study(),indent=2)+'\n')
    files=[Path(__file__),DEFAULT_ENGINE,DEFAULT_INCREMENTAL]+list((ROOT/'solver').glob('*.py'))+list((ROOT/'formal/OracleMachines').glob('*.lean'))+[ROOT/'formal/Solver.lean']
    (args.output/'metadata.json').write_text(json.dumps(dict(source=source,repeats=args.repeats,timeout=args.timeout,
        archive_page_cap=args.cap,host=platform.platform(),python=sys.version,
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True,cwd=ROOT).strip(),
        fingerprints={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}),indent=2)+'\n')
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
