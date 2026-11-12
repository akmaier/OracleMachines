#!/usr/bin/env python3
"""Bind clause-count comparisons to code, archives, formal checks and manuscript."""
import gzip
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
from experiments.compare_cnf_binary_paths import fresh_cases


def main():
    out = ROOT/'experiments/results/cnf-clause-bound-elimination-validation'; out.mkdir(exist_ok=False)
    previous = next(r for r in json.loads((ROOT/'experiments/results/cnf-variable-elimination-originals/report.json').read_text())['results'] if r['mode']=='bounded')
    checks = []; reports = {}; db_hashes = {}
    input_path=ROOT/'experiments/results/cnf-prepared-probes-full/report.json'
    inputs=json.loads(input_path.read_text())
    origin_path=ROOT/'experiments/results/cnf-variable-elimination-probe/raw-opportunity.json'
    origins=json.loads(origin_path.read_text())
    preceding=json.loads((ROOT/'experiments/results/cnf-subsumed-elimination-originals/report.json').read_text())
    leaves=next(r for r in preceding['results'] if r['mode']=='subsumed')['frontier']
    suites = [('remaining',59), ('originals',83)]
    for optional, count in [('remaining-reverse',59), ('fresh',96)]:
        if (ROOT/('experiments/results/cnf-clause-bound-elimination-'+optional+'/report.json')).exists(): suites.append((optional,count))
    for suite,size in suites:
        p = ROOT/('experiments/results/cnf-clause-bound-elimination-'+suite+'/report.json')
        report = json.loads(p.read_text()); reports[suite] = sha(p)
        assert report['source_commit'].startswith('2c422ff')
        for path,digest in report['fingerprints'].items(): assert sha(ROOT/path)==digest,path
        assert report['input_report_sha256']==sha(ROOT/'experiments/results/cnf-prepared-probes-full/report.json')
        assert report['preceding_elimination_report_sha256']==sha(ROOT/'experiments/results/cnf-subsumed-elimination-originals/report.json')
        assert len(report['cases'])==size
        assert report['frontier_sha256']==sha(origin_path)
        options=dict(inputs['options'])
        if suite.startswith('remaining'):
            expected=[dict(group='remaining_elimination_leaf',source=r['cnf'],prior_key_sha256=r['key_sha256']) for r in leaves]
            options['max_depth']=0; assert report['seed'] is None
        elif suite=='originals':
            expected=[dict(inputs['cases'][i],original_case=i) for i in sorted(map(int,origins['origins']))]
            assert report['seed']==inputs['seed'] and report['seed_bytes']==417370112
        else:
            expected=fresh_cases(); assert report['seed']==inputs['seed']
        assert encode(report['cases'])==encode(expected)
        assert report['options']==options
        modes = {r['mode']:r for r in report['results']}; digests=[]
        assert set(modes)=={'baseline','clause_bound'}
        db_hashes[suite]={m:r['database_sha256'] for m,r in modes.items()}
        for mode,result in modes.items():
            assert result['audit']['bytes_unchanged'] and len(result['records'])==size
            for a,b in zip(modes['baseline']['records'],result['records'],strict=True):
                for field in ('case','answer','profile','solver_metrics'): assert encode(a[field])==encode(b[field]),(suite,mode,field)
            archive = ROOT/result['archive_path']; assert sha(archive)==result['archive_sha256']
            edges = growth = 0
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/'a.db'
                with gzip.open(archive,'rb') as src, path.open('wb') as dst: shutil.copyfileobj(src,dst)
                assert sha(path)==result['database_sha256'] and path.stat().st_size==result['database_bytes']
                db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                digests.append(table_digest(db,'cnf_residual_v1'))
                for payload, in db.execute('SELECT payload FROM cnf_patterns_v1 WHERE payload LIKE ?',('%"clause_elimination"%',)):
                    node=json.loads(payload)
                    if node['clause_elimination']['variable'] is None: continue
                    assert node['kind']=='eliminate'; edges+=1
                    target=json.loads(db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(node['edge']['key'],)).fetchone()[0])['cnf']
                    source=node['cnf']; n=len({abs(l) for c in source for l in c})
                    assert len(target)<=len(source) and len({abs(l) for c in target for l in c})<n
                    assert sum(map(len,target))<=len(source)*(n-1)
                    growth+=sum(map(len,target))>sum(map(len,source))
                db.close()
            model=result['edge_models']
            assert edges==model.get('edges',0)==model.get('sat',0)+model.get('unsat',0)
            assert growth==model.get('literal_growing_edges',0)
            for chain in model['chains']:
                assert chain['steps']<=chain['initial_variables']
                assert chain['peak_literals']<=chain['initial_clauses']*chain['initial_variables']
            checks.append(dict(suite=suite, mode=mode, database_sha256=result['database_sha256'],
                archive=result['archive_path'], new_edges=edges, literal_growing_edges=growth,
                closed=sum(r['summary']['closed'] for r in result['records'])))
        assert digests[0]==digests[1]
        if suite=='originals': assert modes['baseline']['database_sha256']==previous['database_sha256']
    if 'remaining-reverse' in db_hashes: assert db_hashes['remaining']==db_hashes['remaining-reverse']
    frontier_path=ROOT/'experiments/results/cnf-clause-bound-elimination-originals/growth-barriers.json'
    frontier=json.loads(frontier_path.read_text())
    assert frontier['script_sha256']==sha(ROOT/'experiments/analyze_cnf_clause_bound_frontier.py')
    for row in frontier['reports']:
        assert row['report_sha256']==reports[row['suite']]
        for leaf in row['leaves']: assert leaf['min_clause_delta'] is None or leaf['min_clause_delta']>0
    tex=ROOT/'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    oldtex=subprocess.check_output(['git','show','e5225f4:'+str(tex.relative_to(ROOT))],cwd=ROOT,text=True)
    proof=r'\\begin\{proof\}(?:\[[^\]]*\])?.*?\\end\{proof\}'
    assert re.findall(proof,tex.read_text(),re.S)==re.findall(proof,oldtex,re.S)
    assert len(re.findall(proof,oldtex,re.S))==63
    labels=re.findall(r'\\label\{([^}]+)\}',tex.read_text()); assert len(labels)==len(set(labels))==227
    for name in ('full','lean','latex'):
        content=Path('/tmp/oraclemachines-clause-bound-'+name+'.log').read_text()
        if name=='full': assert re.search(r'Ran 511 tests in [0-9.]+s\s+OK',content)
        if name=='lean': assert '4195 declarations, 2018 theorem declarations' in content and 'Build completed successfully' in content
        (out/(name+'-validation.txt')).write_text(content.rstrip()+'\n')
    assert not re.search(r'(?:LaTeX|Package .*?) Warning|Overfull|Underfull',tex.with_suffix('.log').read_text())
    result=dict(script_sha256=sha(Path(__file__)), reports=reports, archives=checks, python_tests=511,
        lean_declarations=4195, lean_theorems=2018, old_proof_blocks_preserved=63, unique_labels=227,
        formal_sources={p:sha(ROOT/p) for p in ('formal/OracleMachines/ClauseBoundElimination.lean','formal/OracleMachines/VariableElimination.lean','formal/OracleMachines/Audit.lean')},
        original_baseline_matches_prior_bounded_archive=True, matched_residual_evidence=True,
        frontier_diagnostic_sha256=sha(frontier_path), manuscript_sha256=sha(tex), pdf_sha256=sha(tex.with_suffix('.pdf')),
        limitations=['New edges have independent endpoint/model diagnostics; all archive nodes pass full cold proof checking.',
        'Selected prior failures and reused controls are not an untouched holdout or full-corpus rerun.',
        'Lean proves conditional chain size bounds, not Python refinement, pivot availability or a bound on the whole planner.'])
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(checks))


if __name__=='__main__': main()
