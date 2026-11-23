#!/usr/bin/env python3
"""Keep the ordinary native route when a support provides no new forced value."""
from copy import deepcopy
from pathlib import Path
import subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditional_recovery as study
from experiments.cnf_probed_partition import acquire
base=study.base


def prepare(out):
    assert not (out/'gate-protocol.json').exists();p=base.load(out/'protocol.json')
    base.write(out/'gate-protocol.json',dict(original=study.binding(out/'protocol.json'),orders=[['compact','gated'],['gated','compact']],
        source_fingerprints={**p['source_fingerprints'],__file__.removeprefix(str(Path.cwd())+'/'):base.sha(__file__)},
        limitations=['Gate only changes the earlier experimental repair policy\'s fallback: no new forced value uses original native acquisition. The unit screen is still charged and can be redundant.',
        'Same fifteen sources and supplied guards in two opposite serial orders; this is a follow-up to an exposed regression, not an independent holdout.']))


def worker(out,p,policy):
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    if policy=='gated':
        def fallback(s,source,budget,screen):return acquire(s,source,budget)['result']
        study.native_query=fallback
    study.worker(out,study.bound(p['original']),'repair' if policy=='gated' else 'compact')
    r=base.load(out/'report.json');r['experiment_policy']=policy;r['gate_protocol']=study.binding(out.parent/'gate-protocol.json');base.write(out/'report.json',r)


def run(out):
    p=base.load(out/'gate-protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for policy in order:
            dest=out/f'gate-{policy}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'gate-protocol.json'),policy],check=True)
            samples.append(dict(policy=policy,repeat=repeat,**study.binding(dest/'report.json')))
    means={};groups={}
    for policy in ('compact','gated'):
        rows=[study.bound(s) for s in samples if s['policy']==policy];first=rows[0]['summary']
        means[policy]={k:sum(r['summary'][k] for r in rows)/len(rows) for k in first if type(first[k]) in (int,float)}
        groups[policy]={g:{k:sum(r['groups'][g][k] for r in rows)/len(rows) for k in ('attempts','query_seconds','expanded_nodes')} for g in rows[0]['groups']}
    base.write(out/'gate-report.json',dict(protocol=study.binding(out/'gate-protocol.json'),samples=samples,means=means,groups=groups));print(base.encode(dict(means=means,groups=groups)),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else:run(Path(sys.argv[1]))
