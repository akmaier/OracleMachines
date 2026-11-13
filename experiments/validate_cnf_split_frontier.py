#!/usr/bin/env python3
"""Cold replay of continuation below a saved split, with acquisition disabled."""
from collections import Counter
from contextlib import ExitStack
import argparse
import json
from pathlib import Path
import re
import sqlite3
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_split_frontier import restore_checkpoint,POLICY
from experiments.compare_cnf_split_batch import routes_for,new_probes
from experiments.validate_cnf_split_batch import check_coverage,delta_file
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_probe_continuation import sha,sha_key,unpack
from experiments.compare_cnf_target_probe import checked_target,lift_forced
from experiments.cnf_split_frontier import frontier
from experiments.cnf_split_batch import children
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.continue_cnf_learning import target_state,preserved_reference
from experiments.cnf_learning_batch import selection


def validate(out,test_log):
    started=time.perf_counter();r=json.loads((out/'report.json').read_text());assert r['policy']==POLICY
    with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
        tmp=Path(td);seed=tmp/'seed';path=tmp/'history';delta=tmp/'new-delta'
        for name in ('experiments.cnf_probe_window.discover_probes','experiments.cnf_probe_continuation.discover_probes',
                     'experiments.cnf_trace_learning.discover_equivalence_probes','experiments.cnf_learning_continuation.discover_equivalence_probes'):
            stack.enter_context(patch(name,side_effect=AssertionError('new discovery')))
        stack.enter_context(patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('new recognition')))
        parent,*evidence=restore_checkpoint(Path(r['parent']['path']),seed,tmp)
        assert r['cases']==parent['cases'] and r['options']==parent['options'];before_bytes=sha(seed)
        h=BudgetedInventory(seed,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']==parent['final_closed']
        before=frontier(h,routes,evidence[-1],Counter());saved=read_archive(r['selection'])
        assert saved==dict(before=before,leaf=before['leaves'][0]);h.close();assert sha(seed)==before_bytes
        delta_file(r['delta'],delta);items=new_probes(delta)
        assert read_archive(r['new_probes'])==[dict(kind=x['kind'],id=x['id']) for x in items]
        assert dict(Counter(x['record']['probing']['status'] for x in items))==r['new_probe_summary']
        print('cold child checkpoint and reference proofs',flush=True)
        restored,*evidence=restore_checkpoint(out/'report.json',path,tmp);assert restored==r;before_bytes=sha(path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        check_coverage(h,routes,roots,r,r['baseline_closed']);d=read_archive(r['diagnostics'])
        assert frontier(h,routes,evidence[-1],Counter())==d['after']
        assert children(h,routes,evidence[-1])==d['children'] and target_state(h,routes)==d['targets']
        assert selection(h,routes,Counter())==d['learning']
        result=d['result'];visits=result['visits'];assert len(visits)<=POLICY['step_limit']
        assert len({v['source'] for v in visits})==result['distinct_sources']<=POLICY['source_limit']
        if visits:assert visits[0]['source']==saved['leaf']['source']
        seen={(v['source'],v['kind'],v['offset'],v['status']) for v in visits}
        for v in visits:
            if v['kind'] is None:assert v['offset'] is None and v['status'] is None;continue
            records=routes.windows if v['kind']=='probe_window' else routes.continuations
            record=next(rec for rec in records.values() if rec['source']==v['source'] and rec.get('offset',0)==v['offset'])
            assert record['probing']['status']==v['status'];checked_target(h,routes,v['kind'],record)
        for item in items:
            rec=item['record'];assert (rec['source'],item['kind'],rec.get('offset',0),rec['probing']['status']) in seen
        admitted=set(r['acquisition']['admitted_state_sha256']);assert len(admitted)<=POLICY['state_limit']
        db=sqlite3.connect(delta)
        for key, in db.execute('SELECT id FROM cnf_patterns_v1'):assert sha_key(key) in admitted and h._load(key) is not None
        db.close()
        ep=r['reference'];ref=tmp/'reference';assert sha(ep['path'])==ep['sha256'];unpack(ep['path'],ref,ep['database_sha256'])
        old=parent['reference'];assert sha(old['path'])==old['sha256'];unpack(old['path'],tmp/'reference-seed',old['database_sha256'])
        assert preserved_reference(tmp/'reference-seed',ref)==ep['preserved_nodes'];refbefore=sha(ref);solver=ResidualSolver(ref)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
        assert len(solver.checked)==ep['verified_nodes']
        def answer(source,saved):
            _,_,key=solver._canonical(source);assert key==saved['root'];actual=solver.solve(source);assert actual['answer']==saved['answer']
            if actual['answer']:assert holds(source,actual['model'])
            return actual
        forced={(x['kind'],sha_key(x['id'])):x for x in items if x['record']['edge'] is not None}
        assert {(row['kind'],row['id_sha256']) for row in ep['rows']}==set(forced)
        for row in ep['rows']:
            item=forced[(row['kind'],row['id_sha256'])];record=item['record'];source=h._load(record['source'])['cnf']
            target=checked_target(h,routes,item['kind'],record);a=answer(source,row['source']);b=answer(target,row['target'])
            assert a['answer']==b['answer']
            if b['answer']:lift_forced(source,record,b['model'])
        assert {row['case'] for row in ep['originals']}==set(r['gains'])
        for row in ep['originals']:answer(r['cases'][row['case']]['source'],row['result'])
        assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(ref)==refbefore
        assert not h.admitted and h.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';h.close();assert sha(path)==before_bytes
    log=test_log.read_text();match=re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log);assert match and int(match[1])>=589
    (out/'full-validation.txt').write_text(log)
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),python_tests=int(match[1]),test_log_sha256=sha(out/'full-validation.txt'),
        coverage=sum(r['final_closed']),gains=r['gains'],without_growth=sum(r['without_growth_closed']),reference_nodes=ep['verified_nodes'],
        preserved_reference_nodes=ep['preserved_nodes'],history_bytes_unchanged=True,cold_new_discovery=False,seconds=time.perf_counter()-started,
        original_answers={str(row['case']):row['result']['answer'] for row in ep['originals']})
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--test-log',type=Path,required=True)
    a=p.parse_args();validate(a.output,a.test_log)
