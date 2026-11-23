#!/usr/bin/env python3
"""Price early pool reuse against compact hints and missing-clause recovery."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import random,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditional_recovery as prior
from experiments.cnf_pool_priority import try_pools
from experiments.cnf_conditional_unit_support import match,materialize
from experiments.cnf_conditional_recovery import recover
from experiments.cnf_partition_screen import screen_branch
from experiments.cnf_probed_partition import acquire
from experiments.cnf_residual_dag import restrict
base=prior.base;binding=prior.binding;bound=prior.bound;TABLES=prior.TABLES;read_zip=prior.read_zip;write_zip=prior.write_zip;restore=prior.restore
PARENT=Path('experiments/results/cnf-conditional-recovery')
MODES=('native','compact','gated','pools-native','pools-recovery')
FILES=('experiments/cnf_pool_priority.py','solver/test_cnf_pool_priority.py','experiments/compare_cnf_pool_priority.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json');cases=bound(old['cases']);rng=random.Random(202611231034)
    for origin in (4,7):
        original=cases[origin]
        for j in range(2):
            removed=set(rng.sample(range(len(original['source'])),2));source=[cl for i,cl in enumerate(original['source']) if i not in removed]
            cases.append(dict(index=len(cases),label=f'pool-additional-{origin}-{j}',source=source,queries=deepcopy(original['queries']),deleted_clauses=[original['source'][i] for i in sorted(removed)]))
    assert len(cases)==19;base.write(out/'cases.json',cases)
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    p=deepcopy(old);p.update(parent=binding(PARENT/'checkpoint.json'),parent_manifest=binding(PARENT/'manifest.json'),base_protocol=binding(PARENT/'protocol.json'),cases=binding(out/'cases.json'),orders=[list(MODES),list(reversed(MODES))],source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}})
    p['limitations']+=['Nineteen source CNFs under six supplied guards: fifteen preceding controls plus four fixed-seed two-clause deletions. Root novelty and automatic discovery are not claimed.',
        'Five policies in opposite serial process orders. Early pools are checked only after an exact-template miss. Pools-native isolates early pool reuse without recovery; pools-recovery preserves it before screened recovery with ordinary native fallback.',
        'An early negative probe can perform the existing bounded causal support discovery and materialization; its cost and publications are charged. Negative-pool misses and witness misses may be repeated in later native fallback; there is no miss-cache invalidation assumption.',
        'Successful early reuse publishes through the unchanged native verifier in a bounded publication batch. Zero fresh expansions means no fresh search, not zero matching or verification work.']
    base.write(out/'protocol.json',p)


def query(s,case,q,policy,hints,banks,budget):
    tick=time.perf_counter();s.counts=Counter();c=Counter();target=restrict(case['source'],dict(q['assignment']),c);cnf,_,key=s._canonical(target)
    old=s._read(key,cnf,purpose='conditional_query');route='cached';recovery=None;screen=None
    if old is None:
        template=hints['entries'][q['template']]['template']
        if match(case['source'],template,c):
            materialize(s,case['source'],template,context=q['assignment'],counts=c);route='template'
        else:
            route=try_pools(s,cnf,key) if policy.startswith('pools-') else None
            if route is None:
                if policy!='pools-native':
                    screen=screen_branch(s,target,c)
                    if screen['conflict'] is None:recovery=recover(s,case['source'],template,q['assignment'],screen,budget,c)
                if recovery is not None:route='recovery'
                else:
                    route='native';before=dict(s.counts);acquire(s,target,budget)
                    c.update({'preliminary_'+k:v for k,v in before.items()})
    node=s._read(key,cnf,purpose='conditional_result');status='unresolved' if node is None else 'sat' if node['answer'] else 'unsat'
    return dict(case=case['index'],label=case['label'],template=q['template'],assignment=q['assignment'],root=key,status=status,route=route,recovery=recovery,screen=screen,counts=dict(c),metrics=dict(s.counts),expanded_nodes=s.counts.get('expanded_nodes',0),seconds=time.perf_counter()-tick)


def worker(out,p,policy):
    # Existing wrapper retains compact preparation and full proof/replay costs.
    if policy in ('gated','pools-native','pools-recovery'):
        prior.query=lambda s,case,q,mode,hints,banks,budget:query(s,case,q,policy,hints,banks,budget)
    prior.worker(out,p,'repair' if policy in ('gated','pools-native','pools-recovery') else policy)
    report=base.load(out/'report.json');report['policy']=policy
    rows=bound(report['queries']);report['groups']={label:dict(attempts=len(rs),query_seconds=sum(r['seconds'] for r in rs),expanded_nodes=sum(r['expanded_nodes'] for r in rs),routes=dict(Counter(r['route'] for r in rs)),statuses=dict(Counter(r['status'] for r in rs))) for label,rs in [('controls',[r for r in rows if r['case']<15]),('additional',[r for r in rows if r['case']>=15])]}
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
