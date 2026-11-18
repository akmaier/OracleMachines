"""Spend at most one extra premise probe to complete a retained negative cover.

Candidates come from source clauses with exactly one unrefuted literal and at
least one retained negative SCC condition. The previous discovery pass is kept
verbatim; the extra condition has a separate evidence record. Source checking
and ordinary native publication remain mandatory.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_negative_cover import select as previous_select
from experiments.cnf_residual_dag import propagate, restrict, two_cnf, holds


def choose_gap(source, discovery, counts=None):
    counts = Counter() if counts is None else counts
    negative = {}
    for item in discovery['completions']:
        counts['cover_gap_completion_reads'] += 1
        if 'mixed' in item and item['mixed']['model'] is None:
            index = item['index']
            negative.setdefault(discovery['attempts'][index]['clause'][0], index)
    if not negative:
        return None
    attempted = set()
    for attempt in discovery['attempts']:
        counts['cover_gap_attempt_reads'] += 1
        attempted.add(attempt['clause'][0])
    best = None
    for cid, raw in enumerate(source):
        counts['cover_gap_clause_visits'] += 1
        counts['cover_gap_literal_visits'] += len(raw)
        members = set(raw)
        if any(-l in members for l in members):
            continue
        missing = members - negative.keys()
        if len(missing) != 1 or not members & negative.keys():
            continue
        literal = next(iter(missing))
        if literal in attempted:
            continue
        counts['cover_gap_candidates'] += 1
        rank = (len(members), cid)
        if best is None or rank < best[0]:
            best = (rank, dict(clause_index=cid, clause=sorted(members), literal=literal))
    return None if best is None else best[1]


def probe_gap(solver, source, candidate, counts):
    literal = candidate['literal']; stronger = [list(c) for c in source] + [[literal]]
    counts['cover_gap_premise_literals'] += sum(map(len, stronger))
    cnf, names, root = solver._canonical(stronger)
    fixed, trace, conflict = propagate(cnf, counts)
    residual = () if conflict is not None else restrict(cnf, fixed, counts)
    screen = dict(root=root, trace=trace, conflict=conflict, residual_literals=sum(map(len,residual)))
    counts['cover_gap_probes'] += 1
    evidence = dict(candidate=deepcopy(candidate), attempt=dict(clause=[literal], screen=screen),
                    completion=None, outcome='unit-conflict')
    # The existing cover compiler accepts unit-closed binary refutations only.
    # A unit-conflict condition is retained as a miss, not silently discarded.
    if conflict is not None:
        counts['cover_gap_unit_conflicts'] += 1
        return evidence, None
    counts['cover_gap_recognition_clauses'] += len(residual)
    counts['cover_gap_recognition_literals'] += sum(map(len,residual))
    if any(len(c)>2 for c in residual):
        evidence['outcome'] = 'nonbinary';counts['cover_gap_nonbinary'] += 1
        return evidence, None
    counts['cover_gap_scc_calls'] += 1
    local = Counter(implication_edges=0)
    model, proof = two_cnf(residual, local)
    counts['cover_gap_implication_edges'] += local['implication_edges']
    evidence['completion'] = dict(residual_literals=sum(map(len,residual)),
        mixed=dict(model=None if model is None else sorted(model.items()), proof=deepcopy(proof), metrics=dict(local)))
    if model is None:
        evidence['outcome'] = 'negative';counts['cover_gap_negative'] += 1
        return evidence, None
    merged = {**fixed, **model}; raw_model = {v:merged.get(i+1,False) for i,v in enumerate(names)}
    counts['cover_gap_model_literals'] += sum(map(len,stronger))
    if not holds(stronger,raw_model):
        raise ValueError('Additional premise model fails raw source or assumption')
    evidence['outcome'] = 'positive';counts['cover_gap_positive'] += 1
    return evidence, raw_model


def combined_discovery(trace):
    d = trace['discovery']; gap = trace.get('gap')
    if gap is None or gap['outcome'] != 'negative':
        return d
    detail = dict(gap['completion'], index=len(d['attempts']))
    return dict(d, attempts=[*d['attempts'],gap['attempt']], completions=[*d['completions'],detail])


def select(solver, source, variable_limit=4, counts=None):
    counts = Counter() if counts is None else counts
    choice, trace = previous_select(solver,source,variable_limit,counts)
    d = trace['discovery']
    if d is None or (choice is not None and choice['kind'] != 'fallback-trace'):
        return choice, trace
    candidate = choose_gap(source,d,counts)
    if candidate is None:
        return choice, trace
    gap, model = probe_gap(solver,source,candidate,counts);trace['gap'] = gap
    if gap['outcome'] not in ('negative','positive'):
        return choice, trace
    if choice is not None:
        counts['fallback_trace_reuses'] -= 1
        counts['fallback_forced_variables'] -= len(d['fixed'])
    trace['gap_previous_reason'] = trace['reason']
    _, names, root = solver._canonical(source)
    if model is not None:
        trace['reason'] = 'gap-positive-model'
        return dict(kind='positive-model',root=root,model=[[v,model.get(v,False)] for v in names]),trace
    expanded = combined_discovery(trace);negative = {}
    for item in expanded['completions']:
        if 'mixed' in item and item['mixed']['model'] is None:
            index=item['index'];negative.setdefault(expanded['attempts'][index]['clause'][0],index)
    cover = dict(clause_index=candidate['clause_index'], clause=candidate['clause'],
                 attempts=[negative[l] for l in candidate['clause']])
    trace['reason'] = 'gap-negative-cover';trace['gap_cover'] = cover
    return dict(kind='negative-cover',root=root,**deepcopy(cover)),trace
