#!/usr/bin/env python3
"""Frozen unused inputs and mechanism diagnostics for the seven-priority follow-up.

Full-formula modes share inputs and acceptance boundaries. Supplied-layer/source
and delta diagnostics are separate. Watchdogs are sampled, not hard RSS bounds.
"""
import argparse,gzip,hashlib,json,platform,random,statistics,subprocess,sys,tarfile,tempfile,time,zipfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.run_expanded import dimacs,parse_dimacs,encode_dimacs
from experiments import run_structured as harness
from solver.persistent import PersistentSolver,DEFAULT_ENGINE
from solver.resources import Deadline,BudgetExceeded,bounded_run
from solver.learning import features
from solver.test_interfaces import xor,neg,var,chain
MODES=['direct','checked','portfolio','learned','polarity','proof_live','proof_restart','adaptive']

def digest(data):return hashlib.sha256(data).hexdigest()

def encoding_size(clauses):
    if not clauses:return 4
    return sum(sum(abs(v)+2+(2 if v<0 else 0) for v in c)+8*max(0,len(c)-1)+(2 if not c else 0)
               for c in clauses)+2*(len(clauses)-1)

class PolaritySolver(PersistentSolver):
    def solve(self,bits,**kwargs):
        self.heuristic_input=bits
        return super().solve(bits,**kwargs)
    def _candidates(self):
        observed=features(self.heuristic_input,self._deadline)
        word=['0']*(max(observed,default=-1)+1)
        for v,row in observed.items():word[v]='1' if row[1]>row[2] else '0'
        return [''.join(word)]
    def _proofs(self):return []

def inputs(artifact,archives):
    groups={};source={};public=[]
    for family in ('uf50-218','uuf50-218'):
        path=archives/(family+'.tar.gz')
        with tarfile.open(path) as t:
            members=sorted((m for m in t.getmembers() if m.isfile() and m.name.endswith('.cnf')),key=lambda m:m.name)[6:10]
            for m in members:
                raw=t.extractfile(m).read();public.append(dict(name=m.name,dimacs=raw.decode(),expected=family=='uf50-218',phase='public_shift',sha256=digest(raw)))
        source[family]=dict(sha256=digest(path.read_bytes()),selection='lexicographic members 6:10, zero based; earlier studies used 0:6')
    rng=random.Random(1710);units=[]
    for i in range(32):
        units.append(dict(name=f'fresh_units_{i}',dimacs=dimacs([[(v+1)*rng.choice([-1,1])] for v in range(24+i)]),
                          expected=True,phase='train' if i<8 else 'later_units'))
    groups['chronological_unused']=units[:24]+public+units[24:]
    application=[]
    path=archives/'ssa.tar.gz';names={'ssa2670-141.cnf':False,'ssa7552-159.cnf':True,'ssa7552-160.cnf':True}
    with tarfile.open(path) as t:
        for m in sorted(t.getmembers(),key=lambda m:m.name):
            if m.name in names:
                raw=t.extractfile(m).read();application.append(dict(name=m.name,dimacs=raw.decode(),expected=names[m.name],phase='circuit_fault',sha256=digest(raw)))
    source['ssa']=dict(sha256=digest(path.read_bytes()),members=names,label_source='https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/BF/descr.html')
    with zipfile.ZipFile(artifact) as z:
        p='mallob/instances/incremental/'
        for family,selected in [('towers05',{12,13,38}),('unsat300cubes',{0,1})]:
            permanent=[];labels=z.read(p+family).decode().splitlines();hashes={}
            for i in range(max(selected)+1):
                name=p+family+f'-{i}.cnf';raw=z.read(name);hashes[name]=digest(raw)
                for line in raw.decode().splitlines():
                    parts=line.split()
                    if not parts or parts[0] in ('p','c'):continue
                    assumption=parts[0]=='a';values=list(map(int,parts[1:] if assumption else parts))
                    if values[-1]!=0 or 0 in values[:-1]:raise ValueError('Malformed incremental CNF')
                    if assumption:
                        if i in selected:application.append(dict(name=f'{family}-{i}',dimacs=dimacs(permanent+[[x] for x in values[:-1]]),expected=labels[i]=='sat',phase='application_horizon'))
                    else:permanent.append(values[:-1])
            source[family]=dict(members=hashes,selected=sorted(selected),labels_sha256=digest(z.read(p+family)))
    source['artifact']=dict(url='https://zenodo.org/records/18330441',sha256=digest(artifact.read_bytes()))
    groups['unused_applications']=application
    for cases in groups.values():
        for i,c in enumerate(cases):
            _,clauses=parse_dimacs(c['dimacs']);c.update(stage=i,encoding_bytes=encoding_size(clauses),sha256=digest(c['dimacs'].encode()))
    return groups,source

def worker(mode,cases,cap,timeout):
    with tempfile.TemporaryDirectory(prefix='oracle-priority-worker-') as d:
        directory=Path(d);service=None
        options=dict(backend='cadical',reuse_exact=False,learned=mode=='learned',adaptive=mode=='adaptive',
            incremental_proofs=mode in ('proof_live','proof_restart'),max_archive_bytes=cap,query_timeout=timeout,timeout=timeout)
        try:
            for c in cases:
                start=time.perf_counter_ns();row=dict(event='query',stage=c['stage'],name=c['name'],phase=c['phase'],expected=c['expected'],encoding_bytes=c['encoding_bytes'])
                try:
                    setup=time.perf_counter_ns()
                    if mode!='direct' and service is None:service=(PolaritySolver if mode=='polarity' else PersistentSolver)(directory/'s.db',**options)
                    row['setup_ns']=time.perf_counter_ns()-setup
                    if service is not None:service.last_metrics={}
                    if mode=='direct':
                        variables,clauses=parse_dimacs(c['dimacs'])
                        path=directory/'query.cnf';path.write_text(dimacs(clauses,variables))
                        run=bounded_run([str(harness.find_cadical()),'--quiet',str(path)],directory,Deadline(timeout),timeout,
                            64*1024**2,directory/'unused.proof',16*1024**2)
                        if run.returncode not in (10,20):raise ValueError(f'CaDiCaL exit {run.returncode}')
                        result=dict(answer=run.returncode==10,source='direct_unverified')
                    else:
                        if c['encoding_bytes']>service.max_input_bytes:raise BudgetExceeded('Encoded source exceeds input cap before allocation')
                        convert=time.perf_counter_ns();bits=encode_dimacs(c['dimacs']);row['conversion_ns']=time.perf_counter_ns()-convert
                        assert len(bits)==c['encoding_bytes']
                        result=service.solve(bits,learn=mode in ('portfolio','learned','polarity'))
                    row.update(status='ok' if result['answer']==c['expected'] else 'wrong',result={k:v for k,v in result.items() if k not in ('witness','certificate','original_measurements')})
                except Exception as e:row.update(status='error',error=type(e).__name__+': '+str(e),failure_metrics=service.last_metrics if service else {})
                row['elapsed_ns']=time.perf_counter_ns()-start;print(json.dumps(row),flush=True)
                if mode=='proof_restart' and service is not None:service.close();service=None
            if service:print(json.dumps(dict(event='end',usage=service.archive_usage(),entries=service.stats()['entries'])),flush=True)
        finally:
            if service:service.close()

def diagnostics():
    rows=[];rng=random.Random(1711)
    for repeat in range(3):
        for size in (256,1024):
            with tempfile.TemporaryDirectory() as d:
                path=Path(d)/'s.db';edges=[rng.getrandbits(256)|1 for _ in range(size)]
                with PersistentSolver(path,native_layer_cells=(2*size-1)*256) as s:
                    a=s.layered(4,append=edges,left=1,right=1)
                    b=s.layered(4,a['state'],replace={size//2:0},left=1,right=1)
                    c=s.layered(4,b['state'],left=1,right=1)
                    assert a['answer'] and not b['answer'] and not c['answer']
                    rows.append(dict(kind='distinct_layers',repeat=repeat,size=size,initial=a,edit=b,repeat_query=c))
                with PersistentSolver(path) as s:
                    r=s.layered(4,b['state'],left=1,right=1);assert not r['answer']
                    rows.append(dict(kind='layer_restart',repeat=repeat,size=size,result=r))
        for size in (16,64,320):
            with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db',interfaces=True) as s:
                a=s.expand(add={f'e{i}':xor(i,i+1) for i in range(size)})
                b=s.expand(a['state'],add={'e0':neg(xor(0,1))})
                c=s.expand(b['state'],add={'left':var(0),'right':var(size)})
                e=s.expand(c['state'],remove=['e0'])
                assert a['answer'] and b['answer'] and not c['answer'] and e['answer']
                rows.append(dict(kind='semantic_provenance',repeat=repeat,size=size,initial=a,equal_edit=b,negative=c,deletion=e))
        for size in (16,64,256):
            layers=[[i+1] for i in range(size+1)]
            clauses=[[i+1,i+2] for i in range(size)]+[[-i-1,-i-2] for i in range(size)]+[[1],[-size-1]]
            with tempfile.TemporaryDirectory() as d,PersistentSolver(Path(d)/'s.db') as s:
                r=s.layered_cnf(1,clauses,layers,witness=True);assert not r['answer']
                rows.append(dict(kind='compiled_source',repeat=repeat,size=size,result=r))
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--worker',choices=MODES)
    p.add_argument('--artifact',type=Path);p.add_argument('--archives',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--cap',type=int,default=64*1024**2);p.add_argument('--timeout',type=float,default=3);p.add_argument('--repeats',type=int,default=3)
    a=p.parse_args()
    if a.worker:worker(a.worker,json.load(sys.stdin),a.cap,a.timeout);return
    if not (a.artifact and a.archives and a.output):p.error('Supply archives and a fresh output directory')
    a.output.mkdir(parents=True,exist_ok=False);groups,source=inputs(a.artifact,a.archives)
    with gzip.open(a.output/'inputs.json.gz','wt') as f:json.dump(groups,f,separators=(',',':'))
    files=[Path(__file__),DEFAULT_ENGINE,harness.DEFAULT_INCREMENTAL,harness.find_cadical(),ROOT/'formal/Solver.lean',*sorted((ROOT/'solver').glob('*.py')),*sorted((ROOT/'formal/OracleMachines').glob('*.lean'))]
    metadata=dict(source=source,repeats=a.repeats,timeout=a.timeout,archive_cap=a.cap,input_cap=8*1024**2,
        seed_units=1710,seed_layers=1711,selection_frozen_before_timing=True,python=sys.version,host=platform.platform(),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        rss_watchdog=512*1024**2,scratch_watchdog=256*1024**2,sampling_ms=20,hard_total_resource_cap=False,
        acceptance='All service modes verify SAT/UNSAT; direct is an unverified CNF reference',
        fingerprints={str(f.relative_to(ROOT)) if f.is_relative_to(ROOT) else str(f):digest(f.read_bytes()) for f in files})
    (a.output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    harness.__file__=__file__;rows=[]
    with gzip.open(a.output/'runs.jsonl.gz','wt') as log:
        for name,cases in groups.items():
            for repeat in range(a.repeats):
                for mode in MODES[repeat:]+MODES[:repeat]:
                    row=harness.measured(mode,cases,a.cap,a.timeout);row.update(stream=name,mode=mode,repeat=repeat,planned=len(cases));rows.append(row)
                    log.write(json.dumps(row)+'\n');log.flush();print(name,repeat,mode,'complete',flush=True)
    summary=[]
    for name,cases in groups.items():
        for mode in MODES:
            selected=[r for r in rows if r['stream']==name and r['mode']==mode]
            queries=[q for r in selected for q in r['records'] if q['event']=='query']
            summary.append(dict(stream=name,mode=mode,planned=len(cases)*a.repeats,observed=len(queries),
                outcomes=dict(Counter(q['status'] for q in queries)),stops=dict(Counter(r['stop'] or 'completed' for r in selected)),
                median_stream_ms=statistics.median(sum(q['elapsed_ns'] for q in r['records'] if q['event']=='query')/1e6 for r in selected),
                peak_sampled_rss=max(r['sampled_peak_rss_bytes'] for r in selected),
                learned_hits=sum(q.get('result',{}).get('learned_accepted',False) for q in queries),
                proposal_outcomes=dict(Counter(v['outcome'] for q in queries for v in q.get('result',{}).get('proposals',{}).get('attempts',[])))))
    (a.output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    with gzip.open(a.output/'diagnostics.json.gz','wt') as f:json.dump(diagnostics(),f)
    print('all complete',flush=True)
if __name__=='__main__':main()
