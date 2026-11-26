#!/usr/bin/env python3
"""Matched causal trace slicing, budget ablation and fresh native certification."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_saturation as parent,cnf_sliced_saturation_native as sliced
base=parent.base;old=parent.old;previous=parent.previous
PARENT=Path('experiments/results/cnf-probe-saturation')
MODES=('full','sliced','full_large','fresh')
FILES=('experiments/cnf_sliced_saturation_native.py','experiments/compare_cnf_sliced_saturation.py','solver/test_cnf_sliced_saturation.py')


def build_cases():
    first=base.load(PARENT/'case.json');first['saturation']=base.load(PARENT/'census-saturate-0/result.json')
    second=base.load(parent.PARENT/'case.json');prepared=parent.seed(second,Counter())
    second['saturation']=parent.kernel.discover(prepared[29],Counter(),order_source=prepared[0])
    assert first['saturation']['status']==second['saturation']['status']=='refuted'
    return {'cascade':first,'prior':second}


def compile_case(solver,case,counts,mode):
    module=sliced if mode=='sliced' else parent.compiler
    return module.compile_extension(solver,case['source'],case['templates'],case['prefix'],*case['inputs'][2:],case['search'],
        saturation=case['saturation'],counts=counts,**case['options'],unit_work_limit=2097152 if mode=='full_large' else 262144)


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    cases={}
    for name,case in build_cases().items():
        parent.compact(out/(name+'.json'),case);cases[name]=old.binding(out/(name+'.json'))
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),cases=cases,
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        orders=[list(MODES[i:]+MODES[:i]) for i in range(4)],fresh_node_limit=256,
        limits=dict(unit_work_limit=262144,large_unit_work_limit=2097152,unit_trace_limit=256),limitations=[
        'Four balanced cyclic orders in fresh processes on two already certified frontier snapshots; no new structural coverage.',
        'Full and sliced use the same source-unit budget. Full_large is an eightfold-budget ablation, not an equal-budget optimization.',
        'Every compiler checks original provenance before warm reuse or publication. Only unit-trace dependency slicing changes the native construction.',
        'Complete times include construction/checking, database handling, warm call, both cold readers and compressed persistence. Historical acquisition, discovery, input loading and the final audit are additional.',
        'The slicing memo is private to one compile call and keyed by bank stage, assumption and exact trace. No cross-source or cross-call trust is introduced.',
        'Native graph shape and the source-unit budget interact; the experiment does not establish a uniform polynomial native-size bound or efficient arbitrary-SAT classification.']))


def trial(out,dest,name,mode):
    p=base.load(out/'protocol.json');case=old.bound(p['cases'][name]);dest.mkdir();start=time.perf_counter();cc=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';solver=previous.LazyBinaryClosureSolver(path,node_limit=p['fresh_node_limit']) if mode=='fresh' else sliced.native.ResidualSolver(path)
        try:
            tick=time.perf_counter();result=previous.attempt(solver,case['source']) if mode=='fresh' else dict(status='unsat',result=dict(root=compile_case(solver,case,cc,mode),answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(solver.db);nc=dict(solver.counts);wc=Counter();tick=time.perf_counter()
            if mode=='fresh':assert previous.attempt(solver,case['source'])['status']=='unsat'
            else:assert compile_case(solver,case,wc,mode)==case['root']
            warm=time.perf_counter()-tick;assert tables==old.tables(solver.db)
        finally:solver.close()
        tick=time.perf_counter();actual,readers=previous.audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert actual==tables
        tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
    base.write(dest/'report.json',dict(case=p['cases'][name],name=name,mode=mode,result=result,counts=dict(cc),warm_counts=dict(wc),native_counts=nc,
        solve_seconds=solve,warm_seconds=warm,cold_seconds=cold,persistence_seconds=persistence,complete_seconds=time.perf_counter()-start,
        authority_tables={t:len(v) for t,v in tables.items()},digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},
        record_bytes=sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items()),archive=archive,readers=readers,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for name in p['cases']:
            for mode in order:
                dest=out/f'{name}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),name,mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),name=name,mode=mode,repeat=repeat))
        print(base.encode(dict(completed_order=repeat)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4],sys.argv[5])
    else:globals()[action](out)
