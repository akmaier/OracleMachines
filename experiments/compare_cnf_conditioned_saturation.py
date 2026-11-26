#!/usr/bin/env python3
"""Condition the twelve fixed points; charge acquisition, reuse and certification."""
from collections import Counter
from itertools import permutations
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bootstrap
from experiments import compare_cnf_sliced_saturation as prior,cnf_conditioned_saturation as condition,cnf_conditioned_saturation_native as compiler
s=prior.parent;base=s.base;old=s.old;compact=s.parent.compact;previous=s.previous;k=condition.kernel
PARENT=Path('experiments/results/cnf-sliced-saturation');MODES=('flat','conditioned','resume');NATIVE=('fresh','conditioned')
FILES=('experiments/cnf_conditioned_saturation.py','experiments/cnf_conditioned_saturation_native.py','experiments/compare_cnf_conditioned_saturation.py','solver/test_cnf_conditioned_saturation.py')
LIMITS=dict(round_limit=8,probe_limit=512,work_limit=2097152,trace_limit=256)


def rows():return s.load_frontier(base.load(PARENT/'checkpoint.json')['sliced_saturation']['remaining'])


def build_cases():
    u=s.parent.prior;protocol=old.bound(base.load(s.parent.PARENT/'protocol.json')['parent_protocol']);groups={};cases={}
    for row in rows():
        target,event=row['target'],row['event']
        if target not in groups:groups[target]=u.prior.inputs(protocol,target)
        source,ts,pairs,events=groups[target];ref=next(ref for ref,_ in pairs if ref['event']==event);cc=Counter();tick=time.perf_counter()
        source,templates,tail=u.bind(source,ts,ref,events[event],cc)
        assert list(map(list,tail['local']))==row['final_source'] and [h['template'] for h in tail['hints']]==row['templates']
        cases[f'{target}-{event}']=dict(target=target,event=event,source=source,templates=templates,prefix=ref['program'],root=ref['root'],
            inputs=u.arguments(row,'strengthen'),options=u.options(row,'strengthen'),search=old.bound(row['b13_strength_result']),
            reconstruction_seconds=time.perf_counter()-tick,reconstruction_counts=dict(cc))
    return cases


def seed(case,counts):return s.seed(case,counts)


def order(prepared,counts):
    fixed,_,conflict=k.native.propagate(prepared[29],counts)
    if conflict is not None:raise ValueError('Expected an open frontier seed')
    return list(dict.fromkeys(abs(l) for l in k.frozen.roots(prepared[0]) if abs(l) not in fixed))


def search(prepared,mode,counts,first=None):
    if mode=='flat':return dict(kind='flat',result=k.discover(prepared[29],counts,order_source=prepared[0],**LIMITS))
    trials=[]
    for i,pivot in enumerate(order(prepared,counts)[:16]):
        result=condition.discover(prepared[29],pivot,counts,order_source=prepared[0],previous=first if mode=='resume' and i==0 else None,**LIMITS)
        trials.append(result)
        if result['status']=='refuted':break
    return dict(kind='conditioned',trials=trials,status='refuted' if trials and trials[-1]['status']=='refuted' else 'unresolved')


def check(prepared,result,counts):
    if result['kind']=='flat':
        if set(result)!={'kind','result'}:raise ValueError('Invalid flat result')
        k.validate(prepared[29],result['result'],counts,order_source=prepared[0]);return
    if set(result)!={'kind','trials','status'} or result['kind']!='conditioned' or not isinstance(result['trials'],list):raise ValueError('Invalid conditioning search')
    pivots=order(prepared,counts)[:16];trials=result['trials']
    if len(trials)>len(pivots):raise ValueError('Too many conditioned trials')
    for i,trial in enumerate(trials):
        if trial['pivot']!=pivots[i] or (i<len(trials)-1 and trial['status']=='refuted'):raise ValueError('Invalid pivot prefix')
        condition.validate(prepared[29],trial,counts,order_source=prepared[0])
    refuted=bool(trials) and trials[-1]['status']=='refuted'
    if result['status']!=('refuted' if refuted else 'unresolved') or (not refuted and len(trials)!=len(pivots)):raise ValueError('Incomplete conditioning search')


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    cases={};firsts={};acquisition=[]
    for name,case in build_cases().items():
        compact(out/f'case-{name}.json',case);cases[name]=old.binding(out/f'case-{name}.json');cc=Counter();tick=time.perf_counter();p=seed(case,cc)
        first=condition.discover(p[29],order(p,cc)[0],cc,order_source=p[0],round_limit=1,probe_limit=32,work_limit=2097152,trace_limit=256)
        compact(out/f'first-{name}.json',first);firsts[name]=old.binding(out/f'first-{name}.json')
        acquisition.append(dict(name=name,seconds=time.perf_counter()-tick,counts=dict(cc),bytes=Path(firsts[name]['path']).stat().st_size))
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),cases=cases,firsts=firsts,
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(x) for x in permutations(MODES)],native_orders=[list(NATIVE),list(reversed(NATIVE))],
        limits=LIMITS,pivot_limit=16,fresh_node_limit=256,first_acquisition=acquisition,limitations=[
        'Adaptive development on all twelve retained fixed points, with at most sixteen pivots. It is not held-out evidence or a complete SAT procedure.',
        'Flat has one saturation call; conditioned allows two per pivot. Equal per-call limits do not give equal total search budgets.',
        'Resume reuses a separately acquired 32-probe first pivot in each case; its acquisition, retained bytes and historical preprocessing are additional.',
        'Six fresh-process mode permutations charge seed reconstruction, discovery/resumption, serialization and independent cold seed/proof checking. Original snapshot binding is recorded separately.',
        'One failed branch yields only a forced opposite literal. Both branch refutations and original provenance are needed for source-only certification. Open branches are never SAT certificates.',
        'Native comparison uses two opposite mode orders per successful pair. Conversion, warm reuse, both cold readers and persistence are charged; discovery and acquisition are additional.',
        'Branch assumptions remain local. Source-only split recomposition is checked against the original snapshot; no new native proof format or uniform arbitrary-SAT resource bound is introduced.']))


def census(out,dest,mode):
    p=base.load(out/'protocol.json');loaded={n:old.bound(b) for n,b in p['cases'].items()};firsts={n:old.bound(b) for n,b in p['firsts'].items()} if mode=='resume' else {};dest.mkdir();start=time.perf_counter();events=[]
    for name,case in loaded.items():
        cc=Counter();tick=time.perf_counter();prepared=seed(case,cc);prep=time.perf_counter()-tick
        tick=time.perf_counter();result=search(prepared,mode,cc,firsts.get(name));discovery=time.perf_counter()-tick
        tick=time.perf_counter();compact(dest/f'{name}.json',result);binding=old.binding(dest/f'{name}.json');cold=old.bound(binding);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();check(seed(case,vc),cold,vc);verification=time.perf_counter()-tick
        events.append(dict(name=name,result=binding,counts=dict(cc),verification_counts=dict(vc),preparation_seconds=prep,discovery_seconds=discovery,
            persistence_seconds=persistence,verification_seconds=verification,record_bytes=Path(binding['path']).stat().st_size))
    base.write(dest/'report.json',dict(mode=mode,events=events,complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        **{key:sum(e[key] for e in events) for key in ('preparation_seconds','discovery_seconds','verification_seconds','persistence_seconds','record_bytes')}))


def run_census(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order_ in enumerate(p['orders']):
        for mode in order_:
            dest=out/f'census-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'census',str(out),str(dest),mode],check=True)
            samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=repeat))
        print(base.encode(dict(completed_census_order=repeat)),flush=True)
    base.write(out/'censuses.json',dict(samples=samples))


def compile_case(solver,case,partition,counts):
    return compiler.compile_extension(solver,case['source'],case['templates'],case['prefix'],*case['inputs'][2:],case['search'],partition=partition,counts=counts,**case['options'])


def trial(out,dest,name,mode):
    p=base.load(out/'protocol.json');case=old.bound(p['cases'][name]);partition=base.load(out/f'census-conditioned-0/{name}.json')['trials'][-1];dest.mkdir();cc=Counter();start=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';solver=previous.LazyBinaryClosureSolver(path,node_limit=p['fresh_node_limit']) if mode=='fresh' else compiler.native.ResidualSolver(path)
        try:
            tick=time.perf_counter();result=previous.attempt(solver,case['source']) if mode=='fresh' else dict(status='unsat',result=dict(root=compile_case(solver,case,partition,cc),answer=False,model=None,authority='native'));solve=time.perf_counter()-tick
            tables=old.tables(solver.db);nc=dict(solver.counts);wc=Counter();tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(solver,case['source'])['status']=='unsat'
                else:assert compile_case(solver,case,partition,wc)==case['root']
            warm=time.perf_counter()-tick;assert tables==old.tables(solver.db)
        finally:solver.close()
        tick=time.perf_counter();actual,readers=previous.audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert actual==tables
        tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
    base.write(dest/'report.json',dict(name=name,case=p['cases'][name],mode=mode,result=result,counts=dict(cc),warm_counts=dict(wc),native_counts=nc,
        solve_seconds=solve,warm_seconds=warm,cold_seconds=cold,persistence_seconds=persistence,complete_seconds=time.perf_counter()-start,
        authority_tables={t:len(v) for t,v in tables.items()},digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},
        record_bytes=sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items()),archive=archive,readers=readers,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run_trials(out):
    p=base.load(out/'protocol.json');samples=[]
    candidates=[n for n in p['cases'] if base.load(out/f'census-conditioned-0/{n}.json')['status']=='refuted']
    for repeat,order_ in enumerate(p['native_orders']):
        for name in candidates:
            for mode in order_:
                dest=out/f'native-{name}-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),name,mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),name=name,mode=mode,repeat=repeat))
            print(base.encode(dict(completed_native_case=name,repeat=repeat)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


def load_frontier(binding):
    overlay=old.bound(binding);prior_rows=s.load_frontier(overlay['parent']);keys={(r['target'],r['event']) for r in prior_rows}
    removed={tuple(x) for x in overlay['excluded']}
    if len(removed)!=len(overlay['excluded']) or not removed<=keys:raise ValueError('Invalid conditioned exclusions')
    return [r for r in prior_rows if (r['target'],r['event']) not in removed]


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census':census(out,Path(sys.argv[3]),sys.argv[4])
    elif action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4],sys.argv[5])
    else:globals()[action](out)
