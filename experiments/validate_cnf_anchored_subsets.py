#!/usr/bin/env python3
"""Bind exact-index measurements to prior proof archives and current sources."""
from collections import Counter
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
from experiments.cnf_pattern_inventory import encode


def main():
    out=ROOT/'experiments/results/cnf-anchored-subsets-validation';out.mkdir(exist_ok=False)
    reports={};checks=[];seen_archives=set()
    for name,suite,size in [('remaining','remaining',57),('remaining-reverse','remaining',57),('originals','originals',83),('fresh','fresh',96)]:
        p=ROOT/('experiments/results/cnf-anchored-subsets-'+name+'/report.json');r=json.loads(p.read_text());reports[name]=sha(p)
        assert r['source_commit'].startswith('0fe0936') and r['suite']==suite
        prior_path=ROOT/r['prior_report'];prior=json.loads(prior_path.read_text());assert sha(prior_path)==r['prior_report_sha256']
        old=next(x for x in prior['results'] if x['mode']=='add_two')
        assert encode(r['cases'])==encode(prior['cases']) and len(r['cases'])==size
        assert r['options']==old['configuration']
        for path,digest in r['fingerprints'].items():assert sha(ROOT/path)==digest,path
        modes={x['mode']:x for x in r['results']};assert set(modes)=={'baseline','anchored'}
        assert r['execution_order']==(['anchored','baseline'] if name.endswith('reverse') else ['baseline','anchored'])
        for mode,x in modes.items():
            assert x['database_sha256']==old['database_sha256'] and x['database_bytes']==old['database_bytes']
            assert x['archive_path']==old['archive_path'] and x['archive_sha256']==old['archive_sha256']
            assert x['audit']['bytes_unchanged'] and x['old_rows_preserved']==old['old_rows_preserved']
            assert len(x['records'])==size and x['storage']==old['storage']
            for a,b in zip(x['records'],old['records'],strict=True):
                for field in ('case','answer','profile','summary','root_sha256','root_kind','solver_metrics'):
                    assert encode(a[field])==encode(b[field]),(name,mode,field)
            for field in ('nodes','sources','residuals'):assert x['audit'][field]==old['audit'][field]
            if x['archive_path'] not in seen_archives:
                archive=ROOT/x['archive_path'];assert sha(archive)==x['archive_sha256']
                with tempfile.TemporaryDirectory() as tmp:
                    dbpath=Path(tmp)/'archive.db'
                    with gzip.open(archive,'rb') as src,dbpath.open('wb') as dst:shutil.copyfileobj(src,dst)
                    assert sha(dbpath)==x['database_sha256'] and dbpath.stat().st_size==x['database_bytes']
                    db=sqlite3.connect(f'file:{dbpath}?mode=ro',uri=True)
                    assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
                    for field,table in [('nodes','cnf_patterns_v1'),('sources','cnf_pattern_sources_v1'),('residuals','cnf_residual_v1')]:
                        assert db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]==x['audit'][field]
                    db.close()
                seen_archives.add(x['archive_path'])
            checks.append(dict(suite=name,mode=mode,closed=sum(a['summary']['closed'] for a in x['records']),
                database_sha256=x['database_sha256'],archive_path=x['archive_path'],cold_bytes_unchanged=True))
    trace_path=ROOT/'experiments/results/cnf-subset-reuse-trace/report.json';trace=json.loads(trace_path.read_text())
    calls_path=trace_path.with_name('calls.json.gz');assert sha(calls_path)==trace['trace_sha256']
    assert sha(ROOT/'experiments/trace_cnf_subset_reuse.py')==trace['script_sha256']
    with gzip.open(calls_path,'rt') as f:calls=json.load(f)
    assert len(calls['calls'])==trace['call_count']==1694 and len(calls['sources'])==trace['source_count']==851
    assert dict(Counter(c['phase'] for c in calls['calls']))==trace['phase_counts']
    for role in ('proposal','check'):
        selected=[c for c in calls['calls'] if ('check' in c['phase'])==(role=='check')]
        assert len(selected)==len({c['source'] for c in selected})
    for sim in trace['lru_simulations']:assert not sim.get('proposal_hits',0) and not sim.get('check_hits',0)
    profile_path=ROOT/'experiments/results/cnf-additive-elimination-originals/discovery-profile.json';profile=json.loads(profile_path.read_text())
    assert trace['profile_report_sha256']==sha(profile_path) and trace['database_sha256']==profile['database_sha256']
    assert trace['report_sha256']==sha(ROOT/'experiments/results/cnf-additive-elimination-originals/report.json')
    assert trace['preserved_archive']==profile['archive_path']
    assert sha(ROOT/trace['preserved_archive'])==profile['archive_sha256']
    kernel_path=ROOT/'experiments/results/cnf-anchor-kernel/report.json';kernel=json.loads(kernel_path.read_text())
    assert kernel['trace_sha256']==sha(calls_path) and kernel['script_sha256']==sha(ROOT/'experiments/benchmark_cnf_anchor_kernel.py')
    for p,d in kernel['source_fingerprints'].items():assert sha(ROOT/p)==d
    assert len(kernel['rows'])==60
    for group in {x['group'] for x in kernel['rows']}:
        for mode in ('baseline','anchored'):
            rows=[x for x in kernel['rows'] if x['group']==group and x['mode']==mode]
            assert {x['repeat'] for x in rows}==set(range(5))
            assert all(x['counts']==rows[0]['counts'] for x in rows)
    tex=ROOT/'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    oldtex=subprocess.check_output(['git','show','2303832:'+str(tex.relative_to(ROOT))],cwd=ROOT,text=True)
    proof=r'\\begin\{proof\}(?:\[[^\]]*\])?.*?\\end\{proof\}'
    assert re.findall(proof,tex.read_text(),re.S)==re.findall(proof,oldtex,re.S)
    assert len(re.findall(proof,oldtex,re.S))==63
    labels=re.findall(r'\\label\{([^}]+)\}',tex.read_text());assert len(labels)==len(set(labels))==229
    for name in ('full','lean','latex'):
        content=Path('/tmp/oraclemachines-anchor-'+name+'.log').read_text()
        if name=='full':assert re.search(r'Ran 521 tests in [0-9.]+s\s+OK',content)
        if name=='lean':assert '4219 declarations, 2031 theorem declarations' in content and 'Build completed successfully' in content
        (out/(name+'-validation.txt')).write_text(content.rstrip()+'\n')
    assert not re.search(r'(?:LaTeX|Package .*?) Warning|Overfull|Underfull',tex.with_suffix('.log').read_text())
    result=dict(script_sha256=sha(Path(__file__)),reports=reports,archives=checks,unique_archives=len(seen_archives),
        trace_report_sha256=sha(trace_path),kernel_report_sha256=sha(kernel_path),python_tests=521,lean_declarations=4219,
        lean_theorems=2031,old_proof_blocks_preserved=63,unique_labels=229,manuscript_sha256=sha(tex),pdf_sha256=sha(tex.with_suffix('.pdf')),
        formal_sources={p:sha(ROOT/p) for p in ('formal/OracleMachines/SubsetAnchor.lean','formal/OracleMachines/Audit.lean')},
        limitations=['Eight full cold runs and three unique byte-identical prior acquisition archives; endpoint evidence is reused by exact archive identity.',
        'Selected and repeated workloads, not an untouched holdout or full-corpus rerun. No new recognition coverage.',
        'Lean abstracts the necessary-condition filter and witness order, not Python refinement or machine-cost bounds.'])
    (out/'validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(checks))


if __name__=='__main__':main()
