#!/usr/bin/env python3
"""Charge cross-pivot summary acquisition, cold reuse and source-only conversion."""
from collections import Counter
from itertools import permutations
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bootstrap
from experiments import compare_cnf_conditioned_saturation as prior,cnf_cross_pivot_feedback as joint,cnf_cross_pivot_feedback_native as compiler
base=prior.base;old=prior.old;compact=prior.compact;previous=prior.previous
PARENT=Path('experiments/results/cnf-conditioned-saturation')
MODES=('history','full','compact');NATIVE=('fresh','full','compact')
FILES=('experiments/cnf_cross_pivot_feedback.py','experiments/cnf_cross_pivot_feedback_native.py','experiments/compare_cnf_cross_pivot_feedback.py','solver/test_cnf_cross_pivot_feedback.py')


def rows():return prior.load_frontier(base.load(PARENT/'checkpoint.json')['conditioned_saturation']['remaining'])


def compile_case(solver,case,summary,counts):
    return compiler.compile_extension(solver,case['source'],case['templates'],case['prefix'],*case['inputs'][2:],case['search'],summary=summary,counts=counts,**case['options'])


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');p=base.load(PARENT/'protocol.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    cases={};records={};acquisitions=[]
    for row in rows():
        name=f"{row['target']}-{row['event']}";cases[name]=p['cases'][name];case=old.bound(cases[name]);records[name]={'history':old.binding(PARENT/f'census-conditioned-0/{name}.json')}
        cc=Counter();tick=time.perf_counter();history=old.bound(records[name]['history']);seed=prior.seed(case,cc)
        full=joint.collect(seed[29],history['trials'],cc,order_source=seed[0]);compact(out/f'{name}-full.json',full);full_seconds=time.perf_counter()-tick;fc=dict(cc)
        tick=time.perf_counter();cc=Counter();small=joint.compact(seed[29],full,cc,order_source=seed[0]);compact(out/f'{name}-compact.json',small);small_seconds=time.perf_counter()-tick
        for mode in ('full','compact'):records[name][mode]=old.binding(out/f'{name}-{mode}.json')
        acquisitions.append(dict(name=name,full_seconds=full_seconds,compact_additional_seconds=small_seconds,full_counts=fc,compact_counts=dict(cc),
            bytes={mode:Path(binding['path']).stat().st_size for mode,binding in records[name].items()}))
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),cases=cases,records=records,acquisitions=acquisitions,
        orders=[list(x) for x in permutations(MODES)],native_orders=[list(x) for x in permutations(NATIVE)],fresh_node_limit=256,unit_work_limit=262144,unit_trace_limit=256,
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
        'Selected retained frontier, not held-out evidence. Joint implications are exact but arbitrary SAT acquisition and native expansion remain unbounded.',
        'Summary acquisition includes loading old history, checked seed preparation, branch validation, collection and serialization; compact has an additional checked slicing cost. Historical branch discovery is already paid and additional.',
        'Cold replay includes JSON loading, seed reconstruction, validation/reconstruction of the requested record and serialization of the resulting verdict and units. It never treats an open branch as SAT.',
        'Native trials charge summary loading, original-bank validation, conversion, a checked warm call, both cold readers and persistence. Earlier summary acquisition and historical discovery are additional.',
        'Full and compact share one global 262144 direct-unit allowance per compilation, across all branches. Fresh has the existing 256-node limit, not an equivalent work budget.',
        'Warm incoming provenance is checked before a cached root is used; checked compact summaries do not retain all possible future implications. Original histories and full summaries remain intact.']))


def replay(out,dest,mode):
    p=base.load(out/'protocol.json');dest.mkdir();start=time.perf_counter();events=[]
    for name,binding in p['cases'].items():
        cc=Counter();tick=time.perf_counter();case=old.bound(binding);record=old.bound(p['records'][name][mode]);load=time.perf_counter()-tick
        tick=time.perf_counter();prepared=prior.seed(case,cc);prep=time.perf_counter()-tick
        tick=time.perf_counter()
        if mode=='history':summary=joint.collect(prepared[29],record['trials'],cc,order_source=prepared[0])
        else:joint.validate(prepared[29],record,cc,order_source=prepared[0]);summary=record
        check=time.perf_counter()-tick
        result=dict(status=summary['status'],units=[-r['assumption'] for r in summary['lemmas']],proof=summary['proof'],closure=summary['closure'])
        tick=time.perf_counter();compact(dest/f'{name}.json',result);assert old.bound(old.binding(dest/f'{name}.json'))==result;persist=time.perf_counter()-tick
        events.append(dict(name=name,result=old.binding(dest/f'{name}.json'),counts=dict(cc),load_seconds=load,preparation_seconds=prep,check_seconds=check,persistence_seconds=persist,
            input_bytes=Path(p['records'][name][mode]['path']).stat().st_size,output_bytes=(dest/f'{name}.json').stat().st_size))
    base.write(dest/'report.json',dict(mode=mode,events=events,complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        **{key:sum(e[key] for e in events) for key in ('load_seconds','preparation_seconds','check_seconds','persistence_seconds','input_bytes','output_bytes')}))


def run_replays(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'replay-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'replay',str(out),str(dest),mode],check=True)
            samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=repeat))
        print(base.encode(dict(completed_replay_order=repeat)),flush=True)
    base.write(out/'replays.json',dict(samples=samples))


def trial(out,dest,name,mode):
    p=base.load(out/'protocol.json');dest.mkdir();cc=Counter();start=time.perf_counter();tick=time.perf_counter()
    case=old.bound(p['cases'][name]);summary=None if mode=='fresh' else old.bound(p['records'][name][mode]);load=time.perf_counter()-tick
    with tempfile.TemporaryDirectory() as td:
        db=Path(td)/'db';solver=previous.LazyBinaryClosureSolver(db,node_limit=p['fresh_node_limit']) if mode=='fresh' else compiler.native.ResidualSolver(db)
        try:
            tick=time.perf_counter();result=previous.attempt(solver,case['source']) if mode=='fresh' else dict(status='unsat',result=dict(root=compile_case(solver,case,summary,cc),answer=False,model=None,authority='native'));solve=time.perf_counter()-tick
            tables=old.tables(solver.db);nc=dict(solver.counts);wc=Counter();tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(solver,case['source'])['status']=='unsat'
                else:assert compile_case(solver,case,summary,wc)==case['root']
            warm=time.perf_counter()-tick;assert tables==old.tables(solver.db)
        finally:solver.close()
        tick=time.perf_counter();actual,readers=previous.audit(db,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert actual==tables
        tick=time.perf_counter();archive=base.archive(db,dest);persist=time.perf_counter()-tick
    base.write(dest/'report.json',dict(name=name,mode=mode,case=p['cases'][name],result=result,counts=dict(cc),warm_counts=dict(wc),native_counts=nc,load_seconds=load,
        solve_seconds=solve,warm_seconds=warm,cold_seconds=cold,persistence_seconds=persist,complete_seconds=time.perf_counter()-start,archive=archive,readers=readers,
        authority_tables={t:len(v) for t,v in tables.items()},digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},
        record_bytes=sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items()),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run_trials(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['native_orders']):
        for name in ('61-0','67-0'):
            for mode in order:
                dest=out/f'native-{name}-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),name,mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),name=name,mode=mode,repeat=repeat))
        print(base.encode(dict(completed_native_order=repeat)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


def load_frontier(binding):
    overlay=old.bound(binding);parent=prior.load_frontier(overlay['parent']);keys={(r['target'],r['event']) for r in parent};removed={tuple(x) for x in overlay['excluded']}
    if len(removed)!=len(overlay['excluded']) or not removed<=keys:raise ValueError('Invalid cross-pivot exclusions')
    return [r for r in parent if (r['target'],r['event']) not in removed]


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='replay':replay(out,Path(sys.argv[3]),sys.argv[4])
    elif action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4],sys.argv[5])
    else:globals()[action](out)
