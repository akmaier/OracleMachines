#!/usr/bin/env python3
"""Probe a saved original split frontier while retaining all five evidence lists."""
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_original_splits import restore_checkpoint as restore_base, routes_for
from experiments.continue_cnf_affine_clause import selected_frontiers
from experiments.compare_cnf_split_batch import save_delta,closure,new_probes
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

BASE=Path('experiments/results/cnf-original-split/report.json')
FORMAT='original-split-probe-continuation-v1'
POLICY=dict(step_limit=1,source_limit=1,state_limit=32)


def restore_checkpoint(report_path,path,tmp):
    current=Path(report_path);chain=[];seen=set()
    while current.resolve()!=BASE.resolve():
        if current.resolve() in seen:raise ValueError('Cyclic reuse-frontier lineage')
        seen.add(current.resolve());r=json.loads(current.read_text())
        if r['format']!=FORMAT or sha(r['parent']['path'])!=r['parent']['sha256']:raise ValueError('Changed reuse-continuation parent')
        for p,digest in r['fingerprints'].items():
            if sha(p)!=digest:raise ValueError('Changed continuation implementation')
        chain.append(r);current=Path(r['parent']['path'])
    parent_tmp=tmp/'inherited';parent_tmp.mkdir(exist_ok=True)
    parent,*evidence=restore_base(BASE,path,parent_tmp)
    for i,r in enumerate(reversed(chain)):
        if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:raise ValueError('Incorrect continuation seed')
        d=r['delta'];delta=tmp/f'reuse-frontier-delta-{i}'
        if sha(d['path'])!=d['sha256']:raise ValueError('Changed continuation delta')
        unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
        if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect continuation reconstruction')
        parent=r
    return parent,*evidence


def run(out,parent_path=BASE,preview_path=None):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';path=tmp/'history';started=time.perf_counter();parent,*evidence=restore_checkpoint(parent_path,seed,tmp)
        r=dict(format=FORMAT,parent=dict(path=str(parent_path),sha256=sha(parent_path)),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/cnf_split_frontier.py','experiments/continue_cnf_original_probes.py',
                'experiments/cnf_target_probe.py','experiments/cnf_probe_continuation.py',
                'solver/test_cnf_target_probe.py','solver/test_cnf_original_splits.py')},options=parent['options'],cases=parent['cases'],policy=POLICY,
            baseline_closed=parent['final_closed'],seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,
            restore_seconds=time.perf_counter()-started,
            limitations=['One adaptively selected leaf below saved splits in 83 reused development originals; no independent holdout.',
                'Frontier follows saved splits, selected internal plans and ordinary forced continuations. It is not a minimum-cost decomposition or a traversal of every alternative learned route.',
                'When multiple splits share a source, choose the lexicographically first record identity; missing child obligations stay explicit and are not selected in this acquired-leaf pass.',
                'One probe advance, one visited source, 32 distinct recognition admissions. State counts do not bound CPU, bytes, verification or reference solving.',
                'No competitive runtime comparison, measured peak RAM, new tractability class or unrestricted polynomial construction is established.'])
        assert len(evidence)==5
        r['evidence_counts']=[len(items) for items in evidence]
        started=time.perf_counter();shutil.copyfile(seed,path);h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']];assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']
        r['preparation_seconds']=time.perf_counter()-started;counts=Counter();started=time.perf_counter()
        before=frontier(h,routes,evidence[3],counts)
        if not before['leaves']:raise ValueError('No acquired open split leaf; inspect explicit pending obligations or other queues')
        leaf=before['leaves'][0];r['selection_seconds']=time.perf_counter()-started;r['selection_counts']=dict(counts)
        r['selection']=archive_json(out/'selection.json.gz',dict(before=before,leaf=leaf))
        if preview_path is not None:
            preview=json.loads(preview_path.read_text())
            assert preview['source']==leaf['source']
            assert preview['parent_validation_sha256']==sha(parent_path.parent/'validation.json')
            r['preflight']=archive_json(out/'preflight.json.gz',preview)
        h.counts=Counter();h.prepared.counts=Counter();counts=Counter();started=time.perf_counter()
        result=search(h,leaf['source'],routes,counts,**POLICY);routes.refresh_learning(h)
        r['acquisition']=dict(seconds=time.perf_counter()-started,counts=dict(counts),inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
            admission_counts=dict(h.admission_counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
        assert len(h.admitted)<=POLICY['state_limit'];started=time.perf_counter()
        summary,plan=closure(h,roots,routes,r['baseline_closed']);r.update(summary)
        after=frontier(h,routes,evidence[3],Counter());learning=selection(h,routes,Counter())
        navigation,_=selected_frontiers(h,roots,routes,r['final_closed'])
        diagnostics=dict(result=result,after=after,children=children(h,routes,evidence[3]),targets=target_state(h,routes),learning=learning,open_originals=navigation)
        r['composition_diagnosis_seconds']=time.perf_counter()-started;r['diagnostics']=archive_json(out/'diagnostics.json.gz',diagnostics)
        r['certificate']=archive_json(out/'coverage.json.gz',plan);h.close();r['expanded_database_bytes']=path.stat().st_size
        r['delta']=save_delta(seed,path,tmp/'delta',out/'proof-delta.sqlite3.gz');r['logical_table_digests']=digests(path)
        probes=new_probes(tmp/'delta')
        if preview_path is not None:
            assert any(item['record']['source']==preview['source'] and item['record']['probing']==preview['probing'] for item in probes)
        r['new_probe_summary']=dict(Counter(item['record']['probing']['status'] for item in probes))
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
        assert frontier(h,routes,evidence[3],Counter())==after and not h.admitted;r['cold_routes_seconds']=time.perf_counter()-started
        ep=parent['reference'];assert sha(ep['path'])==ep['sha256'];unpack(ep['path'],tmp/'reference',ep['database_sha256'])
        shutil.copyfile(tmp/'reference',tmp/'reference-seed')
        r['reference']=reference(h,routes,read_archive(r['new_probes']),r,out,tmp)
        r['reference']['preserved_nodes']=preserved_reference(tmp/'reference-seed',tmp/'reference');h.close();assert sha(rebuilt)==before_bytes
    r['pipeline_seconds']=time.perf_counter()-pipeline
    if preview_path is not None:r['pipeline_plus_preflight_seconds']=r['pipeline_seconds']+preview['seconds']
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path,default=BASE)
    p.add_argument('--preview',type=Path)
    a=p.parse_args();run(a.output,a.parent,a.preview)
