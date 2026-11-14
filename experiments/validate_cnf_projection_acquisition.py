#!/usr/bin/env python3
"""Reconstruct both acquisition alternatives with recognition and solving disabled."""
from collections import Counter
import json
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_projection_acquisition import (BASE,DISCOVERY,POLICY,restore_checkpoint,restore_base,
    routes_for,add_splits,select,focus_selection,BudgetedInventory,full,verify_split,verify_positive,verify_bridge,
    read_archive,sha,sha_key,unpack,digests,propose,bridge_key,split_key,remaining)
from experiments.validate_cnf_split_cost import load_report,merge_checked,novel_patterns,split_findings
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_projection_bridge import check,lift
from experiments.continue_cnf_local_forcing import profile
from experiments.validate_cnf_warm_transfer import path as checked_path,shape


def validate(out):
    start=time.perf_counter();r=json.loads((out/'report.json').read_text());parent=load_report(r['parent']);discovery=load_report(r['discovery'])
    assert Path(r['parent']['path'])==BASE and Path(r['discovery']['path'])==DISCOVERY
    assert r['selected_candidate']==read_archive(discovery['selected_diagnostics'])[0]
    assert r['source']==read_archive(parent['next_selection'])['source']
    assert [(a['repeat'],a['mode']) for a in r['arms']]==[(0,'ordinary'),(0,'projection'),(1,'projection'),(1,'ordinary')]
    result=dict(report_sha256=sha(out/'report.json'),arms=[]);findings=dict(arms=[])
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('fresh recognition')):
        tmp=Path(td);tick=time.perf_counter();restored,*evidence=restore_checkpoint(out/'report.json',tmp/'final',tmp)
        assert restored==r;result['restore_seconds']=time.perf_counter()-tick
        ct=tmp/'controls';ct.mkdir();original,*base_evidence=restore_base(BASE,ct/'seed',ct)
        assert original==parent and digests(ct/'seed')==r['seed_table_digests'];seed_hash=sha(ct/'seed')
        d=r['reference'];assert sha(d['path'])==d['sha256'];unpack(d['path'],tmp/'reference',d['database_sha256']);solver=ResidualSolver(tmp/'reference')
        repeats={}
        try:
            with patch.object(solver,'_expand',side_effect=AssertionError('fresh reference search')):
                for bound in r['arms']:
                    ar=load_report(bound);assert ar['policy']==POLICY and ar['seed_table_digests']==r['seed_table_digests']
                    name=f"{bound['repeat']}-{bound['mode']}";history=ct/name;shutil.copyfile(ct/'seed',history);delta=ct/(name+'-delta')
                    merge_checked(ar['delta'],history,delta,r['options']);splits=read_archive(ar['splits']);ev=add_splits(base_evidence,splits)
                    bridges=read_archive(ar['bridges']);h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
                    try:
                        routes=routes_for(h,ev,bridges);closed,_,_=full(h,[r['source']],routes)
                        assert closed==[ar['target_flags'],ar['without_growth_flags']]
                        positive=read_archive(ar['expanded_certificate']);claimed=[r['source']] if closed[0][0] else []
                        verify_positive(h,positive,claimed,ev,bridges,Counter())
                        entered=set();saved=set();projection_result=None
                        for row in ar['steps']:
                            op=read_archive(row['operation']);assert sha_key(op['source'])==row['source_sha256']
                            ids=set(map(sha_key,op['added']));assert not ids&entered;entered.update(ids)
                            assert len(ids)==row['admitted_now'] and len(entered)==row['admitted_total']
                            if op['mode']=='projection_acquisition':
                                assert row['step']==0 and ar['mode']=='projection'
                                assert op['proposal']==propose(h,r['source'],r['selected_candidate']['variable'],Counter())
                                assert op['proposal']['target']==r['selected_candidate']['minimal_key']
                                if op['pending']:assert op['bridge'] is None
                                else:
                                    assert op['bridge']==op['proposal'];verify_bridge(h,op['bridge'],Counter())
                                    assert ar['focus']==op['bridge']['target']
                                projection_result=op
                            elif op.get('record') is not None:
                                verify_split(h,op['record'],Counter());assert len(op['acquisition']['branches'])==2
                                saved.add(split_key(op['record']))
                        assert len(ar['steps'])<=POLICY['step_limit'] and len(entered)<=POLICY['state_limit']
                        assert saved=={split_key(s) for s in splits} and sorted(entered)==ar['admitted_state_sha256']
                        completed=novel_patterns(delta);assert completed<=entered
                        assert sorted(completed)==ar['completed_new_state_sha256'] and sorted(entered-completed)==ar['entered_but_unstored_sha256']
                        if projection_result and projection_result['pending']:
                            selected=dict(mode='pending_projection',proposal=projection_result['proposal'])
                        else:selected=focus_selection(h,routes,ev,splits,ar['focus'],closed[0][0])
                        assert selected==read_archive(ar['next_selection'])
                        record=dict(mode=ar['mode'],repeat=bound['repeat'],closed=closed[0][0],admitted=len(entered),
                            completed=len(completed),unfinished=len(entered-completed),cold_selection_matches=True,idempotent=True)
                        result['arms'].append(record)
                        detail=dict(**record,focus_shape=shape(h._load(ar['focus'])['cnf']),focus_prefix=checked_path(h,ar['focus']),
                            splits=[split_findings(h,routes,solver,s) for s in splits])
                        if selected and selected.get('source'):
                            detail['next_profile']=profile(h,routes,dict(source=selected['source'],variables=shape(h._load(selected['source'])['cnf'])[0]))
                        findings['arms'].append(detail)
                        logical=(digests(history),splits,bridges,sorted(entered),selected,closed)
                        if ar['mode'] in repeats:assert repeats[ar['mode']]==logical
                        else:repeats[ar['mode']]=logical
                        assert not h.admitted;print(json.dumps(record),flush=True)
                    finally:h.close()
                h=BudgetedInventory(tmp/'final',**r['options']);h.set_admission_budget(0)
                try:
                    bridges=read_archive(r['bridges']);tick=time.perf_counter();routes=routes_for(h,evidence,bridges)
                    roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
                    closed,_,counts=full(h,roots,routes);assert closed==[r['final_closed'],r['without_growth_closed']]
                    selected=select(h,routes,evidence,roots,closed[0],Counter());assert selected==read_archive(r['next_selection'])
                    assert remaining(h,[dict(source=x['source'],target=x['target']) for x in bridges],routes,Counter())==read_archive(r['projection_frontier'])
                    result.update(global_coverage_seconds=time.perf_counter()-tick,global_coverage_counts=counts,
                        covered=sum(closed[0]),gains=r['gains'],cold_next_selection_matches=True,evidence_counts=list(map(len,evidence)))
                    for row in r['bridge_reference']:
                        record=row['record'];verify_bridge(h,record,Counter());source=h._load(record['source'])['cnf'];target=h._load(record['target'])['cnf']
                        a=solver.solve(source);b=solver.solve(target)
                        # Cold reads have different timings, counters and archive sizes.
                        # Bind the semantic results and deterministic stored witnesses.
                        for fresh,saved in ((a,row['source']),(b,row['target'])):
                            assert fresh['answer']==saved['answer'] and fresh['root']==saved['root']
                            assert json.loads(json.dumps(fresh['model']))==saved['model']
                        assert a['answer']==b['answer']
                        if b['answer']:assert holds(source,lift(source,target,record['proof'],b['model']))
                    if selected['source'] is not None:
                        findings['next_profile']=profile(h,routes,dict(source=selected['source'],variables=shape(h._load(selected['source'])['cnf'])[0]))
                    assert not h.admitted
                finally:h.close()
                for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
                result['verified_reference_nodes']=len(solver.checked);assert not solver.counts.get('expanded_nodes',0)
        finally:solver.close()
        assert sha(ct/'seed')==seed_hash and digests(tmp/'final')==r['logical_table_digests']
    result.update(passed=True,seconds=time.perf_counter()-start,repeated_logical_results_identical=True,seed_unchanged=True)
    summary=dict(arms=[],limitations=r['limitations'])
    for mode in ('ordinary','projection'):
        arms=[load_report(a) for a in r['arms'] if a['mode']==mode];first=arms[0]
        summary['arms'].append(dict(mode=mode,steps=len(first['steps']),closed=first['target_closed'],
            admitted=len(first['admitted_state_sha256']),completed=len(first['completed_new_state_sha256']),unfinished=len(first['entered_but_unstored_sha256']),
            expansion_mean_seconds=statistics.mean(a['expansion_seconds'] for a in arms),worker_mean_seconds=statistics.mean(a['worker_seconds'] for a in arms),
            costs_mean_seconds={k:statistics.mean(sum(row[k] for row in a['steps']) for a in arms) for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')},
            preparation_mean_seconds=statistics.mean(a['preparation_seconds'] for a in arms),delta_export_mean_seconds=statistics.mean(a['delta']['seconds'] for a in arms),
            compressed_delta_bytes=first['delta']['compressed_bytes'],delta_database_bytes=first['delta']['database_bytes'],history_bytes=first['history_bytes'],
            external_assumption_attempts=first['external_assumption_attempts']))
    for name,data in [('reconstruction.json',result),('structural-findings.json',findings),('comparison-summary.json',summary)]:
        (out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','covered','gains','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
