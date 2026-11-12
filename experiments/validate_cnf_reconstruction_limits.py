#!/usr/bin/env python3
"""Bind the negative reconstruction comparison and source-identity diagnostics."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.compare_cnf_retained_plans import sha
from experiments.cnf_pattern_inventory import encode


def main():
    out=ROOT/'experiments/results/cnf-indexed-check-profile';target=out/'validation.json'
    if target.exists():raise FileExistsError(target)
    path=ROOT/'experiments/results/cnf-indexed-check-empty/report.json'
    report=json.loads(path.read_text())
    assert report['input_report_sha256']==sha(ROOT/'experiments/results/cnf-prepared-probes-full/report.json')
    for name,digest in report['fingerprints'].items():assert sha(ROOT/name)==digest,name
    results={r['mode']:r for r in report['results']};a,b=results['scan'],results['indexed']
    assert a['table_digests']==b['table_digests']
    assert a['database_sha256']==b['database_sha256']
    for x,y in zip(a['records'],b['records'],strict=True):
        for field in ('case','answer','root_sha256','solver_root_sha256','profile','summary',
                      'archive_nodes','archive_payload_units','solver_metrics'):
            assert encode(x[field])==encode(y[field]),(x['case'],field)
        for field in ('verified_simplifications','verified_probe_attempts','probe_attempts'):
            assert x['discovery_metrics'].get(field,0)==y['discovery_metrics'].get(field,0)
    archives=[]
    for r in results.values():
        p=ROOT/r['archive_path'];assert sha(p)==r['archive_sha256']
        digest=hashlib.sha256();size=0
        with gzip.open(p,'rb') as stream:
            while raw:=stream.read(1024*1024):digest.update(raw);size+=len(raw)
        assert digest.hexdigest()==r['database_sha256'] and size==r['database_bytes']
        assert r['audit']['bytes_unchanged']
        archives.append(dict(path=r['archive_path'],bytes=size,raw_sha256=digest.hexdigest()))
    provenance=json.loads((out/'diagnostic-provenance.json').read_text())
    for name,digest in provenance['fingerprints'].items():assert sha(ROOT/name)==digest
    for name,digest in provenance['reports'].items():assert sha(out/name)==digest
    identity=json.loads((out/'identity-diagnostic.json').read_text())
    assert identity['script_sha256']==sha(ROOT/'experiments/diagnose_cnf_reconstruction_identity.py')
    assert identity['evictions']==0
    assert identity['calls']==identity['distinct_identities']+identity['indexed_hits']
    assert identity['distinct_identities']-identity['distinct_structural_values']==identity['equal_value_new_identities']==370
    assert sum(int(k)*v for k,v in identity['identities_per_value_histogram'].items())==identity['distinct_identities']
    for name in ('experiments/cnf_single_pass_inventory.py','experiments/cnf_indexed_check.py','solver/test_cnf_indexed_check.py'):
        assert subprocess.check_output(['git','show','f6fb244:'+name],cwd=ROOT)==(ROOT/name).read_bytes()
    tex=ROOT/'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    previous=subprocess.check_output(['git','show','3d032ef:paper/bounded_domain_sat_and_amortized_reasoning.tex'],cwd=ROOT,text=True)
    current=tex.read_text();pattern=r'\\begin\{proof\}(?:\[[^\]]*\])?.*?\\end\{proof\}'
    old=re.findall(pattern,previous,re.S);new=re.findall(pattern,current,re.S)
    assert old==new and len(old)==63
    labels=re.findall(r'\\label\{([^}]+)\}',current);assert len(labels)==len(set(labels))==224
    for name in ('tests','lean','latex'):
        text=Path('/tmp/oraclemachines-reconstruction-limits-'+name+'.log').read_text()
        if name=='tests':assert re.search(r'Ran 490 tests in [0-9.]+s\s+OK',text)
        if name=='lean':assert '4148 declarations, 1988 theorem declarations' in text and 'Build completed successfully' in text
        (out/(name+'-validation.txt')).write_text(text.rstrip()+'\n')
    latex=(ROOT/'paper/bounded_domain_sat_and_amortized_reasoning.log').read_text()
    assert not re.search(r'(?:LaTeX|Package .*?) Warning|Overfull|Underfull',latex)
    data=dict(script_sha256=sha(Path(__file__)),report_sha256=sha(path),archives=archives,
        python_tests=490,lean_declarations=4148,lean_theorems=1988,unchanged_proofs=63,unique_labels=224,
        runtime_fingerprints_match=True,matched_evidence=True,diagnostic_hashes_match=True,
        manuscript_sha256=sha(tex),pdf_sha256=sha(ROOT/'paper/bounded_domain_sat_and_amortized_reasoning.pdf'),
        added_runtime={name:sha(ROOT/name) for name in ('experiments/cnf_shared_reconstruction.py','solver/test_cnf_shared_reconstruction.py')},
        limitations=['The new full prepared-corpus comparison was not run after the negative control and pilots',
                    'No new Lean refinement; diagnostics identify a reuse limit, not a performance improvement'])
    target.write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data))


if __name__=='__main__':main()
