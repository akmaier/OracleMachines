#!/usr/bin/env python3
"""Cold replay common initial splitting and the two descendant policies."""
from collections import Counter
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

from experiments.compare_cnf_combined_expansion import (BASE,POLICY,restore_checkpoint,restore_base,
    routes_for,add_splits,select,focus_selection,BudgetedInventory,full,verify_split,verify_positive,
    read_archive,sha,sha_key,unpack,digests,split_key,remaining)
from experiments.validate_cnf_split_cost import load_report,merge_checked,novel_patterns,split_findings
from experiments.cnf_residual_dag import ResidualSolver
from experiments.continue_cnf_local_forcing import profile
from experiments.validate_cnf_warm_transfer import path as checked_path,shape
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_window import record_key as window_key
from experiments.cnf_probe_continuation import record_key as continuation_key


def prefix_progress(seed, delta, ar, evidence, bridges, options, output):
    """Replay only rows available after each recorded advance, not the final union.

    New pattern admission IDs bind the rows to their creation advance. Missing
    admitted rows stay missing: an interrupted ancestor is not a stored proof.
    Probe records are inserted at their own logged advance. All other tables
    must be empty in this experiment's delta. No fresh discovery is permitted.
    """
    shutil.copyfile(seed,output)
    db=sqlite3.connect(delta)
    tables=('cnf_patterns_v1','cnf_probe_windows_v1','cnf_probe_continuations_v1')
    try:
        saved={table:dict(db.execute(f'SELECT id,payload FROM {table}')) for table in tables}
        for table, in db.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            if table not in tables:assert db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==0
    finally:db.close()
    h=BudgetedInventory(output,**options);h.set_admission_budget(0)
    inserted={table:set() for table in tables};splits=[];progress=[];entered=set()
    first=read_archive(ar['steps'][0]['operation']);targets=[edge['key'] for edge in first['record']['edges']]
    started=time.perf_counter()
    try:
        for row in ar['steps']:
            op=read_archive(row['operation']);entered.update(op['added'])
            additions={table:[] for table in tables}
            additions[tables[0]]=[(key,saved[tables[0]][key]) for key in op['added'] if key in saved[tables[0]]]
            ordinary=op.get('operation') or {};record=ordinary.get('record')
            if record is not None:
                kind=ordinary['kind'];table={'probe_window':tables[1],'probe_continuation':tables[2]}[kind]
                key=(window_key if kind=='probe_window' else continuation_key)(record)
                payload=encode(record)
                if key in saved[table] and key not in inserted[table]:
                    assert saved[table][key]==payload;additions[table].append((key,payload))
                else:assert h.db.execute(f'SELECT payload FROM {table} WHERE id=?',(key,)).fetchone()==(payload,)
            with h.db:
                for table, rows in additions.items():
                    for key,payload in rows:
                        assert key not in inserted[table]
                        h.db.execute(f'INSERT INTO {table} VALUES (?,?)',(key,payload));inserted[table].add(key)
            if op.get('record') is not None:
                splits=add_splits([[],[],[],splits,[]],[op['record']])[3]
            ev=add_splits(evidence,splits);routes=routes_for(h,ev,bridges)
            closed,_,_=full(h,[ar['focus'],*targets],routes)
            assert closed[0][0]==row['target_closed']
            selection=focus_selection(h,routes,ev,splits,ar['focus'],closed[0][0])
            if row['step']+1<len(ar['steps']):
                assert sha_key(selection['source'])==ar['steps'][row['step']+1]['source_sha256']
            else:assert selection==read_archive(ar['next_selection'])
            progress.append(dict(step=row['step'],root_closed=closed[0][0],common_children_closed=closed[0][1:],
                without_growth=closed[1],admitted=len(entered),stored_new_patterns=len(inserted[tables[0]]),
                cumulative_expansion_seconds=sum(sum(x[k] for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds'))
                    for x in ar['steps'][:row['step']+1])))
        assert all(inserted[table]==set(saved[table]) for table in tables)
        assert not h.admitted
    finally:h.close()
    return dict(steps=progress,first_common_child_completion=[next((row for row in progress if row['common_children_closed'][i]),None) for i in range(2)],
                replay_seconds=time.perf_counter()-started)


def validate(out):
    start=time.perf_counter();r=json.loads((out/'report.json').read_text());parent=load_report(r['parent'])
    assert Path(r['parent']['path'])==BASE
    assert r['source']==read_archive(parent['next_selection'])['source']
    expected=[]
    for case in (1154,):
        for repeat in range(2):
            order=('ordinary','early_saved') if repeat%2==0 else ('early_saved','ordinary')
            expected.extend((case,repeat,mode) for mode in order)
    assert [(a['case'],a['repeat'],a['mode']) for a in r['arms']]==expected
    result=dict(report_sha256=sha(out/'report.json'),arms=[]);findings=dict(arms=[])
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('fresh recognition')):
        tmp=Path(td);tick=time.perf_counter();restored,*evidence=restore_checkpoint(out/'report.json',tmp/'final',tmp)
        assert restored==r;result['restore_seconds']=time.perf_counter()-tick
        seeds={};hashes={}
        for case,base,restore,bound in ((1154,BASE,restore_base,parent),):
            ct=tmp/str(case);ct.mkdir();original,*ev=restore(base,ct/'seed',ct);assert original==bound
            assert digests(ct/'seed')==r['seed_table_digests']
            target=r['source']
            bridges=read_archive(parent['bridges'])
            seeds[case]=(ct,ev,target,bridges);hashes[case]=sha(ct/'seed')
        d=r['reference'];assert sha(d['path'])==d['sha256'];unpack(d['path'],tmp/'reference',d['database_sha256']);solver=ResidualSolver(tmp/'reference')
        repeats={}
        try:
            with patch.object(solver,'_expand',side_effect=AssertionError('fresh reference search')):
                for bound in r['arms']:
                    ar=load_report(bound);case=bound['case'];ct,base_evidence,target,bridges=seeds[case]
                    assert ar['policy']==POLICY and ar['seed_table_digests']==digests(ct/'seed')
                    assert ar['source_sha256']==sha_key(target) and ar['focus']==target
                    name=f"{bound['repeat']}-{bound['mode']}";history=ct/name;shutil.copyfile(ct/'seed',history);delta=ct/(name+'-delta')
                    merge_checked(ar['delta'],history,delta,r['options']);splits=read_archive(ar['splits']);ev=add_splits(base_evidence,splits)
                    assert read_archive(ar['bridges'])==bridges
                    h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
                    try:
                        routes=routes_for(h,ev,bridges);closed,_,_=full(h,[target],routes)
                        assert closed==[ar['target_flags'],ar['without_growth_flags']]
                        verify_positive(h,read_archive(ar['expanded_certificate']),[target] if closed[0][0] else [],ev,bridges,Counter())
                        entered=set();saved=set()
                        for row in ar['steps']:
                            op=read_archive(row['operation']);assert sha_key(op['source'])==row['source_sha256']
                            ids=set(map(sha_key,op['added']));assert not ids&entered;entered.update(ids)
                            assert len(ids)==row['admitted_now'] and len(entered)==row['admitted_total']
                            if op.get('record') is not None:
                                verify_split(h,op['record'],Counter());assert len(op['acquisition']['branches'])==2
                                assert op['pending']==any(b['pending'] for b in op['acquisition']['branches'])
                                saved.add(split_key(op['record']))
                            if row['maintenance']['mode'].startswith('clear_'):
                                assert op['mode']=='ordinary'
                                assert op['operation']['record']['edge'] is None and not op['added'] and not op['pending']
                            if row['step']==0:
                                assert op['mode']=='split_after_ordinary_exhaustion' and op['ranked_pairs'][0]==[2,2,36,906,30]
                            if op['mode']=='early_saved_split':
                                assert row['step']>0 and ar['mode']=='early_saved'
                                assert op['selected_rank']==min(op['ranked_pairs'])
                        assert len(ar['steps'])<=POLICY['step_limit'] and len(entered)<=POLICY['state_limit']
                        assert saved=={split_key(s) for s in splits} and sorted(entered)==ar['admitted_state_sha256']
                        completed=novel_patterns(delta);assert completed<=entered
                        assert sorted(completed)==ar['completed_new_state_sha256'] and sorted(entered-completed)==ar['entered_but_unstored_sha256']
                        selected=focus_selection(h,routes,ev,splits,target,closed[0][0]);assert selected==read_archive(ar['next_selection'])
                        record=dict(case=case,mode=ar['mode'],repeat=bound['repeat'],closed=closed[0][0],admitted=len(entered),
                            completed=len(completed),unfinished=len(entered-completed),cold_selection_matches=True,idempotent=True)
                        result['arms'].append(record)
                        detail=dict(**record,focus_shape=shape(h._load(target)['cnf']),focus_prefix=checked_path(h,target),
                            splits=[split_findings(h,routes,solver,s) for s in splits])
                        if selected and selected.get('source') and selected.get('pending') is None:
                            detail['next_profile']=profile(h,routes,dict(source=selected['source'],variables=shape(h._load(selected['source'])['cnf'])[0]))
                        if bound['repeat']==0:
                            detail['prefix_progress']=prefix_progress(ct/'seed',delta,ar,base_evidence,bridges,r['options'],ct/(name+'-prefix'))
                            assert digests(ct/(name+'-prefix'))==digests(history)
                        findings['arms'].append(detail)
                        logical=(digests(history),splits,bridges,sorted(entered),selected,closed);identity=(case,ar['mode'])
                        if identity in repeats:assert repeats[identity]==logical
                        else:repeats[identity]=logical
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
        for case,(ct,*_) in seeds.items():assert sha(ct/'seed')==hashes[case]
        assert digests(tmp/'final')==r['logical_table_digests']
    result.update(passed=True,seconds=time.perf_counter()-start,repeated_logical_results_identical=True,seed_unchanged=True)
    summary=dict(arms=[],paired=[],limitations=r['limitations'])
    for case in (1154,):
        for mode in ('ordinary','early_saved'):
            arms=[load_report(a) for a in r['arms'] if a['case']==case and a['mode']==mode];first=arms[0]
            summary['arms'].append(dict(case=case,mode=mode,steps=len(first['steps']),closed=first['target_closed'],
                admitted=len(first['admitted_state_sha256']),completed=len(first['completed_new_state_sha256']),unfinished=len(first['entered_but_unstored_sha256']),
                expansion_mean_seconds=statistics.mean(a['expansion_seconds'] for a in arms),worker_mean_seconds=statistics.mean(a['worker_seconds'] for a in arms),
                costs_mean_seconds={k:statistics.mean(sum(row[k] for row in a['steps']) for a in arms) for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')},
                preparation_mean_seconds=statistics.mean(a['preparation_seconds'] for a in arms),delta_export_mean_seconds=statistics.mean(a['delta']['seconds'] for a in arms),
                compressed_delta_bytes=first['delta']['compressed_bytes'],delta_database_bytes=first['delta']['database_bytes'],history_bytes=first['history_bytes'],
                external_assumption_attempts=first['external_assumption_attempts'],
                maintenance_modes=dict(Counter(row['maintenance']['mode'] for row in first['steps'])),
                sidecar_snapshot_bytes=max((row['maintenance'].get('sidecar_snapshot_bytes',0) for row in first['steps']),default=0)))
        originals={mode:load_report(next(a for a in r['arms'] if a['case']==case and a['repeat']==0 and a['mode']==mode))
                   for mode in ('ordinary','early_saved')}
        keys={mode:set(a['completed_new_state_sha256']) for mode,a in originals.items()}
        assert read_archive(originals['ordinary']['steps'][0]['operation'])==read_archive(originals['early_saved']['steps'][0]['operation'])
        summary['paired'].append(dict(case=case,identical_initial_split=True,both_closed=all(a['target_closed'] for a in originals.values()),
            identical_new_pattern_keys=keys['ordinary']==keys['early_saved'],shared_new_patterns=len(keys['ordinary']&keys['early_saved']),
            ordinary_only_patterns=len(keys['ordinary']-keys['early_saved']),early_saved_only_patterns=len(keys['early_saved']-keys['ordinary'])))
    for name,data in [('reconstruction.json',result),('structural-findings.json',findings),('comparison-summary.json',summary)]:
        (out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','covered','gains','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
