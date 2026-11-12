#!/usr/bin/env python3
"""Bind the retained subsumption comparisons to code, archives and proof checks."""
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
from experiments.compare_cnf_clause_mask import table_digest
from experiments.cnf_pattern_inventory import encode


def main():
    out=ROOT/'experiments/results/cnf-subsumed-elimination-validation'
    out.mkdir(exist_ok=False)
    old=json.loads((ROOT/'experiments/results/cnf-variable-elimination-originals/report.json').read_text())
    previous=next(r for r in old['results'] if r['mode']=='bounded')
    checks=[]; reports={}; archive_digests={}
    for suite,size in [('remaining',59),('originals',83),('remaining-reverse',59)]:
        report_path=ROOT/('experiments/results/cnf-subsumed-elimination-'+suite+'/report.json')
        report=json.loads(report_path.read_text()); reports[suite]=sha(report_path)
        assert report['source_commit'].startswith('14ae642')
        for p,digest in report['fingerprints'].items(): assert sha(ROOT/p)==digest,p
        assert report['input_report_sha256']==sha(ROOT/'experiments/results/cnf-prepared-probes-full/report.json')
        assert report['preceding_elimination_report_sha256']==sha(ROOT/'experiments/results/cnf-variable-elimination-originals/report.json')
        assert len(report['cases'])==size
        modes={r['mode']:r for r in report['results']}; digests=[]
        archive_digests[suite]={m:r['database_sha256'] for m,r in modes.items()}
        for mode,result in modes.items():
            assert result['audit']['bytes_unchanged'] and len(result['records'])==size
            for a,b in zip(modes['baseline']['records'],result['records'],strict=True):
                for field in ('case','answer','profile','solver_metrics'): assert encode(a[field])==encode(b[field]),(suite,mode,field)
            archive=ROOT/result['archive_path']; assert sha(archive)==result['archive_sha256']
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)/'a.db'
                with gzip.open(archive,'rb') as src,path.open('wb') as dst: shutil.copyfileobj(src,dst)
                assert sha(path)==result['database_sha256'] and path.stat().st_size==result['database_bytes']
                db=sqlite3.connect(f'file:{path}?mode=ro',uri=True)
                assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                digests.append(table_digest(db,'cnf_residual_v1'))
                edges=omissions=0
                for payload, in db.execute('SELECT payload FROM cnf_patterns_v1 WHERE payload LIKE ?',('%"subsumed_elimination"%',)):
                    node=json.loads(payload); proof=node['subsumed_elimination']
                    if proof['variable'] is not None:
                        edges+=1; omissions+=len(proof['omissions'])
                        assert node['kind']=='eliminate'
                db.close()
            assert edges==result['edge_models'].get('edges',0)
            assert edges==result['edge_models'].get('sat',0)+result['edge_models'].get('unsat',0)
            checks.append(dict(suite=suite,mode=mode,archive=result['archive_path'],
                database_sha256=result['database_sha256'],new_edges=edges,omission_references=omissions,
                closed=sum(r['summary']['closed'] for r in result['records'])))
        assert digests[0]==digests[1]
        if suite=='originals':
            assert modes['baseline']['database_sha256']==previous['database_sha256']
            assert modes['baseline']['records'] and sum(r['summary']['closed'] for r in modes['baseline']['records'])==29
        a={r['case'] for r in modes['baseline']['records'] if r['summary']['closed']}
        b={r['case'] for r in modes['subsumed']['records'] if r['summary']['closed']}
        assert a==b
    assert archive_digests['remaining']==archive_digests['remaining-reverse']
    growth_path=ROOT/'experiments/results/cnf-subsumed-elimination-originals/growth-opportunity.json'
    growth=json.loads(growth_path.read_text())
    assert growth['script_sha256']==sha(ROOT/'experiments/analyze_cnf_elimination_growth.py')
    assert growth['opportunity_helper_sha256']==sha(ROOT/'experiments/analyze_cnf_variable_elimination.py')
    for row in growth['reports']:
        assert row['report_sha256']==reports[row['suite']]
        assert (row['current_rule_available'],row['clause_only_without_subsumption'],row['clause_only_candidates_available'])==(0,48,49)
    initial=json.loads((growth_path.parent/'growth-opportunity-initial.json').read_text())
    assert initial['script_sha256']==sha(growth_path.parent/'growth-analysis-initial.py')
    tex=ROOT/'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    oldtex=subprocess.check_output(['git','show','da58395:'+str(tex.relative_to(ROOT))],cwd=ROOT,text=True)
    proof=r'\\begin\{proof\}(?:\[[^\]]*\])?.*?\\end\{proof\}'
    assert re.findall(proof,tex.read_text(),re.S)==re.findall(proof,oldtex,re.S)
    assert len(re.findall(proof,oldtex,re.S))==63
    labels=re.findall(r'\\label\{([^}]+)\}',tex.read_text()); assert len(labels)==len(set(labels))==226
    for name in ('full','lean','latex'):
        content=Path('/tmp/oraclemachines-subsumed-'+name+'.log').read_text()
        if name=='full': assert re.search(r'Ran 506 tests in [0-9.]+s\s+OK',content)
        if name=='lean': assert '4173 declarations, 2009 theorem declarations' in content and 'Build completed successfully' in content
        (out/(name+'-validation.txt')).write_text(content.rstrip()+'\n')
    assert not re.search(r'(?:LaTeX|Package .*?) Warning|Overfull|Underfull',tex.with_suffix('.log').read_text())
    result=dict(script_sha256=sha(Path(__file__)),reports=reports,archives=checks,python_tests=506,
        lean_declarations=4173,lean_theorems=2009,old_proof_blocks_preserved=63,unique_labels=226,
        original_baseline_matches_prior_bounded_archive=True,matched_residual_evidence=True,
        opposite_order_archives_identical=True,growth_diagnostic_sha256=sha(growth_path),
        manuscript_sha256=sha(tex),pdf_sha256=sha(tex.with_suffix('.pdf')),
        limitations=['Only new subsumed edges have additional endpoint/model diagnostics in these runs; all retained edges pass cold proof checking.',
        'Prior failure subsets and repeated controls are not an untouched holdout or full-corpus rerun.',
        'Lean proves semantic clause/projection lemmas, not Python refinement or resource bounds.'])
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(checks))


if __name__=='__main__': main()
