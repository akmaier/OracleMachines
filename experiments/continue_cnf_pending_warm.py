#!/usr/bin/env python3
"""Resume unfinished cofactors with exact split identity and explicit replay accounting."""
from collections import Counter
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from experiments.compare_cnf_early_closed import restore_checkpoint as restore_base
from experiments.continue_cnf_local_forcing import profile
from experiments.cnf_original_frontier import select
from experiments.continue_cnf_reused_branch import routes_for
from experiments.continue_cnf_original_splits import add_splits
from experiments.cnf_early_closed import EarlyClosedExpansion
from experiments.cnf_route_composition import compose
from experiments.cnf_incremental_coverage import CoverageIndex
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_split_frontier import frontier
from experiments.cnf_trace_split import verify as verify_split, record_key
from experiments.cnf_learning_batch import selection as learning_selection
from experiments.cnf_source_local import check_delta
from experiments.cnf_expanded_coverage import expand, checked_inventory
from experiments.cnf_positive_primitives import verify_positive
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_incremental_coverage import full, check_plans, size
from experiments.compare_cnf_split_batch import save_delta, new_probes
from experiments.compare_cnf_target_probe import reference as probe_reference
from experiments.compare_cnf_trace_split import reference as split_reference, matched_control
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key, digests, apply_delta, unpack, WithoutGrowth

BASE=Path('experiments/results/cnf-early-closed/report.json')
FORMAT='pending-warm-expansion-batch-v1'
POLICY=dict(step_limit=12,state_limit=32,pair_limit=32,candidate_limit=64)
FILES=['experiments/continue_cnf_pending_warm.py','experiments/cnf_original_frontier.py',
       'experiments/cnf_early_closed.py','experiments/cnf_warm_expansion.py',
       'experiments/cnf_incremental_coverage.py']


def restore_checkpoint(report_path,path,tmp):
    current=Path(report_path);chain=[];seen=set()
    while current.resolve()!=BASE.resolve():
        if current.resolve() in seen:raise ValueError('Cyclic warm-batch lineage')
        seen.add(current.resolve());r=json.loads(current.read_text())
        if r['format']!=FORMAT or sha(r['parent']['path'])!=r['parent']['sha256']:
            raise ValueError('Changed warm-batch parent')
        for name,digest in r['fingerprints'].items():
            if sha(name)!=digest:raise ValueError('Changed warm-batch implementation')
        chain.append(r);current=Path(r['parent']['path'])
    inherited=tmp/'pending-warm-inherited';inherited.mkdir(exist_ok=True)
    parent,*evidence=restore_base(BASE,path,inherited)
    for i,r in enumerate(reversed(chain)):
        if (digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed'] or
                parent['options']!=r['options'] or parent['cases']!=r['cases']):
            raise ValueError('Incorrect warm-batch seed')
        d=r['delta'];delta=tmp/f'pending-warm-delta-{i}'
        if sha(d['path'])!=d['sha256']:raise ValueError('Changed warm delta')
        unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
        check_delta(path,delta,r['options'])
        if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect warm reconstruction')
        splits=read_archive(r['splits']);evidence=add_splits(evidence,splits)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
        try:
            for record in splits:verify_split(h,record,Counter())
            roots=[h._canonical(c['source'],h.config['max_depth'])[2]
                   for c,closed in zip(r['cases'],r['final_closed'],strict=True) if closed]
            verify_positive(h,read_archive(r['expanded_certificate']),roots,evidence,Counter())
        finally:h.close()
        if any(a and not b for a,b in zip(r['baseline_closed'],r['final_closed'],strict=True)):
            raise ValueError('Lost previous positive coverage')
        parent=r
    return parent,*evidence


def session(out,tmp,r,parent,evidence,history):
    tick=time.perf_counter();h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
    try:
        routes=routes_for(h,evidence)
        roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
        r['initial_route_preparation_seconds']=time.perf_counter()-tick
        tick=time.perf_counter();counts=Counter()
        indexes=[CoverageIndex(h,roots,v,counts) for v in (routes,WithoutGrowth(routes))]
        r['initial_index_seconds']=time.perf_counter()-tick;r['initial_index_counts']=dict(counts)
        if indexes[0].closed()!=r['baseline_closed']:raise ValueError('Incorrect complete baseline coverage')
        first=select(h,routes,evidence,roots,indexes[0].closed(),Counter())
        if first!=read_archive(parent['next_selection']):raise ValueError('Changed retained starting obligation')
        anchor=first['source'];r['anchor_source_sha256']=sha_key(anchor) if anchor else None
        engine=EarlyClosedExpansion(h,**{k:v for k,v in POLICY.items() if k!='step_limit'})
        h.set_admission_budget(POLICY['state_limit'])  # The only discovery reset.
        r['steps']=[];new_splits=[];stop='step_limit'
        for step in range(POLICY['step_limit']):
            row=dict(step=step);tick=time.perf_counter();counts=Counter()
            chosen=select(h,routes,evidence,roots,indexes[0].closed(),counts)
            if chosen['source'] is None:stop=chosen['mode'];break
            source=chosen['source'];pending_split=chosen['pending_split']
            row['selection_seconds']=time.perf_counter()-tick;row['selection_counts']=dict(counts)
            row['selection']=archive_json(out/f'selection-{step:02d}.json.gz',chosen)
            row['selection_mode']=chosen['mode'];row['selected_original_cases']=chosen['selected_original_cases']
            node=h._load(source);row['source_shape']=[len({abs(l) for c in node['cnf'] for l in c}),len(node['cnf']),sum(map(len,node['cnf']))]
            row['source_sha256']=sha_key(source);tick=time.perf_counter();counts=Counter()
            result=engine.advance(source,routes,counts,pending_split=pending_split)
            row.update(acquisition_seconds=time.perf_counter()-tick,acquisition_counts=dict(counts),
                mode=result['mode'],admitted_total=len(h.admitted),admitted_now=len(result['added']),pending=result['pending'])
            row['operation']=archive_json(out/f'step-{step:02d}.json.gz',result)
            if result['mode'] in ('early_closed_split','split_after_ordinary_exhaustion'):
                new_splits.append(result['record']);evidence[:]=add_splits(evidence,[result['record']])
            tick=time.perf_counter();routes=routes_for(h,evidence)
            row['complete_route_refresh_seconds']=time.perf_counter()-tick
            # Matched warm algorithms on exactly the same post-acquisition graph.
            measurements={}
            for mode in (('full','incremental') if step%2==0 else ('incremental','full')):
                tick=time.perf_counter()
                if mode=='full':closed,plans,cc=full(h,roots,routes)
                else:
                    cc=Counter();closed=[i.refresh(h,v,cc) for i,v in zip(indexes,(routes,WithoutGrowth(routes)),strict=True)]
                    plans=[i.certificate() for i in indexes];check_plans(h,roots,routes,closed,plans);cc=dict(cc)
                measurements[mode]=dict(seconds=time.perf_counter()-tick,counts=cc,closed=closed)
            if measurements['full']['closed']!=measurements['incremental']['closed']:
                raise ValueError('Incremental/full coverage disagreement')
            row['composition']=measurements;row['covered_roots']=sum(indexes[0].closed());r['steps'].append(row)
            print(json.dumps({k:row[k] for k in ('step','source_shape','mode','admitted_total','pending','covered_roots')}),flush=True)
            if result['pending']:stop='admission_limit';break
            if anchor is not None and compose(h,[anchor],routes,Counter())[0][0]:
                stop='initial_obligation_closed';break
            if result['mode']=='no_saved_pair':stop='no_saved_pair';break
        r['stop']=stop;r['admission_counts']=dict(h.admission_counts)
        r['admitted_state_sha256']=sorted(map(sha_key,h.admitted));assert len(h.admitted)<=POLICY['state_limit']
        r['final_closed']=indexes[0].closed();r['without_growth_closed']=indexes[1].closed()
        if any(a and not b for a,b in zip(r['baseline_closed'],r['final_closed'],strict=True)):raise ValueError('Lost coverage')
        r['gains']=[i for i,(a,b) in enumerate(zip(r['baseline_closed'],r['final_closed'],strict=True)) if b and not a]
        r['final_indexes']=list(map(size,indexes));r['evidence_counts_after']=list(map(len,evidence))
        r['splits']=archive_json(out/'splits.json.gz',new_splits)
        tick=time.perf_counter();plan=indexes[0].certificate();check_plans(h,roots,routes,
            [i.closed() for i in indexes],[i.certificate() for i in indexes])
        expanded=expand(h,plan,plan['roots'],routes,Counter())
        r['certificate']=archive_json(out/'coverage.json.gz',plan)
        r['expanded_certificate']=archive_json(out/'expanded-coverage.json.gz',expanded)
        r['positive_production_seconds']=time.perf_counter()-tick
        tick=time.perf_counter();state=frontier(h,routes,evidence[3],Counter())
        r['frontier']=archive_json(out/'frontier.json.gz',state)
        r['frontier_profiles']=archive_json(out/'frontier-profiles.json.gz',[profile(h,routes,row) for row in state['leaves']])
        r['learning']=archive_json(out/'learning.json.gz',learning_selection(h,routes,Counter()))
        r['next_selection']=archive_json(out/'next-selection.json.gz',select(h,routes,evidence,roots,indexes[0].closed(),Counter()))
        r['diagnostics_seconds']=time.perf_counter()-tick
        r['historical_cache']=checked_inventory(h)[1]
        r['split_trace_controls']=[matched_control(h,record) for record in new_splits]
        r['delta']=save_delta(tmp/'seed',history,tmp/'delta',out/'proof-delta.sqlite3.gz')
        ep=parent['reference']
        if sha(ep['path'])!=ep['sha256']:raise ValueError('Changed reference parent')
        unpack(ep['path'],tmp/'reference',ep['database_sha256']);shutil.copyfile(tmp/'reference',tmp/'reference-seed')
        probes=[dict(kind=x['kind'],id=x['id']) for x in new_probes(tmp/'delta')]
        pr=probe_reference(h,routes,probes,r,out,tmp)
        r['probe_reference']={k:pr[k] for k in ('rows','originals','seconds','cold_seconds','verified_nodes')}
        r['reference']=split_reference(h,new_splits,r,out,tmp)
    finally:h.close()


def run(out,parent_path=BASE):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';history=tmp/'history';tick=time.perf_counter()
        parent,*evidence=restore_checkpoint(parent_path,seed,tmp)
        r=dict(format=FORMAT,parent=dict(path=str(parent_path),sha256=sha(parent_path)),
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={name:sha(name) for name in FILES},options=parent['options'],cases=parent['cases'],policy=POLICY,
            baseline_closed=parent['final_closed'],restore_seconds=time.perf_counter()-tick,
            seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,
            evidence_counts_before=list(map(len,evidence)),limitations=[
                'At most twelve advances until the initial retained obligation closes or the shared allowance ends; 83 reused development cases are not a fresh holdout.',
                'Completed immutable nodes are reused; unfinished recognizer stacks are not serialized. Reentered unfinished states consume this new allowance and do not constitute free reuse.',
                'A single 32-state admission allowance covers ordinary forced targets and both split branches; it does not bound CPU, RAM or reference solving.',
                'The complete authoritative database and historical verifier caches stay live; this is not the small source-local working store.',
                'Warm composition comparisons include original plan checking; restoration, first complete index audit, full route refresh, persistence and cold replay are separate.',
                'Only new records and required dependencies are cold-checked, plus final positive coverage; no full new historical archive audit or cold negative-coverage audit.',
                'Clear ordinary probes are inconclusive and exhaustion is limited to the configured ranked pool. Repeated splitting can remain exponential.'])
        tick=time.perf_counter();previous=set(parent.get('admitted_state_sha256',[]))
        for bound in parent.get('arms',[]):
            if sha(bound['path'])!=bound['sha256']:raise ValueError('Changed prior admission evidence')
            previous.update(json.loads(Path(bound['path']).read_text())['admitted_state_sha256'])
        db=sqlite3.connect(seed)
        stored={sha_key(k) for k, in db.execute('SELECT id FROM cnf_patterns_v1')};db.close()
        r['prior_admission_accounting']=dict(entered_sha256=sorted(previous),
            completed_sha256=sorted(previous&stored),unfinished_sha256=sorted(previous-stored))
        r['prior_accounting_seconds']=time.perf_counter()-tick
        original_sha=sha(seed);shutil.copyfile(seed,history)
        try:session(out,tmp,r,parent,evidence,history)
        except BaseException:
            r['failed_delta']=save_delta(seed,history,tmp/'failed-delta',out/'failed-proof-delta.sqlite3.gz')
            r['failed_evidence']=archive_json(out/'failed-evidence.json.gz',evidence)
            (out/'failed-report.json').write_text(encode(r)+'\n');raise
        tick=time.perf_counter();db=sqlite3.connect(history)
        final_stored={sha_key(k) for k, in db.execute('SELECT id FROM cnf_patterns_v1')};db.close()
        admitted=set(r['admitted_state_sha256']);unfinished=previous-stored
        if admitted&stored:raise ValueError('Previously completed node was admitted again')
        r['resume_accounting']=dict(reentered_unfinished_sha256=sorted(admitted&unfinished),
            previously_unfinished_now_stored_sha256=sorted(unfinished&final_stored),
            new_completed_sha256=sorted(final_stored-stored),
            entered_but_unstored_sha256=sorted(admitted-final_stored),
            prior_completed_preserved=stored<=final_stored)
        if not stored<=final_stored:raise ValueError('Lost completed node')
        r['final_accounting_seconds']=time.perf_counter()-tick
        r['logical_table_digests']=digests(history);r['expanded_database_bytes']=history.stat().st_size
        tick=time.perf_counter();r['cold_delta_check']=check_delta(history,tmp/'delta',r['options'])
        r['cold_delta_check_seconds']=time.perf_counter()-tick
        rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,tmp/'delta')
        if digests(rebuilt)!=r['logical_table_digests']:raise ValueError('Incorrect delta reconstruction')
        before=sha(rebuilt);apply_delta(rebuilt,tmp/'delta');assert sha(rebuilt)==before
        assert sha(seed)==original_sha;r['parent_unchanged']=True;r['idempotent_merge']=True
        tick=time.perf_counter();h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0)
        try:
            for record in read_archive(r['splits']):verify_split(h,record,Counter())
            plan=read_archive(r['expanded_certificate']);counts=Counter()
            claimed=[h._canonical(c['source'],h.config['max_depth'])[2]
                     for c,closed in zip(r['cases'],r['final_closed'],strict=True) if closed]
            verify_positive(h,plan,claimed,evidence,counts);assert not h.admitted
            r['cold_positive_counts']=dict(counts)
        finally:h.close()
        r['cold_positive_seconds']=time.perf_counter()-tick
        db=sqlite3.connect(tmp/'delta');r['new_node_kinds']=dict(Counter(json.loads(p)['kind'] for p, in db.execute('SELECT payload FROM cnf_patterns_v1')));db.close()
    r['pipeline_seconds']=time.perf_counter()-pipeline
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(stop=r['stop'],steps=len(r['steps']),admitted=len(r['admitted_state_sha256']),
        closed=sum(r['final_closed']),gains=r['gains'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path,default=BASE)
    a=p.parse_args();run(a.output,a.parent)
