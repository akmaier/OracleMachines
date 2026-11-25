#!/usr/bin/env python3
"""B6 discovery with exact cross-layer cursor migration versus fresh frontiers."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,time,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b5_cursor_feedback as prior,cnf_b6_probe_cursor as candidate,cnf_b6_probe_native as compiler
base=prior.base;old=prior.old;compact=prior.compact;previous=prior.previous;native=candidate.native
PARENT=Path('experiments/results/cnf-b5-cursor-feedback')
SEEDS=PARENT
MODES=('restart','matched','reuse')
FIELDS=('final_source','templates','seed','closure','new','next_closure','third','feedback_closure','probe_cursor','cursor_feedback_closure','b4_probe_cursor','b4_cursor_feedback_closure','b5_probe_cursor','b5_cursor_feedback_closure')
FILES=('experiments/cnf_b6_probe_cursor.py','experiments/cnf_b6_probe_native.py','experiments/compare_cnf_b6_probe_cursor.py','solver/test_cnf_b6_probe_cursor.py')


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');p=base.load(SEEDS/'protocol.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    pilot=base.load(out/'pilot.json')['rows']
    same=[[r['target'],r['event']] for r in pilot if r['arms']['reuse']['counts'].get('b6_imported_cursors',0)]
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        seeds=old.binding(SEEDS/'remaining-closures.json'),seed_protocol=old.binding(SEEDS/'protocol.json'),old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],
        pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),matching_frontier_cases=same,
        limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),orders=[list(MODES),list(reversed(MODES))],compilation_orders=[['fresh','direct'],['direct','fresh']],
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
        'Same19 exposed open B6 cases; seven changed, twelve exact B5/B6 bank and closure matches. No holdout; pilot exposed before timing.',
        'Restart attempts64 per case. Reuse imports a checked B5 cursor only when full bank and closure including trace and trace bound agree, then attempts64 more; changed cases start fresh. Both old and new schedules/proofs are checked.',
        'Matched control reaches the same frontier from scratch:64 plus the retained completed prefix on the12 pilot-identified exact matches,64 otherwise. The matched allowance is262144 times the number of64-attempt chunks rounded up. These fixed matched budgets are experimental controls; all arms still pay current preparation and exact comparison.',
        'A fresh64 chunk has262144 occurrence visits and256 trace steps including closure prefix. Index construction, per-probe initialization, exact content bindings and verification are extra. No global linear-work bound.',
        'All prior history acquisition is already paid and excluded from current continuation costs. Claimed open-history entries remain trusted scheduling data, not SAT or exhaustion proofs. No cross-bank skip without exact equality.',
        'Two opposite-order isolated repetitions. Census includes source-prefix reconstruction, discovery/preparation, serialization/reload, cold semantic verification and reporting. Startup/loading, earlier acquisition and final audit are additional.',
        'Native positive comparisons use fresh bounded solving and the measured direct-unit seven-bank compiler. Warm checks, both cold readers and persistence are charged, but discovery, acquisition and unresolved fallback are excluded.',
        'New results preserve old layers and cursors. Exact bindings duplicate content, isolated archives may duplicate records and lifetime storage remains unbounded. No production default or unrestricted SAT claim.']))



def inputs(p,target):
    source,ts,refs,events=prior.inputs(p,target)
    saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    return source,ts,[dict(ref,b5_cursor_feedback_closure=saved[ref['event']]['b5_cursor_feedback_closure']) for ref in refs],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=prior.bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']]
        assert list(map(list,state['local']))==ref['saved_source'] and hints==ref['saved_templates']
        args=(state['local'],hints,*(ref[k] for k in FIELDS[2:]))
        limits=dict(p['limits'])
        if mode=='matched' and [target,ref['event']] in p['matching_frontier_cases']:
            limits['probe_limit']+=len(ref['b5_probe_cursor']['cursor']['completed']);limits['work_limit']*=((limits['probe_limit']+63)//64)
        c=Counter();tick=time.perf_counter();result=candidate.discover(*args,c,policy='reuse' if mode=='reuse' else 'restart',**limits);discovery=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'cursor-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();candidate.validate(*args,cold,vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,counts=dict(c),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,discovery_seconds=discovery,persistence_seconds=persistence,verification_seconds=verification,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','record_bytes')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter()))))


def run_census(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'census-{target}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'census',str(out),str(dest),str(target),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),target=target,mode=mode,repeat=repeat))
        print(base.encode(dict(completed_target=target)),flush=True)
    base.write(out/'censuses.json',dict(samples=samples))


def cases(out):
    p=base.load(out/'protocol.json');cases=[];seen=set();proposals=[];remaining=[]
    saved={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']}
    known={(r['target'],r['event']):r for r in base.load(Path('experiments/results/cnf-shortening-budget-frontier/residual-diagnosis.json'))['rows']}
    for target in p['targets']:
        source,ts,refs,events=inputs(p,target);byevent={r['event']:r for r in refs}
        for r in base.load(out/f'census-{target}-reuse-0/events.json')['rows']:
            r=dict(r,result=old.bound(r['result']));key=(target,r['event'])
            if r['result']['program']['status']!='refuted':
                remaining.append(dict(saved[key],b6_probe_cursor=r['result']));continue
            snapshot=known[key]['snapshot_answer']
            proposals.append(dict(target=target,event=r['event'],root=r['root'],snapshot_answer=snapshot,duplicate=r['root'] in seen))
            if r['root'] in seen:continue
            seen.add(r['root']);ref=byevent[r['event']];local,templates,state=prior.bind(source,ts,ref,events[r['event']],Counter())
            candidate.validate(state['local'],[h['template'] for h in state['hints']],ref['seed'],ref['closure'],ref['new'],ref['next_closure'],ref['third'],ref['feedback_closure'],ref['probe_cursor'],ref['cursor_feedback_closure'],ref['b4_probe_cursor'],ref['b4_cursor_feedback_closure'],ref['b5_probe_cursor'],ref['b5_cursor_feedback_closure'],r['result'],Counter())
            name=f'new-{target}-{r["event"]}';path=out/(name+'.json')
            compact(path,dict(name=name,source=local,templates=templates,prefix=ref['program'],seed=ref['seed'],closure=ref['closure'],new=ref['new'],next_closure=ref['next_closure'],third=ref['third'],feedback_closure=ref['feedback_closure'],probe_cursor=ref['probe_cursor'],cursor_feedback_closure=ref['cursor_feedback_closure'],b4_probe_cursor=ref['b4_probe_cursor'],b4_cursor_feedback_closure=ref['b4_cursor_feedback_closure'],b5_probe_cursor=ref['b5_probe_cursor'],b5_cursor_feedback_closure=ref['b5_cursor_feedback_closure'],result=r['result'],root=r['root'],target=target,event=r['event'],snapshot_answer=snapshot))
            cases.append(old.binding(path))
    base.write(out/'cases.json',dict(cases=cases,proposals=proposals));compact(out/'remaining.json',dict(rows=remaining))
    print(base.encode(dict(new_roots=len(cases),proposals=len(proposals),remaining=len(remaining))),flush=True)


def trial(out,dest,index,mode):
    binding=base.load(out/'cases.json')['cases'][index];case=old.bound(binding);dest.mkdir();start=time.perf_counter();c=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=previous.LazyBinaryClosureSolver(path,node_limit=256) if mode=='fresh' else native.ResidualSolver(path)
        try:
            tick=time.perf_counter()
            if mode=='fresh':result=previous.attempt(s,case['source'])
            else:
                root=compiler.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['next_closure'],case['third'],case['feedback_closure'],case['probe_cursor'],case['cursor_feedback_closure'],case['b4_probe_cursor'],case['b4_cursor_feedback_closure'],case['b5_probe_cursor'],case['b5_cursor_feedback_closure'],case['result'],c)
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(s.db);nc=dict(s.counts);tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(s,case['source'])['status']=='unsat'
                else:assert compiler.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['next_closure'],case['third'],case['feedback_closure'],case['probe_cursor'],case['cursor_feedback_closure'],case['b4_probe_cursor'],case['b4_cursor_feedback_closure'],case['b5_probe_cursor'],case['b5_cursor_feedback_closure'],case['result'],Counter())==case['root']
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
