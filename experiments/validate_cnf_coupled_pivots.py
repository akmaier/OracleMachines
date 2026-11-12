#!/usr/bin/env python3
"""Validate retained coupled trials, admission accounting and full reconstruction."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_coupled_pivots import TABLES,restore_seed,apply_coupled_delta,digests
from experiments.compare_cnf_frontier_pivots import unpack
from experiments.compare_cnf_retained_plans import sha
from experiments.cnf_coupled_pivots import coupled_key
from experiments.cnf_coupled_pivots import project_pair
from collections import Counter


def main(out):
    out.mkdir(exist_ok=False);evidence=[];analyses=[]
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        for suite,size in [('originals',83),('fresh',96)]:
            rp=Path(f'experiments/results/cnf-coupled-pivots-{suite}/report.json');r=json.loads(rp.read_text())
            assert r['source_commit'].startswith('b79c757') and r['suite']==suite and len(r['cases'])==size
            assert r['budgets']==dict(route_limit=4,trial_limit=8,state_limit=32)
            for p,digest in r['fingerprints'].items():assert sha(p)==digest,p
            for entry in r['inputs']:assert sha(entry['path'])==entry['sha256']
            seed=tmp/(suite+'-seed');prior,inputs=restore_seed(suite,seed,tmp)
            assert inputs==r['inputs'] and r['options']==prior['options'] and r['cases']==prior['cases']
            assert digests(seed)==r['seed_table_digests'] and sha(seed)==r['seed_database_sha256']
            assert seed.stat().st_size==r['seed_database_bytes']
            assert len(r['records'])==size and all(r['baseline_closed']==x['final_closed'] for x in prior['results'])
            assert r['gains']==[i for i,(a,b) in enumerate(zip(r['baseline_closed'],r['final_closed'],strict=True)) if b and not a]
            assert all(b or not a for a,b in zip(r['baseline_closed'],r['final_closed'],strict=True))
            admitted=set()
            for i,row in enumerate(r['records']):
                assert row['case']==i and row['new_trials']<=8
                keys=row['admitted_state_sha256'];assert len(keys)==len(set(keys))<=32
                assert len(keys)==row['admission_counts'].get('entered_states',0)
                assert row['inventory_counts'].get('inserted_nodes',0)<=len(keys)
                if row['budget_stop'] is not None:
                    assert row['budget_stop']['reason']=='admission_limit' and len(keys)==32
                    assert row['admission_counts']['denied_states']==1
                else:assert not row['admission_counts'].get('denied_states',0)
                admitted.update(keys)
            delta=tmp/(suite+'-delta');d=r['delta'];assert sha(d['path'])==d['sha256']
            unpack(d['path'],delta,d['database_sha256']);assert delta.stat().st_size==d['database_bytes']
            rebuilt=tmp/(suite+'-rebuilt');shutil.copyfile(seed,rebuilt);apply_coupled_delta(rebuilt,delta)
            assert digests(rebuilt)==r['logical_table_digests'];before=sha(rebuilt);apply_coupled_delta(rebuilt,delta);assert sha(rebuilt)==before
            db=sqlite3.connect(rebuilt);dd=sqlite3.connect(delta)
            assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            for t in TABLES:
                count=dd.execute(f'SELECT count(*) FROM {t}').fetchone()[0];assert count==r['delta_rows'][t]
                assert r['preserved_rows'][t]==r['seed_table_digests'][t]['rows']
                assert r['logical_table_digests'][t]['rows']==count+r['preserved_rows'][t]
            for key, in dd.execute('SELECT id FROM cnf_patterns_v1'):
                assert hashlib.sha256(key.encode()).hexdigest() in admitted
            assert r['delta_rows']['cnf_patterns_v1']==sum(x['inventory_counts'].get('inserted_nodes',0) for x in r['records'])
            for t in ('cnf_pattern_sources_v1','cnf_residual_v1','cnf_pivot_trials_v1'):assert r['delta_rows'][t]==0
            trials=[]
            for key,payload in dd.execute('SELECT id,payload FROM cnf_coupled_trials_v1'):
                record=json.loads(payload);assert key==coupled_key(record);trials.append(record)
                node=json.loads(db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(record['source'],)).fetchone()[0])
                a,b=record['variables'];assert any(a in set(map(abs,c)) and b in set(map(abs,c)) for c in node['cnf'])
            assert len(trials)==r['new_trials']==sum(x['new_trials'] for x in r['records'])
            assert r['trial_replay']['coupled_counts'].get('verified_coupled_trials',0)==len(trials)
            assert r['trial_replay']['old_counts']['verified_trials']==r['seed_table_digests']['cnf_pivot_trials_v1']['rows']
            assert r['trial_replay']['bytes_unchanged'] and r['audit']['bytes_unchanged']
            for field,t in [('nodes','cnf_patterns_v1'),('sources','cnf_pattern_sources_v1'),('residuals','cnf_residual_v1')]:
                assert r['audit'][field]==r['logical_table_digests'][t]['rows']
            assert len(r['frontier_analysis']['rows'])==len(trials)
            assert {x['trial_sha256'] for x in r['frontier_analysis']['rows']}=={hashlib.sha256(coupled_key(t).encode()).hexdigest() for t in trials}
            ep=r['endpoints'];assert sha(ep['path'])==ep['sha256'];epath=tmp/(suite+'-endpoint')
            unpack(ep['path'],epath,ep['database_sha256'])
            assert {x['trial_id'] for x in ep['records']}=={coupled_key(t) for t in trials if t['summary']['closed']}
            reference=sqlite3.connect(epath)
            assert reference.execute('SELECT count(*) FROM cnf_residual_v1').fetchone()[0]==ep['verified_nodes'];reference.close()
            evidence.append(dict(suite=suite,report_sha256=sha(rp),closed=sum(r['final_closed']),new_trials=len(trials),
                admitted_states=sum(len(x['admitted_state_sha256']) for x in r['records']),distinct_admitted_states=len(admitted),
                new_nodes=r['delta_rows']['cnf_patterns_v1'],budget_stops=sum(x['budget_stop'] is not None for x in r['records']),
                delta_sha256=d['sha256'],reconstructed_table_digests=r['logical_table_digests']))
            ap=rp.parent/'continuation-analysis.json';a=json.loads(ap.read_text())
            assert a['script_sha256']==sha('experiments/analyze_cnf_coupled_pivots.py') and a['report_sha256']==sha(rp)
            assert len(a['rows'])==len(trials)==a['counts']['trials']
            assert a['counts']['same_frontier_as_retained_first_route']==sum(x['same_first_route_frontier'] for x in a['rows'])
            assert a['counts']['only_seed_leaves']==sum(x['novel_seed_leaf_count']==0 for x in a['rows'])
            analyses.append(dict(suite=suite,path=str(ap),sha256=sha(ap)))
            cp=rp.parent/'core-admission-audit.json'
            if cp.exists():
                core=json.loads(cp.read_text())
                assert core['script_sha256']==sha('experiments/audit_cnf_coupled_core.py') and core['report_sha256']==sha(rp)
                for c in core['cores']:
                    assert c['shape']['variables']<64 and c['counts'].get('candidate_budget_skips',0)==0
                    assert c['minimum_first_growth']==min(x['growth'] for x in c['first_pivots'])
                    assert c['minimum_pair_growth']==min(x['net_growth'] for x in c['ordered_pairs'])
                    for pair in c['ordered_pairs']:
                        intermediate,target=project_pair(c['source'],pair['variables'],Counter(),clause_growth_limit=64)
                        assert pair['first_growth']==len(intermediate)-len(c['source']) and pair['net_growth']==len(target)-len(c['source'])
                    assert c['net_four_candidates']==sum(x['net_growth']<=4 for x in c['ordered_pairs'])
                    assert c['net_four_interacting_candidates']==sum(x['net_growth']<=4 and x['interacting'] for x in c['ordered_pairs'])
                analyses.append(dict(suite=suite,path=str(cp),sha256=sha(cp)))
            db.close();dd.close()
    tests=Path('/tmp/oraclemachines-coupled-tests.log').read_text()
    assert re.search(r'Ran 535 tests in [0-9.]+s\s+OK',tests)
    (out/'full-validation.txt').write_text(tests.rstrip()+'\n')
    subprocess.run(['git','diff','--exit-code','fc16148','--','formal','paper'],check=True,capture_output=True)
    result=dict(script_sha256=sha(Path(__file__)),evidence=evidence,analyses=analyses,python_tests=535,
        test_log_resource_warning_count=tests.count('ResourceWarning: unclosed database'),unchanged_paper_and_formal_since='fc16148')
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main(Path(sys.argv[1]))
