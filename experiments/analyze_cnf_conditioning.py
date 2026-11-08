#!/usr/bin/env python3
"""Persist conditioning gains, losses, exact paths and total acquisition costs."""
from collections import Counter, defaultdict
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile


def load_nodes(directory, entry):
    raw = gzip.decompress((directory/entry['path']).read_bytes())
    assert hashlib.sha256(raw).hexdigest() == entry['database_sha256']
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp)/'archive.db';path.write_bytes(raw)
        db = sqlite3.connect(path)
        nodes = {key:json.loads(value) for key,value in db.execute('SELECT * FROM cnf_patterns_v1')}
        db.close()
    return nodes


def selected_mechanism(nodes, key):
    stack, seen, kinds, families = [key], set(), Counter(), Counter()
    units = pure = 0
    while stack:
        current = stack.pop()
        if current in seen: continue
        seen.add(current); n = nodes[current]; kinds[n['kind']] += 1
        if n['kind'] == 'or':
            edges = n['alternatives'][n['selected']]['edges']
        elif n['kind'] == 'and': edges = n['edges']
        elif n['kind'] in ('project', 'simplify'): edges = [n['edge']]
        else: edges = []
        stack.extend(e['key'] for e in edges)
        if n['kind'] == 'simplify':
            cert = n['profile']['simplification']
            units += cert['unit_assignments'];pure += cert['pure_assignments']
        if n['kind'] == 'family':
            families.update(k for k,v in n['profile']['outcomes'].items() if v == 'recognized')
    root = nodes[key]
    return dict(root_kind=root['kind'],
                attempts=[dict(variable=a['variable'], **a['summary']) for a in root.get('alternatives', [])],
                selected=root.get('selected'), selected_node_kinds=dict(kinds),
                selected_family_overlaps=dict(families), selected_unit_assignments=units,
                selected_pure_assignments=pure)


def analyze(directory):
    report = json.loads((directory/'report.json').read_text())
    rows = {(r['mode'],r['case']):r for r in report['records']}
    cases = report['cases']; aggregates = {}
    for mode in report['modes']:
        grouped = defaultdict(lambda: dict(inputs=0, closed=0, total_seconds=0., discovery_seconds=0.,
                                            solver_seconds=0., inserted_nodes=0, candidates=0,
                                            unresolved_literals=0, rank_literal_visits=0))
        for i,c in enumerate(cases):
            r = rows[mode,i]; d = r['discovery']
            # Size-specific strata for genuinely fresh formulae.
            group = c['group']+(':'+c['label'] if c['group'] in ('holdout3','holdout_mixed') else '')
            a = grouped[group];a['inputs'] += 1;a['total_seconds'] += r['total_seconds'];a['solver_seconds'] += r['solver_seconds']
            if d:
                a['closed'] += d['summary']['closed'];a['discovery_seconds'] += d['seconds']
                a['inserted_nodes'] += d['metrics'].get('inserted_nodes',0)
                a['candidates'] += d['metrics'].get('conditioning_candidates',0)
                a['rank_literal_visits'] += d['metrics'].get('conditioning_rank_literal_visits',0)
                a['unresolved_literals'] += d['dag']['unresolved_distinct_literals']
        aggregates[mode] = grouped
    closed = lambda mode,i: rows[mode,i]['discovery']['summary']['closed']
    comparisons = {}
    for mode in ('shortest4','combined4','frequency8'):
        comparisons[mode] = dict(gained=[i for i in range(len(cases)) if closed(mode,i) and not closed('frequency4',i)],
                                lost=[i for i in range(len(cases)) if not closed(mode,i) and closed('frequency4',i)])
    comparisons['shortest4_vs_combined4'] = dict(
        gained=[i for i in range(len(cases)) if closed('shortest4',i) and not closed('combined4',i)],
        lost=[i for i in range(len(cases)) if not closed('shortest4',i) and closed('combined4',i)])
    changed = sorted(set(comparisons['shortest4']['gained']+comparisons['shortest4']['lost']))
    mechanisms, archive_stats = defaultdict(dict), {}
    for mode in ('frequency4','shortest4'):
        nodes = load_nodes(directory, next(a for a in report['archives'] if a['mode']==mode))
        hashes = {hashlib.sha256(k.encode()).hexdigest():k for k in nodes}
        references, kind_bytes = Counter(), Counter()
        for key,n in nodes.items():
            kind_bytes[n['kind']] += len(key.encode())+len(json.dumps(n,sort_keys=True,separators=(',',':')).encode())
            edges = (n['edges'] if n['kind']=='and' else [e for a in n['alternatives'] for e in a['edges']]
                     if n['kind']=='or' else [n['edge']] if n['kind'] in ('project','simplify') else [])
            references.update(e['key'] for e in edges)
        archive_stats[mode] = dict(kinds=dict(Counter(n['kind'] for n in nodes.values())),
            logical_bytes_by_kind=dict(kind_bytes),
            all_child_references=sum(references.values()), distinct_children=len(references),
            repeated_child_references=sum(v-1 for v in references.values()))
        for i in changed:
            key = hashes[rows[mode,i]['discovery']['root_hash']]
            mechanisms[i][mode] = selected_mechanism(nodes,key)
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                comparisons=comparisons, aggregates=aggregates, archive_stats=archive_stats,
                changed_cases=[dict(case=i,group=cases[i]['group'],label=cases[i].get('label'),
                                    modes=mechanisms[i]) for i in changed],
                remaining_shortest=[dict(case=i,group=c['group'],label=c.get('label'))
                                    for i,c in enumerate(cases) if not closed('shortest4',i)],
                limitations=['Source sizes and all alternatives are retained in report/archives',
                             'Signed renamings and edited development cases are transfer controls, not independent holdout',
                             'Equal depth and candidate caps are not equal realized work: stopping and residual sharing differ',
                             'Repeated child references measure graph sharing, not wall-time savings'])


if __name__ == '__main__':
    directory = Path(sys.argv[1])
    (directory/'mechanisms.json').write_text(json.dumps(analyze(directory),indent=2)+'\n')
