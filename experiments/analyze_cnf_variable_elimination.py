#!/usr/bin/env python3
"""Read-only evidence and remaining growth barriers after bounded elimination."""
from collections import Counter
import gzip
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_retained_plans import sha


def opportunity(cnf):
    clauses = [frozenset(c) for c in cnf]
    variables = sorted({abs(l) for c in clauses for l in c})
    candidates = []
    for variable in variables:
        pos = [c - {variable} for c in clauses if variable in c]
        neg = [c - {-variable} for c in clauses if -variable in c]
        pairs = len(pos) * len(neg)
        if pairs > 64:
            continue
        retained = {c for c in clauses if variable not in c and -variable not in c}
        added = set()
        for p in pos:
            for n in neg:
                merged = p | n
                if not any(-lit in merged for lit in merged) and merged not in retained:
                    added.add(merged)
        removed_literals = sum(len(c) for c in clauses if variable in c or -variable in c)
        delta_m = len(added) - len(pos) - len(neg)
        delta_l = sum(map(len, added)) - removed_literals
        # Diagnostic only: a retained subclause would imply a new resolvent.
        # No deleted source clause or unretained new resolvent can justify omission.
        smaller = {c for c in added if not any(d <= c for d in retained)}
        candidates.append(dict(variable=variable, pairs=pairs, clause_delta=delta_m, literal_delta=delta_l,
            retained_subsumption_clause_delta=len(smaller)-len(pos)-len(neg),
            retained_subsumption_literal_delta=sum(map(len, smaller))-removed_literals,
            resolvents_subsumed_by_retained=len(added)-len(smaller)))
    return dict(variables=len(variables), pair_bounded_candidates=len(candidates),
        non_growing=sum(c['clause_delta'] <= 0 and c['literal_delta'] <= 0 for c in candidates),
        subsumption_non_growing=sum(c['retained_subsumption_clause_delta'] <= 0 and c['retained_subsumption_literal_delta'] <= 0 for c in candidates),
        candidates=candidates)


def main(output):
    if output.exists(): raise FileExistsError(output)
    rows = []; archives = []
    for suite in ('frontier', 'originals'):
        report_path = Path('experiments/results/cnf-variable-elimination-' + suite + '/report.json')
        report = json.loads(report_path.read_text()); results = {r['mode']: r for r in report['results']}
        closed = {m: {r['case'] for r in x['records'] if r['summary']['closed']} for m, x in results.items()}
        for mode, result in results.items():
            assert sha(result['archive_path']) == result['archive_sha256']
            groups = {}
            for case, record in zip(report['cases'], result['records'], strict=True):
                group = groups.setdefault(case['group'], dict(cases=0, closed=0))
                group['cases'] += 1; group['closed'] += record['summary']['closed']
            incoming = Counter(); types = Counter(); target_kinds = Counter(); removed_variables = 0
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'archive.db'
                with gzip.open(result['archive_path'], 'rb') as src, path.open('wb') as dst: shutil.copyfileobj(src, dst)
                assert sha(path) == result['database_sha256']
                db = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
                for payload, in db.execute('SELECT payload FROM cnf_patterns_v1 WHERE payload LIKE ?', ('%"kind":"eliminate"%',)):
                    node = json.loads(payload); x = node['elimination']['variable']
                    p = sum(x in c for c in node['cnf']); n = sum(-x in c for c in node['cnf'])
                    types['pure' if p*n == 0 else 'one_occurrence_side' if min(p,n) == 1 else 'both_sides_multiple'] += 1
                    target = json.loads(db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (node['edge']['key'],)).fetchone()[0])
                    incoming[node['edge']['key']] += 1; target_kinds[target['kind']] += 1
                    decrease = len({abs(l) for c in node['cnf'] for l in c}) - len({abs(l) for c in target['cnf'] for l in c})
                    assert decrease > 0
                    removed_variables += decrease
                db.close()
                assert sha(path) == result['database_sha256']
            archives.append(dict(path=result['archive_path'], database_sha256=result['database_sha256'], bytes=result['database_bytes']))
            opportunities = []
            if mode == 'bounded':
                for leaf in result['frontier']:
                    opportunities.append(dict(key_sha256=leaf['key_sha256'], **opportunity(leaf['cnf'])))
            gains = sorted(closed[mode] - closed['baseline'])
            rows.append(dict(suite=suite, mode=mode, report_sha256=sha(report_path), closed=len(closed[mode]),
                provenance_groups=groups,
                gains_original_indices=[report['cases'][i].get('original_case', i) for i in gains],
                mixed_gain_over_pure=len(closed[mode] - closed['pure']) if mode == 'bounded' else None,
                pure_closures_lost=sorted(closed['pure'] - closed[mode]) if mode == 'bounded' else None,
                elimination_types=dict(types), target_kinds=dict(target_kinds), accepted_edges=sum(incoming.values()),
                distinct_elimination_targets=len(incoming), shared_elimination_targets=sum(n > 1 for n in incoming.values()),
                repeated_incoming_edges=sum(n-1 for n in incoming.values()), removed_variable_sum=removed_variables,
                remaining_frontier_leaves=len(result['frontier']), opportunities=opportunities,
                leaves_with_pair_bounded_candidates=sum(r['pair_bounded_candidates'] > 0 for r in opportunities),
                leaves_with_current_non_growing=sum(r['non_growing'] > 0 for r in opportunities),
                leaves_with_retained_subsumption_opportunity=sum(r['subsumption_non_growing'] > 0 for r in opportunities)))
    data = dict(script_sha256=sha(Path(__file__)), rows=rows, archives=archives,
        limitations=['Read-only analysis of the fully cold-checked comparison archives; no new runtime comparison',
            'Shared targets count physical references under the same exact configuration; do not measure temporal cache-hit savings',
            'Retained-clause subsumption is a candidate opportunity only: no new checker integration or coverage gain is measured',
            'Candidate diagnostic examines all variables under the pair cap, beyond the runtime candidate cap if necessary',
            'Whole-input conclusions apply to the 83 previously unresolved sources, not a new run over all 1497 inputs'])
    output.write_text(json.dumps(data, separators=(',', ':')) + '\n')
    print(json.dumps([{k:v for k,v in r.items() if k not in ('opportunities','gains_original_indices')} for r in rows]))


if __name__ == '__main__': main(Path(sys.argv[1]))
