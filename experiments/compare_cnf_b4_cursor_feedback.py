#!/usr/bin/env python3
"""Matched B4/B5 composition and bounded direct native unit certificates."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b4_probe_cursor as prior
from experiments import cnf_b4_cursor_feedback as candidate
base=prior.base;old=prior.old;previous=prior.prior.previous;native=candidate.native
PARENT=Path('experiments/results/cnf-b4-probe-cursor')
MODES=('base','feedback')
FILES=('experiments/cnf_b4_cursor_feedback.py','experiments/compare_cnf_b4_cursor_feedback.py','solver/test_cnf_b4_cursor_feedback.py')
compact=prior.compact;bind=prior.prior.bind


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    p=base.load(PARENT/'protocol.json')
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        seeds=old.binding(PARENT/'remaining.json'),seed_protocol=old.binding(PARENT/'protocol.json'),old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],
        pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),
        limits=dict(work_limit=262144,trace_limit=256),orders=[list(MODES),list(reversed(MODES))],compilation_orders=[['fresh','baseline','direct'],['direct','baseline','fresh']],
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
        'Same29 retained B4 closures/cursors;69 verified failures in13 cases. Pilot exposed before timing; no holdout. Zero new assumed probes.',
        'Both arms check all source/guard/probe/closure provenance, both cursor bindings and failed proofs, and construct B5. Base propagates B4; feedback propagates B5.',
        'Only checked failed assumptions become exclusions. Native reconstruction expands used derivations through strictly decreasing banks B5 to B0; open-history claims never provide axioms.',
        'Two opposite-order isolated repetitions per target and arm. Source-prefix reconstruction, discovery preparation, indexing, checking and propagation are charged. Startup/loading, historical acquisition, final audit and diagnostic open closures are additional.',
        'Native comparisons cover all distinct new roots: fresh bounded solving, new B5 compiler with shortcut disabled, and bounded direct unit closure at every trace entry. Both readers, warm checks and persistence are charged. Prior acquisition, discovery and unresolved fallback are additional.',
        'Direct unit shortcuts use only the canonical source residual, with the inherited262144 work allowance and256 trace bound. Existing source support selection, publication handoff, native rules and checks remain.',
        'Isolated archives may duplicate content. Open states retain old layers and complete B5 closures; old B4 history cannot skip changed B5 candidates. Cumulative tables and production defaults are unchanged.',
        'Finite sampled coverage and cheaper positive certificates do not bound unrestricted SAT, future proof layers, distinct contexts or lifetime memory.']))



def inputs(p,target):
    source,ts,refs,events=prior.inputs(p,target)
    saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    return source,ts,[dict(ref,b4_probe_cursor=saved[ref['event']]['b4_probe_cursor']) for ref in refs],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        c=Counter();tick=time.perf_counter();local,templates,state=bind(source,ts,ref,events[ref['event']],c);reconstruction=time.perf_counter()-tick
        rc=dict(c);c=Counter();tick=time.perf_counter();hints=[h['template'] for h in state['hints']]
        assert list(map(list,state['local']))==ref['saved_source'] and hints==ref['saved_templates']
        program=candidate.discover(state['local'],hints,ref['seed'],ref['closure'],ref['new'],ref['next_closure'],ref['third'],ref['feedback_closure'],ref['probe_cursor'],ref['cursor_feedback_closure'],ref['b4_probe_cursor'],c,mode=mode,**p['limits'])
        elapsed=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],program=program,counts=dict(c),reconstruction_counts=rc,reconstruction_seconds=reconstruction,discovery_seconds=elapsed))
    compact(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        discovery_seconds=sum(r['discovery_seconds'] for r in rows),reconstruction_seconds=sum(r['reconstruction_seconds'] for r in rows),
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter()))))


def cases(out):
    p=base.load(out/'protocol.json');cases=[];seen=set();proposals=[];remaining=[]
    saved={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']}
    known={(r['target'],r['event']):r for r in base.load(Path('experiments/results/cnf-shortening-budget-frontier/residual-diagnosis.json'))['rows']}
    for target in p['targets']:
        source,ts,refs,events=inputs(p,target);byevent={r['event']:r for r in refs}
        for r in base.load(out/f'census-{target}-feedback-0/events.json')['rows']:
            key=(target,r['event'])
            if r['program']['status']!='refuted':
                remaining.append(dict(saved[key],b4_cursor_feedback=r['program']));continue
            snapshot=known[key]['snapshot_answer']
            proposals.append(dict(target=target,event=r['event'],root=r['root'],snapshot_answer=snapshot,duplicate=r['root'] in seen))
            if r['root'] in seen:continue
            seen.add(r['root']);ref=byevent[r['event']];local,templates,state=bind(source,ts,ref,events[r['event']],Counter())
            candidate.validate(state['local'],[h['template'] for h in state['hints']],ref['seed'],ref['closure'],ref['new'],ref['next_closure'],ref['third'],ref['feedback_closure'],ref['probe_cursor'],ref['cursor_feedback_closure'],ref['b4_probe_cursor'],r['program'],Counter())
            name=f'new-{target}-{r["event"]}';path=out/(name+'.json')
            compact(path,dict(name=name,source=local,templates=templates,prefix=ref['program'],seed=ref['seed'],closure=ref['closure'],new=ref['new'],next_closure=ref['next_closure'],third=ref['third'],feedback_closure=ref['feedback_closure'],probe_cursor=ref['probe_cursor'],cursor_feedback_closure=ref['cursor_feedback_closure'],b4_probe_cursor=ref['b4_probe_cursor'],program=r['program'],root=r['root'],target=target,event=r['event'],snapshot_answer=snapshot))
            cases.append(old.binding(path))
    base.write(out/'cases.json',dict(cases=cases,proposals=proposals));compact(out/'remaining.json',dict(rows=remaining))
    print(base.encode(dict(new_roots=len(cases),proposals=len(proposals),remaining=len(remaining))),flush=True)


def run_census(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'census-{target}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'census',str(out),str(dest),str(target),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),target=target,mode=mode,repeat=repeat))
    base.write(out/'censuses.json',dict(samples=samples))


def trial(out,dest,index,mode):
    binding=base.load(out/'cases.json')['cases'][index];case=old.bound(binding);dest.mkdir();start=time.perf_counter();c=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=previous.LazyBinaryClosureSolver(path,node_limit=256) if mode=='fresh' else native.ResidualSolver(path)
        try:
            tick=time.perf_counter()
            if mode=='fresh':result=previous.attempt(s,case['source'])
            else:
                root=candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['next_closure'],case['third'],case['feedback_closure'],case['probe_cursor'],case['cursor_feedback_closure'],case['b4_probe_cursor'],case['program'],c,shortcut='off' if mode=='baseline' else 'all')
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(s.db);nc=dict(s.counts);tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(s,case['source'])['status']=='unsat'
                else:assert candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['next_closure'],case['third'],case['feedback_closure'],case['probe_cursor'],case['cursor_feedback_closure'],case['b4_probe_cursor'],case['program'],Counter(),shortcut='off' if mode=='baseline' else 'all')==case['root']
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
