#!/usr/bin/env python3
"""Retain exact growth margins after each additive policy, without acquiring nodes."""
from collections import Counter
import json
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_retained_plans import sha
from experiments.analyze_cnf_clause_bound_frontier import candidates


def main(output):
    if output.exists(): raise FileExistsError(output)
    started = time.perf_counter(); reports = []
    for suite in ('remaining', 'originals'):
        path = Path('experiments/results/cnf-additive-elimination-'+suite+'/report.json')
        data = json.loads(path.read_text())
        for mode in data['results']:
            allowance = mode['configuration'].get('clause_growth_limit', 0)
            leaves = []; stats = Counter(); plain_hist = Counter(); subsumed_hist = Counter()
            for item in mode['frontier']:
                cnf = item['cnf']; all_rows = candidates(cnf)
                eligible = [r for r in all_rows[:64] if r['pairs'] <= 64]
                plain = min((r['clause_delta'] for r in eligible), default=None)
                sub = min((r['subsumed_clause_delta'] for r in eligible), default=None)
                full = min((r['clause_delta'] for r in all_rows), default=None)
                assert plain is None or plain > allowance
                stats['leaves'] += 1
                stats['pair_bounded_candidates_exist'] += bool(eligible)
                stats['candidate_without_caps_at_current_allowance'] += full is not None and full <= allowance
                stats['subsumed_candidate_at_current_allowance'] += sub is not None and sub <= allowance
                for bound in (1, 2, 3, 4, 8):
                    stats['plain_delta_at_most_'+str(bound)] += plain is not None and plain <= bound
                plain_hist[str(plain)] += 1; subsumed_hist[str(sub)] += 1
                leaves.append(dict(key_sha256=item['key_sha256'], clauses=len(cnf),
                    variables=len({abs(l) for c in cnf for l in c}), literals=sum(map(len,cnf)),
                    width=max(map(len,cnf), default=0), min_clause_delta=plain,
                    min_subsumed_clause_delta=sub, min_clause_delta_without_caps=full, candidates=all_rows))
            reports.append(dict(suite=suite, mode=mode['mode'], allowance=allowance, report_sha256=sha(path),
                statistics=dict(stats), plain_delta_histogram=dict(plain_hist),
                subsumed_delta_histogram=dict(subsumed_hist), leaves=leaves))
    result = dict(script_sha256=sha(Path(__file__)), candidate_helper_sha256=sha(Path('experiments/analyze_cnf_clause_bound_frontier.py')),
        seconds=time.perf_counter()-started, reports=reports, limitations=[
        'Read-only all-pivot diagnostic, charged separately from acquisition; candidate counts are not closure gains.',
        'A growth barrier after one order does not establish a lower bound on other orders or arbitrary SAT.',
        'Subsumption candidates require checked integration and a total-cost comparison; this scan is not that implementation.'])
    output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps([{k:v for k,v in r.items() if k!='leaves'} for r in reports]))


if __name__=='__main__': main(Path(sys.argv[1]))
