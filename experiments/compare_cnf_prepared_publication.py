#!/usr/bin/env python3
"""Matched publication and unchanged-context preparation reuse on saved proofs."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_layered_feedback as prior
from experiments import cnf_prepared_publication as candidate
base=prior.base;old=prior.old;previous=prior.previous;native=prior.native
PARENT=Path('experiments/results/cnf-layered-feedback')
MODES=('fresh','baseline','headers','prepared')
FILES=('experiments/cnf_prepared_publication.py','experiments/compare_cnf_prepared_publication.py','solver/test_cnf_prepared_publication.py')


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),parent_cases=old.binding(PARENT/'cases.json'),
        compilation_orders=[list(MODES),list(reversed(MODES))],source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=['Same15 exposed layered-feedback roots, all already UNSAT in inspected snapshots. No new discovery or coverage gain.',
        'Fresh ordinary solving, unchanged layered compiler, publication-header handoff, and header plus unchanged-context handoff. Two alternating isolated repetitions per case/mode.',
        'Frames arise only from ordinary normalization. Their publishers construct private headers; one exact-object call reuses the producer result. Every proof rule and child relation is still checked.',
        'Prepared mode also carries frames across unchanged contexts into lower-layer proofs and conditional support leaves. No content-indexed cache, retained cross-query preparation or persistent format change.',
        'Compilation includes checks and handoff construction/cleanup. Complete local trials include warm checks, both cold readers and persistence. Prior acquisition/discovery, unresolved fallback, loading/startup and final audits are additional.',
        'Publication handoff assumes exclusive synchronous use of the unchanged native verifier; private-state tampering and concurrent callbacks are outside the existing execution contract.',
        'An earlier general canonicalization cache regressed and remains preserved. This experiment tests direct producer/consumer reuse, not that cache again.']))
    base.write(out/'cases.json',base.load(PARENT/'cases.json'))


def trial(out,dest,index,mode):
    binding=base.load(out/'cases.json')['cases'][index];case=old.bound(binding);dest.mkdir();start=time.perf_counter();c=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=previous.LazyBinaryClosureSolver(path,node_limit=256) if mode=='fresh' else native.ResidualSolver(path)
        try:
            tick=time.perf_counter()
            if mode=='fresh':result=previous.attempt(s,case['source'])
            elif mode=='baseline':
                root=prior.candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['program'],c)
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            else:
                root=candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['program'],c,reuse_frames=mode=='prepared')
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;tables=old.tables(s.db);nc=dict(s.counts);tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert previous.attempt(s,case['source'])['status']=='unsat'
                elif mode=='baseline':assert prior.candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['program'],Counter())==case['root']
                else:assert candidate.compile_extension(s,case['source'],case['templates'],case['prefix'],case['seed'],case['closure'],case['new'],case['program'],Counter(),reuse_frames=mode=='prepared')==case['root']
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
