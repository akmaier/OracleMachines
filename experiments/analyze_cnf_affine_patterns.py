#!/usr/bin/env python3
"""Explain coverage gains and residual interfaces from the preserved study."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile


def analyze(directory):
    report = json.loads((directory/'report.json').read_text())
    rows = {(r['mode'], r['case']): r for r in report['records']}
    archive = next(a for a in report['archives'] if a['mode'] == 'affine2')
    raw = gzip.decompress((directory/archive['path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == archive['database_sha256']
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)/'audit.sqlite3';path.write_bytes(raw)
        db = sqlite3.connect(path)
        nodes = {key: json.loads(payload) for key, payload in db.execute('SELECT * FROM cnf_patterns_v1')}
        db.close()
    hashes = {hashlib.sha256(key.encode()).hexdigest(): key for key in nodes}
    gains, unresolved = [], []
    for i, case in enumerate(report['cases']):
        baseline, revised = rows['baseline2', i]['discovery'], rows['affine2', i]['discovery']
        root = hashes[revised['root_hash']]
        if not revised['summary']['closed']:
            cert = nodes[root]['profile']['evidence']['explicit_affine']
            summary = nodes[root]['profile']['evidence']['affine_conflict']
            unresolved.append(dict(case=i, group=case['group'], label=case.get('label'),
                shape=revised['profile']['shape'], affine_summary=summary,
                equation_widths=[len(e['variables']) for e in cert['equations']],
                selected_unresolved_literals=revised['dag']['unresolved_distinct_literals']))
        if baseline['summary']['closed'] or not revised['summary']['closed']:
            continue
        seen, stack, leaves = set(), [root], []
        while stack:
            key = stack.pop()
            if key in seen:
                continue
            seen.add(key);node = nodes[key]
            if node['kind'] == 'and':
                stack.extend(e['key'] for e in node['edges'])
            elif node['kind'] == 'or':
                stack.extend(e['key'] for e in node['alternatives'][node['selected']]['edges'])
            elif not any(v == 'recognized' for name, v in node['profile']['outcomes'].items()
                         if name not in ('explicit_affine', 'affine_conflict')):
                cert = node['profile']['evidence']['explicit_affine']
                leaves.append(dict(summary=node['profile']['evidence']['affine_conflict'],
                    equation_widths=[len(e['variables']) for e in cert['equations']], cnf=node['cnf']))
        gains.append(dict(case=i, group=case['group'], label=case.get('label'), new_family_leaves=leaves))
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                coverage_gains=gains, unresolved=unresolved,
                interpretation='All random gains use affine-only leaves with equations of width at most two; this is not evidence of large hidden XOR systems.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    directory = parser.parse_args().directory
    result = analyze(directory)
    for gain in result['coverage_gains']:
        if gain['group'] in ('random', 'new_random'):
            assert all(max(leaf['equation_widths'], default=0) <= 2 for leaf in gain['new_family_leaves'])
    (directory/'mechanisms.json').write_text(json.dumps(result, indent=2)+'\n')
