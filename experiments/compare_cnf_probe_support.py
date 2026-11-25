#!/usr/bin/env python3
"""Matched native cost comparison for frozen versus sliced probe proofs."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_complement_probes as prior
from experiments import cnf_probe_support as candidate
base=prior.base;old=prior.old;previous=prior.previous;native=prior.native
PARENT=Path('experiments/results/cnf-complement-probes')
FILES=('experiments/cnf_probe_support.py','experiments/compare_cnf_probe_support.py','solver/test_cnf_probe_support.py')
MODES=('fresh','full','support')


def prepare(out):
    assert not (out/'protocol.json').exists();out.mkdir(exist_ok=True);cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=[];origins=[];seen=set()
    for directory in (prior.PARENT,PARENT):
        oldcases=base.load(directory/'cases.json')['cases']
        for index,binding in enumerate(oldcases):
            case=old.bound(binding);assert case['root'] not in seen;seen.add(case['root']);cases.append(binding)
            origins.append(dict(directory=str(directory),index=index))
    assert len(cases)==60
    base.write(out/'cases.json',dict(cases=cases,origins=origins))
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        cases=old.binding(out/'cases.json'),compilation_orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=['All60 distinct native cases from the two previous probe studies; frozen inputs and discovered programs. No rediscovery or coverage claim.',
        'Two alternating isolated repetitions per case for fresh local solving, full probe compilation and selected causal support compilation. All original checks precede reuse/publication.',
        'The support compiler slices terminal probe traces, selects source reason clauses plus full supports of used guards, transports and checks the compact program, and uses the existing native component rule to lift its refutation.',
        'Binary-prefix compilation remains unchanged. Support selection, transport, validation and checking are included in compilation; warm checking, both cold readers and persistence are reported.',
        'Earlier acquisition, discovery, saved-input loading, process startup and final preservation audit are additional. These are exposed-case proof costs, not a whole-query or unrestricted-SAT theorem.',
        'Coordinate failure falls back to the frozen compiler. A selected support is sufficient, not proven minimum; isolated proof-byte sums can duplicate shared subproofs.']))


def trial(out,dest,index,mode):
    binding=base.load(out/'cases.json')['cases'][index];case=old.bound(binding);dest.mkdir();start=time.perf_counter();c=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=previous.LazyBinaryClosureSolver(path,node_limit=256) if mode=='fresh' else native.ResidualSolver(path)
        try:
            tick=time.perf_counter()
            if mode=='fresh':result=previous.attempt(s,case['source'])
            else:
                compiler=candidate if mode=='support' else prior.candidate
                root=compiler.compile_extension(s,case['source'],case['templates'],case['prefix'],case['program'],c)
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(s.db);nc=dict(s.counts);tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(s,case['source'])['status']=='unsat'
                else:assert compiler.compile_extension(s,case['source'],case['templates'],case['prefix'],case['program'],Counter())==case['root']
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
