#!/usr/bin/env python3
"""Reconstruct probe-window artifacts, replay proof bindings and growth ablation."""
from collections import Counter
import gzip
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_residual_dag import restrict,ResidualSolver,holds
from experiments.cnf_simplification import check_simplification
from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.cnf_probe_window import TABLE,WindowRoutes,record_key,verify_window
from experiments.cnf_route_composition import compose,verify_plan
from experiments.compare_cnf_probe_window import TABLES,CORE,restore,apply_delta,digests,WithoutGrowth,sha,sha_key,unpack


def main(out):
    rp=out/'report.json';r=json.loads(rp.read_text());evidence=dict(script_sha256=sha(Path(__file__)),report_sha256=sha(rp))
    for path,digest in r['fingerprints'].items():assert sha(path)==digest,path
    for entry in r['inputs']:assert sha(entry['path'])==entry['sha256']
    assert r['policy']==dict(source_limit=4,state_limit=32,width=4)
    assert r['gains']==[i for i,(a,b) in enumerate(zip(r['baseline_closed'],r['final_closed'],strict=True)) if b and not a]
    admitted=set()
    for row in r['records']:
        keys=row['admitted_state_sha256'];assert len(keys)==len(set(keys))<=32
        assert len(keys)==row['admission_counts'].get('entered_states',0)
        assert row['inventory_counts'].get('inserted_nodes',0)<=len(keys)
        assert len(row['search']['visits'])==len(set(row['search']['visits']))<=4
        if row['search']['budget_stop'] is not None:
            assert len(keys)==32 and row['admission_counts']['denied_states']==1
        admitted.update(keys)
    # Replay every diagnostic attempt, including complete inconclusive traces,
    # without rerunning unit-propagation discovery.
    conflicts={}
    source=json.loads(CORE.read_text())['cores'][0]['source']
    projection=check_additive_elimination(source,dict(variable=15),Counter(),clause_growth_limit=3)
    assert r['mechanism']['rows'][0]['source']==source
    assert r['mechanism']['rows'][1]['source']==[list(c) for c in projection]
    for row in r['mechanism']['rows']:
        cnf=row['source'];variables=sorted({abs(l) for c in cnf for l in c})
        assert [(a['variable'],a['value']) for a in row['attempts']]==[(v,b) for v in variables for b in (False,True)]
        assert row['choices']==probe_choices(cnf,4,Counter())
        for a in row['attempts']:
            check_simplification(restrict(cnf,{a['variable']:a['value']},Counter()),a['certificate'],Counter(),pure=False)
        conflicts[row['name']]=[[a['variable'],a['value']] for a in row['attempts'] if a['certificate']['conflict'] is not None]
    evidence['single_assumption_conflicts']=conflicts
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);seed=tmp/'seed';prior,inputs=restore(seed,tmp)
        assert inputs==r['inputs'] and prior['final_closed']==r['baseline_closed']
        assert digests(seed)==r['seed_table_digests'] and sha(seed)==r['seed_database_sha256']
        d=r['delta'];assert sha(d['path'])==d['sha256'];delta=tmp/'delta';unpack(d['path'],delta,d['database_sha256'])
        assert delta.stat().st_size==d['database_bytes'] and Path(d['path']).stat().st_size==d['compressed_bytes']
        history=tmp/'history';shutil.copyfile(seed,history);apply_delta(history,delta)
        assert digests(history)==r['logical_table_digests'];before=sha(history);apply_delta(history,delta);assert sha(history)==before
        db=sqlite3.connect(delta)
        for t in TABLES:
            added=db.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
            assert added==r['delta_rows'][t] and r['preserved_rows'][t]==r['seed_table_digests'][t]['rows']
            assert r['logical_table_digests'][t]['rows']==added+r['preserved_rows'][t]
            if t not in (TABLE,'cnf_patterns_v1'):assert added==0
        assert all(sha_key(k) in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1'))
        assert r['delta_rows']['cnf_patterns_v1']==sum(row['inventory_counts'].get('inserted_nodes',0) for row in r['records'])
        assert r['delta_rows'][TABLE]==sum(row['counts'].get('new_probe_windows',0) for row in r['records'])
        db.close();h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0);routes=WindowRoutes(h)
        assert h.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        final,plan=compose(h,roots,routes,Counter());assert final==r['final_closed']
        c=r['certificate'];assert sha(c['path'])==c['sha256'];saved=json.loads(gzip.decompress(Path(c['path']).read_bytes()))
        verify_plan(h,saved,[k for k,b in zip(roots,final,strict=True) if b],routes,Counter())
        ablated,_=compose(h,roots,WithoutGrowth(routes),Counter());assert ablated==r['without_growth_closed']
        statuses=Counter();pending=0
        for record in routes.windows.values():
            verify_window(h,record,Counter());statuses[record['probing']['status']]+=1
            if record['edge'] is not None and h._load(record['edge']['key']) is None:pending+=1
        assert dict(statuses)==r['window_kinds'] and pending==r['pending_windows']
        assert not h.admitted;h.close();assert sha(history)==before
        ep=r['reference'];assert sha(ep['path'])==ep['sha256'];path=tmp/'endpoints';unpack(ep['path'],path,ep['database_sha256'])
        before_ep=sha(path);solver=ResidualSolver(path)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
        assert len(solver.checked)==ep['verified_nodes']
        assert {row['case'] for row in ep['originals']}==set(r['gains'])
        for row in ep['originals']:
            source=r['cases'][row['case']]['source'];_,_,key=solver._canonical(source)
            assert key==row['result']['root'];a=solver.solve(source)
            assert a['answer']==row['result']['answer'] and not solver.counts.get('expanded_nodes',0)
            if a['answer']:assert holds(source,a['model'])
        solver.close();assert sha(path)==before_ep
        evidence.update(coverage=sum(final),without_growth_coverage=sum(ablated),gains=r['gains'],
            original_answers={str(row['case']):row['result']['answer'] for row in ep['originals']},
            logical_table_digests=r['logical_table_digests'],window_kinds=dict(statuses),pending_windows=pending,
            endpoint_verified_nodes=ep['verified_nodes'])
    log=Path('/tmp/oraclemachines-window-tests.log').read_text();assert re.search(r'Ran 543 tests in [0-9.]+s\s+OK',log)
    (out/'full-validation.txt').write_text(log)
    evidence.update(python_tests=543,test_log_sha256=sha(out/'full-validation.txt'),
        resource_warnings=log.count('ResourceWarning: unclosed database'),seven_table_roundtrip=True,
        cold_finite_plan_replay=True,all_new_nodes_admitted=True)
    (out/'validation.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],without_growth=sum(ablated))))


if __name__=='__main__':main(Path(sys.argv[1]))
