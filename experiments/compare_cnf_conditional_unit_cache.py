#!/usr/bin/env python3
"""Paired serial comparison of full provenance and compact conditional hints."""
from collections import Counter
from pathlib import Path
import subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditional_unit_support as study
from experiments.cnf_conditional_unit_cache import compact
base=study.base
FILES=('experiments/cnf_conditional_unit_cache.py','experiments/compare_cnf_conditional_unit_cache.py','solver/test_cnf_conditional_unit_cache.py')


def prepare(out):
    assert not (out/'compact-protocol.json').exists()
    original=base.load(out/'protocol.json')
    sources={**original['source_fingerprints'],**{f:base.sha(f) for f in FILES}}
    base.write(out/'compact-protocol.json',dict(original=study.binding(out/'protocol.json'),source_fingerprints=sources,
        orders=[['templates','compact'],['compact','templates']],
        limitations=['Same donor, guarded queries, worker and historical prefix as the frozen main comparison. Only active hint retention changes. Full provenance remains archived.',
        'Compaction copying and validation are included in preparation. Complete-worker time includes answer cold replay, but persisted hint revalidation is separately audited.',
        'Two paired orders measure local costs, not statistical significance or an unrestricted memory bound.']))


def worker(out,p,policy):
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    original=study.bound(p['original']);prepare_hints=study.prepare_hints
    if policy=='compact':
        def prepare(s,protocol,mode):
            hints,banks,counts=prepare_hints(s,protocol,mode)
            tick=time.perf_counter();c=Counter();hints=compact(hints,c)
            counts['compaction']=dict(c);counts['compaction_seconds']=time.perf_counter()-tick
            return hints,banks,counts
        study.prepare_hints=prepare
    study.worker(out,original,'templates')
    report=base.load(out/'report.json');report['policy']=policy;report['compact_protocol']=study.binding(Path(p['original']['path']).parent/'compact-protocol.json')
    base.write(out/'report.json',report)


def run(out):
    p=base.load(out/'compact-protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for policy in order:
            dest=out/f'cache-{policy}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'compact-protocol.json'),policy],check=True)
            samples.append(dict(policy=policy,repeat=repeat,**study.binding(dest/'report.json')))
    means={}
    for policy in ('templates','compact'):
        rows=[study.bound(s)['summary'] for s in samples if s['policy']==policy]
        means[policy]={k:sum(r[k] for r in rows)/len(rows) for k in rows[0] if type(rows[0][k]) in (int,float)}
    base.write(out/'compact-report.json',dict(protocol=study.binding(out/'compact-protocol.json'),samples=samples,means=means))
    print(base.encode(means),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else:run(Path(sys.argv[1]))
