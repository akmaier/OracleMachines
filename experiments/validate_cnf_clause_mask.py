#!/usr/bin/env python3
"""Bind clause-overlap diagnostics, both matched controls and unchanged proofs."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.compare_cnf_retained_plans import sha
from experiments.cnf_pattern_inventory import encode


def main():
    out = ROOT / 'experiments/results/cnf-clause-mask-pilot'
    target = out / 'validation.json'
    if target.exists():
        raise FileExistsError(target)
    baseline = ROOT / 'experiments/results/cnf-prepared-probes-full/report.json'
    fields = ('case', 'answer', 'root_sha256', 'solver_root_sha256', 'profile',
              'summary', 'archive_nodes', 'archive_payload_units', 'solver_metrics')
    archives, comparisons, report_hashes = [], [], {}
    counts_by_order = []
    for name, order in (('cnf-clause-mask-empty', ['scan', 'masked']),
                        ('cnf-clause-mask-empty-reverse', ['masked', 'scan'])):
        path = ROOT / 'experiments/results' / name / 'report.json'
        report = json.loads(path.read_text())
        report_hashes[str(path.relative_to(ROOT))] = sha(path)
        assert report['input_report_sha256'] == sha(baseline)
        assert report['source_commit'].startswith('c7914b5')
        assert report['execution_order'] == order
        for p, digest in report['fingerprints'].items():
            assert sha(ROOT / p) == digest, p
        modes = {r['mode']: r for r in report['results']}
        a, b = modes['scan'], modes['masked']
        assert a['table_digests'] == b['table_digests']
        assert a['database_sha256'] == b['database_sha256']
        assert len(a['records']) == len(b['records']) == 96
        for x, y in zip(a['records'], b['records'], strict=True):
            for field in fields:
                assert encode(x[field]) == encode(y[field]), (name, x['case'], field)
            for field in ('discovery_metrics', 'prepared_metrics'):
                # All non-reconstruction work remains identical, not just SAT answers.
                def remainder(metrics):
                    return {k: v for k, v in metrics.items()
                            if not k.startswith(('single_check_', 'clause_mask_')) and v}
                assert remainder(x[field]) == remainder(y[field]), (name, x['case'], field)
        counters = {}
        for mode, r in modes.items():
            counters[mode] = sum((Counter(row['discovery_metrics']) + Counter(row['prepared_metrics'])
                                  for row in r['records']), Counter())
            p = ROOT / r['archive_path']
            assert sha(p) == r['archive_sha256']
            digest = hashlib.sha256(); size = 0
            with gzip.open(p, 'rb') as stream:
                while raw := stream.read(1024 * 1024):
                    digest.update(raw); size += len(raw)
            assert digest.hexdigest() == r['database_sha256'] and size == r['database_bytes']
            assert r['audit']['bytes_unchanged']
            archives.append(dict(path=r['archive_path'], bytes=size, raw_sha256=digest.hexdigest()))
        counts_by_order.append(counters)
        previous, masked = counters['scan'], counters['masked']
        assert previous['single_check_calls'] == masked['clause_mask_calls'] == 15071
        assert previous['single_check_clause_positions'] == masked['clause_mask_positions'] == 1529672
        work = masked['clause_mask_preparation_literals'] + masked['clause_mask_scanned_literals']
        assert work == 1873711 and previous['single_check_literal_visits'] == 4173407
        totals = {m: sum(row['total_seconds'] for row in r['records']) for m, r in modes.items()}
        comparisons.append(dict(name=name, execution_order=order, total_seconds=totals,
            discovery_seconds={m: sum(row['discovery_seconds'] for row in r['records']) for m, r in modes.items()},
            total_change_percent=100 * (totals['masked'] / totals['scan'] - 1),
            cold_seconds={m: r['audit']['seconds'] for m, r in modes.items()},
            warm_seconds={m: r['warm_combined_seconds'] for m, r in modes.items()},
            peak_python_bytes={m: r['allocation']['peak_python_bytes'] for m, r in modes.items()},
            closed={m: sum(row['summary']['closed'] for row in r['records']) for m, r in modes.items()},
            previous_literal_visits=previous['single_check_literal_visits'], preparation_plus_scans=work,
            literal_work_reduction_percent=100 * (1 - work / previous['single_check_literal_visits'])))
    assert counts_by_order[0] == counts_by_order[1]
    assert len({r['raw_sha256'] for r in archives}) == 1
    overlap = json.loads((out / 'overlap.json').read_text())
    pilot = json.loads((out / 'pilot.json').read_text())
    for data, script in ((overlap, 'measure_cnf_clause_overlap.py'), (pilot, 'probe_cnf_clause_mask.py')):
        assert data['input_report_sha256'] == sha(baseline)
        assert data['script_sha256'] == sha(ROOT / 'experiments' / script)
    for p, digest in pilot['fingerprints'].items():
        assert sha(ROOT / p) == digest
    for row in overlap['rows']:
        actual = next(r for r in pilot['rows'] if r['case'] == row['case'] and r['mode'] == 'ClauseMaskInventory')
        for observed, measured in [('fifo_clause_hits', 'clause_mask_hits'),
                                   ('fifo_clause_admissions', 'clause_mask_admissions'),
                                   ('fifo_preparation_literals', 'clause_mask_preparation_literals'),
                                   ('fifo_evictions', 'clause_mask_evictions')]:
            assert row['counts'][observed] == actual['metrics'][measured]
        assert row['summary'] == actual['summary']
    for case in (1194, 1441, 1471):
        rows = [r for r in pilot['rows'] if r['case'] == case]
        assert len(rows) == 2 and rows[0]['summary'] == rows[1]['summary']
        assert rows[1]['state']['peak_units'] <= 32768
    tex = ROOT / 'paper/bounded_domain_sat_and_amortized_reasoning.tex'
    old = subprocess.check_output(['git', 'show', '88907a8:' + str(tex.relative_to(ROOT))], cwd=ROOT, text=True)
    pattern = r'\\begin\{proof\}(?:\[[^\]]*\])?.*?\\end\{proof\}'
    proofs = re.findall(pattern, tex.read_text(), re.S)
    assert proofs == re.findall(pattern, old, re.S) and len(proofs) == 63
    labels = re.findall(r'\\label\{([^}]+)\}', tex.read_text())
    assert len(labels) == len(set(labels)) == 224
    for name, log in [('tests', 'full'), ('lean', 'lean'), ('latex', 'latex')]:
        contents = Path('/tmp/oraclemachines-clause-mask-' + log + '.log').read_text()
        if name == 'tests':
            assert re.search(r'Ran 496 tests in [0-9.]+s\s+OK', contents)
        elif name == 'lean':
            assert '4148 declarations, 1988 theorem declarations' in contents and 'Build completed successfully' in contents
        (out / (name + '-validation.txt')).write_text(contents.rstrip() + '\n')
    latex = tex.with_suffix('.log').read_text()
    assert not re.search(r'(?:LaTeX|Package .*?) Warning|Overfull|Underfull', latex)
    analysis = dict(comparisons=comparisons, decision='Keep optional and disabled; prioritize checked variable elimination on unresolved cores',
        limitations=['Two opposite-order controls use the same published 96 synthetic inputs; not an independent holdout',
                     'Python allocation samples four inputs, not native SQLite, RSS or full-history peak',
                     'No new full prepared-corpus run, structural coverage claim or Lean refinement'])
    (out / 'analysis.json').write_text(json.dumps(analysis, indent=2) + '\n')
    data = dict(script_sha256=sha(Path(__file__)), source_checkpoint='c7914b5', reports=report_hashes,
        diagnostics={p.name: sha(p) for p in (out / 'overlap.json', out / 'pilot.json', out / 'analysis.json')},
        archives=archives, python_tests=496, lean_declarations=4148, lean_theorems=1988,
        unchanged_proofs=63, unique_labels=224, matched_evidence=True, matched_non_reconstruction_counters=True,
        observer_matches_actual_cache=True, manuscript_sha256=sha(tex), pdf_sha256=sha(tex.with_suffix('.pdf')))
    target.write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(dict(python_tests=496, unchanged_proofs=63, archives=len(archives), comparisons=comparisons)))


if __name__ == '__main__':
    main()
