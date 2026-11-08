#!/usr/bin/env python3
"""Explain simplification coverage, policy costs, reuse and surviving misses."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile


def analyze(directory):
    report = json.loads((directory/'report.json').read_text())
    cases = report['cases']
    records = {(r['mode'], r['case']): r for r in report['records']}
    archive = next(a for a in report['archives'] if a['mode'] == 'simplified2')
    raw = gzip.decompress((directory/archive['path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == archive['database_sha256']
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)/'archive.sqlite3'; path.write_bytes(raw)
        db = sqlite3.connect(path)
        nodes = {key: json.loads(value) for key, value in db.execute('SELECT * FROM cnf_patterns_v1')}
        db.close()
    hashes = {hashlib.sha256(key.encode()).hexdigest(): key for key in nodes}

    def closed(mode, i):
        return records[mode, i]['discovery']['summary']['closed']

    def chain(key):
        result = []
        while True:
            node = nodes[key]
            step = dict(kind=node['kind'], shape=node['profile']['shape'],
                        hash=hashlib.sha256(key.encode()).hexdigest())
            if node['kind'] == 'simplify':
                step['simplification'] = node['profile']['simplification']
            result.append(step)
            if node['kind'] not in ('project', 'simplify'):
                return result
            key = node['edge']['key']

    totals = defaultdict(lambda: dict(total_seconds=0., discovery_seconds=0., solver_seconds=0., open=0))
    misses, interesting = [], []
    for i, case in enumerate(cases):
        row = records['simplified2', i]
        g = totals[case['group']]
        for name, value in [('total_seconds', row['total_seconds']),
                            ('discovery_seconds', row['discovery']['seconds']),
                            ('solver_seconds', row['solver_seconds'])]:
            g[name] += value
        g['open'] += not closed('simplified2', i)
        key = hashes[row['discovery']['root_hash']]
        if not closed('simplified2', i):
            misses.append(dict(case=i, group=case['group'], label=case.get('label'),
                               shape=row['discovery']['profile']['shape'],
                               unresolved_literals=row['discovery']['dag']['unresolved_distinct_literals']))
        if (case.get('label') == 'coupled_matching_parity' or
                case['group'] in ('simplification_control', 'simplification_variant', 'growing_simplification') or
                (i < 664 and not closed('units2', i) and closed('simplified2', i))):
            interesting.append(dict(case=i, group=case['group'], label=case.get('label'),
                closed={mode:closed(mode, i) for mode in ('projection0', 'simplified0', 'projection2', 'units2', 'pure2', 'simplified2')},
                chain=chain(key)))
    comparisons = {}
    for mode in ('units2', 'pure2', 'simplified2'):
        comparisons[mode] = dict(
            gained=[i for i in range(len(cases)) if not closed('projection2', i) and closed(mode, i)],
            lost=[i for i in range(len(cases)) if closed('projection2', i) and not closed(mode, i)],
            original664_open=[i for i in range(664) if not closed(mode, i)])
    simplified_edges = Counter(n['edge']['key'] for n in nodes.values() if n['kind'] == 'simplify')
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                comparisons=comparisons, group_costs=totals, misses=misses, interesting=interesting,
                node_kinds=dict(Counter(n['kind'] for n in nodes.values())),
                simplified_edges=sum(simplified_edges.values()), distinct_simplified_children=len(simplified_edges),
                reused_child_references=sum(n-1 for n in simplified_edges.values()),
                limitations=['Edge reuse counts are within the same versioned policy/depth; not cross-policy sharing',
                             'Closure is certified structural coverage, not the SAT verdict or a runtime bound',
                             'Pure-chain controls contain a disjoint signed chain plus matching with a pure bridge',
                             'Costs are single sequential samples; native memory and source deletion are not measured'],
                next_gap='38 random 3-CNFs still lack depth-two coverage and dominate discovery time; profile their retained alternatives before choosing structure-aware conditioning. The remaining renamed wide affine case also exceeds direct encoding budget.')


if __name__ == '__main__':
    directory = Path(sys.argv[1])
    (directory/'mechanisms.json').write_text(json.dumps(analyze(directory), indent=2)+'\n')
