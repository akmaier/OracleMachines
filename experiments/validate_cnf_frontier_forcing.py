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
from experiments.continue_cnf_frontier_forcing import restore_checkpoint,POLICY,routes_for
from experiments.continue_cnf_affine_clause import selected_frontiers
from experiments.cnf_failed_literal import check_probes
from experiments.compare_cnf_split_batch import new_probes
from experiments.validate_cnf_split_batch import check_coverage,delta_file
from experiments.compare_cnf_trace_reuse import read_archive,archive_json
from experiments.compare_cnf_probe_continuation import sha,sha_key,unpack
from experiments.compare_cnf_target_probe import checked_target,lift_forced
from experiments.cnf_split_frontier import frontier
from experiments.cnf_split_batch import children
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.continue_cnf_learning import target_state,preserved_reference
from experiments.cnf_learning_batch import selection
from experiments.cnf_trace_reuse import source_attempts
from experiments.cnf_trace_split import candidates
from experiments.cnf_pattern_inventory import encode


TEST_MODULES=['solver.test_cnf_target_probe', 'solver.test_cnf_probe_continuation', 'solver.test_cnf_probe_window', 'solver.test_cnf_split_frontier', 'solver.test_cnf_original_splits', 'solver.test_cnf_affine_clause', 'solver.test_cnf_route_composition', 'solver.test_cnf_trace_split']
TEST_COMMAND='python3 -m unittest '+' '.join(TEST_MODULES)

def validate(out,test_log):
    started=time.perf_counter();r=json.loads((out/'report.json').read_text());assert r['policy']==POLICY
    with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
        tmp=Path(td);seed=tmp/'seed';path=tmp/'history';delta=tmp/'new-delta'
        for name in ('experiments.cnf_probe_window.discover_probes','experiments.cnf_probe_continuation.discover_probes',
                     'experiments.cnf_trace_learning.discover_equivalence_probes','experiments.cnf_learning_continuation.discover_equivalence_probes',
                     'experiments.cnf_affine_clause.discover'):
            stack.enter_context(patch(name,side_effect=AssertionError('new discovery')))
        stack.enter_context(patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('new recognition')))
        parent,*evidence=restore_checkpoint(Path(r['parent']['path']),seed,tmp)
        assert len(evidence)==5 and [len(items) for items in evidence]==r['evidence_counts']
        parent_evidence=evidence
        assert r['cases']==parent['cases'] and r['options']==parent['options'];before_bytes=sha(seed)
        h=BudgetedInventory(seed,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']==parent['final_closed']
        before=frontier(h,routes,evidence[3],Counter());saved=read_archive(r['selection'])
        ranked=candidates(h,before['leaves'][0]['source'],routes,Counter(),candidate_limit=64)
        assert saved==dict(before=before,leaf=before['leaves'][0],ranked=ranked,candidate_limit=64)
        h.close();assert sha(seed)==before_bytes
        delta_file(r['delta'],delta);items=new_probes(delta)
        assert read_archive(r['new_probes'])==[dict(kind=x['kind'],id=x['id']) for x in items]
        assert dict(Counter(x['record']['probing']['status'] for x in items))==r['new_probe_summary']
        print('cold child checkpoint and reference proofs',flush=True)
        restored,*evidence=restore_checkpoint(out/'report.json',path,tmp);assert restored==r
        assert evidence==parent_evidence
        before_bytes=sha(path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        check_coverage(h,routes,roots,r,r['baseline_closed']);d=read_archive(r['diagnostics'])
        assert frontier(h,routes,evidence[3],Counter())==d['after']
        assert children(h,routes,evidence[3])==d['children'] and target_state(h,routes)==d['targets']
        assert selection(h,routes,Counter())==d['learning']
        assert selected_frontiers(h,roots,routes,r['final_closed'])[0]==d['open_originals']
        profiles=[]
        for leaf in d['after']['leaves']:
            node=h._load(leaf['source']);cnf=node['cnf']
            attempts,_=source_attempts(h,leaf['source'],Counter())
            profiles.append(dict(source=leaf['source'],source_sha256=sha_key(leaf['source']),
                variables=leaf['variables'],clauses=len(cnf),literals=sum(map(len,cnf)),
                clause_widths=dict(Counter(map(len,cnf))),outcomes=node['profile']['outcomes'],
                extracted_equations=len(node['profile']['evidence']['explicit_affine']['equations']),
                saved_pair_variables=[a['variable'] for a in attempts[::2]],
                untried_ordinary_variables=leaf['remaining_ranked_variables']))
        profiles_archive=archive_json(out/'frontier-profiles.json.gz',profiles)
        if 'preflight' in r:
            preview=read_archive(r['preflight'])
            assert preview['source']==saved['leaf']['source']
            assert preview['parent_validation_sha256']==sha(Path(r['parent']['path']).parent/'validation.json')
            target,fixed=check_probes(h._load(preview['source'])['cnf'],preview['probing'],4,Counter(),_choices=preview['choices'])
            assert encode(target)==encode(preview['target']) and encode(fixed)==encode(preview['fixed'])
            assert any(x['record']['source']==preview['source'] and x['record']['probing']==preview['probing'] for x in items)
            assert r['pipeline_plus_preflight_seconds']==r['pipeline_seconds']+preview['seconds']
        result=d['result'];visits=result['visits'];assert len(visits)==POLICY['step_limit']==1 and visits[0]['status']=='forced'
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
        db=sqlite3.connect(delta);new_nodes=list(db.execute('SELECT id,payload FROM cnf_patterns_v1'))
        assert {sha_key(key) for key,_ in new_nodes}==admitted
        for key,_ in new_nodes:assert h._load(key) is not None
        kinds=dict(Counter(json.loads(payload)['kind'] for _,payload in new_nodes));db.close()
        ep=r['reference'];ref=tmp/'reference';assert sha(ep['path'])==ep['sha256'];unpack(ep['path'],ref,ep['database_sha256'])
        old=parent['reference'];assert sha(old['path'])==old['sha256'];unpack(old['path'],tmp/'reference-seed',old['database_sha256'])
        assert preserved_reference(tmp/'reference-seed',ref)==ep['preserved_nodes']==old['verified_nodes']
        refbefore=sha(ref);solver=ResidualSolver(ref)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
        assert len(solver.checked)==ep['verified_nodes']
        def answer(source,saved):
            _,_,key=solver._canonical(source);assert key==saved['root'];actual=solver.solve(source);assert actual['answer']==saved['answer']
            assert not solver.counts.get('expanded_nodes',0)
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
    log=test_log.read_text();match=re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log);assert match and int(match[1])==33
    (out/'targeted-validation.txt').write_text(log.rstrip()+'\n')
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),python_tests=int(match[1]),test_log_sha256=sha(out/'targeted-validation.txt'),
        test_command=TEST_COMMAND,
        test_source_sha256={m.replace('.','/')+'.py':sha(m.replace('.','/')+'.py') for m in TEST_MODULES},
        saved_pair_ranks=[row['rank'] for row in ranked],new_node_kinds=kinds,
        remaining_leaves=[[leaf['variables'],leaf['clauses']] for leaf in d['after']['leaves']],pending=len(d['after']['pending']),
        evidence_counts=r['evidence_counts'],frontier_profiles=profiles_archive,
        coverage=sum(r['final_closed']),gains=r['gains'],without_growth=sum(r['without_growth_closed']),reference_nodes=ep['verified_nodes'],
        preserved_reference_nodes=ep['preserved_nodes'],history_bytes_unchanged=True,cold_new_discovery=False,seconds=time.perf_counter()-started,
        original_answers={str(row['case']):row['result']['answer'] for row in ep['originals']})
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--test-log',type=Path,required=True)
    a=p.parse_args();validate(a.output,a.test_log)
