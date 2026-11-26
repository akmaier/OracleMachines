#!/usr/bin/env python3
"""Measure repeated cross-pivot feedback, exact resume and native expansion."""
from collections import Counter
from itertools import permutations
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bootstrap
from experiments import compare_cnf_cross_pivot_feedback as prior,cnf_iterated_cross_pivot as kernel,cnf_iterated_cross_pivot_native as compiler
base=prior.base;old=prior.old;compact=prior.compact;previous=prior.previous
PARENT=Path('experiments/results/cnf-cross-pivot-feedback');MODES=('once','restart','resume');NATIVE=('fresh','full','compact','compact_large')
FILES=('experiments/cnf_iterated_cross_pivot.py','experiments/cnf_iterated_cross_pivot_native.py','experiments/compare_cnf_strengthened_cross_pivot.py','solver/test_cnf_iterated_cross_pivot.py')


def rows():return prior.load_frontier(base.load(PARENT/'checkpoint.json')['cross_pivot_feedback']['remaining'])


def seed(case,counts):return prior.prior.seed(case,counts)


def first_chain(case,summary,counts):
    p=seed(case,counts);chain=dict(format=kernel.FORMAT,seed=list(map(list,p[29])),order_source=list(map(list,p[0])),levels=[summary],status='unresolved',reason='round_limit')
    kernel.validate(p[29],chain,counts,order_source=p[0]);return chain


def compile_case(solver,case,chain,counts,*,unit_work_limit=262144):
    return compiler.compile_extension(solver,case['source'],case['templates'],case['prefix'],*case['inputs'][2:],case['search'],chain=chain,counts=counts,unit_work_limit=unit_work_limit,**case['options'])


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');p=base.load(PARENT/'protocol.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    case=old.bound(p['cases']['61-50']);summary=old.bound(p['records']['61-50']['compact']);cc=Counter();tick=time.perf_counter()
    chain=first_chain(case,summary,cc);compact(out/'first.json',chain);first_seconds=time.perf_counter()-tick
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),case=p['cases']['61-50'],first=old.binding(out/'first.json'),
        first_wrapping=dict(seconds=first_seconds,counts=dict(cc),bytes=(out/'first.json').stat().st_size),earlier_acquisition=next(r for r in p['acquisitions'] if r['name']=='61-50'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(x) for x in permutations(MODES)],
        native_orders=[list(NATIVE[i:]+NATIVE[:i]) for i in range(4)],unit_work_limit=262144,large_unit_work_limit=2097152,fresh_node_limit=256,
        limits=dict(pivot_limit=16,probe_limit=512,work_limit=2097152,trace_limit=256),limitations=[
        'One last retained frontier snapshot, not held-out evidence. Exhausting this finite workload does not solve arbitrary SAT.',
        'Once allows one feedback level; restart allows two; resume checks a previously acquired first level and allows one further level. Restart and resume match exactly, while once has less total search.',
        'Cold census charges case/history loading, original-bank seed reconstruction, discovery/resume, serialization and independent seed/chain checking. Earlier acquired first-level discovery and full historical preprocessing remain additional.',
        'No-new-units denotes only a bounded search outcome and is never SAT. Earlier level bindings are preserved exactly; only the final refuted level can be compacted without reconstructing dependent histories.',
        'Four cyclic native orders charge loading, conversion, warm reuse, both cold readers and compressed persistence. Full and compact have one global 262144 direct-unit allowance; compact_large changes it to 2097152.',
        'Fresh uses the existing 256-node limit, a different algorithm/work budget. Discovery and summary acquisition are additional to native timings.',
        'The generic source compiler checks decreasing feedback level for cross-pivot references and decreasing bank stage within each local trace; expansion size can still grow rapidly.']))


def census(out,dest,mode):
    p=base.load(out/'protocol.json');dest.mkdir();start=time.perf_counter();tick=time.perf_counter();case=old.bound(p['case']);saved=old.bound(p['first']) if mode=='resume' else None;load=time.perf_counter()-tick
    cc=Counter();tick=time.perf_counter();prep=seed(case,cc);preparation=time.perf_counter()-tick
    tick=time.perf_counter();chain,searches=kernel.discover(prep[29],cc,order_source=prep[0],previous=saved,round_limit=2 if mode=='restart' else 1,**p['limits']);discovery=time.perf_counter()-tick
    tick=time.perf_counter();compact(dest/'chain.json',chain);compact(dest/'searches.json',searches);binding=old.binding(dest/'chain.json');cold=old.bound(binding);persist=time.perf_counter()-tick
    vc=Counter();tick=time.perf_counter();cp=seed(case,vc);kernel.validate(cp[29],cold,vc,order_source=cp[0]);check=time.perf_counter()-tick
    base.write(dest/'report.json',dict(mode=mode,case=p['case'],chain=binding,searches=old.binding(dest/'searches.json'),counts=dict(cc),verification_counts=dict(vc),load_seconds=load,
        preparation_seconds=preparation,discovery_seconds=discovery,persistence_seconds=persist,verification_seconds=check,complete_seconds=time.perf_counter()-start,
        chain_bytes=(dest/'chain.json').stat().st_size,search_bytes=(dest/'searches.json').stat().st_size,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run_census(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'census-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'census',str(out),str(dest),mode],check=True)
            samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=repeat))
        print(base.encode(dict(completed_census_order=repeat)),flush=True)
    base.write(out/'censuses.json',dict(samples=samples))
    case=old.bound(p['case']);cc=Counter();tick=time.perf_counter();prep=seed(case,cc);full=base.load(out/'census-restart-0/chain.json');small=kernel.compact(prep[29],full,cc,order_source=prep[0]);compact(out/'compact-chain.json',small)
    base.write(out/'compaction.json',dict(seconds=time.perf_counter()-tick,counts=dict(cc),result=old.binding(out/'compact-chain.json'),bytes=(out/'compact-chain.json').stat().st_size))


def trial(out,dest,mode):
    p=base.load(out/'protocol.json');dest.mkdir();start=time.perf_counter();tick=time.perf_counter();case=old.bound(p['case'])
    chain=None if mode=='fresh' else base.load(out/('census-restart-0/chain.json' if mode=='full' else 'compact-chain.json'));load=time.perf_counter()-tick;cc=Counter()
    budget=p['large_unit_work_limit' if mode=='compact_large' else 'unit_work_limit']
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'db';solver=previous.LazyBinaryClosureSolver(db,node_limit=p['fresh_node_limit']) if mode=='fresh' else compiler.native.ResidualSolver(db)
        try:
            tick=time.perf_counter();result=previous.attempt(solver,case['source']) if mode=='fresh' else dict(status='unsat',result=dict(root=compile_case(solver,case,chain,cc,unit_work_limit=budget),answer=False,model=None,authority='native'));solve=time.perf_counter()-tick
            tables=old.tables(solver.db);nc=dict(solver.counts);wc=Counter();tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(solver,case['source'])['status']=='unsat'
                else:assert compile_case(solver,case,chain,wc,unit_work_limit=budget)==case['root']
            warm=time.perf_counter()-tick;assert tables==old.tables(solver.db)
        finally:solver.close()
        tick=time.perf_counter();actual,readers=previous.audit(db,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert actual==tables
        tick=time.perf_counter();archive=base.archive(db,dest);persist=time.perf_counter()-tick
    base.write(dest/'report.json',dict(mode=mode,case=p['case'],result=result,counts=dict(cc),warm_counts=dict(wc),native_counts=nc,load_seconds=load,solve_seconds=solve,warm_seconds=warm,
        cold_seconds=cold,persistence_seconds=persist,complete_seconds=time.perf_counter()-start,archive=archive,readers=readers,authority_tables={t:len(v) for t,v in tables.items()},
        digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},record_bytes=sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items()),
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run_trials(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['native_orders']):
        for mode in order:
            dest=out/f'native-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),mode],check=True);samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=repeat))
        print(base.encode(dict(completed_native_order=repeat)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


def load_frontier(binding):
    overlay=old.bound(binding);parent=prior.load_frontier(overlay['parent']);removed={tuple(x) for x in overlay['excluded']};keys={(r['target'],r['event']) for r in parent}
    if len(removed)!=len(overlay['excluded']) or not removed<=keys:raise ValueError('Invalid iterated-feedback exclusions')
    return [r for r in parent if (r['target'],r['event']) not in removed]


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census':census(out,Path(sys.argv[3]),sys.argv[4])
    elif action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)
