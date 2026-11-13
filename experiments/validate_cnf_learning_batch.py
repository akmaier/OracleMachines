#!/usr/bin/env python3
"""Independent cold checks for a retained-learning continuation checkpoint."""
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
from experiments.continue_cnf_learning import restore_checkpoint,target_state,preserved_reference
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_probe_continuation import sha,sha_key,unpack,WithoutGrowth
from experiments.cnf_learning_continuation import ContinuedLearningRoutes,record_key
from experiments.cnf_learning_batch import selection
from experiments.cnf_probe_equivalence import check_equivalence_probes
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_pattern_inventory import encode


def validate(out,test_log):
    started=time.perf_counter();r=json.loads((out/'report.json').read_text());diagnostics=read_archive(r['diagnostics'])
    with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
        tmp=Path(td);path=tmp/'history';seed=tmp/'seed'
        for name in ('experiments.cnf_learning_continuation.discover_equivalence_probes','experiments.cnf_trace_learning.discover_equivalence_probes',
                     'experiments.cnf_probe_window.discover_probes','experiments.cnf_probe_continuation.discover_probes'):
            stack.enter_context(patch(name,side_effect=AssertionError('new discovery')))
        parent,rewrites,learning,old=restore_checkpoint(Path(r['parent']['path']),seed,tmp);seed_before=sha(seed)
        h=BudgetedInventory(seed,**r['options']);h.set_admission_budget(0);routes=ContinuedLearningRoutes(h,rewrites,learning,old)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert r['cases']==parent['cases'] and r['options']==parent['options']
        assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']==parent['final_closed']
        assert selection(h,routes,Counter())==diagnostics['selection_before'] and not h.admitted
        h.close();assert sha(seed)==seed_before
        r,rewrites,learning,records=restore_checkpoint(out/'report.json',path,tmp);before=sha(path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=ContinuedLearningRoutes(h,rewrites,learning,records)
        blocks=routes.learned_blocks;entries=read_archive(r['additions']);new={record_key(e['record']):e for e in entries}
        assert len(new)==len(entries) and set(new)==set(blocks.records)-{record_key(rec) for rec in old}
        for entry in entries:
            rec=entry['record'];node,_,ranked=blocks.context(h,rec['base_sha256'],Counter());control=entry['control']
            choices=ranked[rec['offset']:rec['offset']+4]
            assert control['offset']==rec['offset'] and control['choices']==choices
            check_equivalence_probes(node['cnf'],control['probing'],4,Counter(),_choices=choices)
        search=diagnostics['search'];policy=r['policy'];visits=search['visits']
        assert len(visits)<=policy['step_limit']
        eligible={row['base_sha256'] for row in diagnostics['selection_before'] if row['reason'] in ('ready','pending')}
        assert all(v['base_sha256'] in eligible for v in visits)
        assert set(search['queued'])<=eligible and set(search['skipped_covered'])<=eligible
        new_visits=[]
        for v in visits:
            if v['offset'] is None:
                assert v['status'] is None and not v['new']
                assert blocks.advance(h,v['base_sha256'],Counter())==(None,None);continue
            key=encode([v['base_sha256'],4,v['offset']]);rec=blocks.records[key]
            assert v['status']==rec['probing']['status'] and v['new']==(key in new)
            if v['new']:new_visits.append(key)
        assert len(new_visits)==len(new) and set(new_visits)==set(new)
        admitted=set();successful_visits={(v['base_sha256'],v['offset']) for v in visits if v['status'] not in (None,'clear')}
        assert {(a['base_sha256'],a['offset']) for a in search['recognitions']}==successful_visits
        for acquisition in search['recognitions']:
            added=set(acquisition['admitted']);assert len(added)==len(acquisition['admitted'])<=policy['target_limit']
            assert not added&admitted;admitted.update(added)
        assert len(admitted)<=policy['state_limit'] and sorted(map(sha_key,admitted))==r['admitted_state_sha256']
        delta=tmp/'checked-delta';unpack(r['delta']['path'],delta,r['delta']['database_sha256']);db=sqlite3.connect(delta)
        assert all(k in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1'));db.close()
        final,_=compose(h,roots,routes,Counter());assert final==r['final_closed']
        assert all(b or not a for a,b in zip(r['baseline_closed'],final,strict=True))
        assert r['gains']==[i for i,(a,b) in enumerate(zip(r['baseline_closed'],final)) if b and not a]
        verify_plan(h,read_archive(r['certificate']),[k for k,b in zip(roots,final) if b],routes,Counter())
        without,_=compose(h,roots,WithoutGrowth(routes),Counter());assert without==r['without_growth_closed']
        assert selection(h,routes,Counter())==diagnostics['selection_after'] and target_state(h,routes)==diagnostics['targets']
        ep=r['reference'];assert sha(ep['path'])==ep['sha256'];refpath=tmp/'reference'
        unpack(ep['path'],refpath,ep['database_sha256']);refbefore=sha(refpath)
        inherited=parent['reference'];assert sha(inherited['path'])==inherited['sha256']
        unpack(inherited['path'],tmp/'reference-seed',inherited['database_sha256'])
        assert preserved_reference(tmp/'reference-seed',refpath)==ep['preserved_nodes']
        solver=ResidualSolver(refpath)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
        assert len(solver.checked)==ep['verified_nodes']
        successful={key:rec for key,rec in blocks.records.items() if rec['edge'] is not None}
        assert {row['id'] for row in ep['rows']}==set(successful)
        for row in ep['rows']:
            rec=successful[row['id']];source=h._load(blocks.bases[rec['base_sha256']]['source'])['cnf'];target,_=blocks.verify(h,rec,Counter())
            for name,cnf in [('source',source),('target',target)]:
                _,_,key=solver._canonical(cnf);assert key==row[name]['root'] and solver.solve(cnf)['answer']==row[name]['answer']
            assert row['source']['answer']==row['target']['answer'];child=h._load(rec['edge']['key'])
            if child is not None:
                answer=solver.solve(child['cnf']);assert answer['answer']==row['source']['answer']
                if answer['answer']:assert holds(source,blocks.lift(h,rec,answer['model']))
        assert {row['case'] for row in ep['originals']}==set(r['gains'])
        for row in ep['originals']:
            source=r['cases'][row['case']]['source'];_,_,key=solver._canonical(source);assert key==row['result']['root']
            answer=solver.solve(source);assert answer['answer']==row['result']['answer']
            if answer['answer']:assert holds(source,answer['model'])
        assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(refpath)==refbefore
        assert not h.admitted and h.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';h.close();assert sha(path)==before
    log=test_log.read_text();match=re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log);assert match and int(match[1])>=577
    (out/'full-validation.txt').write_text(log)
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),python_tests=int(match[1]),
        test_log_sha256=sha(out/'full-validation.txt'),coverage=sum(final),gains=r['gains'],without_growth=sum(without),
        history_bytes_unchanged=True,cold_new_discovery=False,reference_nodes=ep['verified_nodes'],
        reference_preserved_nodes=ep['preserved_nodes'],new_augmented_blocks=len(entries),seconds=time.perf_counter()-started,
        original_answers={str(row['case']):row['result']['answer'] for row in ep['originals']})
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--test-log',type=Path,required=True)
    a=p.parse_args();validate(a.output,a.test_log)
