#!/usr/bin/env python3
"""Cold replay of source-bound splits and their original-level coverage."""
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
from experiments.compare_cnf_trace_split import restore_checkpoint,restore_parent,select_leaf,POLICY
from experiments.continue_cnf_learning import target_state,preserved_reference
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_probe_continuation import sha,sha_key,unpack,WithoutGrowth
from experiments.cnf_learning_continuation import ContinuedLearningRoutes
from experiments.cnf_trace_split import candidates,verify,attach,lift,record_key
from experiments.cnf_trace_reuse import source_attempts,check_pair,read_attempt
from experiments.cnf_probe_window import verify_window
from experiments.cnf_probe_exhaustion import certify_exhaustion
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_residual_dag import ResidualSolver,holds,restrict
from experiments.cnf_simplification import check_simplification
from experiments.cnf_pattern_inventory import encode


def validate(out,test_log):
    started=time.perf_counter();r=json.loads((out/'report.json').read_text());d=read_archive(r['diagnostics']);assert r['policy']==POLICY
    with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
        tmp=Path(td);path=tmp/'history';seed=tmp/'seed';delta=tmp/'delta'
        for name in ('experiments.cnf_probe_window.discover_probes','experiments.cnf_probe_continuation.discover_probes',
                     'experiments.cnf_trace_learning.discover_equivalence_probes','experiments.cnf_learning_continuation.discover_equivalence_probes'):
            stack.enter_context(patch(name,side_effect=AssertionError('new discovery')))
        assert sha(r['delta']['path'])==r['delta']['sha256'];unpack(r['delta']['path'],delta,r['delta']['database_sha256'])
        parent,rewrites,learning,continuations=restore_parent(Path(r['parent']['path']),seed,tmp)
        assert r['cases']==parent['cases'] and r['options']==parent['options']
        h=BudgetedInventory(seed,**r['options']);h.set_admission_budget(0);routes=ContinuedLearningRoutes(h,rewrites,learning,continuations)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']==parent['final_closed']
        leaf,state=select_leaf(h,routes);assert leaf==d['leaf'] and state==d['before']
        # Restore only saved ordinary blocks at this stage, leaving candidate
        # child availability equal to the pre-acquisition history for ranking.
        db=sqlite3.connect(delta);new_probes=[]
        for table,kind in [('cnf_probe_windows_v1','probe_window'),('cnf_probe_continuations_v1','probe_continuation')]:
            for key,payload in db.execute(f'SELECT id,payload FROM {table}'):
                record=json.loads(payload);assert record['source']==leaf['source'] and record['probing']['status']=='clear'
                with h.db:h.db.execute(f'INSERT INTO {table} VALUES (?,?)',(key,payload))
                if kind=='probe_window':verify_window(h,record,Counter());routes.windows[key]=record
                else:routes.verify(h,record,Counter());routes.continuations[key]=record
                new_probes.append((kind,record.get('offset',0)))
        ordinary=d['ordinary'];assert len(ordinary['visits'])<=POLICY['ordinary_steps']
        assert len({v['source'] for v in ordinary['visits']})==ordinary['distinct_sources']<=POLICY['ordinary_sources']
        assert all(v['source']==leaf['source'] for v in ordinary['visits'])
        assert set(new_probes)=={(v['kind'],v['offset']) for v in ordinary['visits'] if v['kind'] is not None}
        assert all(v['status']=='clear' if v['kind'] is not None else v['status'] is None for v in ordinary['visits'])
        assert routes.advance(h,leaf['source'],Counter())==(None,None,None)
        assert not r['ordinary']['admitted_state_sha256'] and not h.admitted
        attempts,_=source_attempts(h,leaf['source'],Counter());binary,outside=certify_exhaustion(h._load(leaf['source'])['cnf'],attempts,Counter())
        assert d['exhaustion']==dict(binary=binary,outside=outside,attempts=len(attempts))
        ranked=candidates(h,leaf['source'],routes,Counter(),candidate_limit=POLICY['candidate_pairs'])
        assert encode(ranked)==encode(d['candidates'])
        records=read_archive(r['splits']);assert records==[ranked[0]['record']]
        control=d['control'];source=h._load(leaf['source'])['cnf'];check_pair(source,control['attempts'],Counter())
        variable=read_attempt(h,leaf['source'],records[0]['references'][0],Counter())['variable']
        assert all(a['variable']==variable for a in control['attempts'])
        for attempt,edge in zip(control['attempts'],records[0]['edges'],strict=True):
            target,_=check_simplification(restrict(source,{variable:attempt['value']},Counter()),attempt['certificate'],Counter(),pure=False)
            _,names,key=h._canonical(target,h._load(leaf['source'])['depth']);assert edge==dict(key=key,names=names)
        h.close()
        admitted=set(r['acquisition']['admitted_state_sha256']);assert len(admitted)<=POLICY['split_states']
        assert all(sha_key(key) in admitted for key, in db.execute('SELECT id FROM cnf_patterns_v1'));db.close()
        r,rewrites,learning,continuations,records=restore_checkpoint(out/'report.json',path,tmp);before=sha(path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=ContinuedLearningRoutes(h,rewrites,learning,continuations)
        for record in records:attach(h,routes,record,Counter())
        assert r['acquisition']['pending']==any(h._load(e['key']) is None for rec in records for e in rec['edges'])
        final,_=compose(h,roots,routes,Counter());assert final==r['final_closed']
        assert all(b or not a for a,b in zip(r['baseline_closed'],final,strict=True))
        assert r['gains']==[i for i,(a,b) in enumerate(zip(r['baseline_closed'],final)) if b and not a]
        verify_plan(h,read_archive(r['certificate']),[key for key,closed in zip(roots,final) if closed],routes,Counter())
        without,_=compose(h,roots,WithoutGrowth(routes),Counter());assert without==r['without_growth_closed']
        assert target_state(h,routes)==d['after']
        ep=r['reference'];assert sha(ep['path'])==ep['sha256'];refpath=tmp/'reference';unpack(ep['path'],refpath,ep['database_sha256'])
        old=parent['reference'];assert sha(old['path'])==old['sha256'];unpack(old['path'],tmp/'reference-seed',old['database_sha256'])
        assert preserved_reference(tmp/'reference-seed',refpath)==ep['preserved_nodes'];refbefore=sha(refpath);solver=ResidualSolver(refpath)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
        assert len(solver.checked)==ep['verified_nodes'];by_key={record_key(rec):rec for rec in records}
        assert {row['id'] for row in ep['rows']}==set(by_key)
        for row in ep['rows']:
            record=by_key[row['id']];source=h._load(record['source'])['cnf'];targets,_=verify(h,record,Counter())
            _,_,key=solver._canonical(source);assert key==row['source']['root'] and solver.solve(source)['answer']==row['source']['answer']
            assert len(row['children'])==2 and row['source']['answer']==any(c['answer'] for c in row['children'])
            for value,target,edge,saved in zip((False,True),targets,record['edges'],row['children'],strict=True):
                _,_,key=solver._canonical(target);assert key==saved['root'] and solver.solve(target)['answer']==saved['answer']
                child=h._load(edge['key'])
                if child is not None:
                    answer=solver.solve(child['cnf']);assert answer['answer']==saved['answer']
                    if answer['answer']:assert holds(source,lift(h,record,value,answer['model']))
        assert {row['case'] for row in ep['originals']}==set(r['gains'])
        for row in ep['originals']:
            source=r['cases'][row['case']]['source'];_,_,key=solver._canonical(source);assert key==row['result']['root']
            answer=solver.solve(source);assert answer['answer']==row['result']['answer']
            if answer['answer']:assert holds(source,answer['model'])
        assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(refpath)==refbefore
        assert not h.admitted and h.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';h.close();assert sha(path)==before
    log=test_log.read_text();match=re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log);assert match and int(match[1])>=581
    (out/'full-validation.txt').write_text(log)
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),python_tests=int(match[1]),test_log_sha256=sha(out/'full-validation.txt'),
        coverage=sum(final),gains=r['gains'],without_growth=sum(without),new_trace_splits=len(records),reference_nodes=ep['verified_nodes'],
        preserved_reference_nodes=ep['preserved_nodes'],history_bytes_unchanged=True,cold_new_discovery=False,seconds=time.perf_counter()-started,
        original_answers={str(row['case']):row['result']['answer'] for row in ep['originals']})
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--test-log',type=Path,required=True)
    a=p.parse_args();validate(a.output,a.test_log)
