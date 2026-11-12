#!/usr/bin/env python3
"""Bind additive comparisons to code, source inputs, persistent proofs and paper."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.compare_cnf_retained_plans import sha
from experiments.compare_cnf_clause_mask import table_digest
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_binary_paths import fresh_cases


def unpack(archive, path, digest, size):
    with gzip.open(archive,'rb') as src, path.open('wb') as dst: shutil.copyfileobj(src,dst)
    assert sha(path)==digest and path.stat().st_size==size


def main():
    out = ROOT/'experiments/results/cnf-additive-elimination-validation'; out.mkdir(exist_ok=False)
    prior_path=ROOT/'experiments/results/cnf-clause-bound-elimination-originals/report.json'
    prior=next(r for r in json.loads(prior_path.read_text())['results'] if r['mode']=='clause_bound')
    checks = []; reports = {}; db_hashes = {}
    input_path=ROOT/'experiments/results/cnf-prepared-probes-full/report.json'; inputs=json.loads(input_path.read_text())
    origin_path=ROOT/'experiments/results/cnf-variable-elimination-probe/raw-opportunity.json'; origins=json.loads(origin_path.read_text())
    suites = [('remaining',57), ('originals',83), ('fresh',96)]
    for suite,size in suites:
        p = ROOT/('experiments/results/cnf-additive-elimination-'+suite+'/report.json')
        report = json.loads(p.read_text()); reports[suite] = sha(p)
        assert report['source_commit'].startswith('5894bd8')
        for path,digest in report['fingerprints'].items(): assert sha(ROOT/path)==digest,path
        assert report['input_report_sha256']==sha(input_path)
        assert report['preceding_elimination_report_sha256']==sha(prior_path)
        assert len(report['cases'])==size and report['frontier_sha256']==sha(origin_path)
        options=dict(inputs['options'])
        if suite=='remaining':
            expected=[dict(group='remaining_elimination_leaf',source=r['cnf'],prior_key_sha256=r['key_sha256']) for r in prior['frontier']]
            options['max_depth']=0; assert report['seed'] is None
        elif suite=='originals':
            expected=[dict(inputs['cases'][i],original_case=i) for i in sorted(map(int,origins['origins']))]
            assert report['seed']==inputs['seed'] and report['seed_bytes']==417370112
        else:
            expected=fresh_cases(); assert report['seed']==inputs['seed']
        assert encode(report['cases'])==encode(expected) and report['options']==options
        modes = {r['mode']:r for r in report['results']}; digests=[]
        assert set(modes)=={'baseline','add_one','add_two'}
        db_hashes[suite]={m:r['database_sha256'] for m,r in modes.items()}
        for mode,result in modes.items():
            allowance={'baseline':0,'add_one':1,'add_two':2}[mode]
            assert result['configuration']==dict(options,**({} if mode=='baseline' else {'clause_growth_limit':allowance}))
            assert result['audit']['bytes_unchanged'] and len(result['records'])==size
            for a,b in zip(modes['baseline']['records'],result['records'],strict=True):
                for field in ('case','answer','profile','solver_metrics'): assert encode(a[field])==encode(b[field]),(suite,mode,field)
            archive = ROOT/result['archive_path']; assert sha(archive)==result['archive_sha256']
            model=result['edge_models']; reference_archive=ROOT/model['reference_archive']
            assert sha(reference_archive)==model['reference_archive_sha256']
            witness_path=ROOT/model['endpoint_results_path']; assert sha(witness_path)==model['endpoint_results_sha256']
            witnesses=[json.loads(line) for line in witness_path.read_text().splitlines()]
            by_key={w['source_key_sha256']:w for w in witnesses}; assert len(by_key)==len(witnesses)
            edges = clause_growth = literal_growth = sats = 0
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'a.db'; reference_path=Path(tmp)/'reference.db'
                unpack(archive,path,result['database_sha256'],result['database_bytes'])
                unpack(reference_archive,reference_path,model['reference_database_sha256'],model['reference_database_bytes'])
                db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                digests.append(table_digest(db,'cnf_residual_v1'))
                reference=ResidualSolver(reference_path)
                assert reference.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                assert list(reference.archive_storage())==model['reference_storage']
                for key,payload in db.execute('SELECT id,payload FROM cnf_patterns_v1 WHERE payload LIKE ?',('%"additive_elimination"%',)):
                    node=json.loads(payload)
                    if node['additive_elimination']['variable'] is None: continue
                    assert node['kind']=='eliminate'; edges+=1
                    target=json.loads(db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(node['edge']['key'],)).fetchone()[0])['cnf']
                    source=node['cnf']; n=len({abs(l) for c in source for l in c})
                    assert len(target)<=len(source)+allowance and len({abs(l) for c in target for l in c})<n
                    assert sum(map(len,target))<=(len(source)+allowance)*(n-1)
                    clause_growth+=len(target)>len(source); literal_growth+=sum(map(len,target))>sum(map(len,source))
                    witness=by_key.pop(hashlib.sha256(key.encode()).hexdigest())
                    assert witness['target_key_sha256']==hashlib.sha256(node['edge']['key'].encode()).hexdigest()
                    assert witness['source_answer']==witness['target_answer']; sats+=witness['source_answer']
                    for side,cnf in [('source',source),('target',target)]:
                        normalized,_,root=reference._canonical(cnf)
                        assert root==witness[side+'_root']
                        proof=reference._read(root,normalized); assert proof is not None
                        assert proof['answer']==witness[side+'_answer']
                        if proof['answer']:
                            assignment={int(v):b for v,b in witness[side+'_model'].items()}
                            assert holds(cnf,assignment)
                        else: assert witness[side+'_model'] is None
                assert not by_key and not reference.counts.get('expanded_nodes',0)
                reference.close(); assert sha(reference_path)==model['reference_database_sha256']
                db.close()
            assert edges==model.get('edges',0)==model.get('sat',0)+model.get('unsat',0)
            assert sats==model.get('sat',0)
            assert clause_growth==model.get('clause_growing_edges',0) and literal_growth==model.get('literal_growing_edges',0)
            for chain in model['chains']:
                n=chain['initial_variables']; m=chain['initial_clauses']
                assert chain['steps']<=n and chain['peak_literals']<=(m+allowance*n)*n
            checks.append(dict(suite=suite,mode=mode,database_sha256=result['database_sha256'],archive=result['archive_path'],
                new_edges=edges,clause_growing_edges=clause_growth,literal_growing_edges=literal_growth,
                checked_persistent_endpoint_pairs=len(witnesses), reference_archive_sha256=model['reference_archive_sha256'],
                closed=sum(r['summary']['closed'] for r in result['records'])))
        assert all(d==digests[0] for d in digests)
        if suite=='originals': assert modes['baseline']['database_sha256']==prior['database_sha256']
    frontier_path=ROOT/'experiments/results/cnf-additive-elimination-originals/growth-barriers.json'
    frontier=json.loads(frontier_path.read_text())
    assert frontier['script_sha256']==sha(ROOT/'experiments/analyze_cnf_additive_frontier.py')
    assert frontier['candidate_helper_sha256']==sha(ROOT/'experiments/analyze_cnf_clause_bound_frontier.py')
    for row in frontier['reports']:
        assert row['report_sha256']==reports[row['suite']]
        for leaf in row['leaves']: assert leaf['min_clause_delta'] is None or leaf['min_clause_delta']>row['allowance']
    profile_path=ROOT/'experiments/results/cnf-additive-elimination-originals/discovery-profile.json'
    profile=json.loads(profile_path.read_text())
    assert profile['script_sha256']==sha(ROOT/'experiments/profile_cnf_additive_elimination.py')
    assert profile['report_sha256']==reports['originals']
    assert profile['raw_profile_sha256']==sha(profile_path.with_suffix('.pstats'))
    assert profile['archive_sha256']==sha(ROOT/profile['archive_path'])
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'profile.db'
        unpack(ROOT/profile['archive_path'],path,profile['database_sha256'],profile['database_bytes'])
        db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
        assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'; db.close()
    tex=ROOT/'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    oldtex=subprocess.check_output(['git','show','9538b04:'+str(tex.relative_to(ROOT))],cwd=ROOT,text=True)
    proof=r'\\begin\{proof\}(?:\[[^\]]*\])?.*?\\end\{proof\}'
    assert re.findall(proof,tex.read_text(),re.S)==re.findall(proof,oldtex,re.S)
    assert len(re.findall(proof,oldtex,re.S))==63
    labels=re.findall(r'\\label\{([^}]+)\}',tex.read_text()); assert len(labels)==len(set(labels))==228
    for name in ('full','lean','latex'):
        content=Path('/tmp/oraclemachines-additive-'+name+'.log').read_text()
        if name=='full': assert re.search(r'Ran 516 tests in [0-9.]+s\s+OK',content)
        if name=='lean': assert '4216 declarations, 2028 theorem declarations' in content and 'Build completed successfully' in content
        (out/(name+'-validation.txt')).write_text(content.rstrip()+'\n')
    assert not re.search(r'(?:LaTeX|Package .*?) Warning|Overfull|Underfull',tex.with_suffix('.log').read_text())
    result=dict(script_sha256=sha(Path(__file__)),reports=reports,archives=checks,python_tests=516,
        lean_declarations=4216,lean_theorems=2028,old_proof_blocks_preserved=63,unique_labels=228,
        formal_sources={p:sha(ROOT/p) for p in ('formal/OracleMachines/AdditiveElimination.lean','formal/OracleMachines/ClauseBoundElimination.lean','formal/OracleMachines/VariableElimination.lean','formal/OracleMachines/Audit.lean')},
        original_baseline_matches_prior_clause_bound_archive=True,matched_residual_evidence=True,
        frontier_diagnostic_sha256=sha(frontier_path),profile_diagnostic_sha256=sha(profile_path),manuscript_sha256=sha(tex),pdf_sha256=sha(tex.with_suffix('.pdf')),
        limitations=['Every new edge has persistent checked endpoint/model results; all acquisition archives passed full cold proof checking.',
        'Selected prior failures and reused controls are not an untouched holdout or full-corpus rerun.',
        'Lean proves conditional chain size bounds, not Python refinement, pivot availability or a bound on the whole planner.'])
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(checks))


if __name__=='__main__': main()
