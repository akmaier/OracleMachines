#!/usr/bin/env python3
"""Matched bounded direct unit closure before native proof expansion."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cursor_feedback as prior
from experiments import cnf_direct_unit_closure as candidate
base=prior.base;old=prior.old;previous=prior.previous;native=prior.native
PARENT=Path('experiments/results/cnf-cursor-feedback')
MODES=('fresh','baseline','layer','all')
FILES=('experiments/cnf_direct_unit_closure.py','experiments/compare_cnf_direct_unit_closure.py','solver/test_cnf_direct_unit_closure.py')


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),parent_cases=old.binding(PARENT/'cases.json'),
        compilation_orders=[list(MODES),list(reversed(MODES))],source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limits=dict(unit_work_limit=262144,unit_trace_limit=256),
        pilot=old.binding(out/'pilot.json'),profiles=old.binding(out/'profiles.json'),
        limitations=[
        'Same11 exposed positive B4-feedback roots; no holdout, new discovery or coverage gain. The two previous certificate-growth cases were profiled first.',
        'Fresh solving, unchanged publication-only B4 compiler, bounded direct units at layer entry only, and bounded direct units at every trace-walk entry. Two opposite-order isolated repetitions.',
        'Shortcuts use only the actual canonical source residual and publish ordinary native unit proofs. All earlier provenance, source/support bindings, child checks and cold readers remain unchanged.',
        'One query-local allowance charges each gate clause plus index clause/literal slots and occurrence visits. The allowance excludes original compilation, frame preparation, publication and checking. Open or interrupted attempts fall back without asserting a fact.',
        'Each attempt builds a separate occurrence index. No context cache, persistent index, new native rule or production-default change. Exact whole-root warm reuse remains unchanged.',
        'Complete local trials include compilation, warm checks, both cold readers and persistence. Previous acquisition/discovery, unresolved fallback, loading/startup and final audit are additional.',
        'Independent archives may duplicate shared records. Changed proof shape can change cold verification and storage; lifetime history and unrestricted SAT remain unbounded.']))
    base.write(out/'cases.json',base.load(PARENT/'cases.json'))


def trial(out,dest,index,mode):
    limits=base.load(out/'protocol.json')['limits'];binding=base.load(out/'cases.json')['cases'][index];case=old.bound(binding);dest.mkdir();start=time.perf_counter();c=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=previous.LazyBinaryClosureSolver(path,node_limit=256) if mode=='fresh' else native.ResidualSolver(path)
        try:
            tick=time.perf_counter()
            args=[case[k] for k in ('source','templates','prefix','seed','closure','new','next_closure','third','feedback_closure','probe_cursor','program')]
            if mode=='fresh':result=previous.attempt(s,case['source'])
            else:
                compiler=prior.candidate if mode=='baseline' else candidate
                options={} if mode=='baseline' else dict(shortcut=mode,**limits)
                root=compiler.compile_extension(s,*args,c,**options)
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(s.db);nc=dict(s.counts);tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(s,case['source'])['status']=='unsat'
                else:assert compiler.compile_extension(s,*args,Counter(),**options)==case['root']
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
    if action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:globals()[action](out)
