#!/usr/bin/env python3
"""Cold replay both scheduling policies without fresh recognition or solving."""
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

from experiments.compare_cnf_early_saved import (BASE,CONTROL,POLICY,restore_checkpoint,restore_base,restore_control,
    routes_for,add_splits,select,focus_selection,BudgetedInventory,full,verify_split,verify_positive,
    read_archive,sha,sha_key,unpack,digests,split_key,remaining)
from experiments.validate_cnf_split_cost import load_report,merge_checked,novel_patterns,split_findings
from experiments.cnf_residual_dag import ResidualSolver
from experiments.continue_cnf_local_forcing import profile
from experiments.validate_cnf_warm_transfer import path as checked_path,shape


def validate(out):
    start=time.perf_counter();r=json.loads((out/'report.json').read_text());parent=load_report(r['parent'])
    assert Path(r['parent']['path'])==BASE and Path(r['control']['path'])==CONTROL
    control=load_report(r['control']);assert r['source']==read_archive(parent['next_selection'])['source']
    expected=[]
    for case in (1160,1189):
        for repeat in range(2):
            order=('ordinary','early_saved') if (repeat+(case==1189))%2==0 else ('early_saved','ordinary')
            expected.extend((case,repeat,mode) for mode in order)
    assert [(a['case'],a['repeat'],a['mode']) for a in r['arms']]==expected
    result=dict(report_sha256=sha(out/'report.json'),arms=[]);findings=dict(arms=[])
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('fresh recognition')):
        tmp=Path(td);tick=time.perf_counter();restored,*evidence=restore_checkpoint(out/'report.json',tmp/'final',tmp)
        assert restored==r;result['restore_seconds']=time.perf_counter()-tick
        seeds={};hashes={}
        for case,base,restore,bound in ((1160,BASE,restore_base,parent),(1189,CONTROL,restore_control,control)):
            ct=tmp/str(case);ct.mkdir();original,*ev=restore(base,ct/'seed',ct);assert original==bound
            assert digests(ct/'seed')==(r['seed_table_digests'] if case==1160 else r['control']['seed_table_digests'])
            target=r['source'] if case==1160 else read_archive(control['frontier'])['leaves'][0]['source']
            bridges=read_archive(parent['bridges']) if case==1160 else []
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
                            if op['mode']=='early_saved_split':
                                assert ar['mode']=='early_saved' and op['selected_rank']==min(op['ranked_pairs'])
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
                        if selected and selected.get('source'):
                            detail['next_profile']=profile(h,routes,dict(source=selected['source'],variables=shape(h._load(selected['source'])['cnf'])[0]))
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
                    if selected['source'] is not None:
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
    for case in (1160,1189):
        for mode in ('ordinary','early_saved'):
            arms=[load_report(a) for a in r['arms'] if a['case']==case and a['mode']==mode];first=arms[0]
            summary['arms'].append(dict(case=case,mode=mode,steps=len(first['steps']),closed=first['target_closed'],
                admitted=len(first['admitted_state_sha256']),completed=len(first['completed_new_state_sha256']),unfinished=len(first['entered_but_unstored_sha256']),
                expansion_mean_seconds=statistics.mean(a['expansion_seconds'] for a in arms),worker_mean_seconds=statistics.mean(a['worker_seconds'] for a in arms),
                costs_mean_seconds={k:statistics.mean(sum(row[k] for row in a['steps']) for a in arms) for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')},
                preparation_mean_seconds=statistics.mean(a['preparation_seconds'] for a in arms),delta_export_mean_seconds=statistics.mean(a['delta']['seconds'] for a in arms),
                compressed_delta_bytes=first['delta']['compressed_bytes'],delta_database_bytes=first['delta']['database_bytes'],history_bytes=first['history_bytes'],
                external_assumption_attempts=first['external_assumption_attempts']))
        originals={mode:load_report(next(a for a in r['arms'] if a['case']==case and a['repeat']==0 and a['mode']==mode))
                   for mode in ('ordinary','early_saved')}
        keys={mode:set(a['completed_new_state_sha256']) for mode,a in originals.items()}
        summary['paired'].append(dict(case=case,both_closed=all(a['target_closed'] for a in originals.values()),
            identical_new_pattern_keys=keys['ordinary']==keys['early_saved'],shared_new_patterns=len(keys['ordinary']&keys['early_saved']),
            ordinary_only_patterns=len(keys['ordinary']-keys['early_saved']),early_saved_only_patterns=len(keys['early_saved']-keys['ordinary'])))
    for name,data in [('reconstruction.json',result),('structural-findings.json',findings),('comparison-summary.json',summary)]:
        (out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','covered','gains','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
