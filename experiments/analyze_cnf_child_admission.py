#!/usr/bin/env python3
"""Posthoc attribution and structural descriptions of rejected child residuals."""
from collections import Counter
from pathlib import Path
import sys, tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_child_admission as study
from experiments.cnf_residual_dag import normalize, restrict, token
from experiments.validate_cnf_unsat_support import bound
base = study.base


def shape(source):
    cnf, names = normalize(source)
    return dict(variables=len(names), clauses=len(cnf), literals=sum(map(len, cnf)),
                two_cnf=all(len(c) <= 2 for c in cnf),
                horn=all(sum(l > 0 for l in c) <= 1 for c in cnf),
                dual_horn=all(sum(l < 0 for l in c) <= 1 for c in cnf))


def run(out):
    report = base.load(out / 'report.json'); p = bound(report['protocol']); rows = [bound(e) for e in report['samples']]
    totals = {}
    for cohort in ('historical', 'fresh-baseline'):
        totals[cohort] = {}
        for mode in study.MODES:
            selected = [r for r in rows if r['cohort'] == cohort and r['mode'] == mode]
            totals[cohort][mode] = {k: sum(r[k] for r in selected) for k in ('new_nodes', 'new_payload_units', 'retained_bytes', 'selection_seconds', 'evaluation_seconds', 'cold_seconds', 'complete_arm_seconds')}
            totals[cohort][mode].update({k: sum(r['summary'][k] for r in selected) for k in ('expanded_nodes', 'trace_publications', 'propagation_literal_visits')})
    residuals = []
    with tempfile.TemporaryDirectory() as td:
        contexts = {(c['cohort'], c['case']): c for c in study.contexts(p, Path(td))}
        for r in rows:
            if r['mode'] != 'admitted' or r['admission']['reason'] != 'nonterminal-child': continue
            counts = Counter(); proposal = r['admission']['proposal']; screen = r['admission']['child']['screen']
            child = restrict(r['input_target'], {abs(l): l < 0 for l in proposal['clause']}, counts)
            cnf, names = normalize(child, counts); fixed = {abs(l): l > 0 for l, _ in screen['trace']}
            residual = restrict(cnf, fixed, counts); normalized, _ = normalize(residual, counts)
            key = token(normalized, counts); before = contexts[r['cohort'], r['case']]['before']
            assert token(cnf, counts) == screen['root']
            residuals.append(dict(cohort=r['cohort'], case=r['case'], assumption=proposal['clause'],
                input_shape=shape(r['input_target']), child_shape=shape(child), unit_steps=len(screen['trace']),
                residual_shape=shape(residual), residual_root=key, residual_known=key in before, diagnostic_counts=dict(counts)))
    result = dict(passed=True, report=study.old.binding(out / 'report.json'), totals=totals, rejected_residuals=residuals,
        limitations=['Totals aggregate selected exact-prefix controls, not an excluded fresh stream or a trained admission policy.',
                     'The residual diagnostic is posthoc and is not charged to the measured policy. Availability is against the exact saved prefix; all prefix payloads are checked elsewhere.',
                     'Zero child expansions in an admitted unit-conflict case replace solving with explicit trace publication; all inserted rows and total propagation remain counted.'])
    base.write(out / 'cost-attribution.json', result)
    print(base.encode(result), flush=True)


if __name__ == '__main__': run(Path(sys.argv[1]))
