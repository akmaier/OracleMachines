#!/usr/bin/env python3
"""Validate the retained elimination comparisons, proof additions and provenance."""
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
sys.path.insert(0, str(ROOT))
from experiments.compare_cnf_retained_plans import sha
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_clause_mask import table_digest


def main():
    out = ROOT / 'experiments/results/cnf-variable-elimination-probe'
    target = out / 'validation.json'
    if target.exists(): raise FileExistsError(target)
    analysis = json.loads((out / 'structure-reuse.json').read_text())
    assert analysis['script_sha256'] == sha(ROOT / 'experiments/analyze_cnf_variable_elimination.py')
    initial = json.loads((out / 'initial-provenance.json').read_text())
    assert initial['script_sha256'] == sha(out / 'initial-opportunity.py')
    assert initial['report_sha256'] == sha(out / 'raw-opportunity.json')
    archives = []; reports = {}; closures = {}
    for suite, size in (('frontier', 99), ('originals', 83)):
        path = ROOT / ('experiments/results/cnf-variable-elimination-' + suite + '/report.json')
        report = json.loads(path.read_text()); reports[suite] = sha(path)
        assert report['source_commit'].startswith('e7a806b')
        assert report['frontier_sha256'] == sha(out / 'raw-opportunity.json')
        assert report['input_report_sha256'] == sha(ROOT / 'experiments/results/cnf-prepared-probes-full/report.json')
        assert len(report['cases']) == size
        for file, digest in report['fingerprints'].items(): assert sha(ROOT / file) == digest, file
        modes = {r['mode']: r for r in report['results']}; residuals = []
        closures[suite] = {}
        for mode, result in modes.items():
            assert result['audit']['bytes_unchanged']
            assert len(result['records']) == size
            closures[suite][mode] = sum(r['summary']['closed'] for r in result['records'])
            for old, new in zip(modes['baseline']['records'], result['records'], strict=True):
                for field in ('case', 'answer', 'profile', 'solver_metrics'):
                    assert encode(old[field]) == encode(new[field]), (suite, mode, field)
                if old['summary']['closed']: assert new['summary']['closed']
            p = ROOT / result['archive_path']; assert sha(p) == result['archive_sha256']
            with tempfile.TemporaryDirectory() as tmp:
                dbpath = Path(tmp) / 'a.db'
                with gzip.open(p, 'rb') as src, dbpath.open('wb') as dst: shutil.copyfileobj(src, dst)
                assert sha(dbpath) == result['database_sha256'] and dbpath.stat().st_size == result['database_bytes']
                db = sqlite3.connect(f'file:{dbpath}?mode=ro', uri=True)
                residuals.append(table_digest(db, 'cnf_residual_v1'))
                assert db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'; db.close()
            graph = next(r for r in analysis['rows'] if r['suite'] == suite and r['mode'] == mode)
            assert graph['report_sha256'] == sha(path)
            assert graph['accepted_edges'] == result['edge_models'].get('edges', 0)
            assert graph['accepted_edges'] == result['edge_models'].get('sat', 0) + result['edge_models'].get('unsat', 0)
            archives.append(dict(path=result['archive_path'], database_sha256=result['database_sha256'], bytes=result['database_bytes']))
        assert residuals[0] == residuals[1] == residuals[2]
        pure_closed = {r['case'] for r in modes['pure']['records'] if r['summary']['closed']}
        bounded_closed = {r['case'] for r in modes['bounded']['records'] if r['summary']['closed']}
        assert pure_closed <= bounded_closed
    assert closures['frontier'] == dict(baseline=0, pure=14, bounded=37)
    assert closures['originals'] == dict(baseline=0, pure=11, bounded=29)
    tex = ROOT / 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    old = subprocess.check_output(['git', 'show', '7b59e9c:' + str(tex.relative_to(ROOT))], cwd=ROOT, text=True)
    pattern = r'\\begin\{proof\}(?:\[[^\]]*\])?.*?\\end\{proof\}'
    proofs = re.findall(pattern, tex.read_text(), re.S)
    assert proofs == re.findall(pattern, old, re.S) and len(proofs) == 63
    labels = re.findall(r'\\label\{([^}]+)\}', tex.read_text())
    assert len(labels) == len(set(labels)) == 225
    for name, log in [('tests', 'full'), ('lean', 'lean'), ('latex', 'latex')]:
        contents = Path('/tmp/oraclemachines-bve-' + log + '.log').read_text()
        if name == 'tests': assert re.search(r'Ran 501 tests in [0-9.]+s\s+OK', contents)
        if name == 'lean': assert '4168 declarations, 2004 theorem declarations' in contents and 'Build completed successfully' in contents
        (out / (name + '-validation.txt')).write_text(contents.rstrip() + '\n')
    assert not re.search(r'(?:LaTeX|Package .*?) Warning|Overfull|Underfull', tex.with_suffix('.log').read_text())
    data = dict(script_sha256=sha(Path(__file__)), reports=reports, archives=archives, closures=closures,
        python_tests=501, lean_declarations=4168, lean_theorems=2004, old_proof_blocks_preserved=63,
        unique_labels=225, matched_residual_evidence=True, runtime_fingerprints_match=True,
        analysis_sha256=sha(out / 'structure-reuse.json'), manuscript_sha256=sha(tex), pdf_sha256=sha(tex.with_suffix('.pdf')),
        lean_source_sha256=sha(ROOT / 'formal/OracleMachines/VariableElimination.lean'),
        limitations=['The full 1497-source corpus was not rerun; whole-input gains refer to its 83 prior unresolved inputs',
                     'Lean establishes the semantic projection identity, not a refinement of the Python implementation'])
    target.write_text(json.dumps(data, indent=2)+'\n')
    print(json.dumps(dict(closures=closures, archives=len(archives), python_tests=501, unchanged_proofs=63)))


if __name__ == '__main__': main()
