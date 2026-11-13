#!/usr/bin/env python3
"""Independently replay both bounded arms without new recognition or probing."""
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
from experiments.compare_cnf_learning_split import restore_checkpoint,restore_parent,additions,learning_targets,POLICY
from experiments.compare_cnf_split_batch import routes_for
from experiments.validate_cnf_split_batch import check_coverage,delta_file
from experiments.compare_cnf_probe_continuation import sha,sha_key,digests,unpack,apply_delta
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.cnf_split_frontier import frontier
from experiments.cnf_trace_split import candidates,verify,lift,record_key as split_key
from experiments.cnf_split_batch import children
from experiments.cnf_trace_reuse import source_attempts
from experiments.cnf_trace_learning import checked_augmentation,verify_learning,lift_learning,implication_graph,check_graph
from experiments.cnf_probe_learning import learning_batch
from experiments.cnf_probe_exhaustion import certify_exhaustion
from experiments.cnf_learning_continuation import LearningBlocks,base_id,record_key
from experiments.cnf_learning_batch import selection
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.continue_cnf_learning import preserved_reference
from experiments.cnf_pattern_inventory import encode


def check_batch(h,source,bases):
    """Recompute the declared clause selection, without acquiring new traces."""
    attempts,refs=source_attempts(h,source,Counter())
    batch=learning_batch(h._load(source)['cnf'],attempts,POLICY['learning_clauses'],Counter())
    if not batch:
        assert not bases
        return
    assert len(bases)==1 and bases[0]['source']==source
    selected=[];indices={};clauses=[]
    for item in batch:
        ref=refs[item['attempt']];identity=encode(ref)
        if identity not in indices:indices[identity]=len(selected);selected.append(ref)
        clauses.append(dict(reference=indices[identity],unit=item['unit'],clause=item['clause']))
    assert bases[0]['references']==selected and bases[0]['clauses']==clauses
    verify_learning(h,bases[0],Counter())


def check_learning_run(h,bases,blocks,result):
    """Bind resource/stop metadata to the checked records and acquired children."""
    local=LearningBlocks(h,bases,blocks)
    if not bases:
        assert result==dict(kind='no_batch') and not blocks
        return set()
    base=bases[0]
    if base['edge'] is not None:
        assert result['kind']=='base_reduction' and not blocks
        assert result['pending']==(h._load(base['edge']['key']) is None)
        return set(result['admitted'])
    assert result['kind']=='continuation';search=result['search'];visits=search['visits']
    assert len(visits)<=POLICY['learning_steps'] and not search['skipped_covered']
    identity=base_id(base);by_offset={b['offset']:b for b in blocks};seen=set()
    for v in visits:
        assert v['base_sha256']==identity
        if v['offset'] is None:
            assert not v['new'] and v['status'] is None
            _,_,ranked=local.context(h,identity,Counter())
            last=blocks[-1] if blocks else base
            end=(last.get('offset',0)+len(last['probing']['attempts'])//2)
            assert last['probing']['status']=='clear' and end>=len(ranked)
            continue
        rec=by_offset[v['offset']];assert v['new'] and rec['probing']['status']==v['status']
        assert rec['base_sha256']==identity;seen.add(record_key(rec))
    assert seen==set(local.records) and len(seen)==len([v for v in visits if v['new']])
    successful={b['offset']:b for b in blocks if b['edge'] is not None}
    assert {r['offset'] for r in search['recognitions']}==set(successful)
    admitted=set()
    for rec in search['recognitions']:
        assert rec['base_sha256']==identity
        assert rec['pending']==(h._load(successful[rec['offset']]['edge']['key']) is None)
        keys=set(rec['admitted']);assert not admitted&keys;admitted.update(keys)
    assert search['queued']==([identity] if visits and visits[-1]['status']=='clear' else [])
    return admitted


def check_reference(h,routes,records,bases,blocks,r,parent,tmp):
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
    by_key={split_key(rec):rec for rec in records};assert {row['id'] for row in ep['rows']}==set(by_key)
    for row in ep['rows']:
        rec=by_key[row['id']];source=h._load(rec['source'])['cnf'];targets,_=verify(h,rec,Counter())
        answer(source,row['source']);assert row['source']['answer']==any(c['answer'] for c in row['children'])
        for value,target,edge,saved in zip((False,True),targets,rec['edges'],row['children'],strict=True):
            answer(target,saved);child=h._load(edge['key'])
            if child is not None:
                result=solver.solve(child['cnf']);assert result['answer']==saved['answer']
                if result['answer']:assert holds(source,lift(h,rec,value,result['model']))
    by_base={base_id(base):base for base in bases};rows=ep['learning']['rows']
    assert {row['base_sha256'] for row in rows}==set(by_base)
    for row in rows:
        base=by_base[row['base_sha256']];node,expanded=checked_augmentation(h,base,Counter())
        a=answer(node['cnf'],row['source']);b=answer(expanded,row['expanded']);assert a['answer']==b['answer']
        if b['answer']:assert holds(node['cnf'],b['model'])
        relevant={('base',base_id(base)):base} if base['edge'] is not None else {}
        relevant.update({('continuation',record_key(rec)):rec for rec in blocks if rec['base_sha256']==base_id(base) and rec['edge'] is not None})
        assert {(item['kind'],item['identity']) for item in row['targets']}==set(relevant)
        for item in row['targets']:
            kind=item['kind'];rec=relevant[(kind,item['identity'])]
            target,_=verify_learning(h,rec,Counter()) if kind=='base' else routes.learned_blocks.verify(h,rec,Counter())
            result=answer(target,item['target']);assert result['answer']==a['answer'];child=h._load(rec['edge']['key'])
            assert (item['canonical'] is None)==(child is None)
            if child is not None:
                result=answer(child['cnf'],item['canonical']);assert result['answer']==a['answer']
                if result['answer']:
                    model=lift_learning(h,rec,result['model'],Counter()) if kind=='base' else routes.learned_blocks.lift(h,rec,result['model'])
                    assert holds(node['cnf'],model)
    assert {row['case'] for row in ep['originals']}==set(r['gains'])
    for row in ep['originals']:answer(r['cases'][row['case']]['source'],row['result'])
    assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(path)==before


def learned_obstructions(h,bases,blocks):
    """Certify exhaustion only when all binary variables have both clear traces."""
    rows=[]
    for base in bases:
        records=[base]+[b for b in blocks if b['base_sha256']==base_id(base)]
        if any(b['probing']['status']!='clear' for b in records):continue
        _,expanded=checked_augmentation(h,base,Counter())
        attempts=[a for b in records for a in b['probing']['attempts']]
        covered={a['variable'] for a in attempts}
        if not {abs(l) for c in expanded if len(c)==2 for l in c}<=covered:continue
        binary,outside=certify_exhaustion(expanded,attempts,Counter())
        rows.append(dict(base_sha256=base_id(base),source_sha256=sha_key(base['source']),clauses=len(expanded),
            checked_attempts=len(attempts),binary_variables=binary,outside_variables=outside))
    return rows


def validate(out,test_log):
    started=time.perf_counter();r=json.loads((out/'report.json').read_text());assert r['policy']==POLICY
    with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
        tmp=Path(td);seed=tmp/'seed'
        for name in ('experiments.cnf_probe_window.discover_probes','experiments.cnf_probe_continuation.discover_probes',
                     'experiments.cnf_trace_learning.discover_equivalence_probes','experiments.cnf_learning_continuation.discover_equivalence_probes'):
            stack.enter_context(patch(name,side_effect=AssertionError('new discovery')))
        stack.enter_context(patch.object(BudgetedInventory,'_discover',side_effect=AssertionError('new recognition')))
        parent,*evidence=restore_parent(Path(r['parent']['path']),seed,tmp)
        assert r['cases']==parent['cases'] and r['options']==parent['options'];before=sha(seed)
        h=BudgetedInventory(seed,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']==parent['final_closed']
        saved=read_archive(r['selection']);leaves=frontier(h,routes,evidence[-1],Counter());source=saved['leaf']['source']
        assert leaves==saved['before'] and leaves['leaves'][0]==saved['leaf']
        attempts,_=source_attempts(h,source,Counter());graph=implication_graph(h._load(source)['cnf'],attempts,Counter())
        assert check_graph(graph,saved['graph'],Counter())==saved['graph_conclusions']
        ranked=candidates(h,source,routes,Counter(),candidate_limit=POLICY['candidate_pairs']);assert encode(ranked)==encode(saved['ranked'])
        records=read_archive(r['splits']);assert encode(records)==encode([ranked[0]['record']])
        bases=read_archive(r['learning']);blocks=read_archive(r['blocks']);check_batch(h,source,bases)
        h.close();assert sha(seed)==before
        merged=tmp/'merged';shutil.copyfile(seed,merged);assert set(r['arms'])=={'learning','split'}
        for arm,a in r['arms'].items():
            print(f'cold {arm} arm',flush=True);delta=tmp/f'{arm}-delta';delta_file(a['delta'],delta)
            path=tmp/arm;shutil.copyfile(seed,path);apply_delta(path,delta);assert digests(path)==a['logical_table_digests'];before=sha(path)
            apply_delta(merged,delta);h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
            arm_evidence=additions(evidence,bases,blocks) if arm=='learning' else additions(evidence,splits=records)
            routes=routes_for(h,arm_evidence);check_coverage(h,routes,roots,a,r['baseline_closed']);d=read_archive(a['diagnostics'])
            assert frontier(h,routes,arm_evidence[-1],Counter())==d['frontier']
            if arm=='learning':
                assert learning_targets(h,routes,bases,blocks)==d['learning_targets']
                admitted=check_learning_run(h,bases,blocks,d['result'])
            else:
                assert d['learning_targets'] is None;rows=d['result'];assert len(rows)==len(records);admitted=set()
                for row,rec in zip(rows,records,strict=True):
                    assert row['source']==rec['source'] and not row['skipped_covered']
                    assert len(row['branches'])==2;sets=[set(b['admitted']) for b in row['branches']]
                    assert not sets[0]&sets[1] and set().union(*sets)==set(row['admitted'])
                    assert not admitted&set(row['admitted']);admitted.update(row['admitted'])
                    for branch,edge in zip(row['branches'],rec['edges'],strict=True):assert branch['pending']==(h._load(edge['key']) is None)
            assert sorted(map(sha_key,admitted))==a['admitted_state_sha256'] and len(admitted)<=POLICY['state_limit']
            db=sqlite3.connect(delta)
            for key, in db.execute('SELECT id FROM cnf_patterns_v1'):assert key in admitted and h._load(key) is not None
            db.close();assert not h.admitted;h.close();assert sha(path)==before
        assert digests(merged)==r['logical_table_digests']
        print('cold merged checkpoint and references',flush=True)
        path=tmp/'union';restored,*union_evidence=restore_checkpoint(out/'report.json',path,tmp);assert restored==r;before=sha(path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=routes_for(h,union_evidence)
        check_coverage(h,routes,roots,r,r['baseline_closed'])
        for a in r['arms'].values():assert all(b or not a for a,b in zip(a['final_closed'],r['final_closed'],strict=True))
        d=read_archive(r['diagnostics']);assert frontier(h,routes,union_evidence[-1],Counter())==d['frontier']
        assert learning_targets(h,routes,bases,blocks)==d['learning_targets'] and selection(h,routes,Counter())==d['learning_queue']
        assert children(h,routes,records)==d['children'];check_reference(h,routes,records,bases,blocks,r,parent,tmp)
        obstructions=learned_obstructions(h,bases,blocks)
        assert not h.admitted and h.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';h.close();assert sha(path)==before
    log=test_log.read_text();match=re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log);assert match and int(match[1])>=589
    (out/'full-validation.txt').write_text(log)
    result=dict(report_sha256=sha(out/'report.json'),script_sha256=sha(Path(__file__)),python_tests=int(match[1]),test_log_sha256=sha(out/'full-validation.txt'),
        coverage=sum(r['final_closed']),arm_coverage={name:sum(a['final_closed']) for name,a in r['arms'].items()},gains=r['gains'],
        without_growth=sum(r['without_growth_closed']),reference_nodes=r['reference']['verified_nodes'],preserved_reference_nodes=r['reference']['preserved_nodes'],
        learned_obstructions=obstructions,cold_new_discovery=False,history_bytes_unchanged=True,seconds=time.perf_counter()-started)
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps(result),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--test-log',type=Path,required=True)
    a=p.parse_args();validate(a.output,a.test_log)
