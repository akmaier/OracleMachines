#!/usr/bin/env python3
"""Replay a warm discovery checkpoint and extract source-bound transfer evidence."""
from collections import Counter
import argparse
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_pending_warm import (restore_checkpoint, BudgetedInventory,
    routes_for, select, full, verify_split, read_archive, sha, sha_key, unpack)
from experiments.cnf_route_composition import compose
from experiments.cnf_trace_reuse import read_attempt
from experiments.cnf_trace_split import lift, record_key
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.continue_cnf_local_forcing import profile


def shape(cnf):
    return [len({abs(l) for c in cnf for l in c}),len(cnf),sum(map(len,cnf))]


def path(h,key):
    """Describe the stored single-edge prefix; do not confuse its end with closure."""
    rows=[];seen=set()
    while key not in seen:
        seen.add(key);node=h._load(key)
        if node is None:return dict(nodes=rows,missing_sha256=sha_key(key))
        rows.append(dict(key_sha256=sha_key(key),kind=node['kind'],shape=shape(node['cnf'])))
        if 'edge' not in node:
            return dict(nodes=rows,end_outcomes=node['profile']['outcomes'])
        key=node['edge']['key']
    raise ValueError('Cyclic stored prefix')


def validate(out):
    started=time.perf_counter();r=json.loads((out/'report.json').read_text())
    for name,digest in r['fingerprints'].items():assert sha(name)==digest
    parent=json.loads(Path(r['parent']['path']).read_text())
    before=read_archive(parent['next_selection']);result=dict(report_sha256=sha(out/'report.json'))
    findings=dict(steps=[],selected_originals=[dict(index=i,case=r['cases'][i]['original_case'],
        shape=shape(r['cases'][i]['source'])) for i in before['selected_original_cases']])
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',
            side_effect=AssertionError('new recognition during replay')):
        tmp=Path(td);tick=time.perf_counter()
        restored,*evidence=restore_checkpoint(out/'report.json',tmp/'history',tmp)
        assert restored==r
        result.update(restore_seconds=time.perf_counter()-tick,evidence_counts=list(map(len,evidence)))
        db=sqlite3.connect(tmp/'history')
        final={sha_key(k) for k, in db.execute('SELECT id FROM cnf_patterns_v1')};db.close()
        d=r['delta'];assert sha(d['path'])==d['sha256']
        unpack(d['path'],tmp/'delta',d['database_sha256']);db=sqlite3.connect(tmp/'delta')
        novel={sha_key(k) for k, in db.execute('SELECT id FROM cnf_patterns_v1')};db.close()
        old=final-novel;prior=set(parent.get('admitted_state_sha256',[]))
        for bound in parent.get('arms',[]):
            assert sha(bound['path'])==bound['sha256']
            prior.update(json.loads(Path(bound['path']).read_text())['admitted_state_sha256'])
        assert r['prior_admission_accounting']==dict(entered_sha256=sorted(prior),
            completed_sha256=sorted(prior&old),unfinished_sha256=sorted(prior-old))
        admitted=set(r['admitted_state_sha256']);unfinished=prior-old
        expected=dict(reentered_unfinished_sha256=sorted(admitted&unfinished),
            previously_unfinished_now_stored_sha256=sorted(unfinished&final),
            new_completed_sha256=sorted(novel),entered_but_unstored_sha256=sorted(admitted-final),
            prior_completed_preserved=True)
        assert expected==r['resume_accounting'] and not admitted&old
        assert len(admitted)<=r['policy']['state_limit']
        added=set();new_splits=[]
        for row in r['steps']:
            selection=read_archive(row['selection']);operation=read_archive(row['operation'])
            if row['step']==0:assert selection==before
            assert operation['source']==selection['source']
            assert sha_key(operation['source'])==row['source_sha256']
            if selection['pending_split'] is not None:
                assert operation['mode']=='resume_split'
                assert operation['record']==selection['pending_split'] and operation['ranked_pairs']==[]
            if operation['mode'] in ('early_closed_split','split_after_ordinary_exhaustion'):
                new_splits.append(operation['record'])
            now=set(map(sha_key,operation['added']));assert not added&now;added.update(now)
            assert len(now)==row['admitted_now'] and len(added)==row['admitted_total']
        assert added==admitted
        assert {record_key(x) for x in new_splits}=={record_key(x) for x in read_archive(r['splits'])}
        result['resume_accounting']=expected
        print('Checkpoint, source bindings and shared admission account replayed',flush=True)

        h=BudgetedInventory(tmp/'history',**r['options']);h.set_admission_budget(0)
        try:
            tick=time.perf_counter();routes=routes_for(h,evidence)
            roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
            closed,_,counts=full(h,roots,routes)
            assert closed==[r['final_closed'],r['without_growth_closed']]
            selected=select(h,routes,evidence,roots,closed[0],Counter())
            assert selected==read_archive(r['next_selection'])
            result.update(full_cold_coverage_seconds=time.perf_counter()-tick,
                full_cold_coverage_counts=counts,cold_next_selection_matches=True)
            ep=r['reference'];assert sha(ep['path'])==ep['sha256']
            unpack(ep['path'],tmp/'reference',ep['database_sha256']);solver=ResidualSolver(tmp/'reference')
            try:
                with patch.object(solver,'_expand',side_effect=AssertionError('fresh reference search')):
                    for row in r['steps']:
                        operation=read_archive(row['operation']);source=operation['source']
                        item=dict(step=row['step'],mode=operation['mode'],source_sha256=sha_key(source),
                            source_shape=shape(h._load(source)['cnf']))
                        if operation.get('record') is not None:
                            record=operation['record'];targets,_=verify_split(h,record,Counter())
                            item.update(variable=read_attempt(h,source,record['references'][0],Counter())['variable'],
                                rank=operation.get('selected_rank',operation['ranked_pairs'][0] if operation['ranked_pairs'] else None),branches=[])
                            for value,edge,target,acq in zip((False,True),record['edges'],targets,
                                    operation['acquisition']['branches'],strict=True):
                                child=h._load(edge['key']);answer=solver.solve(target)
                                branch=dict(value=value,target_sha256=sha_key(edge['key']),
                                    target_shape=shape(target),admitted=len(acq['admitted']),
                                    pending_at_acquisition=acq['pending'],reference_answer=answer['answer'],
                                    final_closed=compose(h,[edge['key']],routes,Counter())[0][0] if child else False,
                                    prefix=path(h,edge['key']))
                                if child is not None and answer['answer']:
                                    local=solver.solve(child['cnf']);assert local['answer']
                                    assert holds(h._load(source)['cnf'],lift(h,record,value,local['model']))
                                    branch['lifted_source_model_checked']=True
                                item['branches'].append(branch)
                        elif operation.get('operation',{}).get('record') is not None:
                            record=operation['operation']['record'];p=record['probing']
                            item.update(probe_kind=operation['operation']['kind'],offset=record.get('offset',0),
                                status=p['status'],attempts=[dict(variable=a['variable'],value=a['value'],
                                unit_deductions=len(a['certificate']['units'])) for a in p['attempts']])
                            if record['edge'] is not None:item['forced_prefix']=path(h,record['edge']['key'])
                        findings['steps'].append(item)
                    for i in r['gains']:
                        answer=solver.solve(r['cases'][i]['source'])
                        if answer['answer']:assert holds(r['cases'][i]['source'],answer['model'])
                for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
                    assert solver._read(key) is not None
                result['verified_reference_nodes']=len(solver.checked)
                assert not solver.counts.get('expanded_nodes',0)
            finally:solver.close()
            tick=time.perf_counter()
            if selected['source'] is not None:
                source=selected['source'];cnf=h._load(source)['cnf']
                findings['next_profile']=profile(h,routes,dict(source=source,variables=shape(cnf)[0]))
            findings['diagnostics_seconds']=time.perf_counter()-tick
            findings['external_assumption_attempts']=sum(x['acquisition_counts'].get('probe_attempts',0) for x in r['steps'])
            findings['gains']=[dict(index=i,case=r['cases'][i]['original_case']) for i in r['gains']]
            result.update(covered=sum(closed[0]),gains=r['gains'])
            assert not h.admitted
        finally:h.close()
    result.update(seconds=time.perf_counter()-started,passed=True)
    for name,data in [('reconstruction.json',result),('structural-findings.json',findings)]:
        (out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','covered','gains','seconds')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);validate(p.parse_args().output)
