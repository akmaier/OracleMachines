#!/usr/bin/env python3
"""Independently reconstruct both bridge modes and their preserved union."""
from collections import Counter
import argparse
import json
from pathlib import Path
import shutil
import statistics
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_projection_bridge import (BASE, POLICY, restore_checkpoint,
    restore_base, routes_for, add_splits, select, BudgetedInventory, full, verify_split,
    verify_positive, verify_bridge, read_archive, sha, sha_key, unpack, digests)
from experiments.validate_cnf_split_cost import (load_report, merge_checked,
    novel_patterns, split_findings)
from experiments.cnf_trace_split import record_key
from experiments.cnf_projection_bridge import KIND, projection
from experiments.cnf_residual_dag import ResidualSolver
from experiments.continue_cnf_local_forcing import profile
from experiments.validate_cnf_warm_transfer import shape


def validate(out):
    started=time.perf_counter();r=json.loads((out/'report.json').read_text())
    for name,digest in r['fingerprints'].items():assert sha(name)==digest
    assert Path(r['parent']['path'])==BASE
    parent=load_report(r['parent']);bridges=read_archive(r['bridges'])
    targets=read_archive(r['target_keys']);assert len(targets)==2 and len(bridges)==1
    assert bridges[0]['source']==targets[1] and bridges[0]['target']==targets[0]
    assert [(b['repeat'],b['mode']) for b in r['arms']]==[(0,'independent'),(0,'bridge'),(1,'bridge'),(1,'independent')]
    result=dict(report_sha256=sha(out/'report.json'),arms=[]);findings=dict(arms=[])
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',
            side_effect=AssertionError('fresh recognition during replay')):
        tmp=Path(td);tick=time.perf_counter()
        restored,*evidence=restore_checkpoint(out/'report.json',tmp/'final',tmp)
        assert restored==r
        result.update(restore_seconds=time.perf_counter()-tick,evidence_counts=list(map(len,evidence)))
        ct=tmp/'controls';ct.mkdir();seed=ct/'seed'
        original,*base_evidence=restore_base(BASE,seed,ct)
        assert original==parent and digests(seed)==r['seed_table_digests'];before=sha(seed)
        ep=r['reference'];assert sha(ep['path'])==ep['sha256']
        unpack(ep['path'],tmp/'reference',ep['database_sha256']);solver=ResidualSolver(tmp/'reference')
        repeats={}
        try:
            with patch.object(solver,'_expand',side_effect=AssertionError('fresh reference search')):
                for bound in r['arms']:
                    ar=load_report(bound);mode=bound['mode'];name=f"{bound['repeat']}-{mode}"
                    assert ar['mode']==mode and ar['policy']==POLICY
                    assert ar['root_sha256']==list(map(sha_key,targets))
                    assert ar['seed_table_digests']==r['seed_table_digests']
                    history=ct/name;shutil.copyfile(seed,history);delta=ct/(name+'-delta')
                    merge_checked(ar['delta'],history,delta,r['options'])
                    splits=read_archive(ar['splits']);ev=add_splits(base_evidence,splits)
                    used=bridges if mode=='bridge' else []
                    h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
                    try:
                        routes=routes_for(h,ev,used);closed,_,_=full(h,targets,routes)
                        assert closed==[ar['target_flags'],ar['without_growth_flags']]
                        assert all(closed[0])==ar['target_closed']
                        claimed=[t for t,b in zip(targets,closed[0],strict=True) if b]
                        positive=read_archive(ar['expanded_certificate'])
                        verify_positive(h,positive,claimed,ev,used,Counter())
                        selected=None if all(closed[0]) else select(h,routes,[*ev[:3],splits,ev[4]],targets,closed[0],Counter())
                        assert selected==read_archive(ar['next_selection'])
                        added=set();saved=set()
                        for row in ar['steps']:
                            op=read_archive(row['operation']);assert sha_key(op['source'])==row['source_sha256']
                            ids=set(map(sha_key,op['added']));assert not ids&added;added.update(ids)
                            assert len(ids)==row['admitted_now'] and len(added)==row['admitted_total']
                            if op.get('record') is not None:
                                verify_split(h,op['record'],Counter())
                                assert len(op['acquisition']['branches'])==2
                                saved.add(record_key(op['record']))
                        assert saved=={record_key(x) for x in splits}
                        assert added==set(ar['admitted_state_sha256']) and len(added)<=POLICY['state_limit']
                        completed=novel_patterns(delta);assert completed<=added
                        assert sorted(completed)==ar['completed_new_state_sha256']
                        assert sorted(added-completed)==ar['entered_but_unstored_sha256']
                        item=dict(mode=mode,repeat=bound['repeat'],closed=closed[0],admitted=len(added),
                            completed=len(completed),idempotent=True,cold_selection_matches=True,
                            positive_bridge_steps=sum(s['rule']['kind']==KIND for s in positive['steps']))
                        result['arms'].append(item)
                        findings['arms'].append(dict(**item,splits=[split_findings(h,routes,solver,s) for s in splits]))
                        signature=(digests(history),splits,sorted(added),selected,closed)
                        if mode in repeats:assert repeats[mode]==signature
                        else:repeats[mode]=signature
                        assert not h.admitted;print(json.dumps(item),flush=True)
                    finally:h.close()
                h=BudgetedInventory(tmp/'final',**r['options']);h.set_admission_budget(0)
                try:
                    tick=time.perf_counter();routes=routes_for(h,evidence,bridges)
                    roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
                    closed,_,counts=full(h,roots,routes)
                    assert closed==[r['final_closed'],r['without_growth_closed']]
                    selected=select(h,routes,evidence,roots,closed[0],Counter())
                    assert selected==read_archive(r['next_selection'])
                    result.update(full_cold_coverage_seconds=time.perf_counter()-tick,full_cold_coverage_counts=counts,
                        cold_next_selection_matches=True,covered=sum(closed[0]),gains=r['gains'])
                    counts=Counter();verify_bridge(h,bridges[0],counts)
                    b=bridges[0];source=h._load(b['source'])['cnf'];target=h._load(b['target'])['cnf']
                    projected,names=projection(source,b['proof']['variable'],Counter(),64)
                    findings['bridge']=dict(variable=b['proof']['variable'],source_shape=shape(source),
                        projected_shape=shape(projected),target_shape=shape(target),names=list(names),
                        subsumed=[dict(removed=list(projected[i]),retained=target[j]) for i,j in b['proof']['subsumers']],counts=dict(counts))
                    if selected['source'] is not None:
                        findings['next_profile']=profile(h,routes,dict(source=selected['source'],
                            variables=shape(h._load(selected['source'])['cnf'])[0]))
                    assert not h.admitted
                finally:h.close()
                for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
                result['verified_reference_nodes']=len(solver.checked)
                assert not solver.counts.get('expanded_nodes',0)
        finally:solver.close()
        assert sha(seed)==before and digests(tmp/'final')==r['logical_table_digests']
    result.update(passed=True,seconds=time.perf_counter()-started,repeated_logical_results_identical=True)
    summary=dict(arms=[],limitations=r['limitations'])
    for mode in ('independent','bridge'):
        arms=[load_report(b) for b in r['arms'] if b['mode']==mode];first=arms[0]
        costs={k:statistics.mean(sum(row[k] for row in a['steps']) for a in arms)
            for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')}
        summary['arms'].append(dict(mode=mode,steps=len(first['steps']),closed=first['target_flags'],
            admitted=len(first['admitted_state_sha256']),completed=len(first['completed_new_state_sha256']),
            unfinished=len(first['entered_but_unstored_sha256']),costs_mean_seconds=costs,
            expansion_mean_seconds=statistics.mean(a['expansion_seconds'] for a in arms),
            worker_mean_seconds=statistics.mean(a['worker_seconds'] for a in arms),
            preparation_mean_seconds=statistics.mean(a['preparation_seconds'] for a in arms),
            delta_export_mean_seconds=statistics.mean(a['delta']['seconds'] for a in arms),
            history_bytes=first['history_bytes'],compressed_delta_bytes=first['delta']['compressed_bytes'],
            delta_database_bytes=first['delta']['database_bytes'],external_assumption_attempts=first['external_assumption_attempts']))
    for name,data in [('reconstruction.json',result),('structural-findings.json',findings),('comparison-summary.json',summary)]:
        (out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','covered','gains','seconds')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);validate(p.parse_args().output)
