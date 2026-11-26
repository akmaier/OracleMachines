#!/usr/bin/env python3
"""Compare B10 joint expansion, exact reuse, B9 continuation and native costs."""
from collections import Counter
from pathlib import Path
import resource, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b9_probe_cursor as prior, cnf_b10_probe_cursor as candidate, cnf_b10_probe_feedback as feedback
base=prior.base; old=prior.old; compact=prior.compact; FIELDS=prior.FIELDS
PARENT=Path('experiments/results/cnf-b9-probe-cursor')
MODES=('b9', 'restart', 'matched', 'reuse')
NATIVE_MODES=('fresh','disabled','direct')
previous=prior.prior.prior.prior.previous; native=feedback.native
FILES=('experiments/cnf_b10_probe_cursor.py','experiments/cnf_b10_probe_feedback.py','experiments/compare_cnf_b10_probe_cursor.py','solver/test_cnf_b10_probe_cursor.py')


def arguments(row):
    return (*prior.arguments(row), old.bound(row['b9_result']), old.bound(row['b8_comparison_result']))


def options(row):
    return dict(**prior.options(row),joint_closure=row['b9_joint_closure'])


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items(): assert base.sha(f)==h,f
    seeds=cp['b9_probe_cursor']['remaining'];rows=prior.load_frontier(seeds)
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        parent_protocol=old.binding(PARENT/'protocol.json'),seeds=seeds,targets=sorted({r['target'] for r in rows}),
        pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),native_pilot=old.binding(out/'native-pilot.json'),
        feedback_pilot_source=old.binding(out/'feedback-pilot-source.py'),b9_pilot=old.binding(out/'b9-continuation-pilot.json'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES),list(reversed(MODES))],
        compilation_orders=[list(NATIVE_MODES),list(reversed(NATIVE_MODES))],limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),limitations=[
        'Sixteen exposed open inputs. Four changed B10 banks combine B8 continuation and B9 failures, each checked on its original bank. Twelve no-change candidates retain exact bank/closure/trace-bound schedule reuse.',
        'Current reconstruction and cold independent checking are charged in two isolated opposite-order census repetitions. Startup/loading, acquisition, pilots, full feedback/export diagnostics, native compilation and final lineage audit are separate costs.',
        'Matched fresh adds imported completion count and scaled work allowance; equality is checked on this workload. Fixed-budget restart and B9 continuation are coverage/cost comparisons, not matched controls.',
        'Open probe completions are scheduling hints, not SAT authority. All failure proofs, input bindings and schedules are checked. A stronger bank may reach a different capped frontier.',
        'B11 feedback composes B10 failures, including opposite probes. Native dependency expansion strictly decreases the proof bank and publishes only checked source empty/unit/split records.',
        'Fresh, disabled-shortcut and direct native modes cover gained roots only. Complete native trials include warm reuse, both cold readers and persistence but exclude historical discovery and unresolved fallback.',
        'Resume overlay references the prior frontier plus new result files. All old histories, certificates and trials are preserved; lifetime storage grows. No production default or unrestricted SAT bound changes.']))


def inputs(p,target):
    source,ts,pairs,events=prior.inputs(old.bound(p['parent_protocol']),target)
    rows={r['event']:r for r in prior.load_frontier(p['seeds']) if r['target']==target}
    return source,ts,[(ref,rows[ref['event']]) for ref,_ in pairs if ref['event'] in rows],events


def search(args,row,mode,counts,limits):
    if mode=='b9':
        return prior.candidate.discover(*args[:19],**prior.options(row),cursor=args[19]['cursor'],counts=counts,**limits)
    return candidate.discover(*args,**options(row),policy=mode,counts=counts,**limits)


def check(args,row,mode,result,counts):
    if mode=='b9':
        return prior.candidate.validate(*args[:19],**prior.options(row),result=result,counts=counts)
    return candidate.validate(*args,**options(row),result=result,counts=counts)


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json'); source,ts,pairs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref,seed in pairs:
        rc=Counter();tick=time.perf_counter();_,_,state=prior.prior.candidate.bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']]
        assert list(map(list,state['local']))==seed['final_source'] and hints==seed['templates']
        args=(state['local'],hints,*arguments(seed)[2:])
        cc=Counter();tick=time.perf_counter();result=search(args,seed,mode,cc,p['limits']);discovery=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'result-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();check(args,seed,mode,cold,vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,counts=dict(cc),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,discovery_seconds=discovery,persistence_seconds=persistence,verification_seconds=verification,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','record_bytes')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        **{k:dict(sum((Counter(r[k]) for r in rows),Counter())) for k in ('counts','reconstruction_counts','verification_counts')}))


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


def load_frontier(binding):
    overlay=old.bound(binding);seeds={(r['target'],r['event']):r for r in prior.load_frontier(overlay['parent'])}
    excluded={tuple(x) for x in overlay['excluded']};rows=[];seen=set()
    if not excluded<=seeds.keys(): raise ValueError('Unknown excluded frontier case')
    for delta in overlay['rows']:
        key=delta['target'],delta['event']
        if key not in seeds or key in seen or key in excluded or (set(delta)&set(seeds[key]))-{'target','event'}:
            raise ValueError('Invalid B10 frontier overlay')
        seen.add(key);rows.append(dict(seeds[key],**delta))
    if seen!=seeds.keys()-excluded: raise ValueError('Incomplete B10 frontier overlay')
    return rows


def cases(out):
    p=base.load(out/'protocol.json');cases=[];rows=[];diagnostics=[]
    for target in p['targets']:
        source,ts,pairs,events=inputs(p,target)
        results={r['event']:old.bound(r['result']) for r in base.load(out/f'census-{target}-reuse-0/events.json')['rows']}
        for ref,seed in pairs:
            args=arguments(seed);result=results[ref['event']];cc=Counter();tick=time.perf_counter()
            program=feedback.discover(*args,result,**options(seed),counts=cc)
            feedback.validate(*args,result,**options(seed),program=program,counts=Counter())
            diagnostics.append(dict(target=target,event=ref['event'],program=program,counts=dict(cc),seconds=time.perf_counter()-tick))
            if program['status']!='refuted': continue
            local,templates,_=prior.prior.candidate.bind(source,ts,ref,events[ref['event']],Counter())
            path=out/f'new-{target}-{ref["event"]}.json'
            compact(path,dict(source=local,templates=templates,prefix=ref['program'],inputs=args,options=options(seed),search=result,
                program=program,root=ref['root'],target=target,event=ref['event']))
            cases.append(old.binding(path));rows.append(dict(target=target,event=ref['event'],root=ref['root']))
    base.write(out/'cases.json',dict(cases=cases,proposals=rows));compact(out/'feedback-diagnostics.json',dict(rows=diagnostics))


def trial(out,dest,index,mode):
    import tempfile
    binding=base.load(out/'cases.json')['cases'][index];case=old.bound(binding);dest.mkdir();cc=Counter();start=time.perf_counter()
    def compile(solver,counts):
        return feedback.compile_extension(solver,case['source'],case['templates'],case['prefix'],*case['inputs'][2:],case['search'],
            **case['options'],program=case['program'],counts=counts,shortcut='off' if mode=='disabled' else 'all')
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';solver=previous.LazyBinaryClosureSolver(path,node_limit=256) if mode=='fresh' else native.ResidualSolver(path)
        try:
            tick=time.perf_counter()
            result=previous.attempt(solver,case['source']) if mode=='fresh' else dict(status='unsat',result=dict(root=compile(solver,cc),answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(solver.db);nc=dict(solver.counts);tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh': assert previous.attempt(solver,case['source'])['status']=='unsat'
                else: assert compile(solver,Counter())==case['root']
            warm=time.perf_counter()-tick;assert tables==old.tables(solver.db)
        finally: solver.close()
        tick=time.perf_counter();actual,readers=previous.audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert tables==actual
        tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
    base.write(dest/'report.json',dict(case=binding,mode=mode,result=result,counts=dict(cc),native_counts=nc,solve_seconds=solve,warm_seconds=warm,cold_seconds=cold,
        persistence_seconds=persistence,complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        authority_tables={t:len(v) for t,v in tables.items()},digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},
        record_bytes=sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items()),archive=archive,readers=readers))


def run_trials(out):
    p=base.load(out/'protocol.json');samples=[]
    for index in range(len(base.load(out/'cases.json')['cases'])):
        for repeat,order in enumerate(p['compilation_orders']):
            for mode in order:
                dest=out/f'case-{index}-{mode}-{repeat}'
                if not (dest/'report.json').exists():
                    # Keep completed initial trials; an empty failed destination is preserved separately.
                    if dest.exists(): dest.rename(out/(dest.name+'-initial-failed'))
                    subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),str(index),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),index=index,mode=mode,repeat=repeat))
    base.write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census': census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    elif action=='trial': trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else: globals()[action](out)
