#!/usr/bin/env python3
"""Independent cold reconstruction of a bounded learned-target probe pass."""
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

from experiments.compare_cnf_target_probe import restore_checkpoint,checked_target,lift_forced,POLICY
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_probe_continuation import sha,sha_key,unpack,WithoutGrowth
from experiments.cnf_target_probe import targets,remaining
from experiments.cnf_trace_learning import LearnedTraceRoutes
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_residual_dag import ResidualSolver,holds


def validate(out,test_log):
    started=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'history';r,rewrites,learning=restore_checkpoint(out/'report.json',path,tmp);before=sha(path)
        assert r['policy']==POLICY;diagnostics=read_archive(r['diagnostics'])
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
        with ExitStack() as stack:
            for name in ('experiments.cnf_probe_window.discover_probes','experiments.cnf_probe_continuation.discover_probes',
                         'experiments.cnf_trace_learning.discover_equivalence_probes'):
                stack.enter_context(patch(name,side_effect=AssertionError('new discovery during replay')))
            routes=LearnedTraceRoutes(h,rewrites,learning);roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
            selected=targets(h,learning,Counter());assert selected==diagnostics['selected']
            final,_=compose(h,roots,routes,Counter());assert final==r['final_closed']
            assert all(b or not a for a,b in zip(r['baseline_closed'],final,strict=True))
            assert r['gains']==[i for i,(a,b) in enumerate(zip(r['baseline_closed'],final)) if b and not a]
            verify_plan(h,read_archive(r['certificate']),[k for k,b in zip(roots,final) if b],routes,Counter())
            without,_=compose(h,roots,WithoutGrowth(routes),Counter());assert without==r['without_growth_closed']
            assert remaining(h,selected,routes,Counter())==diagnostics['after']
        assert len(selected)==len(r['acquisitions'])==len(diagnostics['passes'])
        for row,acquisition,trial in zip(selected,r['acquisitions'],diagnostics['passes'],strict=True):
            assert sha_key(row['target'])==acquisition['target_sha256'] and row['target']==trial['target']
            result=trial['result'];assert result['stop']==acquisition['stop']
            assert len(result['visits'])<=POLICY['step_limit']
            assert len({v['source'] for v in result['visits']})==result['distinct_sources']<=POLICY['source_limit']
            assert len(acquisition['admitted_state_sha256'])<=POLICY['state_limit']
            for visit in result['visits']:
                if visit['kind'] is None:
                    assert visit['offset'] is None and visit['status'] is None;continue
                records=routes.windows if visit['kind']=='probe_window' else routes.continuations
                matches=[rec for rec in records.values() if rec['source']==visit['source'] and rec.get('offset',0)==visit['offset']]
                assert len(matches)==1 and matches[0]['probing']['status']==visit['status']
        delta=tmp/'current-delta';unpack(r['delta']['path'],delta,r['delta']['database_sha256']);db=sqlite3.connect(delta)
        admitted=set().union(*(set(x['admitted_state_sha256']) for x in r['acquisitions']))
        assert all(sha_key(k) in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1'))
        expected={(kind,k) for kind,table in (('probe_window','cnf_probe_windows_v1'),('probe_continuation','cnf_probe_continuations_v1'))
                  for k, in db.execute(f'SELECT id FROM {table}')};db.close()
        assert expected=={(x['kind'],x['id']) for x in diagnostics['new_records']}
        forced={};statuses=Counter()
        for kind,key in expected:
            record=(routes.windows if kind=='probe_window' else routes.continuations)[key]
            statuses[record['probing']['status']]+=1
            if record['edge'] is not None:forced[(kind,sha_key(key))]=record
        assert dict(statuses)==r['new_probe_summary']
        ep=r['reference'];assert sha(ep['path'])==ep['sha256'];refpath=tmp/'reference'
        unpack(ep['path'],refpath,ep['database_sha256']);refbefore=sha(refpath);solver=ResidualSolver(refpath)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
        assert len(solver.checked)==ep['verified_nodes'] and {(x['kind'],x['id_sha256']) for x in ep['rows']}==set(forced)
        for row in ep['rows']:
            record=forced[(row['kind'],row['id_sha256'])];source=h._load(record['source'])['cnf']
            target=checked_target(h,routes,row['kind'],record)
            for name,cnf in [('source',source),('target',target)]:
                _,_,key=solver._canonical(cnf);assert key==row[name]['root']
                answer=solver.solve(cnf);assert answer['answer']==row[name]['answer']
            assert row['source']['answer']==row['target']['answer']
            answer=solver.solve(target)
            if answer['answer']:lift_forced(source,record,answer['model'])
        assert {x['case'] for x in ep['originals']}==set(r['gains'])
        for row in ep['originals']:
            source=r['cases'][row['case']]['source'];_,_,key=solver._canonical(source);assert key==row['result']['root']
            answer=solver.solve(source);assert answer['answer']==row['result']['answer']
            if answer['answer']:assert holds(source,answer['model'])
        assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(refpath)==refbefore
        assert not h.admitted and h.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';h.close();assert sha(path)==before
    log=test_log.read_text();match=re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log);assert match and int(match[1])>=569
    (out/'full-validation.txt').write_text(log)
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),python_tests=int(match[1]),
        test_log_sha256=sha(out/'full-validation.txt'),coverage=sum(final),gains=r['gains'],without_growth=sum(without),
        reference_nodes=ep['verified_nodes'],new_probe_records=len(expected),history_bytes_unchanged=True,
        cold_new_discovery=False,seconds=time.perf_counter()-started,
        original_answers={str(x['case']):x['result']['answer'] for x in ep['originals']})
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--test-log',type=Path,required=True)
    a=p.parse_args();validate(a.output,a.test_log)
