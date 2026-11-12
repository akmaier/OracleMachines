#!/usr/bin/env python3
"""Validate bounded-search evidence, base-bound deltas, and compatible proof reuse."""
import gzip
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.compare_cnf_retained_plans import sha
from experiments.compare_cnf_pivot_alternatives import apply_delta,TABLES
from experiments.compare_cnf_clause_mask import table_digest
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import ResidualSolver


def unpack(path,destination,digest):
    with gzip.open(path,'rb') as src,destination.open('wb') as dst:shutil.copyfileobj(src,dst)
    assert sha(destination)==digest


def main():
    out=ROOT/'experiments/results/cnf-pivot-alternatives-validation';out.mkdir(exist_ok=False)
    evidence=[];unions=[]
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        for suite,size in [('originals',83),('fresh',96)]:
            reports=[];deltas=[]
            for policy in ('pivot-alternatives','interacting-pivots'):
                directory=ROOT/('experiments/results/cnf-'+policy+'-'+suite);rp=directory/'report.json';r=json.loads(rp.read_text())
                prior_path=ROOT/r['input_report'];prior=json.loads(prior_path.read_text());old=next(x for x in prior['results'] if x['mode']=='add_two')
                assert r['source_commit'].startswith('3f399c9' if policy=='pivot-alternatives' else '3a5f19f')
                assert r['suite']==suite and sha(prior_path)==r['input_report_sha256']
                assert encode(r['cases'])==encode(prior['cases']) and len(r['cases'])==size
                assert r['options']==old['configuration'] and r['budgets']==dict(ancestor_limit=4,trial_limit=8)
                for path,digest in r['fingerprints'].items():assert sha(ROOT/path)==digest,path
                assert r['base_archive']==old['archive_path'] and r['base_archive_sha256']==old['archive_sha256']
                assert r['base_database_sha256']==old['database_sha256'] and r['base_database_bytes']==old['database_bytes']
                if not reports:
                    assert sha(ROOT/r['base_archive'])==r['base_archive_sha256']
                    base=tmp/(suite+'-base');unpack(ROOT/r['base_archive'],base,r['base_database_sha256'])
                delta=tmp/(suite+'-'+policy+'-delta');assert sha(ROOT/r['delta']['path'])==r['delta']['sha256']
                unpack(ROOT/r['delta']['path'],delta,r['delta']['database_sha256']);deltas.append(delta)
                assert delta.stat().st_size==r['delta']['database_bytes']
                history=tmp/(suite+'-'+policy);shutil.copyfile(base,history);apply_delta(history,delta)
                before=sha(history);apply_delta(history,delta);assert sha(history)==before
                db=sqlite3.connect(history);dd=sqlite3.connect(delta)
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                for table in TABLES:
                    assert table_digest(db,table)==r['logical_table_digests'][table]
                    assert dd.execute(f'SELECT count(*) FROM {table}').fetchone()[0]==r['delta_rows'][table]
                for field,table in [('nodes','cnf_patterns_v1'),('sources','cnf_pattern_sources_v1'),('residuals','cnf_residual_v1')]:
                    assert r['audit'][field]==r['logical_table_digests'][table]['rows']
                    assert r['old_rows_preserved'][table]==old['audit'][field]
                assert r['audit']['bytes_unchanged'] and r['trial_replay']['bytes_unchanged']
                assert r['trial_replay']['counts']['verified_trials']==r['unique_trials']==r['delta_rows']['cnf_pivot_trials_v1']
                assert r['trials_attempted']==sum(x['trial_count'] for x in r['records'])
                assert all(0<=x['trial_count']<=8 for x in r['records'])
                assert r['delta_rows']['cnf_residual_v1']==r['delta_rows']['cnf_pattern_sources_v1']==0
                assert all(now or not previous['summary']['closed'] for now,previous in zip(r['final_closed'],old['records'],strict=True))
                gains=[i for i,(now,previous) in enumerate(zip(r['final_closed'],old['records'],strict=True)) if now and not previous['summary']['closed']]
                assert gains==r['gains']
                ap=directory/'frontier-analysis.json';analysis=json.loads(ap.read_text())
                assert analysis['script_sha256']==sha(ROOT/'experiments/analyze_cnf_pivot_alternatives.py')
                assert analysis['report_sha256']==sha(rp) and len(analysis['trials'])==r['unique_trials']
                for field,condition in [('same_selected_frontier_as_source',lambda x:x['same_selected_frontier']),
                    ('target_frontier_only_old_leaves',lambda x:x['only_old_leaves']),
                    ('noninteracting_pivot_pairs',lambda x:x['joint_pivot_clauses']==0),
                    ('noninteracting_same_frontier',lambda x:x['joint_pivot_clauses']==0 and x['same_selected_frontier'])]:
                    assert analysis['statistics'][field]==sum(condition(x) for x in analysis['trials'])
                endpoint=r['endpoints'];assert sha(ROOT/endpoint['path'])==endpoint['sha256']
                ep=tmp/'endpoints';unpack(ROOT/endpoint['path'],ep,endpoint['database_sha256'])
                reference=ResidualSolver(ep);verified=0
                for key, in reference.db.execute('SELECT id FROM cnf_residual_v1'):
                    assert reference._read(key) is not None;verified+=1
                assert verified==endpoint['verified_nodes'];reference.close();assert sha(ep)==endpoint['database_sha256']
                # These actual comparisons have no successful replacement; do
                # not relabel empty initialized endpoint stores as solved proofs.
                assert r['successful_source_count']==0 and not endpoint['records'] and verified==0
                evidence.append(dict(suite=suite,policy=policy,report_sha256=sha(rp),analysis_sha256=sha(ap),
                    closed=sum(r['final_closed']),trials=r['trials_attempted'],unique_trials=r['unique_trials'],
                    delta_sha256=r['delta']['sha256'],cold_bytes_unchanged=True))
                db.close();dd.close();reports.append(r)
            # Both policies use identical immutable proof identities. Their
            # separately retained deltas can be combined with exact conflict checks.
            a,b=map(sqlite3.connect,deltas);overlap={}
            for table in TABLES:
                shared=0
                for key,payload in a.execute(f'SELECT id,payload FROM {table}'):
                    other=b.execute(f'SELECT payload FROM {table} WHERE id=?',(key,)).fetchone()
                    if other is not None:assert other==(payload,);shared+=1
                overlap[table]=shared
            a.close();b.close();merged=tmp/(suite+'-merged');shutil.copyfile(base,merged)
            apply_delta(merged,deltas[0]);apply_delta(merged,deltas[1]);db=sqlite3.connect(merged)
            union={}
            for table in TABLES:
                union[table]=table_digest(db,table)
                base_count=reports[0]['logical_table_digests'][table]['rows']-reports[0]['delta_rows'][table]
                assert union[table]['rows']==base_count+sum(r['delta_rows'][table] for r in reports)-overlap[table]
            assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';db.close()
            unions.append(dict(suite=suite,identical_overlap_rows=overlap,merged_table_digests=union,
                limitation='Union has no changed payloads; each constituent graph already passed cold verification. No extra full merged cold replay or timing claim.'))
    tex=ROOT/'paper/bounded_domain_sat_and_amortized_reasoning.tex';oldtex=subprocess.check_output(['git','show','21a90ac:'+str(tex.relative_to(ROOT))],cwd=ROOT,text=True)
    proof=r'\\begin\{proof\}(?:\[[^\]]*\])?.*?\\end\{proof\}'
    assert re.findall(proof,tex.read_text(),re.S)==re.findall(proof,oldtex,re.S)
    assert len(re.findall(proof,oldtex,re.S))==63
    labels=re.findall(r'\\label\{([^}]+)\}',tex.read_text());assert len(labels)==len(set(labels))==230
    content=Path('/tmp/oraclemachines-interacting-full.log').read_text();assert re.search(r'Ran 527 tests in [0-9.]+s\s+OK',content)
    (out/'full-validation.txt').write_text(content)
    (out/'latex-validation.txt').write_text(Path('/tmp/oraclemachines-pivot-latex.log').read_text())
    assert not re.search(r'(?:LaTeX|Package .*?) Warning|Overfull|Underfull',tex.with_suffix('.log').read_text())
    subprocess.run(['git','diff','--exit-code','21a90ac','--','formal'],cwd=ROOT,check=True,capture_output=True)
    prior_lean=ROOT/'experiments/results/cnf-anchored-subsets-validation/lean-validation.txt'
    result=dict(script_sha256=sha(Path(__file__)),evidence=evidence,compatible_unions=unions,python_tests=527,
        old_proof_blocks_preserved=63,unique_labels=230,unchanged_formal_sources_since='21a90ac',
        prior_lean_audit=str(prior_lean.relative_to(ROOT)),prior_lean_audit_sha256=sha(prior_lean),
        manuscript_sha256=sha(tex),pdf_sha256=sha(tex.with_suffix('.pdf')))
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(evidence=evidence,unions=unions)))


if __name__=='__main__':main()
