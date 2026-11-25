#!/usr/bin/env python3
"""Compare full-clause probes with source-only and binary-guard controls."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_budget_frontier as prior
from experiments import cnf_wide_guard_probes as candidate
base=prior.base;old=prior.old;previous=prior.previous;native=prior.native
PARENT=Path('experiments/results/cnf-shortening-budget-frontier')
MODES=('source','binary','all')
FILES=('experiments/cnf_wide_guard_probes.py','experiments/compare_cnf_wide_guard_probes.py','solver/test_cnf_wide_guard_probes.py')


def compact(path,data):path.write_text(base.encode(data)+'\n')


def prepare(out):
    assert not (out/'protocol.json').exists();out.mkdir(exist_ok=True);cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    p=old.bound(cp['shortening_budget_frontier']['protocol'])
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],
        limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),orders=[list(MODES),list(reversed(MODES))],compilation_orders=[['fresh','extension'],['extension','fresh']],
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=['All246 remaining events after frozen prepared256 discovery, including one root-budget stop and15 snapshot-unknown events. Two alternating isolated repetitions per target/arm.',
        'Source-only, source plus binary guards, and source plus all guards use the same source-based literal order and64 single-literal assumptions plus one unconditional probe. Failed exclusions are not iteratively fed back.',
        'One clause-occurrence index per discovery, reused across probes. Every probe initializes clause counters; copying, XOR bookkeeping, recognition and index work are charged separately from the262144 occurrence-visit cap.',
        'Input binding and independent binary-prefix replay are timed as reconstruction. Earlier prepared256 discovery, acquisition, loading, startup and final audits are additional. No live default or whole-query speed claim.',
        'Every successful probe has a separately checked extended-clause trace, with each guard bound to source-only evidence. Native compilation uses only existing unit, empty and split rules; no extended clause is accepted as a native axiom.',
        'All newly refuted local roots across the three arms enter fresh/extension comparisons, including the earlier binary prefix. Incomplete outcomes remain unresolved, never SAT.']))


def inputs(p,target):
    source,ts,refs,events=prior.prior.reuse.inputs(p,target)
    report=base.load(PARENT/f'census-{target}-prepared256-0/report.json')
    remaining=[r for r in old.bound(report['events'])['rows'] if r['program']['status']!='refuted']
    return source,ts,remaining,events


def bind(source,ts,row,event,c):
    local,hints,_=previous.local_hints(source,ts,event,c);templates=[h['template'] for h in hints]
    frames,state=candidate.bind_prefix(local,templates,row['program'],c)
    return local,templates,state


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        c=Counter();tick=time.perf_counter();local,templates,state=bind(source,ts,ref,events[ref['event']],c);reconstruction=time.perf_counter()-tick
        rc=dict(c);c=Counter();tick=time.perf_counter();program=candidate.discover(state['local'],[h['template'] for h in state['hints']],c,mode=mode,**p['limits']);elapsed=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],program=program,counts=dict(c),reconstruction_counts=rc,reconstruction_seconds=reconstruction,discovery_seconds=elapsed))
    compact(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        discovery_seconds=sum(r['discovery_seconds'] for r in rows),reconstruction_seconds=sum(r['reconstruction_seconds'] for r in rows),
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter()))))


def run_census(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'census-{target}-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'census',str(out),str(dest),str(target),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),target=target,mode=mode,repeat=repeat))
        print(base.encode(dict(target=target)),flush=True)
    base.write(out/'censuses.json',dict(samples=samples))


def cases(out):
    p=base.load(out/'protocol.json');cases=[];seen=set();proposals=[]
    known={(r['target'],r['event']):r for r in base.load(PARENT/'residual-diagnosis.json')['rows']}
    for target in p['targets']:
        source,ts,refs,events=inputs(p,target);byevent={r['event']:r for r in refs}
        for mode in MODES:
            report=base.load(out/f'census-{target}-{mode}-0/report.json')
            for r in old.bound(report['events'])['rows']:
                if r['program']['status']!='refuted':continue
                snapshot=known[(target,r['event'])]['snapshot_answer']
                proposals.append(dict(target=target,event=r['event'],root=r['root'],mode=mode,snapshot_answer=snapshot,duplicate=r['root'] in seen))
                if r['root'] in seen:continue
                seen.add(r['root']);ref=byevent[r['event']];local,templates,state=bind(source,ts,ref,events[r['event']],Counter())
                candidate.validate(state['local'],[h['template'] for h in state['hints']],r['program'],Counter())
                name=f'new-{target}-{r["event"]}';path=out/(name+'.json')
                compact(path,dict(name=name,source=local,templates=templates,prefix=ref['program'],program=r['program'],root=r['root'],target=target,event=r['event'],mode=mode,snapshot_answer=snapshot))
                cases.append(old.binding(path))
    base.write(out/'cases.json',dict(cases=cases,proposals=proposals));print(base.encode(dict(new_roots=len(cases),proposals=len(proposals))),flush=True)


def trial(out,dest,index,mode):
    binding=base.load(out/'cases.json')['cases'][index];case=old.bound(binding);dest.mkdir();start=time.perf_counter();c=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=previous.LazyBinaryClosureSolver(path,node_limit=256) if mode=='fresh' else native.ResidualSolver(path)
        try:
            tick=time.perf_counter()
            if mode=='fresh':result=previous.attempt(s,case['source'])
            else:
                root=candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['program'],c)
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(s.db);nc=dict(s.counts);tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(s,case['source'])['status']=='unsat'
                else:assert candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['program'],Counter())==case['root']
            warm=time.perf_counter()-tick;assert tables==old.tables(s.db)
        finally:s.close()
        tick=time.perf_counter();actual,readers=previous.audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert tables==actual
        tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
    base.write(dest/'report.json',dict(case=binding,mode=mode,result=result,counts=dict(c),native_counts=nc,solve_seconds=solve,warm_seconds=warm,cold_seconds=cold,
        persistence_seconds=persistence,complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        authority_tables={t:len(v) for t,v in tables.items()},digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},
        record_bytes=sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items()),archive=archive,readers=readers))


def run_trials(out):
    p=base.load(out/'protocol.json');cases=base.load(out/'cases.json')['cases'];samples=[]
    for index in range(len(cases)):
        for repeat,order in enumerate(p['compilation_orders']):
            for mode in order:
                dest=out/f'case-{index}-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),str(index),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),index=index,mode=mode,repeat=repeat))
        print(base.encode(dict(case=index,total=len(cases))),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census':census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:globals()[action](out)
