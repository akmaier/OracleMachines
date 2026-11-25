#!/usr/bin/env python3
"""One-pass feedback of saved failed-probe exclusions, including native costs."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_complement_probes as prior
from experiments import cnf_probe_feedback as candidate
base=prior.base;old=prior.old;previous=prior.previous;native=prior.native
PARENT=Path('experiments/results/cnf-probe-support')
SEEDS=Path('experiments/results/cnf-complement-probes')
MODES=('base','feedback')
FILES=('experiments/cnf_probe_feedback.py','experiments/compare_cnf_probe_feedback.py','solver/test_cnf_probe_feedback.py')
compact=prior.compact;bind=prior.bind


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    p=base.load(SEEDS/'protocol.json')
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        seed_protocol=old.binding(SEEDS/'protocol.json'),old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],
        limits=dict(work_limit=262144,trace_limit=256),orders=[list(MODES),list(reversed(MODES))],compilation_orders=[['fresh','feedback'],['feedback','fresh']],
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=['Same180 unresolved all-guard complement-schedule events. Base and feedback each check saved seeds and run one unconditional propagation pass; no new assumed probes.',
        'Feedback adds the opposite of each retained failed assumption as a unit with its independently checked original-bank proof. Only one pass; no new failed-literal discovery or iterative closure.',
        'Saved-prefix reconstruction, seed checking, bank/index preparation and propagation are charged. Earlier seed acquisition/discovery, input loading, startup and final audit are additional.',
        'The pilot exposed all180 outcomes before this fixed matched timing/certification study; no independent holdout or novelty claim.',
        'Every used learned unit expands through its original failed-probe proof under the current context. Causal source supports, existing native splits and subset wrappers preserve authority; binary-prefix lifting is unchanged.',
        'All newly refuted roots enter fresh/feedback native comparisons including warm checking, both cold readers and persistence. Open/budget outcomes remain unresolved, never SAT.']))


def inputs(p,target):
    source,ts,refs,events=prior.inputs(p,target);byevent={r['event']:r for r in refs}
    report=base.load(SEEDS/f'census-{target}-all-complement-0/report.json');rows=[]
    for row in old.bound(report['events'])['rows']:
        if row['program']['status']=='refuted':continue
        rows.append(dict(byevent[row['event']],seed=row['program']))
    return source,ts,rows,events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        c=Counter();tick=time.perf_counter();local,templates,state=bind(source,ts,ref,events[ref['event']],c);reconstruction=time.perf_counter()-tick
        rc=dict(c);c=Counter();tick=time.perf_counter();hints=[h['template'] for h in state['hints']]
        if mode=='feedback':program=candidate.discover(state['local'],hints,ref['seed'],c,**p['limits'])
        else:
            _,_,bank,_=candidate.frozen.validate(state['local'],hints,ref['seed'],c);index=candidate.frozen.UnitIndex(bank,c);begin=c['probe_occurrence_visits']
            try:proof=index.probe(None,c,lambda:p['limits']['work_limit']-(c['probe_occurrence_visits']-begin),p['limits']['trace_limit']);reason='units' if proof is not None else 'open'
            except candidate.frozen.ProbeLimit as error:proof=None;reason=str(error)
            program=dict(status='refuted' if proof is not None else 'unresolved',reason=reason,trace_limit=p['limits']['trace_limit'],proof=proof)
        elapsed=time.perf_counter()-tick
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
    known={(r['target'],r['event']):r for r in base.load(prior.prior.PARENT/'residual-diagnosis.json')['rows']}
    for target in p['targets']:
        source,ts,refs,events=inputs(p,target);byevent={r['event']:r for r in refs}
        report=base.load(out/f'census-{target}-feedback-0/report.json')
        for r in old.bound(report['events'])['rows']:
            if r['program']['status']!='refuted':continue
            snapshot=known[(target,r['event'])]['snapshot_answer'];proposals.append(dict(target=target,event=r['event'],root=r['root'],snapshot_answer=snapshot,duplicate=r['root'] in seen))
            if r['root'] in seen:continue
            seen.add(r['root']);ref=byevent[r['event']];local,templates,state=bind(source,ts,ref,events[r['event']],Counter())
            candidate.validate(state['local'],[h['template'] for h in state['hints']],ref['seed'],r['program'],Counter())
            name=f'new-{target}-{r["event"]}';path=out/(name+'.json')
            compact(path,dict(name=name,source=local,templates=templates,prefix=ref['program'],seed=ref['seed'],program=r['program'],root=r['root'],target=target,event=r['event'],snapshot_answer=snapshot))
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
                root=candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['program'],c)
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(s.db);nc=dict(s.counts);tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(s,case['source'])['status']=='unsat'
                else:assert candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['program'],Counter())==case['root']
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
