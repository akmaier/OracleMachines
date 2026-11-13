#!/usr/bin/env python3
"""Batch bounded frontier advances and measure repeated checked-route preparation."""
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_frontier_forcing import restore_checkpoint as restore_base, routes_for
from experiments.cnf_probe_batch_control import ObservedRoutes
from experiments.cnf_trace_split import candidates
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

BASE=Path('experiments/results/cnf-frontier-forcing/report.json')
FORMAT='frontier-batched-continuation-v1'
POLICY=dict(step_limit=8,source_limit=4,state_limit=32)


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


def run(out,parent_path=BASE):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';path=tmp/'history';started=time.perf_counter();parent,*evidence=restore_checkpoint(parent_path,seed,tmp)
        r=dict(format=FORMAT,parent=dict(path=str(parent_path),sha256=sha(parent_path)),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/cnf_split_frontier.py','experiments/continue_cnf_frontier_batch.py','experiments/cnf_probe_batch_control.py','solver/test_cnf_probe_batch_control.py','experiments/cnf_trace_split.py',
                'experiments/cnf_target_probe.py','experiments/cnf_probe_continuation.py',
                'solver/test_cnf_target_probe.py','solver/test_cnf_original_splits.py')},options=parent['options'],cases=parent['cases'],policy=POLICY,
            baseline_closed=parent['final_closed'],seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,
            restore_seconds=time.perf_counter()-started,
            limitations=['One adaptively selected split descendant in 83 reused development originals; no independent holdout.',
                'Eight advances, four sources and one shared 32-state allowance; exhaustion consumes a step and state counts do not bound CPU or bytes.',
                'Matched control rebuilds all checked routes between advances but retains a warm inventory cache; it does not repeat full cold restore/audit.',
                'Single batch-first measurement, no randomized order or timing confidence interval; no full-solver speedup or peak-RAM claim.',
                'Saved pairs are ranked before acquisition but competing split plans are not acquired; no globally cheapest policy or unrestricted polynomial bound.'])
        assert len(evidence)==5
        r['evidence_counts']=[len(items) for items in evidence]
        started=time.perf_counter();shutil.copyfile(seed,path);h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']];assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']
        r['preparation_seconds']=time.perf_counter()-started;counts=Counter();started=time.perf_counter()
        before=frontier(h,routes,evidence[3],counts)
        if not before['leaves']:raise ValueError('No acquired open split leaf; inspect explicit pending obligations or other queues')
        leaf=before['leaves'][0];r['selection_seconds']=time.perf_counter()-started;r['selection_counts']=dict(counts)
        started=time.perf_counter();rank_counts=Counter();ranked=candidates(h,leaf['source'],routes,rank_counts,candidate_limit=64)
        r['ranking_seconds']=time.perf_counter()-started;r['ranking_counts']=dict(rank_counts)
        r['selection']=archive_json(out/'selection.json.gz',dict(before=before,leaf=leaf,ranked=ranked,candidate_limit=64))
        print(json.dumps(dict(saved_ranks=[row['rank'] for row in ranked])),flush=True)
        h.counts=Counter();h.prepared.counts=Counter();counts=Counter();started=time.perf_counter()
        observed=ObservedRoutes(h,routes,roots)
        result=search(h,leaf['source'],observed,counts,**POLICY);routes.refresh_learning(h)
        batch_observation=observed.finish()
        r['acquisition']=dict(seconds=time.perf_counter()-started,counts=dict(counts),inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
            admission_counts=dict(h.admission_counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
        assert len(h.admitted)<=POLICY['state_limit']
        r['batch_observation']=archive_json(out/'batch-prefixes.json.gz',batch_observation)
        started=time.perf_counter()
        summary,plan=closure(h,roots,routes,r['baseline_closed']);r.update(summary)
        after=frontier(h,routes,evidence[3],Counter());learning=selection(h,routes,Counter())
        navigation,_=selected_frontiers(h,roots,routes,r['final_closed'])
        diagnostics=dict(result=result,after=after,children=children(h,routes,evidence[3]),targets=target_state(h,routes),learning=learning,open_originals=navigation)
        r['composition_diagnosis_seconds']=time.perf_counter()-started;r['diagnostics']=archive_json(out/'diagnostics.json.gz',diagnostics)
        r['certificate']=archive_json(out/'coverage.json.gz',plan);h.close();r['expanded_database_bytes']=path.stat().st_size
        r['delta']=save_delta(seed,path,tmp/'delta',out/'proof-delta.sqlite3.gz');r['logical_table_digests']=digests(path)
        probes=new_probes(tmp/'delta')
        r['new_probe_summary']=dict(Counter(item['record']['probing']['status'] for item in probes))
        r['new_probes']=archive_json(out/'new-probes.json.gz',[dict(kind=item['kind'],id=item['id']) for item in probes])
        print(json.dumps(dict(leaf_variables=leaf['variables'],steps=len(result['visits']),stop=result['stop'],new_probes=r['new_probe_summary'],
            admitted=len(r['acquisition']['admitted_state_sha256']),closed=sum(r['final_closed']),gains=r['gains'],
            remaining_leaves=[row['variables'] for row in after['leaves']],pending=len(after['pending']))),flush=True)
        print('matched sequential control: rebuild checked routes between advances',flush=True)
        started=time.perf_counter();control_path=tmp/'control';shutil.copyfile(seed,control_path)
        control_h=BudgetedInventory(control_path,**r['options']);control_h.set_admission_budget(0)
        control_routes=routes_for(control_h,evidence)
        assert compose(control_h,roots,control_routes,Counter())[0]==r['baseline_closed']
        control_preparation=time.perf_counter()-started
        control_counts=Counter();started=time.perf_counter()
        control=ObservedRoutes(control_h,control_routes,roots,rebuild=lambda inv:routes_for(inv,evidence))
        control_result=search(control_h,leaf['source'],control,control_counts,**POLICY)
        control.refresh_learning(control_h);control_observation=control.finish()
        control_seconds=time.perf_counter()-started
        control_summary,_=closure(control_h,roots,control,r['baseline_closed'])
        assert all(control_summary[k]==r[k] for k in control_summary)
        assert control_result==result
        assert control_observation['prefixes']==batch_observation['prefixes']
        assert sorted(map(sha_key,control_h.admitted))==r['acquisition']['admitted_state_sha256']
        assert dict(control_h.admission_counts)==r['acquisition']['admission_counts']
        control_h.close();assert digests(control_path)==r['logical_table_digests']
        r['control']=dict(preparation_seconds=control_preparation,search_seconds=control_seconds,
            counts=dict(control_counts),observation=archive_json(out/'sequential-prefixes.json.gz',control_observation),
            identical_visits=True,identical_prefixes=True,identical_admissions=True,identical_logical_tables=True,
            identical_final_coverage=True)
        print(json.dumps(dict(batch_search_seconds=r['acquisition']['seconds'],control_search_seconds=control_seconds,
            repeated_preparations=len(control_observation['repeated_preparation_seconds']),matched=True)),flush=True)
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
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path,default=BASE)
    a=p.parse_args();run(a.output,a.parent)
