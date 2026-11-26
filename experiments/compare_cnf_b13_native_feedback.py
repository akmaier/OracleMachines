#!/usr/bin/env python3
"""Certify a retained B13 conflict and compare source-only native costs."""
from collections import Counter
from itertools import permutations
from pathlib import Path
import resource, subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b13_strengthened_histories as prior
from experiments import compare_cnf_b10_probe_cursor as frozen
from experiments import cnf_b13_probe_feedback as feedback
base=prior.base; old=prior.old; compact=prior.compact; native=feedback.native
previous=frozen.previous
PARENT=Path('experiments/results/cnf-b13-strengthened-histories')
MODES=('fresh','disabled','direct')
FILES=('experiments/cnf_b13_probe_feedback.py','experiments/compare_cnf_b13_native_feedback.py','solver/test_cnf_b13_native_feedback.py')


def seeds():
    return prior.load_frontier(base.load(PARENT/'checkpoint.json')['b13_strengthened_histories']['remaining'])


def build_case():
    row=next(r for r in seeds() if (r['target'],r['event'])==(67,63))
    p=base.load(PARENT/'protocol.json');source,ts,pairs,events=prior.inputs(p,67)
    ref=next(ref for ref,_ in pairs if ref['event']==63);cc=Counter();tick=time.perf_counter()
    local,templates,tail=prior.bind(source,ts,ref,events[63],cc)
    assert list(map(list,tail['local']))==row['final_source'] and [h['template'] for h in tail['hints']]==row['templates']
    args=prior.arguments(row,'strengthen');kw=prior.options(row,'strengthen')
    return dict(source=local,templates=templates,prefix=ref['program'],inputs=args,options=kw,
                search=old.bound(row['b13_strength_result']),program=row['b13_strength_feedback_program'],
                root=ref['root'],target=67,event=63,reconstruction_seconds=time.perf_counter()-tick,reconstruction_counts=dict(cc))


def prepare(out):
    assert not (out/'protocol.json').exists()
    cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    compact(out/'case.json',build_case())
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        seeds=cp['b13_strengthened_histories']['remaining'],case=old.binding(out/'case.json'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        orders=[list(x) for x in permutations(MODES)],fresh_node_limit=256,
        unit_work_limit=262144,unit_trace_limit=256,limitations=[
        'One exposed candidate (67,63), selected by the preceding augmented-bank contradiction; not held-out or representative arbitrary SAT evidence.',
        'Six balanced order permutations run in fresh processes before heavy checks. Native solve includes all original-bank history checking and prefix reconstruction.',
        'Fresh solving receives a 256-node limit. Disabled follows checked provenance without direct unit shortcuts; direct adds the existing bounded source-unit shortcut.',
        'Warm compiler reuse revalidates supplied histories before root lookup. Cold archive readers use source-only native records and need no B13 histories.',
        'Timed complete cost includes database creation, native conversion/solving, warm reuse, both cold readers and compressed persistence. Historical acquisition, candidate discovery, input loading and final audit are additional.',
        'All prior source files, archives and frontier fields remain unchanged. A supplemental archive certifies one original snapshot root, not the full target formula or all unrestricted SAT.',
        'Recursive proof dependencies strictly decrease bank stage; within a trace its index advances. Repeated contexts can still produce exponential native graphs.']))


def compile_case(solver,case,counts,mode):
    return feedback.compile_extension(solver,case['source'],case['templates'],case['prefix'],*case['inputs'][2:],case['search'],
        **case['options'],program=case['program'],counts=counts,shortcut='off' if mode=='disabled' else 'all')


def trial(out,dest,mode):
    p=base.load(out/'protocol.json');binding=p['case'];case=old.bound(binding);dest.mkdir();cc=Counter();start=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db'
        solver=previous.LazyBinaryClosureSolver(path,node_limit=p['fresh_node_limit']) if mode=='fresh' else native.ResidualSolver(path)
        try:
            tick=time.perf_counter()
            result=previous.attempt(solver,case['source']) if mode=='fresh' else dict(status='unsat',result=dict(root=compile_case(solver,case,cc,mode),answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(solver.db);nc=dict(solver.counts);wc=Counter();tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(solver,case['source'])['status']=='unsat'
                else:assert compile_case(solver,case,wc,mode)==case['root']
            warm=time.perf_counter()-tick;assert tables==old.tables(solver.db)
        finally:solver.close()
        tick=time.perf_counter();actual,readers=previous.audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert tables==actual
        tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
    base.write(dest/'report.json',dict(case=binding,mode=mode,result=result,counts=dict(cc),warm_counts=dict(wc),native_counts=nc,
        solve_seconds=solve,warm_seconds=warm,cold_seconds=cold,persistence_seconds=persistence,complete_seconds=time.perf_counter()-start,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,authority_tables={t:len(v) for t,v in tables.items()},
        digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},
        record_bytes=sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items()),archive=archive,readers=readers))


def run_trials(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'case-{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),mode],check=True)
            samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=repeat))
        print(base.encode(dict(completed_order=repeat)),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


def load_frontier(binding):
    overlay=old.bound(binding);rows=prior.load_frontier(overlay['parent']);excluded={tuple(x) for x in overlay['excluded']}
    if excluded!={(67,63)}:raise ValueError('Invalid certified exclusion')
    if not excluded<={(r['target'],r['event']) for r in rows}:raise ValueError('Unknown certified case')
    return [r for r in rows if (r['target'],r['event']) not in excluded]


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='trial':trial(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)
