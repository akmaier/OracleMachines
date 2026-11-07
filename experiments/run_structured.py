#!/usr/bin/env python3
"""Frozen full-input comparison; separate supplied-layer and delta studies.

Five sequential repeats, rotating mode order; every attempted query is retained.
RSS/scratch limits are sampled watchdog thresholds, not hard kernel limits.
"""
import argparse,hashlib,itertools,json,os,platform,random,signal,statistics,subprocess,sys,tempfile,time,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.run_expanded import dimacs,encode_dimacs,parse_dimacs,workloads
from experiments.run_interfaces import storage
from solver.persistent import PersistentSolver,DEFAULT_ENGINE,find_cadical
from solver.incremental import DEFAULT_INCREMENTAL
from solver.resources import Deadline,bounded_run
MODES=['direct','checked','exact','portfolio','learned','proof_live','adaptive']

def digest(data):return hashlib.sha256(data).hexdigest()

def inputs(archive,archives):
    groups={};source={};members={}
    with zipfile.ZipFile(archive) as z:
        prefix='mallob/instances/incremental/'
        for family in ['roverg10','transportg29','entertainment08']:
            labels=z.read(prefix+family).decode().splitlines();permanent=[];cases=[]
            members[prefix+family]=digest(z.read(prefix+family))
            for i in range(2):
                name=prefix+family+f'-{i}.cnf';raw=z.read(name);members[name]=digest(raw)
                for line in raw.decode().splitlines():
                    v=line.split()
                    if not v or v[0] in ('c','p'):continue
                    assumption=v[0]=='a';clause=list(map(int,v[1:] if assumption else v))
                    if clause[-1]!=0 or 0 in clause[:-1]:raise ValueError('Malformed incremental clause')
                    if assumption:cases.append(dict(name=name,dimacs=dimacs(permanent+[[x] for x in clause[:-1]]),expected=labels[len(cases)]=='sat',phase='application_prefix'))
                    else:permanent.append(clause[:-1])
            assert len(cases)==2
            groups['tacas26_'+family]=cases
        source['tacas26']=dict(url='https://zenodo.org/records/18330441',sha256=digest(archive.read_bytes()),
            md5=hashlib.md5(archive.read_bytes()).hexdigest(),members=members,
            selection='first two increments of roverg10, transportg29 and entertainment08, fixed before timing; later horizons excluded by design')
    provenance,old=workloads(archives);source['satlib']=provenance
    public=[]
    for family in ('satlib_uf50-218','satlib_uuf50-218','satlib_flat30-60'):
        public+=next(g['cases'] for g in old if g['name']==family)[:2]
    groups['satlib_holdout']=public
    rng=random.Random(1707);units=[]
    for i in range(48):
        n=12+i;clause=[[(v+1)*rng.choice((-1,1))] for v in range(n)]
        units.append(dict(name=f'units_{i}',dimacs=dimacs(clause),expected=True,
                          phase='train' if i<16 else 'heldout_online'))
    groups['chronological_shift']=units[:16]+units[16:32]+[dict(c,phase='public_shift') for c in public]+units[32:]+[dict(c,phase='repeat') for c in units[-4:]]
    for cases in groups.values():
        for i,c in enumerate(cases):
            c['stage']=i;c['bits']=encode_dimacs(c['dimacs']);c['input_sha256']=digest(c['dimacs'].encode())
    return groups,source

def worker(mode,cases,cap,timeout):
    with tempfile.TemporaryDirectory(prefix='oracle-structured-') as d:
        directory=Path(d);service=None
        options=dict(backend='cadical',reuse_exact=mode!='checked',learned=mode=='learned',
            adaptive=mode=='adaptive',incremental_proofs=mode=='proof_live',
            max_archive_bytes=cap,query_timeout=timeout,timeout=timeout)
        try:
            start=time.perf_counter_ns()
            if mode!='direct':service=PersistentSolver(directory/'s.db',**options)
            print(json.dumps(dict(event='setup',elapsed_ns=time.perf_counter_ns()-start,options=options)),flush=True)
            for c in cases:
                start=time.perf_counter_ns();row=dict(event='query',stage=c['stage'],phase=c['phase'],expected=c['expected'])
                try:
                    if mode=='direct':
                        n,clauses=parse_dimacs(c['dimacs']);path=directory/'query.cnf';path.write_text(dimacs(clauses,n))
                        run=bounded_run([str(find_cadical()),'--quiet',str(path)],directory,Deadline(timeout),timeout,
                            64*1024**2,directory/'unused.proof',16*1024**2)
                        if run.returncode not in (10,20):raise ValueError(f'CaDiCaL exit {run.returncode}')
                        result=dict(answer=run.returncode==10,source='direct_unverified')
                    else:
                        bits=encode_dimacs(c['dimacs']);row['conversion_ns']=time.perf_counter_ns()-start
                        assert bits==c['bits']
                        result=service.solve(bits,learn=mode in ('portfolio','learned'))
                        assert sum(result['phase_ns'].values())==result['wall_ns']
                    row.update(status='ok' if result['answer']==c['expected'] else 'wrong',result={k:v for k,v in result.items() if k not in ('witness','certificate','original_measurements')})
                except Exception as e:row.update(status='error',error=type(e).__name__+': '+str(e),failure_metrics=service.last_metrics if service else {})
                row['elapsed_ns']=time.perf_counter_ns()-start;print(json.dumps(row),flush=True)
            end=dict(event='end')
            if service:end.update(storage(service));end['usage']=service.archive_usage()
            print(json.dumps(end),flush=True)
        finally:
            if service:service.close()

def measured(mode,cases,cap,timeout):
    import psutil
    with tempfile.TemporaryDirectory(prefix='oracle-monitor-') as d:
        d=Path(d);scratch=d/'scratch';scratch.mkdir();inp=d/'input';inp.write_text(json.dumps(cases));out=d/'out';err=d/'err'
        peak=disk=wal=samples=misses=0;interval=0;previous=None;stop=None;start=time.perf_counter_ns()
        with inp.open() as i,out.open('w') as o,err.open('w') as e:
            p=subprocess.Popen([sys.executable,__file__,'--worker',mode,'--cap',str(cap),'--timeout',str(timeout)],
                stdin=i,stdout=o,stderr=e,env=os.environ|{'TMPDIR':str(scratch)},start_new_session=True)
            root=psutil.Process(p.pid);deadline=time.monotonic()+timeout*len(cases)+30
            while p.poll() is None:
                now=time.monotonic()
                if previous is not None:interval=max(interval,now-previous)
                previous=now;rss=0
                try:
                    for child in [root]+root.children(recursive=True):
                        try:rss+=child.memory_info().rss
                        except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):misses+=1
                    peak=max(peak,rss);samples+=1
                except (psutil.NoSuchProcess,psutil.AccessDenied,PermissionError):misses+=1
                total=journals=0
                for f in scratch.rglob('*'):
                    try:
                        if f.is_file():
                            size=f.stat().st_size;total+=size
                            if f.name.endswith(('-wal','-shm')):journals+=size
                    except OSError:pass
                disk=max(disk,total);wal=max(wal,journals)
                if rss>512*1024**2:stop='sampled_rss_threshold'
                elif total>256*1024**2:stop='sampled_scratch_threshold'
                elif now>deadline:stop='worker_deadline'
                if stop:
                    os.killpg(p.pid,signal.SIGKILL);break
                time.sleep(.02)
            p.wait()
        records=[]
        for line in out.read_text().splitlines():
            try:records.append(json.loads(line))
            except json.JSONDecodeError:pass
        return dict(exit=p.returncode,stop=stop,records=records,stderr=err.read_text(),elapsed_ns=time.perf_counter_ns()-start,
            sampled_peak_rss_bytes=peak,sampled_peak_scratch_bytes=disk,sampled_peak_wal_shm_bytes=wal,
            samples=samples,sampling_misses=misses,max_sample_interval_ms=interval*1000,hard_memory_bound=False)

def structural_study():
    from solver.test_interfaces import chain,var,neg
    rows=[]
    for width,size,cache in itertools.product((2,3,4),(16,64,256,1024),(65536,2*1024**2)):
        q=1<<width;step=sum(1<<(q*x+(x+1)%q) for x in range(q));identity=sum(1<<(q*x+x) for x in range(q))
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',active_cache_bytes=cache) as s:
            first=s.layered(width,append=[step]*size,left=1,right=1)
            changed=s.layered(width,first['state'],replace={size//2:identity},left=1,right=1)
            yes=s.layered(width,changed['state'],left=1,right=1<<(q-1),witness=True)
            assert first['answer'] and not changed['answer'] and yes['answer']
            assert changed['layered']['compositions']==size.bit_length()-1
            assert yes['layered']['witness_checks']==size
            rows.append(dict(kind='layers',width=width,size=size,cache=cache,initial=first,changed=changed,witness=yes))
    for size in (16,64,256):
        with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',interfaces=True) as s:
            first=s.expand(add={'chain':chain(size),'start':var(0),'end':neg(var(size))})
            edited=s.expand(first['state'],add={'end':var(size)})
            assert not first['answer'] and edited['answer']
            assert edited['interfaces']['source_comparisons']==edited['interfaces']['plan_copy_entries']==0
            rows.append(dict(kind='delta',size=size,initial=first,changed=edited))
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--worker',choices=MODES)
    p.add_argument('--artifact',type=Path);p.add_argument('--archives',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--cap',type=int,default=64*1024**2);p.add_argument('--timeout',type=float,default=5);p.add_argument('--repeats',type=int,default=5)
    a=p.parse_args()
    if a.worker:worker(a.worker,json.load(sys.stdin),a.cap,a.timeout);return
    if not (a.artifact and a.archives and a.output):p.error('Supply source archives and fresh output')
    a.output.mkdir(parents=True,exist_ok=False);groups,source=inputs(a.artifact,a.archives)
    (a.output/'inputs.json').write_text(json.dumps(groups,separators=(',',':'))+'\n')
    files=[Path(__file__),DEFAULT_ENGINE,DEFAULT_INCREMENTAL,find_cadical()]+list((ROOT/'solver').glob('*.py'))+list((ROOT/'formal/OracleMachines').glob('*.lean'))+[ROOT/'formal/Solver.lean']
    metadata=dict(source=source,repeats=a.repeats,timeout=a.timeout,archive_cap=a.cap,rss_watchdog=512*1024**2,scratch_watchdog=256*1024**2,
        sampling_ms=20,hard_total_resource_cap=False,host=platform.platform(),python=sys.version,
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        fingerprints={str(f):digest(f.read_bytes()) for f in files})
    (a.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n');rows=[]
    with (a.output/'runs.jsonl').open('w') as log:
        for name,cases in groups.items():
            for repeat in range(a.repeats):
                for mode in MODES[repeat%len(MODES):]+MODES[:repeat%len(MODES)]:
                    row=measured(mode,cases,a.cap,a.timeout);row.update(stream=name,mode=mode,repeat=repeat,planned=len(cases));rows.append(row)
                    log.write(json.dumps(row)+'\n');log.flush()
                print(name,repeat,'complete',flush=True)
    summary=[]
    for name,cases in groups.items():
        for mode in MODES:
            selected=[r for r in rows if r['stream']==name and r['mode']==mode]
            queries=[q for r in selected for q in r['records'] if q['event']=='query']
            complete=[sum(q['elapsed_ns'] for q in r['records'] if q['event'] in ('query','setup'))/1e6 for r in selected
                if r['exit']==0 and sum(q.get('status')=='ok' for q in r['records'])==len(cases)]
            summary.append(dict(stream=name,mode=mode,statuses=dict(Counter(q['status'] for q in queries)),planned=len(cases)*a.repeats,
                missing=len(cases)*a.repeats-len(queries),complete_runs=len(complete),
                median_complete_ms=statistics.median(complete) if complete else None,min_complete_ms=min(complete) if complete else None,max_complete_ms=max(complete) if complete else None,
                learned_hits=sum(q.get('result',{}).get('learned_accepted',False) for q in queries),
                sources=dict(Counter(q.get('result',{}).get('source','error') for q in queries)),
                max_sampled_rss_bytes=max(r['sampled_peak_rss_bytes'] for r in selected)))
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    (a.output/'structure.json').write_text(json.dumps(structural_study(),separators=(',',':'))+'\n')
    if any(q.get('status')=='wrong' for r in rows for q in r['records']):raise SystemExit('Wrong answer retained')
if __name__=='__main__':main()
