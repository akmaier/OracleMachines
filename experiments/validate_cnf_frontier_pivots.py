#!/usr/bin/env python3
"""Validate matched frontier discovery evidence and preserve its compatible union."""
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_frontier_pivots import unpack,digests
from experiments.compare_cnf_pivot_alternatives import TABLES,apply_delta,trial_key
from experiments.compare_cnf_retained_plans import sha


def main(out):
    out.mkdir(exist_ok=False);evidence=[];unions=[]
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        for suite,size in [('originals',83),('fresh',96)]:
            directory=Path(f'experiments/results/cnf-frontier-pivots-{suite}')
            rp=directory/'report.json';r=json.loads(rp.read_text())
            assert r['source_commit'].startswith('691e52a') and len(r['cases'])==size
            assert r['suite']==suite and r['budgets']==dict(ancestor_limit=4,new_trial_limit=8)
            for path,digest in r['fingerprints'].items():assert sha(path)==digest,path
            assert sha(r['union_validation']['path'])==r['union_validation']['sha256']
            seed=tmp/(suite+'-seed')
            for i,entry in enumerate(r['inputs']):
                assert sha(entry['path'])==entry['sha256'];old=json.loads(Path(entry['path']).read_text())
                assert r['options']==old['options'] and r['cases']==old['cases']
                if i==0:
                    assert sha(old['base_archive'])==old['base_archive_sha256']
                    unpack(old['base_archive'],seed,old['base_database_sha256'])
                delta=tmp/(suite+'-input-'+str(i));d=old['delta'];assert sha(d['path'])==d['sha256']
                unpack(d['path'],delta,d['database_sha256']);apply_delta(seed,delta)
            assert digests(seed)==r['seed_table_digests'] and sha(seed)==r['seed_database_sha256']
            assert seed.stat().st_size==r['seed_database_bytes']
            merged=tmp/(suite+'-merged');shutil.copyfile(seed,merged);overlap=Counter();mode_reports=[]
            for result in r['results']:
                mode=result['policy'];assert mode in ('early','frontier')
                assert json.loads((directory/mode/'report.json').read_text())==result
                assert len(result['records'])==size and result['baseline_closed']==old['final_closed']
                assert all(row['new_trials']<=8 for row in result['records'])
                assert result['new_trials']==sum(row['new_trials'] for row in result['records'])
                assert result['gains']==[i for i,(a,b) in enumerate(zip(result['baseline_closed'],result['final_closed'],strict=True)) if b and not a]
                assert all(b or not a for a,b in zip(result['baseline_closed'],result['final_closed'],strict=True))
                delta=tmp/(suite+'-'+mode+'-delta');d=result['delta'];assert sha(d['path'])==d['sha256']
                unpack(d['path'],delta,d['database_sha256']);assert delta.stat().st_size==d['database_bytes']
                history=tmp/(suite+'-'+mode);shutil.copyfile(seed,history);apply_delta(history,delta)
                before=sha(history);apply_delta(history,delta);assert sha(history)==before
                assert digests(history)==result['logical_table_digests']
                with sqlite3.connect(delta) as db,sqlite3.connect(merged) as union:
                    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                    for table in TABLES:
                        assert db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==result['delta_rows'][table]
                        assert result['preserved_rows'][table]==r['seed_table_digests'][table]['rows']
                        assert result['logical_table_digests'][table]['rows']==result['preserved_rows'][table]+result['delta_rows'][table]
                        for key,payload in db.execute(f'SELECT id,payload FROM {table}'):
                            previous=union.execute(f'SELECT payload FROM {table} WHERE id=?',(key,)).fetchone()
                            if previous is not None:assert previous==(payload,);overlap[table]+=1
                    trials=[json.loads(p) for k,p in db.execute('SELECT id,payload FROM cnf_pivot_trials_v1')]
                    for key,payload in db.execute('SELECT id,payload FROM cnf_pivot_trials_v1'):
                        assert trial_key(json.loads(payload))==key
                assert len(trials)==result['new_trials']==result['delta_rows']['cnf_pivot_trials_v1']
                assert result['total_trials']==result['base_trials']+result['new_trials']
                assert result['base_trials']==r['seed_table_digests']['cnf_pivot_trials_v1']['rows']
                assert result['trial_replay']['counts']['verified_trials']==result['total_trials']
                assert result['trial_replay']['bytes_unchanged'] and result['audit']['bytes_unchanged']
                for field,table in [('nodes','cnf_patterns_v1'),('sources','cnf_pattern_sources_v1'),('residuals','cnf_residual_v1')]:
                    assert result['audit'][field]==result['logical_table_digests'][table]['rows']
                assert result['delta_rows']['cnf_pattern_sources_v1']==result['delta_rows']['cnf_residual_v1']==0
                analysis=result['frontier_analysis'];assert len(analysis['trials'])==len(trials)
                assert analysis['counts'].get('same_selected_frontier',0)==sum(t['same_selected_frontier'] for t in analysis['trials'])
                assert analysis['counts'].get('closed_targets',0)==sum(t['summary']['closed'] for t in trials)
                ep=result['endpoints'];assert sha(ep['path'])==ep['sha256'];path=tmp/(suite+'-'+mode+'-endpoints')
                unpack(ep['path'],path,ep['database_sha256'])
                with sqlite3.connect(path) as db:assert db.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0]==ep['verified_nodes']
                assert {t['trial_id'] for t in ep['records']}=={trial_key(t) for t in trials if t['summary']['closed']}
                apply_delta(merged,delta);mode_reports.append(result)
                evidence.append(dict(suite=suite,policy=mode,report_sha256=sha(directory/mode/'report.json'),
                    closed=sum(result['final_closed']),new_trials=result['new_trials'],delta_sha256=d['sha256']))
            assert {a['policy'] for a in mode_reports}=={'early','frontier'} and len(mode_reports)==2
            union=digests(merged)
            for table in TABLES:
                assert union[table]['rows']==r['seed_table_digests'][table]['rows']+sum(m['delta_rows'][table] for m in mode_reports)-overlap[table]
            with sqlite3.connect(merged) as db:assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            unions.append(dict(suite=suite,report_sha256=sha(rp),identical_overlap_rows=dict(overlap),merged_table_digests=union,
                limitation='Each constituent passed full cold and trial checking; union checks immutable payload agreement, logical row counts and SQLite integrity, not an extra full merged cold replay.'))
    tests=Path('/tmp/oraclemachines-frontier-final-tests.log').read_text()
    assert re.search(r'Ran 531 tests in [0-9.]+s\s+OK',tests)
    (out/'full-validation.txt').write_text(tests.rstrip()+'\n')
    subprocess.run(['git','diff','--exit-code','16fdf79','--','formal','paper'],check=True,capture_output=True)
    result=dict(script_sha256=sha(Path(__file__)),evidence=evidence,compatible_unions=unions,python_tests=531,
        unchanged_paper_and_formal_since='16fdf79')
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main(Path(sys.argv[1]))
