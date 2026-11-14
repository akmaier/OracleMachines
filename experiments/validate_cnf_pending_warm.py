#!/usr/bin/env python3
"""Cold-replay pending acquisition, full coverage and unfinished-state accounting."""
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
from experiments.cnf_trace_split import lift
from experiments.cnf_residual_dag import ResidualSolver, holds


def shape(cnf):
    return [len({abs(l) for c in cnf for l in c}),len(cnf),sum(map(len,cnf))]


def validate(out):
    tick=time.perf_counter();r=json.loads((out/'report.json').read_text())
    for name,digest in r['fingerprints'].items():assert sha(name)==digest
    parent=json.loads(Path(r['parent']['path']).read_text())
    before=read_archive(parent['next_selection'])
    result=dict(report_sha256=sha(out/'report.json'));findings=dict(branches=[])
    with tempfile.TemporaryDirectory() as td,patch.object(BudgetedInventory,'_discover',
            side_effect=AssertionError('new recognition during cold validation')):
        tmp=Path(td);started=time.perf_counter()
        restored,*evidence=restore_checkpoint(out/'report.json',tmp/'history',tmp)
        assert restored==r
        result['restore_seconds']=time.perf_counter()-started
        result['evidence_counts']=list(map(len,evidence))
        db=sqlite3.connect(tmp/'history')
        final_ids={sha_key(k) for k, in db.execute('SELECT id FROM cnf_patterns_v1')};db.close()
        d=r['delta'];assert sha(d['path'])==d['sha256']
        unpack(d['path'],tmp/'delta',d['database_sha256']);db=sqlite3.connect(tmp/'delta')
        new_ids={sha_key(k) for k, in db.execute('SELECT id FROM cnf_patterns_v1')};db.close()
        old_ids=final_ids-new_ids;prior=set(r['prior_admission_accounting']['entered_sha256'])
        unfinished=prior-old_ids;admitted=set(r['admitted_state_sha256'])
        assert sorted(unfinished)==r['prior_admission_accounting']['unfinished_sha256']
        assert sorted(prior&old_ids)==r['prior_admission_accounting']['completed_sha256']
        expected=dict(reentered_unfinished_sha256=sorted(admitted&unfinished),
            previously_unfinished_now_stored_sha256=sorted(unfinished&final_ids),
            new_completed_sha256=sorted(new_ids),entered_but_unstored_sha256=sorted(admitted-final_ids),
            prior_completed_preserved=True)
        assert expected==r['resume_accounting'] and not admitted&old_ids
        assert len(admitted)<=r['policy']['state_limit']
        added=set()
        for row in r['steps']:
            operation=read_archive(row['operation']);now=set(map(sha_key,operation['added']))
            assert not added&now;added.update(now)
            assert len(now)==row['admitted_now'] and len(added)==row['admitted_total']
        assert added==admitted
        first=read_archive(r['steps'][0]['operation'])
        assert first['mode']=='resume_split' and first['record']==before['pending_split']
        assert first['ranked_pairs']==[]
        result['resume_accounting']=expected
        print('Checkpoint and exact pending split restored without new recognition',flush=True)

        h=BudgetedInventory(tmp/'history',**r['options']);h.set_admission_budget(0)
        try:
            started=time.perf_counter();routes=routes_for(h,evidence)
            roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
            closed,_,counts=full(h,roots,routes)
            assert closed==[r['final_closed'],r['without_growth_closed']]
            assert select(h,routes,evidence,roots,closed[0],Counter())==read_archive(r['next_selection'])
            result['full_cold_coverage_seconds']=time.perf_counter()-started
            result['full_cold_coverage_counts']=counts
            record=first['record'];verify_split(h,record,Counter())
            findings['source_shape']=shape(h._load(record['source'])['cnf'])
            findings['source_closed']=compose(h,[record['source']],routes,Counter())[0][0]
            findings['variable']=read_attempt(h,record['source'],record['references'][0],Counter())['variable']
            ep=r['reference'];assert sha(ep['path'])==ep['sha256']
            unpack(ep['path'],tmp/'reference',ep['database_sha256'])
            # Only read certified saved reference answers; do not acquire new ones.
            solver=ResidualSolver(tmp/'reference')
            try:
                targets,_=verify_split(h,record,Counter())
                for value,edge,target,acq in zip((False,True),record['edges'],targets,
                        first['acquisition']['branches'],strict=True):
                    key=edge['key'];path=[];seen=set()
                    branch=dict(value=value,target_sha256=sha_key(key),
                        admitted=len(acq['admitted']),pending=acq['pending'])
                    while key not in seen:
                        seen.add(key);node=h._load(key)
                        if node is None:branch['missing_sha256']=sha_key(key);break
                        path.append(dict(key_sha256=sha_key(key),kind=node['kind'],shape=shape(node['cnf'])))
                        if 'edge' not in node:
                            branch['terminal_outcomes']=node['profile']['outcomes'];break
                        key=node['edge']['key']
                    else:raise ValueError('Cyclic branch path')
                    branch['path']=path;branch['closed']=compose(h,[edge['key']],routes,Counter())[0][0] if path else False
                    # solve() may use a retained answer; forbid fresh reference search.
                    with patch.object(solver,'_expand',side_effect=AssertionError('fresh reference search')):
                        answer=solver.solve(target)
                    branch['reference_answer']=answer['answer']
                    if answer['answer'] and path:
                        with patch.object(solver,'_expand',side_effect=AssertionError('fresh reference search')):
                            child=solver.solve(h._load(edge['key'])['cnf'])
                        assert child['answer']
                        model=lift(h,record,value,child['model'])
                        assert holds(h._load(record['source'])['cnf'],model)
                        branch['lifted_source_model_checked']=True
                    findings['branches'].append(branch)
                for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
                    assert solver._read(key) is not None
                result['verified_reference_nodes']=len(solver.checked)
                assert not solver.counts.get('expanded_nodes',0)
            finally:solver.close()
            findings['gains']=[dict(index=i,case=r['cases'][i]['original_case'],
                shape=shape(r['cases'][i]['source'])) for i in r['gains']]
            findings['next_frontier']=read_archive(r['frontier_profiles'])
            result.update(covered=sum(closed[0]),gains=r['gains'],cold_next_selection_matches=True)
            assert not h.admitted
        finally:h.close()
    result.update(seconds=time.perf_counter()-tick,passed=True)
    for name,data in [('reconstruction.json',result),('structural-findings.json',findings)]:
        (out/name).write_text(json.dumps(data,indent=2,sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','covered','gains','seconds')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);validate(p.parse_args().output)
