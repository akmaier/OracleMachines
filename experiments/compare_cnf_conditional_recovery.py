#!/usr/bin/env python3
"""Compare current reuse, unit screening and one missing-clause guidance."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import random,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditional_unit_support as prior
from experiments.cnf_conditional_unit_cache import compact
from experiments.cnf_conditional_unit_support import match,materialize
from experiments.cnf_conditional_recovery import recover
from experiments.cnf_residual_dag import restrict
from experiments.cnf_partition_screen import screen_branch
from experiments.cnf_transported_partition import native_query
base=prior.base;binding=prior.binding;bound=prior.bound;TABLES=prior.TABLES;read_zip=prior.read_zip;restore=prior.restore;write_zip=prior.write_zip
PARENT=Path('experiments/results/cnf-conditional-unit-support');MODES=('native','compact','screen','repair')
FILES=('experiments/cnf_conditional_recovery.py','solver/test_cnf_conditional_recovery.py','experiments/probe_cnf_conditional_recovery.py','experiments/compare_cnf_conditional_recovery.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json');cases=bound(old['cases']);rng=random.Random(202611230933)
    for origin in (4,7):
        original=cases[origin]
        for j in range(2):
            removed=rng.randrange(len(original['source']));source=[cl for i,cl in enumerate(original['source']) if i!=removed]
            cases.append(dict(index=len(cases),label=f'additional-{origin}-{j}',source=source,queries=deepcopy(original['queries']),deleted_clause=original['source'][removed]))
    assert len(cases)==15;base.write(out/'cases.json',cases)
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    p=deepcopy(old);p.update(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),base_protocol=binding(PARENT/'protocol.json'),
        exploration_recovery=binding(out/'exploration.json'),cases=binding(out/'cases.json'),orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}})
    p['limitations']+=['Fifteen source CNFs with six supplied guards each. Eleven controls are identical to the previous study; four fixed-seed additional clause deletions follow the exposed negative and positive misses. No automatic correspondence or whole-CNF coverage claim.',
        'Four policies in two opposite serial process orders. Screen and repair reuse the same checked full-target unit prefix; only repair uses a missing clause to choose extra forced values. The existing deletion-guard implication is not a novel inference rule.',
        'Active hints are the previous compact unit cache in all three reuse arms. The donor and preparation are charged per worker. Repair publication uses ordinary native split/unit proofs or a checked full-target model.',
        'Worker cold replay checks native answers only; active hint reload is audited separately. Other discarded matching candidates and exposed probes are retained.']
    base.write(out/'protocol.json',p)


def query(s,case,q,policy,hints,banks,budget):
    tick=time.perf_counter();s.counts=Counter();c=Counter();fixed=dict(q['assignment']);target=restrict(case['source'],fixed,c);cnf,_,key=s._canonical(target)
    old=s._read(key,cnf,purpose='conditional_query');route='cached';recovery=None;result=None;screen=None
    if old is None:
        template=hints['entries'][q['template']]['template']
        if match(case['source'],template,c):
            materialize(s,case['source'],template,context=q['assignment'],counts=c);route='template'
        else:
            screen=screen_branch(s,target,c);route='screen'
            if policy=='repair' and screen['conflict'] is None:
                recovery=recover(s,case['source'],template,q['assignment'],screen,budget,c)
                if recovery is not None:route='recovery';result=recovery['result']
            if recovery is None:
                before=dict(s.counts);result=native_query(s,target,budget,screen)
                c.update({'preliminary_'+k:v for k,v in before.items()})
    node=s._read(key,cnf,purpose='conditional_result') if recovery is None or result is not None else None
    status='unresolved' if node is None else 'sat' if node['answer'] else 'unsat'
    return dict(case=case['index'],label=case['label'],template=q['template'],assignment=q['assignment'],root=key,status=status,route=route,
        recovery=recovery,screen=screen,counts=dict(c),metrics=dict(s.counts),expanded_nodes=s.counts.get('expanded_nodes',0),seconds=time.perf_counter()-tick)


def worker(out,p,policy):
    prepare_hints=prior.prepare_hints
    def prepare(s,protocol,mode):
        hints,banks,counts=prepare_hints(s,protocol,mode)
        if mode!='native':
            c=Counter();hints=compact(hints,c);counts['compaction']=dict(c)
        return hints,banks,counts
    prior.prepare_hints=prepare
    if policy in ('screen','repair'):
        prior.query=lambda s,case,q,mode,hints,banks,budget:query(s,case,q,policy,hints,banks,budget)
    prior.worker(out,p,'native' if policy=='native' else 'templates')
    report=base.load(out/'report.json');report['policy']=policy;report['protocol']=binding(out.parent/'protocol.json')
    rows=bound(report['queries']);report['groups']={label:dict(attempts=len(rs),query_seconds=sum(r['seconds'] for r in rs),expanded_nodes=sum(r['expanded_nodes'] for r in rs),routes=dict(Counter(r['route'] for r in rs)),statuses=dict(Counter(r['status'] for r in rs))) for label,rs in [('controls',[r for r in rows if r['case']<11]),('additional',[r for r in rows if r['case']>=11])]}
    base.write(out/'report.json',report)


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for policy in order:
            dest=out/f'{policy}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),policy],check=True)
            samples.append(dict(policy=policy,repeat=repeat,**binding(dest/'report.json')))
    means={};groups={}
    for policy in MODES:
        rows=[bound(s) for s in samples if s['policy']==policy];first=rows[0]['summary']
        means[policy]={k:sum(r['summary'][k] for r in rows)/len(rows) for k in first if type(first[k]) in (int,float)}
        groups[policy]={g:{k:sum(r['groups'][g][k] for r in rows)/len(rows) for k in ('attempts','query_seconds','expanded_nodes')} for g in rows[0]['groups']}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,means=means,groups=groups));print(base.encode(dict(means=means,groups=groups)),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else:run(Path(sys.argv[1]))
