#!/usr/bin/env python3
"""Record near edits of unfinished origins without treating them as proofs.

This posthoc census reads every base/edit pair in the frozen fresh stream. It
does not run a new policy, select cases for timed results, or infer reusable
conditional supports from a shared clause count.
"""
from collections import Counter
from pathlib import Path
import sys
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_binary_lazy as study
from experiments.cnf_residual_dag import normalize
base = study.base


def inspect(out):
    began = time.perf_counter()
    p = base.load(out/'protocol.json')
    cases = study.bound(p['cases']['holdout'])
    rows = base.load(out/'holdout-lazy-0/queries.json')
    profile = base.load(out/'profiling.json')
    pairs = []
    for c in cases:
        if c['variant'] != 'edit': continue
        i, j = c['base_case'], c['case']
        left, left_names = normalize(cases[i]['source'])
        right, right_names = normalize(c['source'])
        a, b = rows[i], rows[j]
        pairs.append(dict(origin_case=i, target_case=j, family=c['family'],
            same_variable_coordinates=left_names==right_names,
            removed_clauses=len(set(left)-set(right)), added_clauses=len(set(right)-set(left)),
            origin_status=a['status'], target_status=b['status'],
            origin_dispatches=a['metrics'].get('expanded_nodes',0),
            target_dispatches=b['metrics'].get('expanded_nodes',0),
            plan_attempts=b['metrics'].get('whole_plan_attempts',0),
            plan_candidates=b['metrics'].get('whole_plan_candidates_scanned',0),
            plan_intact_leaves=b['metrics'].get('whole_plan_selected_intact',0),
            plan_leaves=b['metrics'].get('whole_plan_selected_leaves',0)))
    selected = next(r for r in pairs if r['target_case']==profile['case']['case'])
    assert selected['target_case']==64 and selected['origin_case']==63
    assert selected['same_variable_coordinates'] and selected['removed_clauses']==selected['added_clauses']==1
    assert selected['origin_status']==selected['target_status']=='unresolved'
    assert selected['plan_attempts']==0 and selected['plan_candidates']==10
    base.write(out/'stopped-origins.json',dict(protocol=study.binding(out/'protocol.json'),
        queries=study.binding(out/'holdout-lazy-0/queries.json'),
        profile=study.binding(out/'profiling.json'),pairs=pairs,selected=selected,
        origin_statuses=dict(Counter(r['origin_status'] for r in pairs)),
        seconds=time.perf_counter()-began,limitations=[
            'Posthoc census includes all 24 base/edit pairs. Construction labels describe reports and never enter a candidate solver.',
            'Origin status refers to its base attempt immediately before the edit. A later repeat may complete that root; future answers cannot be used at the earlier edit.',
            'Canonical clause overlap is interpreted only when variable coordinate lists agree. General edits may require explicit renaming transport.',
            'WholeProofReuseSolver._try_whole_plan searches earlier checked negative roots; extract_partial requires a checked negative origin. An unfinished origin is not eligible through that route.',
            'Stored individual residuals can already be reused. This identifies an absent whole-plan origin route, not an absence of all reuse.',
            'No stopped search is certified negative. No reusable leaf count, preserved source-support map, coverage gain or timing saving is established for unfinished origins.',
            'Before implementing a new gate, census source-bound checked conditional leaves, exact branch guards, edit invalidation and open-frontier coverage under bounded retention.']))


if __name__ == '__main__': inspect(Path(sys.argv[1]))
