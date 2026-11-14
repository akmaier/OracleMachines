#!/usr/bin/env python3
"""Independently reconstruct matched maintenance runs and every first-repeat prefix."""
from collections import Counter
import copy
import json
from pathlib import Path
import shutil
import sqlite3
import statistics
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_pending_maintenance import (BASE,CONTROL,POLICY,restore_checkpoint,restore_base,restore_control,
    routes_for,add_splits,select,focus_selection,BudgetedInventory,full,verify_split,verify_positive,
    read_archive,sha,sha_key,unpack,digests,split_key,remaining,ClearProbeMaintenance,PendingSplitMaintenance)
from experiments.validate_cnf_split_cost import load_report,merge_checked,novel_patterns,split_findings
from experiments.cnf_residual_dag import ResidualSolver
from experiments.continue_cnf_local_forcing import profile
from experiments.validate_cnf_warm_transfer import path as checked_path,shape
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_window import record_key as window_key
from experiments.cnf_probe_continuation import record_key as continuation_key


def prefix_replay(seed,delta,ar,evidence,bridges,options,output):
    """Insert only then-available rows; compare maintained and full catalogs each step."""
    shutil.copyfile(seed,output);db=sqlite3.connect(delta)
    tables=('cnf_patterns_v1','cnf_probe_windows_v1','cnf_probe_continuations_v1')
    try:
        payloads={table:dict(db.execute(f'SELECT id,payload FROM {table}')) for table in tables}
        for table, in db.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            if table not in tables:assert db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==0
    finally:db.close()
    h=BudgetedInventory(output,**options);h.set_admission_budget(POLICY['state_limit'])
    inserted={table:set() for table in tables};progress=[];started=time.perf_counter()
    saved=copy.deepcopy(evidence[3]) if ar['scenario']=='resume' else [];ev=copy.deepcopy(evidence)
    maintenance=(ClearProbeMaintenance if ar['mode']=='clear' else PendingSplitMaintenance)(h,ev,bridges,routes_for)
    try:
        for row in ar['steps']:
            op=read_archive(row['operation']);before_changes=h.db.total_changes
            closed,_,_=full(h,[ar['focus']],maintenance.routes)
            chosen=focus_selection(h,maintenance.routes,ev,saved,ar['focus'],closed[0][0])
            assert chosen['source']==op['source']
            if chosen['pending_split'] is not None:
                assert op['mode']=='resume_split' and op['record']==chosen['pending_split']
            additions={table:[] for table in tables}
            additions[tables[0]]=[(key,payloads[tables[0]][key]) for key in op['added'] if key in payloads[tables[0]]]
            ordinary=op.get('operation') or {};record=ordinary.get('record')
            if record is not None:
                kind=ordinary['kind'];table={'probe_window':tables[1],'probe_continuation':tables[2]}[kind]
                key=(window_key if kind=='probe_window' else continuation_key)(record);payload=encode(record)
                if key in payloads[table] and key not in inserted[table]:
                    assert payloads[table][key]==payload;additions[table].append((key,payload))
                else:assert h.db.execute(f'SELECT payload FROM {table} WHERE id=?',(key,)).fetchone()==(payload,)
            with h.db:
                for table,rows in additions.items():
                    for key,payload in rows:
                        assert key not in inserted[table]
                        h.db.execute(f'INSERT INTO {table} VALUES (?,?)',(key,payload));inserted[table].add(key)
            assert not (set(op['added'])&h.admitted);h.admitted.update(op['added'])
            assert len(h.admitted)==row['admitted_total']
            if op.get('record') is not None:
                saved=add_splits([[],[],[],saved,[]],[op['record']])[3];ev=add_splits(ev,[op['record']])
            maintained=maintenance.refresh(op,ev,bridges)
            assert maintained['mode']==row['maintenance']['mode']
            fresh=routes_for(h,ev,bridges)
            assert dict(maintenance.routes.by_source)==dict(fresh.by_source)
            assert maintenance.routes.windows==fresh.windows and maintenance.routes.continuations==fresh.continuations
            full_flags,_,_=full(h,[ar['focus']],fresh);warm_flags,_,_=full(h,[ar['focus']],maintenance.routes)
            assert full_flags==warm_flags and full_flags[0][0]==row['target_closed']
            selected=focus_selection(h,fresh,ev,saved,ar['focus'],full_flags[0][0])
            assert selected==focus_selection(h,maintenance.routes,ev,saved,ar['focus'],full_flags[0][0])
            if row['step']+1<len(ar['steps']):assert sha_key(selected['source'])==ar['steps'][row['step']+1]['source_sha256']
            else:assert selected==read_archive(ar['next_selection'])
            if maintained['mode'].startswith('pending_split_'):
                assert h.db.total_changes==before_changes
                assert any(h._load(edge['key']) is None for edge in op['record']['edges'])
            progress.append(dict(step=row['step'],mode=maintained['mode'],closed=full_flags[0][0],
                admitted=len(h.admitted),stored_new_patterns=len(inserted[tables[0]]),
                inserted_rows=h.db.total_changes-before_changes,complete_catalog_equal=True,next_selection_equal=True))
        assert all(inserted[table]==set(payloads[table]) for table in tables)
    finally:h.close()
    return dict(steps=progress,replay_seconds=time.perf_counter()-started)


def validate(out):
    start=time.perf_counter();r=json.loads((out/'report.json').read_text());parent=load_report(r['parent']);control=load_report(r['control'])
    assert Path(r['parent']['path'])==BASE and Path(r['control']['path'])==CONTROL and r['source']==parent['source']
    expected=[]
    for scenario in ('interruption','resume'):
        for repeat in range(2):
            for mode in (('clear','pending') if repeat%2==0 else ('pending','clear')):expected.append((scenario,repeat,mode))
    assert [(a['scenario'],a['repeat'],a['mode']) for a in r['arms']]==expected
    result=dict(report_sha256=sha(out/'report.json'),arms=[]);findings=dict(arms=[])
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('fresh recognition')):
        tmp=Path(td);tick=time.perf_counter();restored,*evidence=restore_checkpoint(out/'report.json',tmp/'final',tmp)
        assert restored==r;result['restore_seconds']=time.perf_counter()-tick;seeds={};hashes={}
        for scenario,base,restore,bound in [('interruption',CONTROL,restore_control,control),('resume',BASE,restore_base,parent)]:
            ct=tmp/scenario;ct.mkdir();original,*ev=restore(base,ct/'seed',ct);assert original==bound
            bridges=read_archive(bound['bridges']);seeds[scenario]=(ct,ev,r['source'],bridges);hashes[scenario]=sha(ct/'seed')
        d=r['reference'];assert sha(d['path'])==d['sha256'];unpack(d['path'],tmp/'reference',d['database_sha256']);solver=ResidualSolver(tmp/'reference')
        repeats={};operations={}
        old_arm=load_report(next(a for a in parent['arms'] if a['mode']=='early_saved' and a['repeat']==0))
        old_ops=[read_archive(row['operation']) for row in old_arm['steps']]
        try:
            with patch.object(solver,'_expand',side_effect=AssertionError('fresh reference search')):
                for bound in r['arms']:
                    ar=load_report(bound);scenario=bound['scenario'];ct,base_evidence,target,bridges=seeds[scenario]
                    assert ar['policy']==POLICY and ar['seed_table_digests']==digests(ct/'seed') and ar['focus']==target
                    name=f"{bound['repeat']}-{bound['mode']}";history=ct/name;shutil.copyfile(ct/'seed',history);delta=ct/(name+'-delta')
                    merge_checked(ar['delta'],history,delta,r['options']);splits=read_archive(ar['splits']);ev=add_splits(base_evidence,splits)
                    saved=ev[3] if scenario=='resume' else splits
                    assert read_archive(ar['bridges'])==bridges
                    h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
                    try:
                        routes=routes_for(h,ev,bridges);closed,_,_=full(h,[target],routes)
                        assert closed==[ar['target_flags'],ar['without_growth_flags']]
                        verify_positive(h,read_archive(ar['expanded_certificate']),[target] if closed[0][0] else [],ev,bridges,Counter())
                        entered=set();op_records={};ops=[]
                        for row in ar['steps']:
                            op=read_archive(row['operation']);ops.append(op);assert sha_key(op['source'])==row['source_sha256']
                            ids=set(map(sha_key,op['added']));assert not ids&entered;entered.update(ids)
                            assert len(ids)==row['admitted_now'] and len(entered)==row['admitted_total']
                            if op.get('record') is not None:
                                verify_split(h,op['record'],Counter());assert len(op['acquisition']['branches'])==2
                                assert op['pending']==any(b['pending'] for b in op['acquisition']['branches'])
                                op_records[split_key(op['record'])]=op['record']
                            if op['mode']=='early_saved_split':assert op['selected_rank']==min(op['ranked_pairs'])
                        assert len(ar['steps'])<=POLICY['step_limit'] and len(entered)<=POLICY['state_limit']
                        inherited={split_key(s) for s in base_evidence[3]}
                        assert set(op_records)-inherited=={split_key(s) for s in splits}
                        assert sorted(entered)==ar['admitted_state_sha256']
                        completed=novel_patterns(delta);assert completed<=entered
                        assert sorted(completed)==ar['completed_new_state_sha256'] and sorted(entered-completed)==ar['entered_but_unstored_sha256']
                        selected=focus_selection(h,routes,ev,saved,target,closed[0][0]);assert selected==read_archive(ar['next_selection'])
                        record=dict(scenario=scenario,mode=ar['mode'],repeat=bound['repeat'],closed=closed[0][0],admitted=len(entered),
                            completed=len(completed),unfinished=len(entered-completed),cold_selection_matches=True,idempotent=True)
                        result['arms'].append(record)
                        detail=dict(**record,splits=[split_findings(h,routes,solver,s) for s in op_records.values()])
                        if scenario=='resume':
                            lost=set(old_arm['entered_but_unstored_sha256'])
                            detail['previous_interrupted_reentered']=sorted(lost&entered)
                            detail['previous_interrupted_now_stored']=sorted(lost&completed)
                            assert ops[0]['mode']=='resume_split' and ops[0]['record']==old_ops[-1]['record']
                        else:assert ops==old_ops
                        if selected and selected.get('source') and selected.get('pending') is None:
                            detail['next_profile']=profile(h,routes,dict(source=selected['source'],variables=shape(h._load(selected['source'])['cnf'])[0]))
                        if bound['repeat']==0:
                            detail['prefix_replay']=prefix_replay(ct/'seed',delta,ar,base_evidence,bridges,r['options'],ct/(name+'-prefix'))
                            assert digests(ct/(name+'-prefix'))==digests(history)
                        findings['arms'].append(detail)
                        logical=(digests(history),splits,bridges,sorted(entered),selected,closed)
                        if scenario in repeats:assert repeats[scenario]==logical and operations[scenario]==ops
                        else:repeats[scenario]=logical;operations[scenario]=ops
                        assert not h.admitted;print(json.dumps(record),flush=True)
                    finally:h.close()
                h=BudgetedInventory(tmp/'final',**r['options']);h.set_admission_budget(0)
                try:
                    bridges=read_archive(r['bridges']);assert bridges==read_archive(parent['bridges'])
                    tick=time.perf_counter();routes=routes_for(h,evidence,bridges)
                    roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
                    closed,_,counts=full(h,roots,routes);assert closed==[r['final_closed'],r['without_growth_closed']]
                    selected=select(h,routes,evidence,roots,closed[0],Counter());assert selected==read_archive(r['next_selection'])
                    assert remaining(h,[dict(source=x['source'],target=x['target']) for x in bridges],routes,Counter())==read_archive(r['projection_frontier'])
                    result.update(global_coverage_seconds=time.perf_counter()-tick,global_coverage_counts=counts,
                        covered=sum(closed[0]),gains=r['gains'],cold_next_selection_matches=True,evidence_counts=list(map(len,evidence)))
                    if selected['source'] is not None and selected.get('pending') is None:
                        findings['next_profile']=profile(h,routes,dict(source=selected['source'],variables=shape(h._load(selected['source'])['cnf'])[0]))
                    assert not h.admitted
                finally:h.close()
                for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
                result['verified_reference_nodes']=len(solver.checked);assert not solver.counts.get('expanded_nodes',0)
        finally:solver.close()
        for scenario,(ct,*_) in seeds.items():assert sha(ct/'seed')==hashes[scenario]
        assert digests(tmp/'final')==r['logical_table_digests']
    result.update(passed=True,seconds=time.perf_counter()-start,matched_operations_and_logical_results_identical=True,seed_unchanged=True)
    summary=dict(arms=[],limitations=r['limitations'])
    for scenario in ('interruption','resume'):
        for mode in ('clear','pending'):
            arms=[load_report(a) for a in r['arms'] if a['scenario']==scenario and a['mode']==mode];first=arms[0]
            summary['arms'].append(dict(scenario=scenario,mode=mode,steps=len(first['steps']),closed=first['target_closed'],
                admitted=len(first['admitted_state_sha256']),completed=len(first['completed_new_state_sha256']),unfinished=len(first['entered_but_unstored_sha256']),
                expansion_mean_seconds=statistics.mean(a['expansion_seconds'] for a in arms),worker_mean_seconds=statistics.mean(a['worker_seconds'] for a in arms),
                costs_mean_seconds={k:statistics.mean(sum(row[k] for row in a['steps']) for a in arms) for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')},
                preparation_mean_seconds=statistics.mean(a['preparation_seconds'] for a in arms),delta_export_mean_seconds=statistics.mean(a['delta']['seconds'] for a in arms),
                compressed_delta_bytes=first['delta']['compressed_bytes'],delta_database_bytes=first['delta']['database_bytes'],history_bytes=first['history_bytes'],
                external_assumption_attempts=first['external_assumption_attempts'],
                maintenance_modes=dict(Counter(row['maintenance']['mode'] for row in first['steps'])),
                sidecar_snapshot_bytes=max((row['maintenance'].get('sidecar_snapshot_bytes',0) for row in first['steps']),default=0)))
    for name,data in [('reconstruction.json',result),('structural-findings.json',findings),('comparison-summary.json',summary)]:
        (out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','covered','gains','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
