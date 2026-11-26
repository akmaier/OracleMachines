#!/usr/bin/env python3
"""Measure reusable failed-literal rounds and their native certification cost."""
from collections import Counter
from itertools import permutations
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b13_native_feedback as parent
from experiments import cnf_checked_probe_saturation as kernel,cnf_saturated_probe_native as compiler
base=parent.base;old=parent.old;compact=parent.compact;previous=parent.previous
PARENT=Path('experiments/results/cnf-b13-native-feedback')
MODES=('once','saturate','resume');NATIVE_MODES=('fresh','direct')
FILES=('experiments/cnf_checked_probe_saturation.py','experiments/cnf_saturated_probe_native.py','experiments/compare_cnf_probe_saturation.py','solver/test_cnf_probe_saturation.py')


def rows():return parent.load_frontier(base.load(PARENT/'checkpoint.json')['b13_native_feedback']['remaining'])


def build_case():
    row=next(r for r in rows() if (r['target'],r['event'])==(37,39));s=parent.prior
    source,ts,pairs,events=s.inputs(base.load(parent.PARENT/'protocol.json'),37)
    ref=next(ref for ref,_ in pairs if ref['event']==39);cc=Counter();tick=time.perf_counter()
    local,templates,tail=s.bind(source,ts,ref,events[39],cc)
    assert list(map(list,tail['local']))==row['final_source'] and [h['template'] for h in tail['hints']]==row['templates']
    return dict(source=local,templates=templates,prefix=ref['program'],inputs=s.arguments(row,'strengthen'),options=s.options(row,'strengthen'),
        search=old.bound(row['b13_strength_result']),root=ref['root'],target=37,event=39,reconstruction_seconds=time.perf_counter()-tick,reconstruction_counts=dict(cc))


def seed(case,counts):return parent.feedback.prepare(*case['inputs'],case['search'],**case['options'],counts=counts)


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    case=build_case();compact(out/'case.json',case);prepared=seed(case,Counter())
    once=kernel.discover(prepared[29],Counter(),order_source=prepared[0],round_limit=1)
    compact(out/'once.json',once)
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        seeds=cp['b13_native_feedback']['remaining'],case=old.binding(out/'case.json'),once=old.binding(out/'once.json'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(x) for x in permutations(MODES)],
        native_orders=[list(NATIVE_MODES),list(reversed(NATIVE_MODES))],limits=dict(round_limit=8,probe_limit=512,work_limit=2097152,trace_limit=256),
        fresh_node_limit=256,limitations=[
        'One changed case (37,39) selected by its saved B13 closure. Twelve unchanged exhausted banks are checked for exact identity rather than searched again.',
        'Once spends one full round; saturate allows up to eight. Their coverage comparison does not give equal aggregate budgets. Resume reuses the separately acquired first round and matches the complete saturation result.',
        'Six fresh-process mode permutations charge original-bank seed preparation, kernel discovery/resume, serialization/reload, independent seed reconstruction and round checking.',
        'The existing honest-production assumption for claimed open probes is unchanged; fixed_point denotes only this exhausted propagation procedure and never SAT.',
        'Fresh/direct source-only certificate trials use two opposite orders, charging solve/conversion, warm reuse, both cold readers and compressed persistence. Discovery/acquisition/input loading and final audits are additional.',
        'A completed productive round fixes at least one previously unassigned seed variable or refutes; at most n productive rounds can occur. This bounds this inference process, not complete unrestricted SAT solving.',
        'Every earlier proof bank and artifact remains intact. Supplemental native archives certify one additional original snapshot root, not the generating target formula.']))


def census(out,dest,mode):
    p=base.load(out/'protocol.json');case=old.bound(p['case']);saved=old.bound(p['once']) if mode=='resume' else None
    dest.mkdir();start=time.perf_counter();cc=Counter();tick=time.perf_counter();prepared=seed(case,cc);preparation=time.perf_counter()-tick
    limits=dict(p['limits']);limits['round_limit']=1 if mode=='once' else limits['round_limit']
    tick=time.perf_counter();result=kernel.discover(prepared[29],cc,order_source=prepared[0],previous=saved,**limits);discovery=time.perf_counter()-tick
    tick=time.perf_counter();compact(dest/'result.json',result);binding=old.binding(dest/'result.json');reloaded=old.bound(binding);persistence=time.perf_counter()-tick
    vc=Counter();tick=time.perf_counter();cold=seed(case,vc);kernel.validate(cold[29],reloaded,vc,order_source=cold[0]);checking=time.perf_counter()-tick
    base.write(dest/'report.json',dict(case=p['case'],mode=mode,result=binding,preparation_seconds=preparation,discovery_seconds=discovery,
        persistence_seconds=persistence,verification_seconds=checking,complete_seconds=time.perf_counter()-start,
        counts=dict(cc),verification_counts=dict(vc),record_bytes=Path(binding['path']).stat().st_size,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run_census(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'census-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'census',str(out),str(dest),mode],check=True)
            samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=repeat))
    base.write(out/'censuses.json',dict(samples=samples))


def compile_case(solver,case,result,counts):
    return compiler.compile_extension(solver,case['source'],case['templates'],case['prefix'],*case['inputs'][2:],case['search'],
        saturation=result,counts=counts,**case['options'])


def trial(out,dest,mode):
    p=base.load(out/'protocol.json');case=old.bound(p['case']);saturation=old.bound(old.bound(old.binding(out/'census-saturate-0/report.json'))['result'])
    dest.mkdir();cc=Counter();start=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';solver=previous.LazyBinaryClosureSolver(path,node_limit=p['fresh_node_limit']) if mode=='fresh' else compiler.native.ResidualSolver(path)
        try:
            tick=time.perf_counter();result=previous.attempt(solver,case['source']) if mode=='fresh' else dict(status='unsat',result=dict(root=compile_case(solver,case,saturation,cc),answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(solver.db);nc=dict(solver.counts);wc=Counter();tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(solver,case['source'])['status']=='unsat'
                else:assert compile_case(solver,case,saturation,wc)==case['root']
            warm=time.perf_counter()-tick;assert tables==old.tables(solver.db)
        finally:solver.close()
        tick=time.perf_counter();actual,readers=previous.audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert actual==tables
        tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
    base.write(dest/'report.json',dict(case=p['case'],mode=mode,result=result,counts=dict(cc),warm_counts=dict(wc),native_counts=nc,
        solve_seconds=solve,warm_seconds=warm,cold_seconds=cold,persistence_seconds=persistence,complete_seconds=time.perf_counter()-start,
        authority_tables={t:len(v) for t,v in tables.items()},digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},
        record_bytes=sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items()),archive=archive,readers=readers,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run_trials(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['native_orders']):
        for mode in order:
            dest=out/f'native-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),mode],check=True)
            samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=repeat))
        print(base.encode(dict(completed_native_order=repeat)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


def load_frontier(binding):
    overlay=old.bound(binding);prior=parent.load_frontier(overlay['parent'])
    if overlay['excluded']!=[[37,39]]:raise ValueError('Invalid saturation exclusion')
    if (37,39) not in {(r['target'],r['event']) for r in prior}:raise ValueError('Missing certified case')
    return [r for r in prior if (r['target'],r['event'])!=(37,39)]


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action in ('census','trial'):globals()[action](out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)
