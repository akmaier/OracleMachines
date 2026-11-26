#!/usr/bin/env python3
"""Compare B6/B7 failure composition and source-only native certificates."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_fused_b7_expansion as prior,compare_cnf_b5_cursor_feedback as legacy,cnf_joint_cursor_feedback as candidate
base=prior.base;old=prior.old;compact=prior.compact;bind=prior.bind;previous=legacy.previous;native=candidate.native
PARENT=Path('experiments/results/cnf-fused-b7-expansion')
FIELDS=(*prior.FIELDS,'b6_cursor_feedback_closure','b7_probe_cursor','b6_comparison_cursor')
MODES=candidate.MODES;NATIVE_MODES=('fresh','disabled','b7_direct','joint_direct')
FILES=('experiments/cnf_joint_cursor_feedback.py','experiments/compare_cnf_joint_cursor_feedback.py','solver/test_cnf_joint_cursor_feedback.py')


def pilot(out):
    out.mkdir();rows=[];cp=base.load(PARENT/'checkpoint.json')
    for seed in old.bound(cp['fused_b7_expansion']['remaining'])['rows']:
        args=tuple(seed[k] for k in FIELDS);arms={}
        for mode in MODES:
            cc=Counter();p=candidate.discover(*args,counts=cc,mode=mode);prepared=candidate.validate(*args,program=p,counts=Counter())
            dc=Counter();fixed,trace,conflict=native.propagate(prepared[17],dc)
            scan=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]),conflict=conflict)
            arms[mode]=dict(program=p,counts=dict(cc),scan=scan,scan_counts=dict(dc))
        rows.append(dict(target=seed['target'],event=seed['event'],arms=arms))
    compact(out/'pilot.json',dict(rows=rows));(out/'pilot-source.py').write_bytes(Path(FILES[0]).read_bytes())


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');p=base.load(PARENT/'protocol.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),seeds=cp['fused_b7_expansion']['remaining'],
        old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES),list(reversed(MODES))],compilation_orders=[list(NATIVE_MODES),list(reversed(NATIVE_MODES))],
        limits=dict(work_limit=262144,trace_limit=256),limitations=[
        'Eighteen exposed inputs; no held-out coverage claim. Both complete histories are checked on their original banks before composition. All controls pay this same validation; base is an ablation, not an optimized old-search runtime baseline.',
        'Base retains B7. B6-only adds the B6 comparison failures, B7-only adds the new B7 failures, and joint adds both. All use zero fresh assumptions. Duplicate units retain an earlier valid origin.',
        'Two opposite-order isolated census repetitions charge source-prefix reconstruction, complete discovery/preparation/recognition/indexing, serialization/reload and independent semantic verification. Startup/loading, historical acquisition, scan diagnostics and final audit are additional.',
        'Both B7-only and joint refute the same new sampled case. Joint must not be credited with a refutation unavailable to B7-only; its benefit is the source-only certificate cost.',
        'Native compilation checks inputs before warm lookup, follows strictly decreasing bank dependencies, and uses only source-clause native records. The first generic compiler retains the full source without support selection.',
        'Native comparisons cover all newly recognized roots: bounded fresh solving, joint reconstruction with direct units disabled, B7-only direct reconstruction and joint direct reconstruction. Warm checking, both cold readers and serialization are charged. Prior acquisition, discovery and unresolved fallback are additional.',
        'Direct units use only canonical source residuals with a global 262144 work allowance and 256 trace bound. Earlier source results, proofs, cumulative tables and production defaults remain unchanged; archives are supplemental.',
        'Open exports retain both original histories and append checked joint closures. Changed clause sets invalidate earlier scheduling bindings. Native context growth, lifetime storage and unrestricted-SAT bounds remain open.']))


def inputs(p,target):
    source,ts,refs,events=prior.prior.inputs(p,target);saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    return source,ts,[dict(r,**{k:saved[r['event']][k] for k in FIELDS[15:]}) for r in refs],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==ref['saved_source'] and hints==ref['saved_templates']
        args=(state['local'],hints,*(ref[k] for k in FIELDS[2:]));cc=Counter();tick=time.perf_counter();program=candidate.discover(*args,counts=cc,mode=mode,**p['limits']);discovery=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'program-{ref["event"]}.json';compact(path,program);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();candidate.validate(*args,program=cold,counts=vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],program=binding,counts=dict(cc),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,discovery_seconds=discovery,persistence_seconds=persistence,verification_seconds=verification,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows));base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','record_bytes')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter()))))


def run_census(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'census-{target}-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'census',str(out),str(dest),str(target),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),target=target,mode=mode,repeat=repeat))
        print(base.encode(dict(completed_target=target)),flush=True)
    base.write(out/'censuses.json',dict(samples=samples))


def cases(out):
    p=base.load(out/'protocol.json');saved={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']}
    known={(r['target'],r['event']):r for r in base.load(Path('experiments/results/cnf-shortening-budget-frontier/residual-diagnosis.json'))['rows']}
    cases=[];proposals=[];remaining=[];seen=set()
    for target in p['targets']:
        source,ts,refs,events=inputs(p,target);byevent={r['event']:r for r in refs}
        controls={mode:{r['event']:old.bound(r['program']) for r in base.load(out/f'census-{target}-{mode}-0/events.json')['rows']} for mode in MODES}
        for event,ref in byevent.items():
            seed=saved[target,event];program=controls['joint'][event]
            if program['status']!='refuted':remaining.append(dict(seed,joint_cursor_feedback=program));continue
            proposals.append(dict(target=target,event=event,root=ref['root'],snapshot_answer=known[target,event]['snapshot_answer'],duplicate=ref['root'] in seen))
            if ref['root'] in seen:continue
            seen.add(ref['root']);local,templates,state=bind(source,ts,ref,events[event],Counter());name=f'new-{target}-{event}';path=out/(name+'.json')
            compact(path,dict(name=name,source=local,templates=templates,prefix=ref['program'],**{k:seed[k] for k in FIELDS[2:]},
                programs={mode:controls[mode][event] for mode in MODES},root=ref['root'],target=target,event=event,snapshot_answer=known[target,event]['snapshot_answer']))
            cases.append(old.binding(path))
    base.write(out/'cases.json',dict(cases=cases,proposals=proposals));compact(out/'remaining.json',dict(rows=remaining))


def trial(out,dest,index,mode):
    binding=base.load(out/'cases.json')['cases'][index];case=old.bound(binding);dest.mkdir();start=time.perf_counter();cc=Counter()
    def compile(solver,counts):
        program=case['programs']['b7_only' if mode=='b7_direct' else 'joint']
        return candidate.compile_extension(solver,case['source'],case['templates'],case['prefix'],*(case[k] for k in FIELDS[2:]),program=program,counts=counts,shortcut='off' if mode=='disabled' else 'all')
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=previous.LazyBinaryClosureSolver(path,node_limit=256) if mode=='fresh' else native.ResidualSolver(path)
        try:
            tick=time.perf_counter()
            if mode=='fresh':result=previous.attempt(s,case['source'])
            else:result=dict(status='unsat',result=dict(root=compile(s,cc),answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(s.db);nc=dict(s.counts);tick=time.perf_counter()
            if mode=='fresh':assert previous.attempt(s,case['source'])['status']=='unsat'
            else:assert compile(s,Counter())==case['root']
            warm=time.perf_counter()-tick;assert tables==old.tables(s.db)
        finally:s.close()
        tick=time.perf_counter();actual,readers=previous.audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert tables==actual
        tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
    base.write(dest/'report.json',dict(case=binding,mode=mode,result=result,counts=dict(cc),native_counts=nc,solve_seconds=solve,warm_seconds=warm,cold_seconds=cold,
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
    base.write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census':census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:globals()[action](out)
