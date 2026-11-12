#!/usr/bin/env python3
"""Read-only exact clause-growth barriers on the new selected frontier."""
from collections import Counter
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_retained_plans import sha


def candidates(cnf):
    clauses = set(map(frozenset, cnf)); assert len(clauses) == len(cnf)
    variables = sorted({abs(l) for c in clauses for l in c}); rows = []
    for v in variables:
        positive = [c-{v} for c in clauses if v in c]
        negative = [c-{-v} for c in clauses if -v in c]
        retained = {c for c in clauses if v not in c and -v not in c}
        added = set()
        for a in positive:
            for b in negative:
                r = a | b
                if not any(-l in r for l in r) and r not in retained: added.add(r)
        reduced = {r for r in added if not any(c <= r for c in retained)}
        removed = len(positive)+len(negative)
        rows.append(dict(variable=v, pairs=len(positive)*len(negative),
            clause_delta=len(added)-removed, subsumed_clause_delta=len(reduced)-removed,
            literal_delta=sum(map(len, added))-sum(len(c) for c in clauses if v in c or -v in c)))
    return sorted(rows, key=lambda r: (r['pairs'], r['variable']))


def main(output):
    if output.exists(): raise FileExistsError(output)
    started = time.perf_counter(); reports = []
    for suite in ('remaining', 'originals'):
        path = Path('experiments/results/cnf-clause-bound-elimination-'+suite+'/report.json')
        data = json.loads(path.read_text()); mode = next(r for r in data['results'] if r['mode']=='clause_bound')
        leaves = []; stats = Counter(); plain_hist = Counter(); subsumed_hist = Counter()
        for item in mode['frontier']:
            cnf = item['cnf']; all_rows = candidates(cnf)
            eligible = [r for r in all_rows[:64] if r['pairs'] <= 64]
            plain = min((r['clause_delta'] for r in eligible), default=None)
            sub = min((r['subsumed_clause_delta'] for r in eligible), default=None)
            full = min((r['clause_delta'] for r in all_rows), default=None)
            # The independent observer should agree that this terminal policy
            # cannot make a further plain step under its actual budgets.
            assert plain is None or plain > 0
            stats['leaves'] += 1
            stats['pair_bounded_candidates_exist'] += bool(eligible)
            stats['plain_candidate_without_caps'] += full is not None and full <= 0
            stats['retained_subsumption_candidate_with_caps'] += sub is not None and sub <= 0
            for bound in (1, 2, 4, 8):
                stats['plain_delta_at_most_'+str(bound)] += plain is not None and plain <= bound
            plain_hist[str(plain)] += 1; subsumed_hist[str(sub)] += 1
            leaves.append(dict(key_sha256=item['key_sha256'], clauses=len(cnf),
                variables=len({abs(l) for c in cnf for l in c}), literals=sum(map(len,cnf)),
                width=max(map(len,cnf), default=0), min_clause_delta=plain,
                min_subsumed_clause_delta=sub, min_clause_delta_without_caps=full, candidates=all_rows))
        reports.append(dict(suite=suite, report_sha256=sha(path), statistics=dict(stats),
            plain_delta_histogram=dict(plain_hist), subsumed_delta_histogram=dict(subsumed_hist), leaves=leaves))
    result = dict(script_sha256=sha(Path(__file__)), seconds=time.perf_counter()-started, reports=reports,
        limitations=['Read-only all-pivot diagnostics, charged separately from acquisition; no policy or coverage gain.',
        'A local clause-growth obstruction under one order is not a lower bound on other elimination orders or arbitrary SAT.',
        'With a fixed opposing-pair cap B and decreasing support, an elimination-only chain has at most m0+B*n0 clauses; this does not guarantee an eligible pivot or bound the whole planner.',
        'Retained-clause subsumption opportunities need integrated checking and total-cost comparison; prior fallback was negative.'])
    output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='leaves'} for r in reports]))


if __name__=='__main__': main(Path(sys.argv[1]))
