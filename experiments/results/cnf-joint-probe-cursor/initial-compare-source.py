#!/usr/bin/env python3
"""Matched discovery and native trials for probes on the joint B8 frontier."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_cursor_feedback as prior,cnf_joint_probe_cursor as candidate,cnf_joint_probe_feedback as feedback
base=prior.base;old=prior.old;compact=prior.compact;bind=prior.bind;previous=prior.previous;native=feedback.native
PARENT=Path('experiments/results/cnf-joint-cursor-feedback')
FIELDS=prior.FIELDS
MODES=('restart','matched','reuse');NATIVE_MODES=('fresh','disabled','direct')
FILES=('experiments/cnf_joint_probe_cursor.py','experiments/cnf_joint_probe_feedback.py','experiments/compare_cnf_joint_probe_cursor.py','solver/test_cnf_joint_probe_cursor.py')


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');seeds=old.bound(cp['joint_cursor_feedback']['remaining-closures'])['rows']
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),parent_protocol=old.binding(PARENT/'protocol.json'),seeds=cp['joint_cursor_feedback']['remaining-closures'],
        targets=sorted({r['target'] for r in seeds}),pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES),list(reversed(MODES))],compilation_orders=[list(NATIVE_MODES),list(reversed(NATIVE_MODES))],
        limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),limitations=[
        'Seventeen exposed unresolved inputs; four changed joint banks, thirteen exact no-change candidates. No held-out or arbitrary-SAT coverage claim.',
        'Exact bank, closure including reason order, source-derived order and trace-bound equality permits checked B7 schedule reuse. Changed banks start fresh; open scheduling history is not a SAT certificate.',
        'Matched fresh adds the number of reused completions to its probe budget and scales its work allowance; outcomes must match. Restart is a bounded-frontier ablation, not the matched control.',
        'Two opposite-order isolated census repetitions charge full source-prefix reconstruction, joint preparation/discovery/search, independent cold semantic checking and serialization/reload. Historical acquisition, input loading/startup and final audit are additional.',
        'Feedback composition and complete remaining closures are separate measured diagnostics outside census totals. Native compilation trials cover only gained roots and exclude prior acquisition, census, composition and unresolved fallback.',
        'Every new failed assumption is checked on bank 8; feedback creates bank 9. Native recursion strictly decreases the proof bank and only publishes source-clause empty, units or split rules.',
        'Fresh, disabled-shortcut reconstruction and bounded direct reconstruction are measured on identical roots including warm checks, both cold readers and persistence. Direct unit work is globally bounded at 262144 with trace bound 256.',
        'All earlier proof/artifact/source fingerprints and cumulative/reference tables remain unchanged; new archives are supplemental. Retained input history is still duplicated and lifetime storage grows.']))


def inputs(p,target):
    source,ts,refs,events=prior.inputs(old.bound(p['parent_protocol']),target)
    saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    return source,ts,[(r,saved[r['event']]) for r in refs if r['event'] in saved],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref,seed in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==seed['final_source'] and hints==seed['templates']
        args=(state['local'],hints,*(seed[k] for k in FIELDS[2:]));cc=Counter();tick=time.perf_counter()
        result=candidate.discover(*args,closure=seed['joint_cursor_feedback_closure'],counts=cc,policy=mode,**p['limits']);discovery=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'result-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();candidate.validate(*args,closure=seed['joint_cursor_feedback_closure'],result=cold,counts=vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,counts=dict(cc),verification_counts=dict(vc),reconstruction_counts=dict(rc),
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
    p=base.load(out/'protocol.json');known={(r['target'],r['event']):r for r in base.load(Path('experiments/results/cnf-shortening-budget-frontier/residual-diagnosis.json'))['rows']}
    cases=[];proposals=[];remaining=[];diagnostics=[];seen=set()
    for target in p['targets']:
        source,ts,refs,events=inputs(p,target);results={r['event']:old.bound(r['result']) for r in base.load(out/f'census-{target}-reuse-0/events.json')['rows']}
        for ref,seed in refs:
            result=results[ref['event']];args=tuple(seed[k] for k in FIELDS);cl=seed['joint_cursor_feedback_closure'];cc=Counter();tick=time.perf_counter()
            program=feedback.discover(*args,result,closure=cl,counts=cc);feedback.validate(*args,result,closure=cl,program=program,counts=Counter());seconds=time.perf_counter()-tick
            diagnostics.append(dict(target=target,event=ref['event'],program=program,counts=dict(cc),seconds=seconds))
            row=dict(seed,joint_probe_cursor=result,joint_probe_feedback=program)
            if program['status']!='refuted':remaining.append(row);continue
            key=(target,ref['event']);proposals.append(dict(target=target,event=ref['event'],root=ref['root'],snapshot_answer=known[key]['snapshot_answer'],duplicate=ref['root'] in seen))
            if ref['root'] in seen:continue
            seen.add(ref['root']);local,templates,state=bind(source,ts,ref,events[ref['event']],Counter());name=f'new-{target}-{ref["event"]}';path=out/(name+'.json')
            compact(path,dict(name=name,source=local,templates=templates,prefix=ref['program'],**{k:seed[k] for k in FIELDS[2:]},closure=cl,
                search=result,program=program,root=ref['root'],target=target,event=ref['event'],snapshot_answer=known[key]['snapshot_answer']))
            cases.append(old.binding(path))
    base.write(out/'cases.json',dict(cases=cases,proposals=proposals));compact(out/'remaining.json',dict(rows=remaining));compact(out/'feedback-diagnostics.json',dict(rows=diagnostics))


def trial(out,dest,index,mode):
    binding=base.load(out/'cases.json')['cases'][index];case=old.bound(binding);dest.mkdir();start=time.perf_counter();cc=Counter()
    def compile(solver,counts):
        program=case['program']
        return feedback.compile_extension(solver,case['source'],case['templates'],case['prefix'],*(case[k] for k in FIELDS[2:]),case['search'],closure=case['closure'],program=program,counts=counts,shortcut='off' if mode=='disabled' else 'all')
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
