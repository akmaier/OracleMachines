#!/usr/bin/env python3
"""Explain projected supports, cap failures and retained discovery misses."""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile


def analyze(directory):
    report = json.loads((directory/'report.json').read_text())
    records = {(r['mode'], r['case']): r for r in report['records']}
    archive = next(a for a in report['archives'] if a['mode'] == 'projection2')
    raw = gzip.decompress((directory/archive['path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == archive['database_sha256']
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)/'archive.sqlite3';path.write_bytes(raw)
        db = sqlite3.connect(path)
        nodes = {key: json.loads(value) for key, value in db.execute('SELECT * FROM cnf_patterns_v1')}
        db.close()
    hashes = {hashlib.sha256(key.encode()).hexdigest(): key for key in nodes}
    roots = []
    for i, case in enumerate(report['cases']):
        row = records['projection2', i];node = nodes[hashes[row['discovery']['root_hash']]]
        projection = node['profile']['projection']
        previous = records['affine2', i]['discovery']['summary']['closed']
        current = row['discovery']['summary']['closed']
        if node['kind'] != 'project' and projection['status'] != 'encoding_cap' and current:
            continue
        item = dict(case=i, group=case['group'], label=case.get('label'),
                    previous_closed=previous, closed=current, root_kind=node['kind'],
                    shape=node['profile']['shape'], projection_status=projection['status'],
                    unresolved_literals=row['discovery']['dag']['unresolved_distinct_literals'])
        if projection['status'] != 'not_applicable':
            cert = projection['certificate']
            item.update(eliminated_variables=len(cert['internal']),
                        interface=node['profile']['evidence']['affine_conflict']['interface_variables'],
                        boundary_widths=[cert['rows'][j]['mask'].bit_count() for j in cert['boundary']])
        if node['kind'] == 'project':
            child = nodes[node['edge']['key']]
            item.update(projected_shape=child['profile']['shape'], target_kind=child['kind'],
                        target_cnf=child['cnf'], parent_binding=node['edge']['names'])
        roots.append(item)
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                archived_node_kinds=dict(Counter(n['kind'] for n in nodes.values())),
                archived_projection_statuses=dict(Counter(n['profile']['projection']['status'] for n in nodes.values())),
                roots=roots,
                next_gap='Matching/parity shrinks but retains one positive-only coupling variable; strict matching recognition and frequency-first conditioning miss its simple extension.')


if __name__ == '__main__':
    directory = Path(sys.argv[1])
    (directory/'mechanisms.json').write_text(json.dumps(analyze(directory), indent=2)+'\n')
