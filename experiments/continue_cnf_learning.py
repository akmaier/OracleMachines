#!/usr/bin/env python3
"""Resume later probes on saved learned formulas without reacquiring clauses."""
from collections import Counter
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_frontier_learning import restore_checkpoint as restore_base,control,reference
from experiments.compare_cnf_trace_reuse import read_archive,archive_json
from experiments.compare_cnf_probe_continuation import sha,sha_key,digests,export_delta,apply_delta,compressed,unpack,audit,WithoutGrowth
from experiments.cnf_learning_continuation import ContinuedLearningRoutes,record_key
from experiments.cnf_learning_batch import selection,search
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_target_probe import remaining
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_pattern_inventory import encode

BASE=Path('experiments/results/cnf-frontier-learning/report.json')
FORMAT='learning-batch-v1'


def restore_checkpoint(report_path,path,tmp):
    chain=[];seen=set();current=Path(report_path)
    while current.resolve()!=BASE.resolve():
        if current.resolve() in seen:raise ValueError('Cyclic learning checkpoint lineage')
        seen.add(current.resolve());r=json.loads(current.read_text())
        if r.get('format')!=FORMAT:raise ValueError('Unknown learning checkpoint')
        if sha(r['parent']['path'])!=r['parent']['sha256']:raise ValueError('Changed learning parent')
        for p,digest in r['fingerprints'].items():
            if sha(p)!=digest:raise ValueError('Changed learning implementation')
        chain.append(r);current=Path(r['parent']['path'])
    previous,rewrites,learning,records=restore_base(BASE,path,tmp)
    known={record_key(rec) for rec in records}
    for index,r in enumerate(reversed(chain)):
        if digests(path)!=r['seed_table_digests'] or r['baseline_closed']!=previous['final_closed']:
            raise ValueError('Incorrect learning seed')
        delta=tmp/f'learning-batch-delta-{index}';d=r['delta']
        if sha(d['path'])!=d['sha256']:raise ValueError('Changed learning delta')
        unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
        for entry in read_archive(r['additions']):
            rec=entry['record'];key=record_key(rec)
            if key in known:raise ValueError('Repeated immutable augmented block')
            known.add(key);records.append(rec)
        if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect learning reconstruction')
        previous=r
    return previous,rewrites,learning,records


def target_state(h,routes):
    selected=[];pending=[]
    for rec in routes.learned_blocks.records.values():
        if rec['edge'] is None:continue
        item=dict(source=routes.learned_blocks.bases[rec['base_sha256']]['source'],target=rec['edge']['key'])
        (pending if h._load(item['target']) is None else selected).append(item)
    return dict(selected=selected,pending=pending,remaining=remaining(h,selected,routes,Counter()))


def preserved_reference(seed,path):
    db=sqlite3.connect(path);db.execute('ATTACH DATABASE ? AS seed',(str(seed),))
    count=db.execute('SELECT COUNT(*) FROM seed.cnf_residual_v1').fetchone()[0]
    for row in db.execute('SELECT id,payload FROM seed.cnf_residual_v1 EXCEPT SELECT id,payload FROM main.cnf_residual_v1'):
        raise ValueError('Changed retained reference proof')
    db.close();return count


def run(out,parent_path,policy):
    pipeline=time.perf_counter();out.mkdir(parents=True,exist_ok=True)
    if any(out.iterdir()):raise ValueError('Output already contains work; preserve it and choose another directory')
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';history=tmp/'history';started=time.perf_counter()
        parent,rewrites,learning,old_records=restore_checkpoint(parent_path,seed,tmp)
        r=dict(format=FORMAT,parent=dict(path=str(parent_path),sha256=sha(parent_path)),
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/cnf_learning_batch.py','experiments/continue_cnf_learning.py',
                'solver/test_cnf_learning_batch.py')},options=parent['options'],cases=parent['cases'],policy=policy,
            restore_seconds=time.perf_counter()-started,seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,
            limitations=['Reused development originals and retained learning bases; no independent holdout.',
                'No new clause selection: original clauses and checked learned clauses remain fixed.',
                'Probe pool capped at 64 variables; state admissions bound distinct entered keys, not bytes, CPU or reference solving.',
                'Matched original-source controls isolate propagation only; no equal-cost solver comparison or peak RAM measurement.',
                'Restricted structural closure is distinct from SAT truth and gives no unrestricted polynomial bound.'])
        shutil.copyfile(seed,history);started=time.perf_counter();h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        routes=ContinuedLearningRoutes(h,rewrites,learning,old_records);baseline,_=compose(h,roots,routes,Counter())
        assert baseline==parent['final_closed'];r['baseline_closed']=baseline
        before_selection=selection(h,routes,Counter());r['preparation_seconds']=time.perf_counter()-started
        print(json.dumps(dict(selection=dict(Counter(row['reason'] for row in before_selection)))),flush=True)
        additions=[];counts=Counter();controls=Counter();r['control_seconds']=r['journal_seconds']=0.0
        journal=out/'acquisition.jsonl'
        def save(rec):
            started=time.perf_counter();node,expanded,_=routes.learned_blocks.context(h,rec['base_sha256'],controls)
            entry=dict(record=rec,control=control(node['cnf'],expanded,rec['offset'],controls))
            r['control_seconds']+=time.perf_counter()-started;started=time.perf_counter()
            with journal.open('a') as stream:stream.write(encode(entry)+'\n')
            additions.append(entry);r['journal_seconds']+=time.perf_counter()-started
        h.counts=Counter();h.prepared.counts=Counter();started=time.perf_counter()
        result=search(h,routes,before_selection,counts,save,**policy);r['search_seconds']=time.perf_counter()-started
        started=time.perf_counter();r['additions']=archive_json(out/'additions.json.gz',additions)
        if journal.exists():
            assert [json.loads(line) for line in journal.read_text().splitlines()]==read_archive(r['additions'])
            journal.unlink()
        r['archive_seconds']=time.perf_counter()-started
        r['admitted_state_sha256']=sorted(map(sha_key,h.admitted));r['admission_counts']=dict(h.admission_counts)
        r['inventory_counts']=dict(h.counts);r['prepared_counts']=dict(h.prepared.counts)
        r['discovery_counts']=dict(counts);r['control_counts']=dict(controls)
        started=time.perf_counter();final,plan=compose(h,roots,routes,Counter());verify_plan(h,plan,plan['roots'],routes,Counter())
        assert all(b or not a for a,b in zip(baseline,final,strict=True));r['final_closed']=final
        r['gains']=[i for i,(a,b) in enumerate(zip(baseline,final)) if b and not a]
        r['without_growth_closed'],without=compose(h,roots,WithoutGrowth(routes),Counter())
        verify_plan(h,without,without['roots'],WithoutGrowth(routes),Counter())
        diagnostics=dict(selection_before=before_selection,selection_after=selection(h,routes,Counter()),search=result,targets=target_state(h,routes))
        r['composition_seconds']=time.perf_counter()-started;r['diagnostics']=archive_json(out/'diagnostics.json.gz',diagnostics)
        r['certificate']=archive_json(out/'coverage.json.gz',plan);h.close();r['expanded_database_bytes']=history.stat().st_size
        print(json.dumps(dict(closed=sum(final),gains=r['gains'],blocks=len(additions),admitted=len(r['admitted_state_sha256']),
            statuses=dict(Counter(e['record']['probing']['status'] for e in additions)))),flush=True)
        delta=tmp/'delta';started=time.perf_counter();r['preserved_rows'],r['delta_rows']=export_delta(seed,history,delta)
        compressed(delta,out/'proof-delta.sqlite3.gz');r['delta']=dict(path=str(out/'proof-delta.sqlite3.gz'),sha256=sha(out/'proof-delta.sqlite3.gz'),
            database_sha256=sha(delta),database_bytes=delta.stat().st_size,compressed_bytes=(out/'proof-delta.sqlite3.gz').stat().st_size,
            export_seconds=time.perf_counter()-started)
        r['logical_table_digests']=digests(history);rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,delta)
        assert digests(rebuilt)==r['logical_table_digests'];before=sha(rebuilt);apply_delta(rebuilt,delta);assert sha(rebuilt)==before
        print('cold inventory audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        print('cold routes and retained reference proofs',flush=True);started=time.perf_counter()
        h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0)
        routes=ContinuedLearningRoutes(h,rewrites,learning,old_records+[e['record'] for e in read_archive(r['additions'])])
        verify_plan(h,read_archive(r['certificate']),plan['roots'],routes,Counter());assert compose(h,roots,routes,Counter())[0]==final
        assert selection(h,routes,Counter())==diagnostics['selection_after'] and target_state(h,routes)==diagnostics['targets']
        assert not h.admitted;r['cold_routes']=dict(seconds=time.perf_counter()-started,counts=dict(routes.counts),block_counts=dict(routes.learned_blocks.counts))
        started=time.perf_counter();ep=parent['reference'];assert sha(ep['path'])==ep['sha256']
        unpack(ep['path'],tmp/'reference',ep['database_sha256']);shutil.copyfile(tmp/'reference',tmp/'reference-seed')
        r['reference_seed_seconds']=time.perf_counter()-started;r['reference']=reference(h,routes,r,out,tmp)
        r['reference']['preserved_nodes']=preserved_reference(tmp/'reference-seed',tmp/'reference')
        h.close();assert sha(rebuilt)==before
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],added=r['delta_rows'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path,default=BASE)
    for name,default in [('step-limit',144),('state-limit',128),('target-limit',32)]:p.add_argument('--'+name,type=int,default=default)
    a=p.parse_args();run(a.output,a.parent,{name:getattr(a,name) for name in ('step_limit','state_limit','target_limit')})
