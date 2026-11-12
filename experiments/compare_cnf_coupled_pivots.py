#!/usr/bin/env python3
"""Resume every retained pivot history and test state-capped coupled deviations."""
import argparse
from collections import Counter
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
from experiments.cnf_coupled_pivots import BudgetedInventory,FrontierIndex,search,verify_coupled,coupled_key,lift_pair
from experiments.cnf_pivot_alternatives import covered
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.compare_cnf_frontier_pivots import unpack
from experiments.compare_cnf_pivot_alternatives import TABLES as OLD_TABLES,apply_delta,compressed,replay
from experiments.compare_cnf_retained_plans import sha,audit
from experiments.compare_cnf_clause_mask import table_digest

TABLES=OLD_TABLES+('cnf_coupled_trials_v1',)


def digests(path):
    db=sqlite3.connect(path)
    try:return {t:table_digest(db,t) for t in TABLES}
    finally:db.close()


def restore_seed(suite,path,tmp):
    report_path=Path(f'experiments/results/cnf-frontier-pivots-{suite}/report.json')
    report=json.loads(report_path.read_text());inputs=[dict(path=str(report_path),sha256=sha(report_path))]
    for i,entry in enumerate(report['inputs']):
        assert sha(entry['path'])==entry['sha256'];r=json.loads(Path(entry['path']).read_text())
        if i==0:
            assert sha(r['base_archive'])==r['base_archive_sha256']
            unpack(r['base_archive'],path,r['base_database_sha256'])
        d=r['delta'];assert sha(d['path'])==d['sha256'];unpacked=tmp/f'old-{i}'
        unpack(d['path'],unpacked,d['database_sha256']);apply_delta(path,unpacked)
    for i,r in enumerate(report['results']):
        d=r['delta'];assert sha(d['path'])==d['sha256'];unpacked=tmp/f'new-{i}'
        unpack(d['path'],unpacked,d['database_sha256']);apply_delta(path,unpacked)
    validation_path=Path('experiments/results/cnf-frontier-pivots-validation/validation.json')
    validation=json.loads(validation_path.read_text());union=next(x for x in validation['compatible_unions'] if x['suite']==suite)
    assert union['report_sha256']==sha(report_path)
    db=sqlite3.connect(path)
    assert {t:table_digest(db,t) for t in OLD_TABLES}==union['merged_table_digests']
    db.execute('CREATE TABLE cnf_coupled_trials_v1 (id TEXT PRIMARY KEY,payload TEXT NOT NULL)');db.commit();db.close()
    inputs.append(dict(path=str(validation_path),sha256=sha(validation_path)))
    return report,inputs


def export_delta(seed,history,path):
    db=sqlite3.connect(history);db.execute('ATTACH DATABASE ? AS old',(str(seed),));out=sqlite3.connect(path)
    preserved={};added={}
    try:
        for t in TABLES:
            assert db.execute(f'SELECT count(*) FROM old.{t} o LEFT JOIN main.{t} n ON o.id=n.id WHERE n.id IS NULL OR n.payload!=o.payload').fetchone()[0]==0
            preserved[t]=db.execute(f'SELECT count(*) FROM old.{t}').fetchone()[0]
            out.execute(f'CREATE TABLE {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            rows=db.execute(f'SELECT n.id,n.payload FROM main.{t} n WHERE NOT EXISTS (SELECT 1 FROM old.{t} o WHERE o.id=n.id) ORDER BY n.rowid')
            out.executemany(f'INSERT INTO {t} VALUES (?,?)',rows)
            added[t]=out.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
        out.commit();return preserved,added
    finally:out.close();db.close()


def apply_coupled_delta(history,path):
    db=sqlite3.connect(history);delta=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
    try:
        for t in TABLES:
            db.execute(f'CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            for key,payload in delta.execute(f'SELECT id,payload FROM {t} ORDER BY rowid'):
                old=db.execute(f'SELECT payload FROM {t} WHERE id=?',(key,)).fetchone()
                if old is not None and old!=(payload,):raise ValueError('Conflicting coupled delta payload')
                db.execute(f'INSERT OR IGNORE INTO {t} VALUES (?,?)',(key,payload))
        db.commit()
    finally:delta.close();db.close()


def replay_coupled(h,first_trials):
    successes=set();counts=Counter()
    for key,payload in h.db.execute('SELECT id,payload FROM cnf_coupled_trials_v1'):
        record=json.loads(payload)
        if key!=coupled_key(record):raise ValueError('Incorrect coupled trial identity')
        if verify_coupled(h,record,first_trials,counts):successes.add(record['source'])
    return successes,counts


def endpoints(history,options,records,out,tmp):
    h=AnchoredAdditiveInventory(history,**options);path=tmp/'endpoints';solver=AccountedResidualSolver(path)
    results=[];started=time.perf_counter()
    for r in records:
        if not r['summary']['closed']:continue
        node=h._load(r['source']);child=h._load(r['edge']['key']);a,b=solver.solve(node['cnf']),solver.solve(child['cnf'])
        assert a['answer']==b['answer']
        if b['answer']:
            model={v:b['model'][i] for i,v in enumerate(r['edge']['names'],1)}
            lifted=lift_pair(node['cnf'],r['variables'],model,Counter(),pair_limit=options.get('elimination_pair_limit',64),clause_growth_limit=options['clause_growth_limit'])
            assert holds(node['cnf'],lifted)
        results.append(dict(trial_id=coupled_key(r),source=a,target=b))
    solver.close();h.close();elapsed=time.perf_counter()-started
    before=sha(path);started=time.perf_counter();solver=ResidualSolver(path);verified=0
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
        assert solver._read(key) is not None;verified+=1
    assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(path)==before
    cold=time.perf_counter()-started;archive=out/'endpoints.sqlite3.gz';compressed(path,archive)
    return dict(records=results,seconds=elapsed,cold_seconds=cold,path=str(archive),sha256=sha(archive),
        database_sha256=before,database_bytes=path.stat().st_size,verified_nodes=verified)


def main(out,suite):
    out.mkdir(exist_ok=False);history=out/'working.sqlite3'
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);seed=tmp/'seed';started=time.perf_counter();prior,inputs=restore_seed(suite,seed,tmp)
        restore_seconds=time.perf_counter()-started;options=prior['options'];cases=prior['cases']
        files=set(prior['fingerprints'])|{'experiments/cnf_coupled_pivots.py','experiments/compare_cnf_coupled_pivots.py','solver/test_cnf_coupled_pivots.py'}
        r=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),suite=suite,
            inputs=inputs,fingerprints={p:sha(p) for p in sorted(files)},options=options,cases=cases,
            budgets=dict(route_limit=4,trial_limit=8,state_limit=32),seed_restore_seconds=restore_seconds,
            seed_database_bytes=seed.stat().st_size,seed_database_sha256=sha(seed),seed_table_digests=digests(seed),records=[],limitations=[
            'Resume the complete paid union of both earlier pivot schedules and both ancestor schedules; all failed trials and ordinary proofs remain.',
            'Up to four retained divergent first routes, followed by one interacting second pivot and the unchanged recognizer. Both steps keep the old pair/growth caps.',
            'At most eight new completed coupled trials and 32 distinct newly entered recognizer states per open original, including descendants and unfinished ancestors.',
            'Admission caps do not bound candidate preparation, profile costs, repeated old verification, prior-history memory or total bytes. Budget stops assert no negative semantic result.',
            'Selected development originals and reused controls, not exhaustive order search, independent holdouts, an ordinary SAT speedup or a uniform polynomial bound.'])
        started=time.perf_counter();shutil.copyfile(seed,history);r['clone_seconds']=time.perf_counter()-started
        h=BudgetedInventory(history,**options);h.set_admission_budget(0);started=time.perf_counter();roots=[]
        for case in cases:roots.append(h.inspect(case['source'])['root']['key'])
        successes,counts=replay(h);first_trials={k:json.loads(p) for k,p in h.db.execute('SELECT id,payload FROM cnf_pivot_trials_v1')}
        r['seed_verification_seconds']=time.perf_counter()-started;r['seed_trial_replay_counts']=dict(counts)
        assert not h.admitted
        baseline=[covered(h,k,successes,Counter()) for k in roots]
        assert all(baseline==x['final_closed'] for x in prior['results'])
        index=FrontierIndex(h);known={};total=Counter();new=[]
        for i,root in enumerate(roots):
            h.counts=Counter();h.prepared.counts=Counter();counts=Counter();started=time.perf_counter()
            before=covered(h,root,successes,counts);h.set_admission_budget(0)
            records,stop=([],None) if before else search(h,root,first_trials,known,index,counts,**r['budgets'])
            for record in records:
                key=coupled_key(record);assert key not in known
                with h.db:h.db.execute('INSERT INTO cnf_coupled_trials_v1 VALUES (?,?)',(key,encode(record)))
                known[key]=record
                if verify_coupled(h,record,first_trials,counts):successes.add(record['source'])
            after=covered(h,root,successes,counts)
            row=dict(case=i,closed_before=before,closed_after=after,new_trials=len(records),budget_stop=stop,
                seconds=time.perf_counter()-started,search_counts=dict(counts),inventory_counts=dict(h.counts),
                prepared_counts=dict(h.prepared.counts),admission_counts=dict(h.admission_counts),
                admitted_state_sha256=sorted(hashlib.sha256(k.encode()).hexdigest() for k in h.admitted))
            assert len(h.admitted)<=32 and h.counts.get('inserted_nodes',0)<=len(h.admitted)
            r['records'].append(row);new.extend(records);total.update(counts)
            (out/'checkpoint.json').write_text(encode(r)+'\n')
            if records or stop:print('case',i,'trials',len(records),'states',len(h.admitted),'stopped',bool(stop),'closed',before,after,flush=True)
        started=time.perf_counter();final=[covered(h,k,successes,Counter()) for k in roots]
        r['warm_recomposition_seconds']=time.perf_counter()-started
        r.update(baseline_closed=baseline,final_closed=final,gains=[i for i,(a,b) in enumerate(zip(baseline,final,strict=True)) if b and not a],
            new_trials=len(new),search_counts=dict(total),storage=h.storage(),frontier_index_counts=dict(index.counts),
            frontier_index_nodes=len(index.memo),frontier_index_leaf_entries=sum(len(v) for v in index.memo.values()))
        assert all(b or not a for a,b in zip(baseline,final,strict=True))
        # Selected-frontier analysis is outside the expansion timer.
        started=time.perf_counter();analysis=[];old=set().union(*(set(index.frontier(k)) for k in roots));novel=set()
        for record in new:
            a=index.frontier(record['source']);b=index.frontier(record['edge']['key']);novel.update(set(b)-old)
            analysis.append(dict(trial_sha256=hashlib.sha256(coupled_key(record).encode()).hexdigest(),
                same_frontier=a==b,source_open_literals=index.literals(a),target_open_literals=index.literals(b),
                novel_leaf_count=len(set(b)-old),closed=record['summary']['closed']))
        r['frontier_analysis']=dict(rows=analysis,old_distinct_leaves=len(old),novel_distinct_leaves=len(novel),seconds=time.perf_counter()-started)
        h.close();r['expanded_database_bytes']=history.stat().st_size
        delta=tmp/'delta';started=time.perf_counter();r['preserved_rows'],r['delta_rows']=export_delta(seed,history,delta)
        archive=out/'proof-delta.sqlite3.gz';compressed(delta,archive)
        r['delta']=dict(path=str(archive),sha256=sha(archive),database_sha256=sha(delta),database_bytes=delta.stat().st_size,
            compressed_bytes=archive.stat().st_size,export_seconds=time.perf_counter()-started)
        delta.unlink();unpack(archive,delta,r['delta']['database_sha256']);rebuilt=tmp/'rebuilt';started=time.perf_counter()
        shutil.copyfile(seed,rebuilt);apply_coupled_delta(rebuilt,delta);r['logical_table_digests']=digests(history)
        assert digests(rebuilt)==r['logical_table_digests'];before=sha(rebuilt);apply_coupled_delta(rebuilt,delta);assert sha(rebuilt)==before
        r['rebuild_seconds']=time.perf_counter()-started
        print('complete cold audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,options)
        before=sha(rebuilt);started=time.perf_counter();h=AnchoredAdditiveInventory(rebuilt,**options)
        checked,old_counts=replay(h);first={k:json.loads(p) for k,p in h.db.execute('SELECT id,payload FROM cnf_pivot_trials_v1')}
        pair_success,counts=replay_coupled(h,first);checked.update(pair_success);assert checked==successes
        assert [covered(h,k,checked,Counter()) for k in roots]==final
        h.close();assert sha(rebuilt)==before
        r['trial_replay']=dict(seconds=time.perf_counter()-started,old_counts=dict(old_counts),coupled_counts=dict(counts),bytes_unchanged=True)
        r['endpoints']=endpoints(rebuilt,options,new,out,tmp)
    (out/'report.json').write_text(encode(r)+'\n');(out/'checkpoint.json').unlink();history.unlink()
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],new_trials=len(new),new_nodes=r['delta_rows']['cnf_patterns_v1'],
        budget_stops=sum(x['budget_stop'] is not None for x in r['records']),expansion_seconds=sum(x['seconds'] for x in r['records']))),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path)
    p.add_argument('--suite',choices=('originals','fresh'),default='originals');a=p.parse_args();main(a.output,a.suite)
