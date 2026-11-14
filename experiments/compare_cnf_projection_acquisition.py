#!/usr/bin/env python3
"""Compare bounded projection acquisition with ordinary continuation."""
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

from experiments.compare_cnf_projection_bridge import (restore_checkpoint as restore_base,
    routes_for, add_splits, select, BudgetedInventory, EarlyClosedExpansion, full, expand,
    archive_json, read_archive, sha, sha_key, digests, unpack, apply_delta, check_delta,
    save_delta, new_probes, probe_reference, split_reference, frontier, profile,
    learning_selection, checked_inventory, verify_split, verify_positive, verify_bridge, shape)
from experiments.cnf_projection_acquisition import propose, acquire_projection
from experiments.cnf_projection_bridge import record_key as bridge_key, lift as lift_bridge
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_residual_dag import holds
from experiments.cnf_target_probe import remaining
from experiments.cnf_trace_split import record_key as split_key
from experiments.cnf_pattern_inventory import encode

BASE=Path('experiments/results/cnf-projection-bridge/report.json')
DISCOVERY=Path('experiments/results/cnf-projection-lookup/report.json')
FORMAT='projection-acquisition-comparison-v1'
POLICY=dict(step_limit=12,state_limit=32,pair_limit=32,candidate_limit=64)
FILES=['experiments/compare_cnf_projection_acquisition.py','experiments/cnf_projection_acquisition.py',
       'solver/test_cnf_projection_acquisition.py','experiments/cnf_projection_bridge.py',
       'experiments/cnf_early_closed.py','experiments/cnf_learning_batch.py',
       'experiments/cnf_original_frontier.py','experiments/cnf_split_batch.py']


def restore_checkpoint(report_path,path,tmp):
    r=json.loads(Path(report_path).read_text())
    if r['format']!=FORMAT or Path(r['parent']['path'])!=BASE or sha(BASE)!=r['parent']['sha256']:
        raise ValueError('Changed projection acquisition parent')
    for name,digest in r['fingerprints'].items():
        if sha(name)!=digest:raise ValueError('Changed projection acquisition implementation')
    parent,*evidence=restore_base(BASE,path,tmp)
    if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:
        raise ValueError('Incorrect projection acquisition seed')
    d=r['delta'];delta=tmp/'projection-acquisition-delta'
    if sha(d['path'])!=d['sha256']:raise ValueError('Changed projection acquisition delta')
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


def focus_selection(h,routes,evidence,saved,focus,root_closed):
    return None if root_closed else select(h,routes,[*evidence[:3],saved,evidence[4]],[focus],[False],Counter())


def worker(out,tmp,seed,parent,evidence,old_bridges,root,variable,expected,mode):
    out.mkdir();tmp.mkdir();started=time.perf_counter();history=tmp/'history';shutil.copyfile(seed,history)
    r=dict(mode=mode,policy=POLICY,source_sha256=sha_key(root),steps=[],seed_table_digests=digests(seed))
    h=BudgetedInventory(history,**parent['options']);h.set_admission_budget(0)
    saved=[];bridges=copy.deepcopy(old_bridges);evidence=copy.deepcopy(evidence);focus=root
    try:
        routes=routes_for(h,evidence,bridges);closed,plans,_=full(h,[root],routes)
        assert closed[0]==[False];r['source_shape']=shape(h,root);r['preparation_seconds']=time.perf_counter()-started
        engine=EarlyClosedExpansion(h,**{k:v for k,v in POLICY.items() if k!='step_limit'})
        h.set_admission_budget(POLICY['state_limit']);stop='step_limit'
        for step in range(POLICY['step_limit']):
            if closed[0][0]:stop='target_closed';break
            tick=time.perf_counter();counts=Counter()
            if mode=='projection' and step==0:
                source=root;chosen=None
            else:
                chosen=focus_selection(h,routes,evidence,saved,focus,False);source=chosen['source'];assert source is not None
            row=dict(step=step,selection_seconds=time.perf_counter()-tick,source_sha256=sha_key(source),source_shape=shape(h,source))
            tick=time.perf_counter()
            if mode=='projection' and step==0:
                record=propose(h,root,variable,counts)
                if record['target']!=expected:raise ValueError('Projection differs from saved discovery candidate')
                op=acquire_projection(h,record,counts,state_limit=POLICY['state_limit'],target_limit=POLICY['pair_limit'])
                result=dict(mode='projection_acquisition',source=root,**op)
                if op['bridge'] is not None:bridges.append(record);focus=record['target']
            else:
                result=engine.advance(source,routes,counts,pending_split=chosen['pending_split'])
            row.update(acquisition_seconds=time.perf_counter()-tick,acquisition_counts=dict(counts),
                mode=result['mode'],admitted_total=len(h.admitted),admitted_now=len(result['added']),pending=result['pending'])
            row['operation']=archive_json(out/f'step-{step:02d}.json.gz',result)
            if result['mode'] in ('preselected_split','early_closed_split','split_after_ordinary_exhaustion','resume_split'):
                saved=add_splits([[],[],[],saved,[]],[result['record']])[3];evidence=add_splits(evidence,[result['record']])
            tick=time.perf_counter();routes=routes_for(h,evidence,bridges);row['route_refresh_seconds']=time.perf_counter()-tick
            tick=time.perf_counter();closed,plans,cc=full(h,[root],routes)
            row.update(coverage_seconds=time.perf_counter()-tick,coverage_counts=cc,target_closed=closed[0][0]);r['steps'].append(row)
            print(json.dumps(dict(arm=out.name,step=step,shape=row['source_shape'],mode=result['mode'],
                admitted=len(h.admitted),closed=closed[0][0],pending=result['pending'])),flush=True)
            if result['pending']:stop='admission_limit';break
            if result['mode']=='no_saved_pair':stop='no_saved_pair';break
        if closed[0][0]:stop='target_closed'
        r.update(stop=stop,target_closed=closed[0][0],target_flags=closed[0],without_growth_flags=closed[1],focus=focus,
            admitted_state_sha256=sorted(map(sha_key,h.admitted)),admission_counts=dict(h.admission_counts))
        r['bridges']=archive_json(out/'bridges.json.gz',bridges);r['splits']=archive_json(out/'splits.json.gz',saved)
        r['certificate']=archive_json(out/'coverage.json.gz',plans[0])
        r['expanded_certificate']=archive_json(out/'expanded-coverage.json.gz',expand(h,plans[0],plans[0]['roots'],routes,Counter()))
        if r['steps'][-1]['mode']=='projection_acquisition' and r['steps'][-1]['pending']:
            next_selection=dict(mode='pending_projection',proposal=read_archive(r['steps'][-1]['operation'])['proposal'])
        else:next_selection=focus_selection(h,routes,evidence,saved,focus,closed[0][0])
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


def bridge_reference(h,record,tmp):
    solver=AccountedResidualSolver(tmp/'reference');start=time.perf_counter()
    try:
        source=h._load(record['source'])['cnf'];target=h._load(record['target'])['cnf']
        a=solver.solve(source);b=solver.solve(target);assert a['answer']==b['answer']
        if b['answer']:assert holds(source,lift_bridge(source,target,record['proof'],b['model']))
        return dict(record=record,source=a,target=b,seconds=time.perf_counter()-start,counts=dict(solver.counts))
    finally:solver.close()


def run(out):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    r=dict(format=FORMAT,parent=dict(path=str(BASE),sha256=sha(BASE)),discovery=dict(path=str(DISCOVERY),sha256=sha(DISCOVERY)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),fingerprints={name:sha(name) for name in FILES},
        policy=POLICY,arms=[],limitations=[
        'One preselected development projection from the preserved discovery experiment; two repetitions per mode in reversed order.',
        'Both modes start from independent identical seeds and seek closure of the same 37-variable source under twelve advances and one 32-state allowance.',
        'Projection acquisition and certificate construction consume the first advance and the same shared admission budget. Thereafter the unchanged continuation engine follows the projected target.',
        'Candidate discovery was paid in the previous experiment; this comparison is conditional on the saved candidate and does not rebuild the optional global lookup index.',
        'All preparation, acquisition, route refresh, persistence and cold replay are charged. Incomplete paths do not establish a completion-time saving.',
        'All arm results and old bridges survive in the union. Reference answers do not establish structural coverage; disk size is not peak RAM or an unrestricted SAT bound.'])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';tick=time.perf_counter();parent,*base_evidence=restore_base(BASE,seed,tmp)
        r.update(restore_seconds=time.perf_counter()-tick,options=parent['options'],cases=parent['cases'],baseline_closed=parent['final_closed'],
            seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,evidence_counts_before=list(map(len,base_evidence)))
        parent_hash=sha(seed);selected=read_archive(parent['next_selection']);root=selected['source'];r['source']=root
        discovery=json.loads(DISCOVERY.read_text());diagnostics=read_archive(discovery['selected_diagnostics']);assert len(diagnostics)==1
        variable=diagnostics[0]['variable'];expected=diagnostics[0]['minimal_key'];r['selected_candidate']=diagnostics[0]
        old_bridges=read_archive(parent['bridges']);bridge_map={bridge_key(x):x for x in old_bridges}
        history=tmp/'history';shutil.copyfile(seed,history);evidence=copy.deepcopy(base_evidence)
        for repeat,order in enumerate((('ordinary','projection'),('projection','ordinary'))):
            for mode in order:
                name=f'{repeat}-{mode}';arm=worker(out/name,tmp/name,seed,parent,base_evidence,old_bridges,root,variable,expected,mode)
                r['arms'].append(dict(mode=mode,repeat=repeat,path=str(out/name/'report.json'),sha256=sha(out/name/'report.json')))
                apply_delta(history,tmp/name/'delta');check_delta(history,tmp/name/'delta',r['options'])
                evidence=add_splits(evidence,read_archive(arm['splits']))
                for record in read_archive(arm['bridges']):bridge_map[bridge_key(record)]=record
        assert sha(seed)==parent_hash;r['parent_unchanged']=True
        previous={split_key(x) for x in base_evidence[3]};new_splits=[x for x in evidence[3] if split_key(x) not in previous]
        bridges=list(bridge_map.values());new_bridges=[x for x in bridges if bridge_key(x) not in {bridge_key(y) for y in old_bridges}]
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
            r['bridge_reference']=[bridge_reference(h,x,tmp) for x in new_bridges]
            r['reference']=split_reference(h,new_splits,r,out,tmp)
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
