#!/usr/bin/env python3
"""Matched selective activation after real acquisition on current and saved cases."""
from collections import Counter
import copy
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_pending_pair import (
    restore_checkpoint as restore_base, FILES as INHERITED_FILES,
    routes_for, add_splits, select, BudgetedInventory, full, expand,
    archive_json, read_archive, sha, sha_key, digests, unpack, apply_delta,
    check_delta, save_delta, new_probes, probe_reference, split_reference,
    frontier, profile, learning_selection, checked_inventory, verify_split,
    verify_positive, verify_bridge, remaining, split_key)
from experiments.compare_cnf_pending_maintenance import restore_checkpoint as restore_control, focus_selection, shape
from experiments.cnf_early_saved import EarlySavedExpansion
from experiments.cnf_pending_split_maintenance import PendingSplitMaintenance
from experiments.cnf_pattern_activation import PatternActivationMaintenance
from experiments.cnf_pattern_inventory import encode

BASE=Path('experiments/results/cnf-pending-pair/report.json')
CONTROL=Path('experiments/results/cnf-pending-maintenance/report.json')
FORMAT='pattern-activation-comparison-v1'
POLICY=dict(step_limit=12,state_limit=32,pair_limit=32,candidate_limit=64)
FILES=['experiments/compare_cnf_pattern_activation.py','experiments/cnf_pattern_activation.py',
       'solver/test_cnf_pattern_activation.py',*INHERITED_FILES]

def restore_checkpoint(report_path,path,tmp):
    r=json.loads(Path(report_path).read_text())
    if r['format']!=FORMAT or Path(r['parent']['path'])!=BASE or sha(BASE)!=r['parent']['sha256']:
        raise ValueError('Changed pattern-activation parent')
    for name,digest in r['fingerprints'].items():
        if sha(name)!=digest:raise ValueError('Changed pattern-activation implementation')
    parent,*evidence=restore_base(BASE,path,tmp)
    if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:
        raise ValueError('Incorrect pattern-activation seed')
    d=r['delta'];delta=tmp/'pattern-activation-delta'
    if sha(d['path'])!=d['sha256']:raise ValueError('Changed pattern-activation delta')
    unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta);check_delta(path,delta,r['options'])
    if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect acquisition reconstruction')
    evidence=add_splits(evidence,read_archive(r['splits']));bridges=read_archive(r['bridges'])
    h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
    try:
        for record in bridges:verify_bridge(h,record,Counter())
        roots=[h._canonical(c['source'],h.config['max_depth'])[2]
            for c,b in zip(r['cases'],r['final_closed'],strict=True) if b]
        verify_positive(h,read_archive(r['expanded_certificate']),roots,evidence,bridges,Counter())
        assert not h.admitted
    finally:h.close()
    return r,*evidence


def worker(out,tmp,seed,parent,evidence,old_bridges,root,mode,scenario):
    out.mkdir();tmp.mkdir();started=time.perf_counter();history=tmp/'history';shutil.copyfile(seed,history)
    r=dict(mode=mode,scenario=scenario,policy=POLICY,source_sha256=sha_key(root),steps=[],seed_table_digests=digests(seed))
    h=BudgetedInventory(history,**parent['options']);h.set_admission_budget(0)
    inherited={split_key(x) for x in evidence[3]}
    saved=copy.deepcopy(evidence[3])
    bridges=copy.deepcopy(old_bridges);evidence=copy.deepcopy(evidence);focus=root
    try:
        assert mode in ('pending','activation')
        maintained=(PendingSplitMaintenance if mode=='pending' else PatternActivationMaintenance)(h,evidence,bridges,routes_for)
        routes=maintained.routes
        r['initial_activation_index']=maintained.statistics() if mode=='activation' else None
        closed,plans,_=full(h,[root],routes)
        assert closed[0]==[False];r['source_shape']=shape(h,root);r['preparation_seconds']=time.perf_counter()-started
        settings={k:v for k,v in POLICY.items() if k!='step_limit'}
        engine=EarlySavedExpansion(h,**settings)
        h.set_admission_budget(POLICY['state_limit']);stop='step_limit'
        for step in range(POLICY['step_limit']):
            if closed[0][0]:stop='target_closed';break
            tick=time.perf_counter();counts=Counter()
            chosen=focus_selection(h,routes,evidence,saved,focus,False);source=chosen['source'];assert source is not None
            row=dict(step=step,selection_seconds=time.perf_counter()-tick,source_sha256=sha_key(source),source_shape=shape(h,source))
            tick=time.perf_counter()
            result=engine.advance(source,routes,counts,pending_split=chosen['pending_split'])
            row.update(acquisition_seconds=time.perf_counter()-tick,acquisition_counts=dict(counts),
                mode=result['mode'],admitted_total=len(h.admitted),admitted_now=len(result['added']),pending=result['pending'])
            row['operation']=archive_json(out/f'step-{step:02d}.json.gz',result)
            if result['mode'] in ('early_saved_split','early_closed_split','split_after_ordinary_exhaustion','resume_split'):
                saved=add_splits([[],[],[],saved,[]],[result['record']])[3];evidence=add_splits(evidence,[result['record']])
            tick=time.perf_counter()
            if maintained:
                row['maintenance']=maintained.refresh(result,evidence,bridges);routes=maintained.routes
            else:
                routes=routes_for(h,evidence,bridges);row['maintenance']=dict(mode='full_rebuild')
            row['route_refresh_seconds']=time.perf_counter()-tick
            row['database_changes']=h.db.total_changes
            tick=time.perf_counter();closed,plans,cc=full(h,[root],routes)
            row.update(coverage_seconds=time.perf_counter()-tick,coverage_counts=cc,target_closed=closed[0][0]);r['steps'].append(row)
            print(json.dumps(dict(arm=out.name,step=step,shape=row['source_shape'],mode=result['mode'],
                admitted=len(h.admitted),closed=closed[0][0],pending=result['pending'])),flush=True)
            if result['pending']:stop='admission_limit';break
            if result['mode']=='no_saved_pair':stop='no_saved_pair';break
        if closed[0][0]:stop='target_closed'
        r['final_activation_index']=maintained.statistics() if mode=='activation' else None
        r.update(stop=stop,target_closed=closed[0][0],target_flags=closed[0],without_growth_flags=closed[1],focus=focus,
            admitted_state_sha256=sorted(map(sha_key,h.admitted)),admission_counts=dict(h.admission_counts))
        r['bridges']=archive_json(out/'bridges.json.gz',bridges);r['splits']=archive_json(out/'splits.json.gz',[x for x in saved if split_key(x) not in inherited])
        r['certificate']=archive_json(out/'coverage.json.gz',plans[0])
        r['expanded_certificate']=archive_json(out/'expanded-coverage.json.gz',expand(h,plans[0],plans[0]['roots'],routes,Counter()))
        next_selection=focus_selection(h,routes,evidence,saved,focus,closed[0][0])
        r['next_selection']=archive_json(out/'next-selection.json.gz',next_selection)
        r['delta']=save_delta(seed,history,tmp/'delta',out/'proof-delta.sqlite3.gz')
        tick=time.perf_counter();r['cold_delta_counts']=check_delta(history,tmp/'delta',parent['options']);r['cold_delta_seconds']=time.perf_counter()-tick
        with sqlite3.connect(tmp/'delta') as db:stored={sha_key(k) for k, in db.execute('SELECT id FROM cnf_patterns_v1')}
        entered=set(r['admitted_state_sha256']);assert stored<=entered and len(entered)<=POLICY['state_limit']
        r.update(completed_new_state_sha256=sorted(stored),entered_but_unstored_sha256=sorted(entered-stored),history_bytes=history.stat().st_size)
    except BaseException:
        r['splits']=archive_json(out/'failed-splits.json.gz',saved);r['bridges']=archive_json(out/'failed-bridges.json.gz',bridges)
        r['failed_delta']=save_delta(seed,history,tmp/'failed-delta',out/'failed-proof-delta.sqlite3.gz')
        (out/'failed-report.json').write_text(encode(r)+'\n');raise
    finally:h.close()
    r['worker_seconds']=time.perf_counter()-started
    r['expansion_seconds']=sum(sum(row[k] for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')) for row in r['steps'])
    r['external_assumption_attempts']=sum(row['acquisition_counts'].get('probe_attempts',0) for row in r['steps'])
    (out/'report.json').write_text(encode(r)+'\n');return r


def run(out):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    r=dict(format=FORMAT,parent=dict(path=str(BASE),sha256=sha(BASE)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={name:sha(name) for name in FILES},policy=POLICY,arms=[],limitations=[
        'Matched pending-split versus selective pattern activation with identical EarlySavedExpansion scheduling. Current original 1062 and historical original 1154 are separate workloads.',
        'Two reversed repetitions per workload, independent seed copies, twelve advances and one shared 32-state allowance per worker.',
        'Fast updates permit only admitted pattern appends and the reported split sidecar. A reverse index activates old pending dependencies and preserves complete builder order. Other writes or sidecars use existing maintenance; external writers require reopening.',
        'Full worker time charges preparation, acquisition, checking and export. Historical/current restoration and union/global costs are separate.',
        'Both polarities remain structural obligations, independently of SAT answers. All previous history and unfinished admissions are retained explicitly.',
        'Shared process/OS caches and development cases, no confidence intervals or holdout. Stored bytes are not peak RAM; no globally minimal expansion or unrestricted SAT bound.'])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';tick=time.perf_counter();parent,*base_evidence=restore_base(BASE,seed,tmp)
        r.update(restore_seconds=time.perf_counter()-tick,options=parent['options'],cases=parent['cases'],baseline_closed=parent['final_closed'],
            seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,evidence_counts_before=list(map(len,base_evidence)))
        parent_hash=sha(seed);root=read_archive(parent['next_selection'])['source'];r['source']=root
        assert read_archive(parent['next_selection'])['selected_original_cases']==[14]
        old_bridges=read_archive(parent['bridges'])
        ct=tmp/'control';ct.mkdir();tick=time.perf_counter()
        control,*control_evidence=restore_control(CONTROL,ct/'seed',ct)
        r['control']=dict(path=str(CONTROL),sha256=sha(CONTROL),restore_seconds=time.perf_counter()-tick)
        control_hash=sha(ct/'seed')
        history=tmp/'history';shutil.copyfile(seed,history);evidence=copy.deepcopy(base_evidence)
        workloads=[('historical',ct/'seed',control,control_evidence,control['source'],1154),('current',seed,parent,base_evidence,root,1062)]
        touched={}
        for scenario,worker_seed,seed_report,worker_evidence,worker_root,case in workloads:
            for repeat in range(2):
                order=('pending','activation') if repeat%2==0 else ('activation','pending')
                for mode in order:
                    name=f'{scenario}-{repeat}-{mode}'
                    arm=worker(out/name,tmp/name,worker_seed,seed_report,worker_evidence,old_bridges,worker_root,mode,scenario)
                    r['arms'].append(dict(case=case,scenario=scenario,repeat=repeat,mode=mode,
                        path=str(out/name/'report.json'),sha256=sha(out/name/'report.json')))
                    apply_delta(history,tmp/name/'delta');check_delta(history,tmp/name/'delta',r['options'])
                    evidence=add_splits(evidence,read_archive(arm['splits']))
                    for step in arm['steps']:
                        op=read_archive(step['operation'])
                        if op.get('record') is not None:touched[split_key(op['record'])]=op['record']
        assert sha(seed)==parent_hash and sha(ct/'seed')==control_hash;r['parent_unchanged']=True
        previous={split_key(x) for x in base_evidence[3]};new_splits=[x for x in evidence[3] if split_key(x) not in previous]
        bridges=old_bridges
        r['touched_splits']=archive_json(out/'touched-splits.json.gz',list(touched.values()))
        r['splits']=archive_json(out/'splits.json.gz',new_splits);r['bridges']=archive_json(out/'bridges.json.gz',bridges)
        r['evidence_counts_after']=list(map(len,evidence));tick=time.perf_counter();h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
        try:
            routes=routes_for(h,evidence,bridges);roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
            r['global_route_preparation_seconds']=time.perf_counter()-tick;tick=time.perf_counter();closed,plans,cc=full(h,roots,routes)
            r.update(global_coverage_seconds=time.perf_counter()-tick,global_counts=cc,final_closed=closed[0],without_growth_closed=closed[1])
            assert not any(a and not b for a,b in zip(r['baseline_closed'],closed[0],strict=True))
            r['gains']=[i for i,(a,b) in enumerate(zip(r['baseline_closed'],closed[0],strict=True)) if b and not a]
            r['certificate']=archive_json(out/'coverage.json.gz',plans[0]);r['expanded_certificate']=archive_json(out/'expanded-coverage.json.gz',expand(h,plans[0],plans[0]['roots'],routes,Counter()))
            state=frontier(h,routes,evidence[3],Counter());r['frontier']=archive_json(out/'frontier.json.gz',state)
            r['frontier_profiles']=archive_json(out/'frontier-profiles.json.gz',[profile(h,routes,row) for row in state['leaves']])
            r['projection_frontier']=archive_json(out/'projection-frontier.json.gz',remaining(h,[dict(source=x['source'],target=x['target']) for x in bridges],routes,Counter()))
            r['learning']=archive_json(out/'learning.json.gz',learning_selection(h,routes,Counter()))
            r['next_selection']=archive_json(out/'next-selection.json.gz',select(h,routes,evidence,roots,closed[0],Counter()))
            r['historical_cache']=checked_inventory(h)[1];r['delta']=save_delta(seed,history,tmp/'delta',out/'proof-delta.sqlite3.gz')
            d=parent['reference'];assert sha(d['path'])==d['sha256'];unpack(d['path'],tmp/'reference',d['database_sha256']);shutil.copyfile(tmp/'reference',tmp/'reference-seed')
            pr=probe_reference(h,routes,[dict(kind=x['kind'],id=x['id']) for x in new_probes(tmp/'delta')],r,out,tmp)
            r['probe_reference']={k:pr[k] for k in ('rows','originals','seconds','cold_seconds','verified_nodes')}
            r['reference']=split_reference(h,list(touched.values()),r,out,tmp)
        finally:h.close()
        r['logical_table_digests']=digests(history);r['expanded_database_bytes']=history.stat().st_size
        tick=time.perf_counter();r['cold_delta_counts']=check_delta(history,tmp/'delta',r['options']);r['cold_delta_seconds']=time.perf_counter()-tick
        rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,tmp/'delta');assert digests(rebuilt)==r['logical_table_digests']
        before=sha(rebuilt);apply_delta(rebuilt,tmp/'delta');assert sha(rebuilt)==before;r['idempotent_merge']=True
        tick=time.perf_counter();h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0)
        try:
            for record in new_splits:verify_split(h,record,Counter())
            for record in bridges:verify_bridge(h,record,Counter())
            claimed=[h._canonical(c['source'],h.config['max_depth'])[2] for c,b in zip(r['cases'],r['final_closed'],strict=True) if b]
            verify_positive(h,read_archive(r['expanded_certificate']),claimed,evidence,bridges,Counter());assert not h.admitted
        finally:h.close()
        r['cold_positive_seconds']=time.perf_counter()-tick
        with sqlite3.connect(tmp/'delta') as db:r['new_node_kinds']=dict(Counter(json.loads(p)['kind'] for p, in db.execute('SELECT payload FROM cnf_patterns_v1')))
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],new_kinds=r['new_node_kinds'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
