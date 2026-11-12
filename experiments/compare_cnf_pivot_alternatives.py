#!/usr/bin/env python3
"""Incremental bounded pivot deviations, preserving the paid original proof graph."""
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
from experiments.cnf_pivot_alternatives import search,covered,verify_trial
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_additive_elimination import lift_additive_elimination
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.compare_cnf_retained_plans import sha,audit,check_old_rows
from experiments.compare_cnf_clause_mask import table_digest

TABLES=('cnf_patterns_v1','cnf_pattern_sources_v1','cnf_residual_v1','cnf_pivot_trials_v1')


def compressed(source,target):
    with Path(source).open('rb') as src,Path(target).open('wb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as dst:shutil.copyfileobj(src,dst)


def write_delta(base,history,path):
    db=sqlite3.connect(history);db.execute('ATTACH DATABASE ? AS old',(str(base),));delta=sqlite3.connect(path);counts={}
    for table in TABLES:
        delta.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        if table=='cnf_pivot_trials_v1':query=f'SELECT id,payload FROM main.{table} ORDER BY rowid'
        else:query=f'SELECT n.id,n.payload FROM main.{table} n WHERE NOT EXISTS (SELECT 1 FROM old.{table} o WHERE o.id=n.id) ORDER BY n.rowid'
        count=0
        for row in db.execute(query):delta.execute(f'INSERT INTO {table} VALUES (?,?)',row);count+=1
        counts[table]=count
    delta.commit();delta.close();db.close();return counts


def apply_delta(history,delta_path):
    db=sqlite3.connect(history);delta=sqlite3.connect(f'file:{delta_path}?mode=ro',uri=True)
    for table in TABLES:
        db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
        for key,payload in delta.execute(f'SELECT id,payload FROM {table} ORDER BY rowid'):
            old=db.execute(f'SELECT payload FROM {table} WHERE id=?',(key,)).fetchone()
            if old is not None and old!=(payload,):raise ValueError('Conflicting persistent delta row')
            db.execute(f'INSERT OR IGNORE INTO {table} VALUES (?,?)',(key,payload))
    db.commit();delta.close();db.close()


def trial_key(record):return encode([record['source'],record['variable']])


def replay(h):
    successes=set();counts=Counter()
    for key,payload in h.db.execute('SELECT id,payload FROM cnf_pivot_trials_v1'):
        record=json.loads(payload)
        if key!=trial_key(record):raise ValueError('Incorrect persisted trial identity')
        if verify_trial(h,record,counts):successes.add(record['source'])
    return successes,counts


def main(out,suite='originals'):
    out.mkdir(exist_ok=False);input_path=Path('experiments/results/cnf-additive-elimination-'+suite+'/report.json')
    prior=json.loads(input_path.read_text());baseline=next(r for r in prior['results'] if r['mode']=='add_two')
    options=baseline['configuration'];cases=prior['cases'];source_archive=Path(baseline['archive_path'])
    assert sha(source_archive)==baseline['archive_sha256']
    files=set(prior['fingerprints'])|{'experiments/cnf_anchored_subsets.py','experiments/cnf_pivot_alternatives.py',
        'experiments/compare_cnf_pivot_alternatives.py','solver/test_cnf_pivot_alternatives.py','solver/fixtures/pivot-alternatives.json'}
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        suite=suite,input_report=str(input_path),input_report_sha256=sha(input_path),base_archive=str(source_archive),base_archive_sha256=sha(source_archive),
        base_database_sha256=baseline['database_sha256'],base_database_bytes=baseline['database_bytes'],
        options=options,budgets=dict(ancestor_limit=4,trial_limit=8),cases=cases,
        fingerprints={p:sha(p) for p in sorted(files)},records=[],limitations=[
        f'Incremental expansion from an already paid {baseline["database_bytes"]:,}-byte archive, not a fresh baseline comparison.',
        'At most four selected open elimination ancestors and eight full target recognitions per previously unresolved original; all candidate/ranking work is additional.',
        'One projection deviation followed by the existing bounded recognizer; not exhaustive order search or a total time/memory bound.',
        'All old rows and failed targets persist. New proof rows are archived as a base-bound delta rather than a duplicate base.',
        'Closure is recognized structural coverage, not SAT or UNSAT. Final composition may reuse all checked old conditioning alternatives.',
        'Selected old failures, not an untouched holdout; no full-corpus coverage, uniform polynomial SAT or peak RSS claim.'])
    # Retain the working file if interrupted; remove only after delta rebuild,
    # complete cold checking and persistent endpoint checks have succeeded.
    history=out/'working.sqlite3'
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);base=tmp/'base.db';started=time.perf_counter()
        with gzip.open(source_archive,'rb') as src,base.open('wb') as dst:shutil.copyfileobj(src,dst)
        assert sha(base)==baseline['database_sha256'];shutil.copyfile(base,history)
        report['restore_clone_seconds']=time.perf_counter()-started
        h=AnchoredAdditiveInventory(history,**options);roots=[];started=time.perf_counter()
        for i,case in enumerate(cases):
            found=h.inspect(case['source']);roots.append(found['root']['key'])
            assert hashlib.sha256(roots[-1].encode()).hexdigest()==baseline['records'][i]['root_sha256']
            assert found['summary']==baseline['records'][i]['summary']
        report['base_verification_seconds']=time.perf_counter()-started
        h.db.execute('CREATE TABLE cnf_pivot_trials_v1 (id TEXT PRIMARY KEY,payload TEXT NOT NULL)');h.db.commit()
        successes=set();trials=[];total_counts=Counter()
        for i,(case,root) in enumerate(zip(cases,roots,strict=True)):
            counts=Counter();h.counts=Counter();h.prepared.counts=Counter();started=time.perf_counter()
            before=covered(h,root,successes,counts)
            records=[] if before else search(h,root,counts,**report['budgets'])
            for record in records:
                key=trial_key(record);payload=encode(record)
                with h.db:
                    old=h.db.execute('SELECT payload FROM cnf_pivot_trials_v1 WHERE id=?',(key,)).fetchone()
                    if old is not None and old!=(payload,):raise ValueError('Changed persisted trial')
                    h.db.execute('INSERT OR IGNORE INTO cnf_pivot_trials_v1 VALUES (?,?)',(key,payload))
                if verify_trial(h,record,counts):successes.add(record['source'])
                trials.append(record)
            after=covered(h,root,successes,counts)
            row=dict(case=i,original_case=case.get('original_case',i),baseline_closed=baseline['records'][i]['summary']['closed'],
                closed_before_search=before,closed_after_search=after,trial_count=len(records),seconds=time.perf_counter()-started,
                search_counts=dict(counts),inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts))
            total_counts.update(counts);report['records'].append(row)
            (out/'checkpoint.json').write_text(encode(report)+'\n')
            if records:print('case',i,'trials',len(records),'closed',before,after,'successful nodes',len(successes),flush=True)
        started=time.perf_counter();final=[covered(h,r,successes,Counter()) for r in roots]
        report['warm_recomposition_seconds']=time.perf_counter()-started
        report['final_closed']=final;report['successful_source_count']=len(successes);report['search_counts']=dict(total_counts)
        report['trials_attempted']=len(trials);report['unique_trials']=h.db.execute('SELECT count(*) FROM cnf_pivot_trials_v1').fetchone()[0]
        report['storage']=h.storage();h.close()
        started=time.perf_counter();report['old_rows_preserved']=check_old_rows(base,history);report['preservation_seconds']=time.perf_counter()-started
        delta=tmp/'delta.db';started=time.perf_counter();report['delta_rows']=write_delta(base,history,delta)
        archive=out/'proof-delta.sqlite3.gz';compressed(delta,archive)
        report['delta']=dict(path=str(archive),sha256=sha(archive),database_sha256=sha(delta),database_bytes=delta.stat().st_size,
            compressed_bytes=archive.stat().st_size,write_compress_seconds=time.perf_counter()-started)
        report['expanded_database_bytes']=history.stat().st_size
        # Rebuild from the emitted compressed delta, with no working-file dependence.
        delta.unlink()
        with gzip.open(archive,'rb') as src,delta.open('wb') as dst:shutil.copyfileobj(src,dst)
        assert sha(delta)==report['delta']['database_sha256']
        rebuilt=tmp/'rebuilt.db';started=time.perf_counter();shutil.copyfile(base,rebuilt);apply_delta(rebuilt,delta)
        a=sqlite3.connect(history);b=sqlite3.connect(rebuilt);digests={}
        for table in TABLES:
            digests[table]=table_digest(a,table);assert digests[table]==table_digest(b,table)
        a.close();b.close();report['logical_table_digests']=digests;report['rebuild_comparison_seconds']=time.perf_counter()-started
        print('delta rebuilt; complete cold audit',flush=True)
        report['audit']=audit(rebuilt,AnchoredAdditiveInventory,options)
        before=sha(rebuilt);started=time.perf_counter();h=AnchoredAdditiveInventory(rebuilt,**options)
        checked_successes,check_counts=replay(h);assert checked_successes==successes
        assert [covered(h,r,checked_successes,Counter()) for r in roots]==final
        h.close();assert sha(rebuilt)==before
        report['trial_replay']=dict(seconds=time.perf_counter()-started,counts=dict(check_counts),bytes_unchanged=True)
        # Independent source/target SAT results are acquired only for successful
        # replacement edges. All failed edges still undergo full projection checking.
        h=AnchoredAdditiveInventory(rebuilt,**options);reference=tmp/'endpoints.db';solver=AccountedResidualSolver(reference)
        endpoints=[];started=time.perf_counter()
        for record in {trial_key(r):r for r in trials if r['summary']['closed']}.values():
            node=h._load(record['source']);child=h._load(record['edge']['key'])
            source_result,target_result=solver.solve(node['cnf']),solver.solve(child['cnf'])
            assert source_result['answer']==target_result['answer']
            if target_result['answer']:
                model={v:target_result['model'][i] for i,v in enumerate(record['edge']['names'],1)}
                lifted=lift_additive_elimination(node['cnf'],dict(variable=record['variable']),model,Counter(),
                    pair_limit=options.get('elimination_pair_limit',64),clause_growth_limit=options['clause_growth_limit'])
                assert holds(node['cnf'],lifted)
            endpoints.append(dict(trial_id=trial_key(record),source=source_result,target=target_result))
        h.close();solver.close();report['endpoint_seconds']=time.perf_counter()-started
        before=sha(reference);started=time.perf_counter();solver=ResidualSolver(reference);verified=0
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
            assert solver._read(key) is not None;verified+=1
        assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(reference)==before
        cold_seconds=time.perf_counter()-started;endpoint_archive=out/'endpoints.sqlite3.gz';started=time.perf_counter();compressed(reference,endpoint_archive)
        report['endpoints']=dict(records=endpoints,path=str(endpoint_archive),sha256=sha(endpoint_archive),database_sha256=before,
            database_bytes=reference.stat().st_size,verified_nodes=verified,cold_seconds=cold_seconds,compression_seconds=time.perf_counter()-started)
    report['gains']=[i for i,(now,old) in enumerate(zip(final,baseline['records'],strict=True)) if now and not old['summary']['closed']]
    assert all(now or not old['summary']['closed'] for now,old in zip(final,baseline['records'],strict=True))
    (out/'report.json').write_text(encode(report)+'\n');(out/'checkpoint.json').unlink();history.unlink()
    print(json.dumps(dict(closed=sum(final),gains=report['gains'],successful_nodes=len(successes),trials=len(trials),
        expansion_seconds=sum(r['seconds'] for r in report['records']),delta_bytes=report['delta']['database_bytes'])),flush=True)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path)
    ap.add_argument('--suite',choices=('originals','fresh'),default='originals');args=ap.parse_args()
    main(args.output,args.suite)
