#!/usr/bin/env python3
"""Matched ancestor schedules from the exact union of both paid pivot histories."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_frontier_pivots import search
from experiments.cnf_pivot_alternatives import covered,verify_trial
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_additive_elimination import lift_additive_elimination
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.compare_cnf_pivot_alternatives import TABLES,apply_delta,compressed,trial_key,replay
from experiments.compare_cnf_retained_plans import sha,audit
from experiments.compare_cnf_clause_mask import table_digest


def unpack(archive,path,digest):
    with gzip.open(archive,'rb') as src,path.open('wb') as dst:shutil.copyfileobj(src,dst)
    assert sha(path)==digest


def digests(path):
    with sqlite3.connect(path) as db:return {t:table_digest(db,t) for t in TABLES}


def delta_from_seed(seed,history,path):
    """Export only new rows in every table, including trials; reject old edits."""
    db=sqlite3.connect(history);db.execute('ATTACH DATABASE ? AS old',(str(seed),))
    delta=sqlite3.connect(path);preserved={};added={}
    for table in TABLES:
        changed=db.execute(f'SELECT count(*) FROM old.{table} o LEFT JOIN main.{table} n ON o.id=n.id WHERE n.id IS NULL OR n.payload!=o.payload').fetchone()[0]
        if changed:raise ValueError('Changed or missing prior rows')
        preserved[table]=db.execute(f'SELECT count(*) FROM old.{table}').fetchone()[0]
        delta.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        rows=db.execute(f'SELECT n.id,n.payload FROM main.{table} n WHERE NOT EXISTS (SELECT 1 FROM old.{table} o WHERE o.id=n.id) ORDER BY n.rowid')
        delta.executemany(f'INSERT INTO {table} VALUES (?,?)',rows)
        added[table]=delta.execute(f'SELECT count(*) FROM {table}').fetchone()[0]
    delta.commit();delta.close();db.close();return preserved,added


def frontier_analysis(h,roots,records):
    """Read-only selected-frontier comparison after the measured expansion."""
    cache={}
    def frontier(key):
        if key in cache:return cache[key]
        n=h._load(key);result=Counter()
        if n['summary']['closed']:pass
        elif n['kind']=='unresolved':result[key]=1
        elif n['kind']=='and':
            for e in n['edges']:result.update(frontier(e['key']))
        elif n['kind']=='or':
            for e in n['alternatives'][n['selected']]['edges']:result.update(frontier(e['key']))
        elif 'edge' in n:result.update(frontier(n['edge']['key']))
        else:raise ValueError('Unknown open node')
        cache[key]=result;return result
    old=set().union(*(set(frontier(root)) for root in roots));novel=set();counts=Counter();rows=[]
    for record in records:
        a,b=frontier(record['source']),frontier(record['edge']['key'])
        before=sum(h._load(k)['profile']['shape']['literals']*n for k,n in a.items())
        after=sum(h._load(k)['profile']['shape']['literals']*n for k,n in b.items())
        new=set(b)-old;novel.update(new);counts['same_selected_frontier']+=a==b
        counts['novel_frontier_trials']+=bool(new);counts['fewer_open_literals']+=after<before
        counts['more_open_literals']+=after>before;counts['closed_targets']+=record['summary']['closed']
        rows.append(dict(trial_sha256=hashlib.sha256(trial_key(record).encode()).hexdigest(),
            same_selected_frontier=a==b,novel_leaf_count=len(new),source_open_literals=before,target_open_literals=after))
    return dict(counts=dict(counts),old_distinct_leaves=len(old),novel_distinct_leaves=len(novel),trials=rows)


def endpoint_checks(history,options,records,output,tmp):
    h=AnchoredAdditiveInventory(history,**options);path=tmp/'endpoints.db';solver=AccountedResidualSolver(path)
    endpoints=[];started=time.perf_counter()
    for record in records:
        if not record['summary']['closed']:continue
        node=h._load(record['source']);child=h._load(record['edge']['key'])
        a,b=solver.solve(node['cnf']),solver.solve(child['cnf']);assert a['answer']==b['answer']
        if b['answer']:
            model={v:b['model'][i] for i,v in enumerate(record['edge']['names'],1)}
            lifted=lift_additive_elimination(node['cnf'],dict(variable=record['variable']),model,Counter(),
                pair_limit=options.get('elimination_pair_limit',64),clause_growth_limit=options['clause_growth_limit'])
            assert holds(node['cnf'],lifted)
        endpoints.append(dict(trial_id=trial_key(record),source=a,target=b))
    h.close();solver.close();seconds=time.perf_counter()-started
    before=sha(path);started=time.perf_counter();solver=ResidualSolver(path);verified=0
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
        assert solver._read(key) is not None;verified+=1
    assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(path)==before
    cold=time.perf_counter()-started;archive=output/'endpoints.sqlite3.gz';compressed(path,archive)
    return dict(records=endpoints,seconds=seconds,cold_seconds=cold,verified_nodes=verified,
        path=str(archive),sha256=sha(archive),database_sha256=before,database_bytes=path.stat().st_size)


def run_policy(seed,options,cases,policy,out):
    out.mkdir();history=out/'working.sqlite3';started=time.perf_counter();shutil.copyfile(seed,history)
    report=dict(policy=policy,clone_seconds=time.perf_counter()-started,records=[])
    h=AnchoredAdditiveInventory(history,**options);roots=[];started=time.perf_counter()
    for case in cases:roots.append(h.inspect(case['source'])['root']['key'])
    successes,counts=replay(h)
    known={key:json.loads(p) for key,p in h.db.execute('SELECT id,payload FROM cnf_pivot_trials_v1')}
    report['base_verification_seconds']=time.perf_counter()-started
    report['base_trial_replay_counts']=dict(counts);report['base_trials']=len(known)
    baseline=[covered(h,key,successes,Counter()) for key in roots];new_records=[];total=Counter()
    for i,root in enumerate(roots):
        counts=Counter();h.counts=Counter();h.prepared.counts=Counter();started=time.perf_counter()
        before=covered(h,root,successes,counts)
        records=[] if before else search(h,root,counts,known,policy=policy,ancestor_limit=4,trial_limit=8)
        for record in records:
            key=trial_key(record);assert key not in known
            with h.db:h.db.execute('INSERT INTO cnf_pivot_trials_v1 VALUES (?,?)',(key,encode(record)))
            known[key]=record
            if verify_trial(h,record,counts):successes.add(record['source'])
        after=covered(h,root,successes,counts);new_records.extend(records);total.update(counts)
        report['records'].append(dict(case=i,closed_before=before,closed_after=after,new_trials=len(records),
            seconds=time.perf_counter()-started,search_counts=dict(counts),inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts)))
        (out/'checkpoint.json').write_text(encode(report)+'\n')
        if records:print(policy,'case',i,'new trials',len(records),'closed',before,after,flush=True)
    started=time.perf_counter();final=[covered(h,key,successes,Counter()) for key in roots]
    report['warm_recomposition_seconds']=time.perf_counter()-started
    report.update(baseline_closed=baseline,final_closed=final,search_counts=dict(total),new_trials=len(new_records),
        total_trials=len(known),successful_source_count=len(successes),storage=h.storage(),
        gains=[i for i,(a,b) in enumerate(zip(baseline,final,strict=True)) if b and not a])
    assert all(b or not a for a,b in zip(baseline,final,strict=True))
    started=time.perf_counter();report['frontier_analysis']=frontier_analysis(h,roots,new_records)
    report['frontier_analysis_seconds']=time.perf_counter()-started;h.close()
    report['expanded_database_bytes']=history.stat().st_size
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);delta=tmp/'delta';started=time.perf_counter()
        report['preserved_rows'],report['delta_rows']=delta_from_seed(seed,history,delta)
        archive=out/'proof-delta.sqlite3.gz';compressed(delta,archive)
        report['delta']=dict(path=str(archive),sha256=sha(archive),database_sha256=sha(delta),database_bytes=delta.stat().st_size,
            compressed_bytes=archive.stat().st_size,export_compress_seconds=time.perf_counter()-started)
        delta.unlink();unpack(archive,delta,report['delta']['database_sha256'])
        rebuilt=tmp/'rebuilt';started=time.perf_counter();shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,delta)
        report['logical_table_digests']=digests(history);assert report['logical_table_digests']==digests(rebuilt)
        before=sha(rebuilt);apply_delta(rebuilt,delta);assert sha(rebuilt)==before
        report['rebuild_verify_seconds']=time.perf_counter()-started
        print(policy,'complete cold audit',flush=True);report['audit']=audit(rebuilt,AnchoredAdditiveInventory,options)
        before=sha(rebuilt);started=time.perf_counter();h=AnchoredAdditiveInventory(rebuilt,**options)
        checked,counts=replay(h);assert checked==successes
        assert [covered(h,r,checked,Counter()) for r in roots]==final
        h.close();assert sha(rebuilt)==before
        report['trial_replay']=dict(seconds=time.perf_counter()-started,counts=dict(counts),bytes_unchanged=True)
        report['endpoints']=endpoint_checks(rebuilt,options,new_records,out,tmp)
    (out/'report.json').write_text(encode(report)+'\n');(out/'checkpoint.json').unlink();history.unlink()
    print(json.dumps(dict(policy=policy,closed=sum(final),gains=report['gains'],new_trials=len(new_records),
        expansion_seconds=sum(r['seconds'] for r in report['records']),delta_bytes=report['delta']['database_bytes'])),flush=True)
    return report


def main(out,suite,reverse=False):
    out.mkdir(exist_ok=False);reports=[];inputs=[]
    for name in ('pivot-alternatives','interacting-pivots'):
        path=Path(f'experiments/results/cnf-{name}-{suite}/report.json');reports.append(json.loads(path.read_text()))
        inputs.append(dict(path=str(path),sha256=sha(path)))
    prior=reports[0];assert all(r['options']==prior['options'] and r['cases']==prior['cases'] for r in reports)
    validation_path=Path('experiments/results/cnf-pivot-alternatives-validation/validation.json')
    validation=json.loads(validation_path.read_text());union=next(r for r in validation['compatible_unions'] if r['suite']==suite)
    files=set().union(*(set(r['fingerprints']) for r in reports))|{
        'experiments/cnf_frontier_pivots.py','experiments/compare_cnf_frontier_pivots.py','solver/test_cnf_frontier_pivots.py'}
    result=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),suite=suite,
        inputs=inputs,union_validation=dict(path=str(validation_path),sha256=sha(validation_path)),
        fingerprints={p:sha(p) for p in sorted(files)},options=prior['options'],cases=prior['cases'],
        budgets=dict(ancestor_limit=4,new_trial_limit=8),results=[],limitations=[
        'Both modes start from the same paid base plus both prior pivot deltas, including all failed trials. Preparation, verification and export are separately charged.',
        'Frontier order uses longest selected open distance to a terminal; it scans the entire selected open DAG. Only the first four elimination nodes in that order are tried.',
        'Eight NEW trial recognitions per open input, with prior exact trials checked and skipped. Not the earlier eight-attempt comparison and not a total descendant-state bound.',
        'Both modes rank interacting pivots first; no semantic pruning or coupled-deviation search. The previous recognizer handles each target.',
        'Selected/reused development inputs and single ordered runs; no untouched holdout, peak RSS, faster ordinary SAT solver or unrestricted polynomial bound.'])
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);seed=tmp/'seed';started=time.perf_counter()
        assert sha(prior['base_archive'])==prior['base_archive_sha256']
        unpack(prior['base_archive'],seed,prior['base_database_sha256'])
        for i,r in enumerate(reports):
            delta=tmp/f'delta-{i}';assert sha(r['delta']['path'])==r['delta']['sha256']
            unpack(r['delta']['path'],delta,r['delta']['database_sha256']);apply_delta(seed,delta)
        result['seed_restore_merge_seconds']=time.perf_counter()-started
        result['seed_table_digests']=digests(seed);assert result['seed_table_digests']==union['merged_table_digests']
        result['seed_database_bytes']=seed.stat().st_size;result['seed_database_sha256']=sha(seed)
        modes=('frontier','early') if reverse else ('early','frontier')
        for mode in modes:
            result['results'].append(run_policy(seed,prior['options'],prior['cases'],mode,out/mode))
            (out/'checkpoint.json').write_text(encode(result)+'\n')
    assert result['results'][0]['baseline_closed']==result['results'][1]['baseline_closed']==prior['final_closed']
    (out/'report.json').write_text(encode(result)+'\n');(out/'checkpoint.json').unlink()


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path)
    ap.add_argument('--suite',choices=('originals','fresh'),default='originals');ap.add_argument('--reverse',action='store_true')
    args=ap.parse_args();main(args.output,args.suite,args.reverse)
