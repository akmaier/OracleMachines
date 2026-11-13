#!/usr/bin/env python3
"""Resume ordinary continuation at a checked leaf of a saved external split."""
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_split_batch import restore_checkpoint as restore_base,routes_for,save_delta,closure,new_probes
from experiments.compare_cnf_trace_reuse import read_archive,archive_json
from experiments.compare_cnf_probe_continuation import sha,sha_key,digests,apply_delta,unpack,audit
from experiments.compare_cnf_target_probe import reference
from experiments.continue_cnf_learning import preserved_reference,target_state
from experiments.cnf_split_frontier import frontier
from experiments.cnf_split_batch import children
from experiments.cnf_target_probe import search
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_learning_batch import selection
from experiments.cnf_pattern_inventory import encode

BASE=Path('experiments/results/cnf-split-batch/report.json')
FORMAT='retained-split-frontier-continuation-v1'
POLICY=dict(step_limit=8,source_limit=4,state_limit=32)


def restore_checkpoint(report_path,path,tmp):
    current=Path(report_path);chain=[];seen=set()
    while current.resolve()!=BASE.resolve():
        if current.resolve() in seen:raise ValueError('Cyclic split-frontier lineage')
        seen.add(current.resolve());r=json.loads(current.read_text())
        if r['format']!=FORMAT or sha(r['parent']['path'])!=r['parent']['sha256']:raise ValueError('Changed continuation parent')
        for p,digest in r['fingerprints'].items():
            if sha(p)!=digest:raise ValueError('Changed continuation implementation')
        chain.append(r);current=Path(r['parent']['path'])
    parent,*evidence=restore_base(BASE,path,tmp)
    for i,r in enumerate(reversed(chain)):
        if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:raise ValueError('Incorrect continuation seed')
        d=r['delta'];delta=tmp/f'split-frontier-delta-{i}'
        if sha(d['path'])!=d['sha256']:raise ValueError('Changed continuation delta')
        unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
        if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect continuation reconstruction')
        parent=r
    return parent,*evidence


def run(out,parent_path=BASE):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';path=tmp/'history';started=time.perf_counter();parent,*evidence=restore_checkpoint(parent_path,seed,tmp)
        r=dict(format=FORMAT,parent=dict(path=str(parent_path),sha256=sha(parent_path)),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/cnf_split_frontier.py','experiments/continue_cnf_split_frontier.py',
                'solver/test_cnf_split_frontier.py','solver/fixtures/split-frontier.json')},options=parent['options'],cases=parent['cases'],policy=POLICY,
            baseline_closed=parent['final_closed'],seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,
            restore_seconds=time.perf_counter()-started,
            limitations=['One adaptively selected leaf below saved splits in 83 reused development originals; no independent holdout.',
                'Frontier follows saved splits, selected internal plans and ordinary forced continuations. It is not a minimum-cost decomposition or a traversal of every alternative learned route.',
                'When multiple splits share a source, choose the lexicographically first record identity; missing child obligations stay explicit and are not selected in this acquired-leaf pass.',
                'Eight probe advances, four visited sources, 32 distinct recognition admissions. State counts do not bound CPU, bytes, verification or reference solving.',
                'No competitive runtime comparison, measured peak RAM, new tractability class or unrestricted polynomial construction is established.'])
        started=time.perf_counter();shutil.copyfile(seed,path);h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']];assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']
        r['preparation_seconds']=time.perf_counter()-started;counts=Counter();started=time.perf_counter()
        before=frontier(h,routes,evidence[-1],counts)
        if not before['leaves']:raise ValueError('No acquired open split leaf; inspect explicit pending obligations or other queues')
        leaf=before['leaves'][0];r['selection_seconds']=time.perf_counter()-started;r['selection_counts']=dict(counts)
        r['selection']=archive_json(out/'selection.json.gz',dict(before=before,leaf=leaf))
        h.counts=Counter();h.prepared.counts=Counter();counts=Counter();started=time.perf_counter()
        result=search(h,leaf['source'],routes,counts,**POLICY);routes.refresh_learning(h)
        r['acquisition']=dict(seconds=time.perf_counter()-started,counts=dict(counts),inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
            admission_counts=dict(h.admission_counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
        assert len(h.admitted)<=POLICY['state_limit'];started=time.perf_counter()
        summary,plan=closure(h,roots,routes,r['baseline_closed']);r.update(summary)
        after=frontier(h,routes,evidence[-1],Counter());learning=selection(h,routes,Counter())
        diagnostics=dict(result=result,after=after,children=children(h,routes,evidence[-1]),targets=target_state(h,routes),learning=learning)
        r['composition_diagnosis_seconds']=time.perf_counter()-started;r['diagnostics']=archive_json(out/'diagnostics.json.gz',diagnostics)
        r['certificate']=archive_json(out/'coverage.json.gz',plan);h.close();r['expanded_database_bytes']=path.stat().st_size
        r['delta']=save_delta(seed,path,tmp/'delta',out/'proof-delta.sqlite3.gz');r['logical_table_digests']=digests(path)
        probes=new_probes(tmp/'delta');r['new_probe_summary']=dict(Counter(item['record']['probing']['status'] for item in probes))
        r['new_probes']=archive_json(out/'new-probes.json.gz',[dict(kind=item['kind'],id=item['id']) for item in probes])
        print(json.dumps(dict(leaf_variables=leaf['variables'],steps=len(result['visits']),stop=result['stop'],new_probes=r['new_probe_summary'],
            admitted=len(r['acquisition']['admitted_state_sha256']),closed=sum(r['final_closed']),gains=r['gains'],
            remaining_leaves=[row['variables'] for row in after['leaves']],pending=len(after['pending']))),flush=True)
        rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,tmp/'delta');assert digests(rebuilt)==r['logical_table_digests']
        before_bytes=sha(rebuilt);apply_delta(rebuilt,tmp/'delta');assert sha(rebuilt)==before_bytes
        print('cold inventory audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        print('cold routes and independent reference proofs',flush=True);started=time.perf_counter()
        h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        cold,_=closure(h,roots,routes,r['baseline_closed']);assert all(cold[k]==r[k] for k in cold)
        assert frontier(h,routes,evidence[-1],Counter())==after and not h.admitted;r['cold_routes_seconds']=time.perf_counter()-started
        ep=parent['reference'];assert sha(ep['path'])==ep['sha256'];unpack(ep['path'],tmp/'reference',ep['database_sha256'])
        shutil.copyfile(tmp/'reference',tmp/'reference-seed')
        r['reference']=reference(h,routes,read_archive(r['new_probes']),r,out,tmp)
        r['reference']['preserved_nodes']=preserved_reference(tmp/'reference-seed',tmp/'reference');h.close();assert sha(rebuilt)==before_bytes
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path,default=BASE)
    a=p.parse_args();run(a.output,a.parent)
