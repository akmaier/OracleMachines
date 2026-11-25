#!/usr/bin/env python3
"""Matched all/changed discovery and native compilation of newly exposed roots."""
from collections import Counter
from pathlib import Path
import resource, subprocess, sys, tempfile, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_layered_feedback as prior
from experiments import cnf_changed_closure_probes as search
from experiments import cnf_changed_closure_native as candidate
base=prior.base;old=prior.old;previous=prior.previous;native=prior.native
PARENT=Path('experiments/results/cnf-prepared-publication')
SEEDS=Path('experiments/results/cnf-layered-feedback')
MODES=('all','changed')
FILES=('experiments/cnf_changed_closure_probes.py','experiments/cnf_changed_closure_native.py','experiments/compare_cnf_changed_closure_probes.py','solver/test_cnf_changed_closure_probes.py')
compact=prior.compact;bind=prior.bind


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    p=base.load(SEEDS/'protocol.json')
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        seeds=old.binding(SEEDS/'remaining-closures.json'),seed_protocol=old.binding(SEEDS/'protocol.json'),
        old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],
        limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),orders=[list(MODES),list(reversed(MODES))],
        compilation_orders=[['fresh','layered'],['layered','fresh']],
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=['Same53 retained unresolved events, with21 changed closures and32 unchanged. Pilot exposed before timing; no holdout.',
        'All repeats a bounded deterministic search on every B2 bank. Changed checks exact B1/B2 bank and fixed-assignment equality, skipping unchanged banks as unresolved. This is a search policy, not proof of search exhaustion or guaranteed coverage equivalence for arbitrary prior histories or budgets.',
        'Both arms check every old seed, new seed, old closure and B2 closure. Preparation and scheduling remain charged even on skipped cases. Budgets are additional to all earlier acquisition.',
        'Saved source-prefix reconstruction, checking, indexing and propagation are charged. Startup, input loading, earlier acquisition and final audit remain additional. Two reverse-order isolated repetitions are descriptive timings.',
        'New failures are proofs on B2; old failures on B0 and preceding failures on B1 remain separate. Open and budget stops are unresolved, never SAT.',
        'Native reconstruction slices supports, expands proof leaves through decreasing layers and uses publication-only preparation reuse. Native proof rules and cold readers are unchanged.',
        'Positive-only native comparisons exclude unresolved fallback and seed acquisition. Isolated archives duplicate shared content; cumulative solver tables remain untouched. No unrestricted SAT or P-versus-NP bound.']))


def inputs(p,target):
    source,ts,refs,events=prior.inputs(p,target)
    saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    rows=[]
    for ref in refs:
        if ref['event'] not in saved:continue
        r=saved[ref['event']]
        for k in ('seed','closure','new'):assert r[k]==ref[k]
        assert r['final_source']==ref['saved_source'] and r['templates']==ref['saved_templates']
        rows.append(dict(ref,next_closure=r['next_closure']))
    return source,ts,rows,events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        c=Counter();tick=time.perf_counter();local,templates,state=bind(source,ts,ref,events[ref['event']],c);reconstruction=time.perf_counter()-tick
        rc=dict(c);c=Counter();tick=time.perf_counter();hints=[h['template'] for h in state['hints']]
        assert list(map(list,state['local']))==ref['saved_source'] and hints==ref['saved_templates']
        result=search.discover(state['local'],hints,ref['seed'],ref['closure'],ref['new'],ref['next_closure'],c,policy=mode,**p['limits'])
        elapsed=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=result,counts=dict(c),reconstruction_counts=rc,reconstruction_seconds=reconstruction,discovery_seconds=elapsed))
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
                dest=out/f'census-{target}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'census',str(out),str(dest),str(target),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),target=target,mode=mode,repeat=repeat))
    base.write(out/'censuses.json',dict(samples=samples))


def cases(out):
    p=base.load(out/'protocol.json');cases=[];seen=set();proposals=[];remaining=[]
    saved={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']}
    known={(r['target'],r['event']):r for r in base.load(Path('experiments/results/cnf-shortening-budget-frontier/residual-diagnosis.json'))['rows']}
    for target in p['targets']:
        source,ts,refs,events=inputs(p,target);byevent={r['event']:r for r in refs}
        for r in base.load(out/f'census-{target}-changed-0/events.json')['rows']:
            q=r['result'];key=(target,r['event'])
            if q['action']=='unchanged' or q['program']['status']!='refuted':
                remaining.append(dict(saved[key],third=q));continue
            snapshot=known[key]['snapshot_answer']
            proposals.append(dict(target=target,event=r['event'],root=r['root'],snapshot_answer=snapshot,duplicate=r['root'] in seen))
            if r['root'] in seen:continue
            seen.add(r['root']);ref=byevent[r['event']];local,templates,state=bind(source,ts,ref,events[r['event']],Counter())
            search.validate(state['local'],[h['template'] for h in state['hints']],ref['seed'],ref['closure'],ref['new'],ref['next_closure'],q,Counter())
            name=f'new-{target}-{r["event"]}';path=out/(name+'.json')
            compact(path,dict(name=name,source=local,templates=templates,prefix=ref['program'],seed=ref['seed'],closure=ref['closure'],new=ref['new'],next_closure=ref['next_closure'],result=q,root=r['root'],target=target,event=r['event'],snapshot_answer=snapshot))
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
                root=candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['next_closure'],case['result'],c)
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(s.db);nc=dict(s.counts);tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(s,case['source'])['status']=='unsat'
                else:assert candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['next_closure'],case['result'],Counter())==case['root']
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
