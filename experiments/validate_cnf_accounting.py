#!/usr/bin/env python3
"""Bind matched accounting evidence, runtime fingerprints and unchanged proofs."""
import gzip
import hashlib
import json
from pathlib import Path
import platform
import re
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.compare_cnf_retained_plans import sha
from experiments.cnf_pattern_inventory import encode


def main():
    parent = ROOT / 'experiments/results/cnf-accounting-full'
    target = parent / 'validation.json'
    if target.exists(): raise FileExistsError(target)
    checked = []
    prior_path = ROOT / 'experiments/results/cnf-retained-plans-full/report.json'
    prior = json.loads(prior_path.read_text())
    previous = {r['case']: r for r in prior['records'] if r['mode'] == 'retained'}
    for suite in ('full', 'fresh', 'empty'):
        directory = ROOT / ('experiments/results/cnf-accounting-' + suite)
        path = directory / 'report.json'; report = json.loads(path.read_text())
        assert report['input_report_sha256'] == sha(prior_path)
        for filename, digest in report['fingerprints'].items():
            assert sha(ROOT / filename) == digest, filename
        results = {r['mode']: r for r in report['results']}
        assert results['census']['table_digests'] == results['accounted']['table_digests']
        for a, b in zip(results['census']['records'], results['accounted']['records'], strict=True):
            for field in ('case', 'answer', 'root_sha256', 'solver_root_sha256', 'profile',
                          'summary', 'archive_nodes', 'archive_payload_units',
                          'discovery_metrics', 'prepared_metrics'):
                assert encode(a[field]) == encode(b[field]), (suite, a['case'], field)
            assert a['solver_metrics'] == {k: v for k, v in b['solver_metrics'].items()
                                          if not k.startswith('accounting_')}
            if suite == 'full':
                old = previous[a['case']]
                assert a['answer'] == old['answer']
                assert a['root_sha256'] == old['root_hash']
                assert encode(a['summary']) == encode(old['discovery']['summary'])
                assert encode(a['profile']) == encode(old['discovery']['profile'])
        for mode, result in results.items():
            archive = ROOT / result['archive_path']
            assert sha(archive) == result['archive_sha256']
            digest = hashlib.sha256(); size = 0
            with gzip.open(archive, 'rb') as stream:
                while raw := stream.read(1024 * 1024):
                    digest.update(raw); size += len(raw)
            assert digest.hexdigest() == result['database_sha256']
            assert size == result['database_bytes']
            assert result['audit']['bytes_unchanged']
            checked.append(dict(suite=suite, mode=mode, database_bytes=size,
                                database_sha256=digest.hexdigest(), report_sha256=sha(path)))
    manuscript = ROOT / 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    before = subprocess.check_output(['git', 'show', 'f883780:paper/bounded_domain_sat_and_amortized_reasoning.tex'], cwd=ROOT, text=True)
    after = manuscript.read_text()
    proof = r'\\begin\{proof\}(?:\[[^\]]*\])?.*?\\end\{proof\}'
    old_proofs = re.findall(proof, before, re.S); new_proofs = re.findall(proof, after, re.S)
    assert len(old_proofs) == 63 and old_proofs == new_proofs
    labels = re.findall(r'\\label\{([^}]+)\}', after)
    assert len(labels) == len(set(labels))
    # The full test run precedes the benchmark: verify that the tested runtime
    # and test file have not changed since that tested implementation commit.
    for filename in ('experiments/cnf_residual_dag.py', 'experiments/cnf_accounted_residuals.py',
                     'solver/test_cnf_accounted_residuals.py'):
        frozen = subprocess.check_output(['git', 'show', 'e32b33f:' + filename], cwd=ROOT)
        assert frozen == (ROOT / filename).read_bytes()
    python_log = Path('/tmp/oraclemachines-accounting-tests.log').read_text()
    lean_log = Path('/tmp/oraclemachines-accounting-lean.log').read_text()
    assert re.search(r'Ran 476 tests in [0-9.]+s\s+OK', python_log)
    assert '4148 declarations, 1988 theorem declarations' in lean_log and 'Build completed successfully' in lean_log
    (parent / 'python-validation.txt').write_text(python_log)
    (parent / 'lean-validation.txt').write_text(lean_log)
    data = dict(validation_script_sha256=sha(Path(__file__)), archives=checked,
                runtime_fingerprints_match=True, paired_records_match=True,
                prior_full_results_unchanged=True, python_tests=476,
                tested_runtime_commit='e32b33f', lean_declarations=4148, lean_theorems=1988,
                unchanged_manuscript_proofs=len(old_proofs), unique_labels=len(labels),
                python=platform.python_version(), sqlite=sqlite3.sqlite_version,
                platform=platform.platform(), manuscript_sha256=sha(manuscript),
                limitations=['No new Lean database refinement; original runtime and theorem scope remain unchanged',
                             'Archive checks bind the saved cold audits; they do not rerun the timed acquisitions'])
    target.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(dict(archives=len(checked), python_tests=476,
                         unchanged_proofs=len(old_proofs), unique_labels=len(labels))))


if __name__ == '__main__':
    main()
