#!/usr/bin/env python3
"""Cold replay of isolated comparison arms and their immutable evidence union."""
from collections import Counter
from contextlib import ExitStack
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_split_batch import restore_checkpoint,restore_parent,routes_for,new_probes,POLICY
from experiments.compare_cnf_probe_continuation import sha,sha_key,digests,unpack,apply_delta,WithoutGrowth
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_target_probe import checked_target,lift_forced
from experiments.cnf_trace_split import candidates,verify,lift,record_key
from experiments.cnf_split_batch import leaves,children
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.continue_cnf_learning import target_state,preserved_reference
from experiments.cnf_learning_batch import selection
from experiments.cnf_pattern_inventory import encode


def delta_file(metadata,path):
    assert sha(metadata['path'])==metadata['sha256'];unpack(metadata['path'],path,metadata['database_sha256'])
    db=sqlite3.connect(path)
    for table,n in metadata['added_rows'].items():assert db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==n
    db.close()


def check_coverage(h,routes,roots,saved,baseline):
    final,_=compose(h,roots,routes,Counter());assert final==saved['final_closed']
    assert all(b or not a for a,b in zip(baseline,final,strict=True))
    assert saved['gains']==[i for i,(a,b) in enumerate(zip(baseline,final)) if b and not a]
    verify_plan(h,read_archive(saved['certificate']),[k for k,b in zip(roots,final) if b],routes,Counter())
    assert compose(h,roots,WithoutGrowth(routes),Counter())[0]==saved['without_growth_closed']


def check_reference(h,routes,records,r,parent,tmp,probe_delta):
    ep=r['reference'];path=tmp/'reference';assert sha(ep['path'])==ep['sha256'];unpack(ep['path'],path,ep['database_sha256'])
    old=parent['reference'];assert sha(old['path'])==old['sha256'];unpack(old['path'],tmp/'reference-seed',old['database_sha256'])
    assert preserved_reference(tmp/'reference-seed',path)==ep['preserved_nodes'];before=sha(path);solver=ResidualSolver(path)
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
    assert len(solver.checked)==ep['verified_nodes']
    def answer(source,saved):
        _,_,key=solver._canonical(source);assert key==saved['root']
        result=solver.solve(source);assert result['answer']==saved['answer']
        if result['answer']:assert holds(source,result['model'])
        return result
    by_key={record_key(rec):rec for rec in records};assert {row['id'] for row in ep['rows']}==set(by_key)
    for row in ep['rows']:
        record=by_key[row['id']];source=h._load(record['source'])['cnf'];targets,_=verify(h,record,Counter())
        answer(source,row['source']);assert row['source']['answer']==any(c['answer'] for c in row['children'])
        for value,target,edge,saved in zip((False,True),targets,record['edges'],row['children'],strict=True):
            answer(target,saved);child=h._load(edge['key'])
            if child is not None:
                result=solver.solve(child['cnf']);assert result['answer']==saved['answer']
                if result['answer']:assert holds(source,lift(h,record,value,result['model']))
    forced={ (item['kind'],sha_key(item['id'])):item for item in new_probes(probe_delta) if item['record']['edge'] is not None }
    assert {(row['kind'],row['id_sha256']) for row in ep['probes']}==set(forced)
    for row in ep['probes']:
        item=forced[(row['kind'],row['id_sha256'])];record=item['record'];source=h._load(record['source'])['cnf']
        target=checked_target(h,routes,item['kind'],record);answer(source,row['source']);result=answer(target,row['target'])
        assert row['source']['answer']==row['target']['answer']
        if result['answer']:lift_forced(source,record,result['model'])
    assert {row['case'] for row in ep['originals']}==set(r['gains'])
    for row in ep['originals']:answer(r['cases'][row['case']]['source'],row['result'])
    assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(path)==before


def validate(out,test_log):
    started=time.perf_counter();r=json.loads((out/'report.json').read_text());assert r['policy']==POLICY
    with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
        tmp=Path(td);seed=tmp/'seed'
        for name in ('experiments.cnf_probe_window.discover_probes','experiments.cnf_probe_continuation.discover_probes',
                     'experiments.cnf_trace_learning.discover_equivalence_probes','experiments.cnf_learning_continuation.discover_equivalence_probes'):
            stack.enter_context(patch(name,side_effect=AssertionError('new discovery')))
        stack.enter_context(patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('new recognition')))
        parent,*evidence=restore_parent(Path(r['parent']['path']),seed,tmp);assert r['cases']==parent['cases'] and r['options']==parent['options']
        before=sha(seed);h=BudgetedInventory(seed,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']==parent['final_closed']
        saved=read_archive(r['selection']);selected=leaves(h,routes)[:POLICY['source_limit']];assert selected==saved['selected']
        ranked=[dict(source=row['source'],candidates=candidates(h,row['source'],routes,Counter(),candidate_limit=POLICY['candidate_pairs'])) for row in selected]
        assert encode(ranked)==encode(saved['ranked']);records=read_archive(r['splits']);assert records==[row['candidates'][0]['record'] for row in ranked if row['candidates']]
        h.close();assert sha(seed)==before
        merged=tmp/'merged';shutil.copyfile(seed,merged)
        for arm,a in r['arms'].items():
            print(f'cold {arm} arm',flush=True);delta=tmp/f'{arm}-delta';delta_file(a['delta'],delta)
            path=tmp/arm;shutil.copyfile(seed,path);apply_delta(path,delta);assert digests(path)==a['logical_table_digests'];before=sha(path)
            apply_delta(merged,delta);h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
            arm_evidence=[*evidence[:-1],evidence[-1]+(records if arm=='split' else [])];routes=routes_for(h,arm_evidence)
            check_coverage(h,routes,roots,a,r['baseline_closed']);d=read_archive(a['diagnostics']);assert target_state(h,routes)==d['targets']
            admission_sets=[set(row['admitted']) for row in d['passes']];admitted=set().union(*admission_sets)
            assert sorted(map(sha_key,admitted))==a['admitted_state_sha256']
            assert all(len(keys)<=POLICY['pair_states'] for keys in admission_sets)
            charged=len(admitted) if arm=='split' else sum(map(len,admission_sets))
            assert charged==a['charged_admissions']<=POLICY['total_states']
            if arm=='split':
                assert [row['source'] for row in d['passes']]==[rec['source'] for rec in records]
                assert sum(map(len,admission_sets))==len(admitted)
                for row in d['passes']:
                    if row['skipped_covered']:assert not row['admitted'] and not row['branches']
                    else:
                        assert len(row['branches'])==2
                        branch_sets=[set(branch['admitted']) for branch in row['branches']]
                        assert not branch_sets[0]&branch_sets[1] and set().union(*branch_sets)==set(row['admitted'])
                assert children(h,routes,records)==d['children']
            else:
                assert [row['source'] for row in d['passes']]==[row['source'] for row in selected]
                visits=[]
                for row in d['passes']:
                    result=row['result'];assert len(result['visits'])<=POLICY['probe_steps']
                    assert len({v['source'] for v in result['visits']})==result['distinct_sources']<=POLICY['probe_sources']
                    visits.extend(result['visits'])
                seen={(v['source'],v['kind'],v['offset'],v['status']) for v in visits}
                for item in new_probes(delta):
                    record=item['record'];checked_target(h,routes,item['kind'],record)
                    assert (record['source'],item['kind'],record.get('offset',0),record['probing']['status']) in seen
            db=sqlite3.connect(delta)
            for key, in db.execute('SELECT id FROM cnf_patterns_v1'):
                assert key in admitted and h._load(key) is not None
            db.close();assert not h.admitted;h.close();assert sha(path)==before
        assert digests(merged)==r['logical_table_digests']
        print('cold merged checkpoint and references',flush=True)
        path=tmp/'union';restored,*union_evidence=restore_checkpoint(out/'report.json',path,tmp);assert restored==r
        before=sha(path);h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=routes_for(h,union_evidence)
        check_coverage(h,routes,roots,r,r['baseline_closed'])
        for a in r['arms'].values():assert all(b or not a for a,b in zip(a['final_closed'],r['final_closed'],strict=True))
        d=read_archive(r['diagnostics']);assert children(h,routes,records)==d['children'] and target_state(h,routes)==d['targets']
        assert selection(h,routes,Counter())==d['learning']
        check_reference(h,routes,records,r,parent,tmp,tmp/'probe-delta')
        assert not h.admitted and h.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';h.close();assert sha(path)==before
    log=test_log.read_text();match=re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log);assert match and int(match[1])>=585
    (out/'full-validation.txt').write_text(log)
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),python_tests=int(match[1]),test_log_sha256=sha(out/'full-validation.txt'),
        coverage=sum(r['final_closed']),arm_coverage={name:sum(a['final_closed']) for name,a in r['arms'].items()},gains=r['gains'],
        without_growth=sum(r['without_growth_closed']),new_trace_splits=len(records),reference_nodes=r['reference']['verified_nodes'],
        preserved_reference_nodes=r['reference']['preserved_nodes'],cold_new_discovery=False,history_bytes_unchanged=True,seconds=time.perf_counter()-started)
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--test-log',type=Path,required=True)
    a=p.parse_args();validate(a.output,a.test_log)
