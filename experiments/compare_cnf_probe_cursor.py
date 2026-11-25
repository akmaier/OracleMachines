#!/usr/bin/env python3
"""Measure cold resumable probing against a single pass and growing restarts."""
from collections import Counter
from pathlib import Path
import json,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_third_feedback as prior
from experiments import cnf_probe_cursor as search,cnf_probe_cursor_native as candidate
base=prior.base;old=prior.old;previous=prior.previous;native=prior.native
PARENT=Path('experiments/results/cnf-third-feedback')
MODES=('single','restart','resume')
FILES=('experiments/cnf_probe_cursor.py','experiments/cnf_probe_cursor_native.py','experiments/compare_cnf_probe_cursor.py','solver/test_cnf_probe_cursor.py')
compact=prior.compact;bind=prior.bind


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    p=base.load(PARENT/'protocol.json')
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        seeds=old.binding(PARENT/'remaining-closures.json'),seed_protocol=old.binding(PARENT/'protocol.json'),old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],
        limits=dict(chunk_probes=64,chunk_work=262144,trace_limit=256),orders=[list(MODES),list(reversed(MODES))],compilation_orders=[['fresh','layered'],['layered','fresh']],
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
        'Same43 retained B3 closures. Pilot exposed before timing; no holdout. No unrecorded historical prefix is assumed tested: the first64 are reacquired and charged.',
        'Single runs128 probes; restart runs64 then starts over with128 if unresolved; resume runs64, writes/reloads the exact cursor, then attempts up to64 additional probes. First-stage refutations are retained without a second search in both chunked arms.',
        'Each64 chunk has262144 occurrence visits; single/restart128 have524288. These limits are additional to older acquisition; work/trace interruptions are not completed probes and must be retried. Prefix equality requires no differing active work limits.',
        'Cursors bind exact full source/B3/closure/order/trace policy content, replay the completed schedule and recheck every saved failure. Open-probe history is trusted scheduling data, not a certified search-exhaustion claim; forged open histories can lose coverage but cannot establish SAT or unchecked UNSAT.',
        'Two opposite-order isolated repetitions. Source-prefix reconstruction, discovery, JSON serialization/reload, final semantic validation and reporting are timed. Startup/input loading, earlier seed acquisition and final audit are additional. Both chunked arms retain initial/final files.',
        'Native proofs expand B3 failures through existing strictly decreasing proof banks and use publication-only preparation reuse. Both cold readers and warm validation remain unchanged.',
        'Positive-only native comparisons exclude discovery, old acquisition and unresolved fallback. Archives may duplicate content; cumulative tables and production defaults are unchanged. No unrestricted-SAT or finite-history size bound.']))


def inputs(p,target):
    source,ts,refs,events=prior.inputs(p,target)
    saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    return source,ts,[dict(ref,feedback_closure=saved[ref['event']]['feedback_closure']) for ref in refs],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        args=(state['local'],[h['template'] for h in state['hints']],ref['seed'],ref['closure'],ref['new'],ref['next_closure'],ref['third'],ref['feedback_closure'])
        phases=[];persistence=0.0;initial=None;kw=dict(trace_limit=p['limits']['trace_limit'])
        c=Counter();tick=time.perf_counter()
        result=search.discover(*args,c,probe_limit=128 if mode=='single' else 64,work_limit=524288 if mode=='single' else 262144,**kw)
        phases.append(dict(counts=dict(c),seconds=time.perf_counter()-tick))
        if mode!='single':
            tick=time.perf_counter();path=dest/f'prefix-{ref["event"]}.json';compact(path,result);result=base.load(path);initial=old.binding(path);persistence+=time.perf_counter()-tick
            if result['program']['status']!='refuted':
                c=Counter();tick=time.perf_counter()
                result=search.discover(*args,c,cursor=result['cursor'] if mode=='resume' else None,
                    probe_limit=64 if mode=='resume' else 128,work_limit=262144 if mode=='resume' else 524288,**kw)
                phases.append(dict(counts=dict(c),seconds=time.perf_counter()-tick))
        tick=time.perf_counter();path=dest/f'final-{ref["event"]}.json';compact(path,result);result=base.load(path);binding=old.binding(path);persistence+=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();search.validate(*args,result,vc);verification=time.perf_counter()-tick
        counts=sum((Counter(x['counts']) for x in phases),Counter())
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,initial=initial,phases=phases,counts=dict(counts),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,discovery_seconds=sum(x['seconds'] for x in phases),persistence_seconds=persistence,verification_seconds=verification))
    compact(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter()))))


def cases(out):
    p=base.load(out/'protocol.json');cases=[];seen=set();proposals=[];remaining=[]
    saved={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']}
    known={(r['target'],r['event']):r for r in base.load(Path('experiments/results/cnf-shortening-budget-frontier/residual-diagnosis.json'))['rows']}
    for target in p['targets']:
        source,ts,refs,events=inputs(p,target);byevent={r['event']:r for r in refs}
        for r in base.load(out/f'census-{target}-resume-0/events.json')['rows']:
            key=(target,r['event']);result=old.bound(r['result'])
            if result['program']['status']!='refuted':remaining.append(dict(saved[key],probe_cursor=result));continue
            snapshot=known[key]['snapshot_answer'];proposals.append(dict(target=target,event=r['event'],root=r['root'],snapshot_answer=snapshot,duplicate=r['root'] in seen))
            if r['root'] in seen:continue
            seen.add(r['root']);ref=byevent[r['event']];local,templates,_=bind(source,ts,ref,events[r['event']],Counter())
            name=f'new-{target}-{r["event"]}';path=out/(name+'.json')
            compact(path,dict(name=name,source=local,templates=templates,prefix=ref['program'],seed=ref['seed'],closure=ref['closure'],new=ref['new'],next_closure=ref['next_closure'],third=ref['third'],feedback_closure=ref['feedback_closure'],result=result,root=r['root'],target=target,event=r['event'],snapshot_answer=snapshot))
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
                root=candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['next_closure'],case['third'],case['feedback_closure'],case['result'],c)
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(s.db);nc=dict(s.counts);tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(s,case['source'])['status']=='unsat'
                else:assert candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['next_closure'],case['third'],case['feedback_closure'],case['result'],Counter())==case['root']
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
