#!/usr/bin/env python3
"""Cold replay of learned implications, exact graph closures and matched controls."""
from collections import Counter
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

from experiments.compare_cnf_trace_learning import restore_checkpoint
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_probe_continuation import sha,sha_key,unpack,WithoutGrowth
from experiments.cnf_trace_reuse import source_attempts
from experiments.cnf_trace_learning import (implication_graph,check_graph,LearnedTraceRoutes,
    checked_augmentation,verify_learning,lift_learning,PROBE_LIMIT,LEARN_LIMIT)
from experiments.cnf_probe_learning import learning_batch
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_probe_equivalence import check_equivalence_probes
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_pattern_inventory import encode


def validate(out,test_log):
    started=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);path=tmp/'history';r,rewrites,records=restore_checkpoint(out/'report.json',path,tmp);before=sha(path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
        parent=json.loads(Path(r['parent']['path']).read_text());inputs=read_archive(parent['opportunities'])
        diagnostics=read_archive(r['diagnostics']);assert len(inputs)==len(diagnostics)
        used=set()
        with patch('experiments.cnf_trace_learning.discover_equivalence_probes',side_effect=AssertionError('new probing')):
            with patch('experiments.cnf_trace_learning.discover_graph',side_effect=AssertionError('new graph discovery')):
                for i,(source_row,row) in enumerate(zip(inputs,diagnostics,strict=True)):
                    source=source_row['source'];node=h._load(source)
                    assert row['input_row']==i and row['source_sha256']==sha_key(source) and row['cases']==source_row['cases']
                    attempts,refs=source_attempts(h,source,Counter());graph=implication_graph(node['cnf'],attempts,Counter())
                    check_graph(graph,row['graph'],Counter())
                    expected=learning_batch(node['cnf'],attempts,LEARN_LIMIT,Counter())
                    if not expected:
                        assert row['learning_index'] is None and row['control'] is None;continue
                    index=row['learning_index'];assert type(index) is int and 0<=index<len(records) and index not in used
                    used.add(index);record=records[index];assert record['source']==source
                    actual=[dict(reference=record['references'][b['reference']],unit=b['unit'],clause=b['clause']) for b in record['clauses']]
                    expected=[dict(reference=refs[b['attempt']],unit=b['unit'],clause=b['clause']) for b in expected]
                    assert actual==expected
                    _,expanded=checked_augmentation(h,record,Counter());verify_learning(h,record,Counter())
                    choices=probe_choices(expanded,PROBE_LIMIT,Counter());assert row['control']['choices']==choices
                    check_equivalence_probes(node['cnf'],row['control']['probing'],PROBE_LIMIT,Counter(),_choices=choices)
                assert used==set(range(len(records)))
                routes=LearnedTraceRoutes(h,rewrites,records);roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
                final,_=compose(h,roots,routes,Counter());assert final==r['final_closed']
                plan=read_archive(r['certificate']);verify_plan(h,plan,[k for k,b in zip(roots,final) if b],routes,Counter())
                without,_=compose(h,roots,WithoutGrowth(routes),Counter());assert without==r['without_growth_closed']
        admitted=set().union(*(set(row['admitted_state_sha256']) for row in r['acquisitions']))
        assert all(len(row['admitted_state_sha256'])<=32 for row in r['acquisitions'])
        db=sqlite3.connect(tmp/'learning-delta')
        assert all(sha_key(k) in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1'));db.close()
        successful={sha_key(rec['source']):rec for rec in records if rec['edge'] is not None}
        assert {x['source_sha256'] for x in r['acquisitions']}==set(successful)
        for row in r['acquisitions']:
            assert (h._load(successful[row['source_sha256']]['edge']['key']) is None)==row['pending']
        assert not h.admitted and h.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
        ep=r['reference'];assert sha(ep['path'])==ep['sha256'];refpath=tmp/'reference'
        unpack(ep['path'],refpath,ep['database_sha256']);refbefore=sha(refpath);solver=ResidualSolver(refpath)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
        assert len(solver.checked)==ep['verified_nodes'] and {x['source_sha256'] for x in ep['rows']}==set(successful)
        for row in ep['rows']:
            record=successful[row['source_sha256']];source=h._load(record['source'])['cnf'];target,_=verify_learning(h,record,Counter())
            for name,cnf in [('source',source),('target',target)]:
                _,_,key=solver._canonical(cnf);assert key==row[name]['root'];answer=solver.solve(cnf)
                assert answer['answer']==row[name]['answer']
            assert row['source']['answer']==row['target']['answer']
            child=h._load(record['edge']['key'])
            if child is not None:
                answer=solver.solve(child['cnf']);assert answer['answer']==row['source']['answer']
                if answer['answer']:assert holds(source,lift_learning(h,record,answer['model'],Counter()))
        assert {x['case'] for x in ep['originals']}==set(r['gains'])
        for row in ep['originals']:
            source=r['cases'][row['case']]['source'];_,_,key=solver._canonical(source);assert key==row['result']['root']
            answer=solver.solve(source);assert answer['answer']==row['result']['answer']
            if answer['answer']:assert holds(source,answer['model'])
        assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(refpath)==refbefore
        h.close();assert sha(path)==before
    log=test_log.read_text();match=re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log);assert match and int(match[1])>=566
    (out/'full-validation.txt').write_text(log)
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),python_tests=int(match[1]),
        test_log_sha256=sha(out/'full-validation.txt'),coverage=sum(final),gains=r['gains'],without_growth=sum(without),
        reference_nodes=ep['verified_nodes'],graph_sources=len(diagnostics),learning_records=len(records),history_bytes_unchanged=True,
        cold_new_discovery=False,seconds=time.perf_counter()-started,
        original_answers={str(x['case']):x['result']['answer'] for x in ep['originals']})
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--test-log',type=Path,required=True)
    a=p.parse_args();validate(a.output,a.test_log)
