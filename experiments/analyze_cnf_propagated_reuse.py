#!/usr/bin/env python3
"""Posthoc attribution for exact-prefix and fresh propagated-residual reuse."""
from pathlib import Path
from itertools import product
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_propagated_reuse as study
from experiments.validate_cnf_unsat_support import bound
base = study.base


def residual_diagnostic(row):
    """Read-only structural diagnosis; no alternate execution or claimed saving."""
    discovery = row['local_probe']; exposed = discovery.get('exposed')
    if exposed is None or exposed['known'] or exposed['family'] is not None:
        return None
    prefix = 'cnf-residual-v1:'
    assert exposed['root'].startswith(prefix)
    cnf = base.load_json(exposed['root'][len(prefix):])
    variables = sorted({abs(l) for c in cnf for l in c})
    candidates = []; visits = 0
    for v in variables:
        branches = []
        for bit in (False, True):
            true_literal = v if bit else -v
            residual = []
            for clause in cnf:
                reduced = []; satisfied = False
                for literal in clause:
                    visits += 1
                    if literal == true_literal: satisfied = True
                    elif literal != -true_literal: reduced.append(literal)
                if not satisfied: residual.append(reduced)
            branches.append(residual)
        if all(len(c) <= 2 for branch in branches for c in branch):
            candidates.append(dict(variable=v, branches=branches))
    # For the small positive diagnostic, independently check both restrictions
    # on every full assignment. This is posthoc checking, outside timed workers.
    checked = 0
    if candidates and len(variables) <= 12:
        for bits in product((False, True), repeat=len(variables)):
            assignment = dict(zip(variables, bits))
            value = all(any(assignment[abs(l)] == (l > 0) for l in c) for c in cnf)
            for candidate in candidates:
                branch = candidate['branches'][int(assignment[candidate['variable']])]
                assert value == all(any(assignment[abs(l)] == (l > 0) for l in c) for c in branch)
            checked += 1
    return dict(case=row['case'], baseline_forced_variables=len(discovery['fixed']),
        variables=len(variables), clauses=len(cnf), literals=sum(map(len, cnf)),
        max_width=max(map(len, cnf), default=0), wide_clauses=[c for c in cnf if len(c) > 2],
        one_variable_two_cnf_candidates=candidates, candidate_variables_checked=len(variables),
        candidate_literal_visits=visits, exhaustive_assignments_checked=checked,
        native_child_expansions=row['child']['metrics'].get('expanded_nodes', 0),
        limitation='Posthoc structural certificate only; no alternate acquisition, timing or row saving measured.')


def run(out):
    report = base.load(out / 'report.json'); p = bound(report['protocol']); controls = [bound(e) for e in bound(report['controls'])['samples']]
    historical = []
    for cohort, cid in sorted({(r['cohort'], r['case']) for r in controls}):
        historical.append(dict(cohort=cohort, case=cid, arms={r['mode']: dict(rows=r['new_nodes'], native_bytes=r['new_payload_units'],
            retained_bytes=r['retained_bytes'], **r['summary'], selection_seconds=r['selection_seconds'], evaluation_seconds=r['evaluation_seconds'],
            cold_seconds=r['cold_seconds'], complete_seconds=r['complete_arm_seconds'], reason=None if r['admission'] is None else r['admission']['reason'])
            for r in controls if (r['cohort'], r['case']) == (cohort, cid)}))
    totals = {mode: {k: sum(r['arms'][mode][k] for r in historical) for k in ('rows', 'native_bytes', 'retained_bytes', 'expanded_nodes', 'trace_publications', 'propagation_literal_visits')} for mode in study.MODES}
    summaries = report['summary']; comparisons = {}
    for mode in ('baseline', 'admitted'):
        b, a = summaries[mode], summaries['propagated']; pair = {}
        for key in ('new_nodes', 'new_payload_units', 'expanded_nodes', 'propagation_literal_visits', 'mean_query_seconds', 'mean_complete_worker_seconds', 'mean_peak_rss_bytes'):
            pair[key] = dict(control=b[key], propagated=a[key], difference=a[key] - b[key], percent=None if not b[key] else 100 * (a[key] - b[key]) / b[key])
        bbytes = sum(b['sidecar_bytes']) / len(b['sidecar_bytes']); abytes = sum(a['sidecar_bytes']) / len(a['sidecar_bytes'])
        pair['mean_sidecar_bytes'] = dict(control=bbytes, propagated=abytes, percent=100 * (abytes - bbytes) / bbytes)
        comparisons[mode] = pair
    samples = [(e, bound(e)) for e in report['samples']]; details = {}; diagnostics = []
    for entry, trial in samples:
        if entry['repeat']: continue
        mode = entry['mode']; details[mode] = {}
        for r in bound(trial['queries']):
            if mode == 'propagated' and r['child']['metrics'].get('expanded_nodes', 0):
                diagnostic = residual_diagnostic(r)
                if diagnostic is not None: diagnostics.append(diagnostic)
            choice = r['local_choice']; admission = r['admission']; discovery = r['local_probe']
            details[mode][r['case']] = dict(case=r['case'], template_case=r['template_case'], answer=r['record']['answer'], rows=r['new_nodes'],
                child_root=r['child']['root'], engine_rows=sum(c['metrics'].get('inserted_nodes', 0) for c in (r['premise'], r['child']) if c is not None),
                child_expansions=r['child']['metrics'].get('expanded_nodes', 0), summary=study.summarize([r]),
                admission_reason=None if admission is None else admission['reason'],
                choice_kind=None if choice is None else choice['kind'],
                exposed=None if discovery is None else discovery.get('exposed'),
                probe_counts=r['probe_counts'], probe_metrics=r['probe_metrics'], child_metrics=r['child']['metrics'], seconds=r['seconds'])
    affected = [dict(case=cid, arms={m: details[m][cid] for m in study.MODES}) for cid, r in details['propagated'].items()
                if r['admission_reason'] is not None or any(r['rows'] != details[m][cid]['rows'] for m in ('baseline', 'admitted'))]
    remaining = sorted((r for r in details['propagated'].values() if r['child_expansions']), key=lambda r: (-r['child_expansions'], r['case']))
    paired = []
    for repeat, order in enumerate(p['orders']):
        values = {e['mode']: s['summary']['complete_worker_seconds'] for e, s in samples if e['repeat'] == repeat}
        paired.append(dict(repeat=repeat, order=order, seconds=values, propagated_minus_admitted=values['propagated'] - values['admitted'],
                           propagated_minus_baseline=values['propagated'] - values['baseline']))
    result = dict(passed=True, report=study.binding(out / 'report.json'), historical=historical, historical_totals=totals,
        fresh_comparisons=comparisons, affected=affected, remaining_child_work=remaining, paired_complete_times=paired,
        residual_diagnostics=diagnostics,
        limitations=['Exact-prefix arms isolate the same native state; fresh-query contributions come from streams whose prefixes can diverge.',
                    'Zero expansion calls can coexist with explicit trace publication and retained native rows. Count propagation, checking, source copies and persistence separately.',
                    'Two reversed-order timing pairs and process peak RSS provide no stable general runtime or live-memory bound.',
                    'Fresh queries remain double-deletion neighbours of three existing templates. No new general structural authority or unrestricted-SAT result.'])
    base.write(out / 'cost-attribution.json', result)
    print(base.encode(dict(control_totals=totals, comparisons=comparisons, paired_times=paired,
        affected=[dict(case=r['case'], reasons={m:a['admission_reason'] for m,a in r['arms'].items()}, rows={m:a['rows'] for m,a in r['arms'].items()}) for r in affected],
        remaining=[dict(case=r['case'], expansions=r['child_expansions']) for r in remaining])), flush=True)


if __name__ == '__main__': run(Path(sys.argv[1]))
