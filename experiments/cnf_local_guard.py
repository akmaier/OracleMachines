"""Target-local failed-literal discovery with one shared baseline propagation.

Rank unforced variables by original binary incidence, then source identifier.
The bound limits attempted variables, not normalization, sorting or child search.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_residual_dag import propagate, restrict
from experiments.cnf_partition_screen import screen_branch


def probe(solver, source, variable_limit=4, counts=None):
    if type(variable_limit) is not int or variable_limit < 0:
        raise ValueError('Expected a nonnegative variable bound')
    counts = Counter() if counts is None else counts
    record = dict(baseline=None, fixed=[], ranks=[], candidates=[], attempts=[], selected=None)
    if not variable_limit:
        return None, record
    cnf, names, root = solver._canonical(source)
    fixed, trace, conflict = propagate(cnf, counts)
    residual = () if conflict is not None else restrict(cnf, fixed, counts)
    baseline = dict(root=root, trace=trace, conflict=conflict, residual_literals=sum(map(len, residual)))
    record['baseline'] = baseline
    record['fixed'] = [[names[v - 1], bit] for v, bit in sorted(fixed.items())]
    counts['local_baseline_probes'] += 1
    if conflict is not None:
        counts['local_terminal_targets'] += 1
        return dict(kind='terminal', screen=deepcopy(baseline)), record
    binary = Counter()
    counts['local_ranking_clause_visits'] += len(cnf)
    counts['local_ranking_literal_visits'] += sum(map(len, cnf))
    for c in cnf:
        if len(c) == 2:
            binary.update(abs(l) for l in c)
    remaining = set(range(1, len(names) + 1)) - set(fixed)
    ranked = sorted(remaining, key=lambda v: (-binary[v], names[v - 1]))
    record['ranks'] = [dict(variable=names[v - 1], binary_incidence=binary[v]) for v in ranked]
    record['candidates'] = [[sign * names[v - 1]] for v in ranked[:variable_limit] for sign in (-1, 1)]
    for clause in record['candidates']:
        stronger = [list(c) for c in source] + [clause]
        counts['local_premise_literals_copied'] += sum(map(len, stronger))
        screen = screen_branch(solver, stronger, counts)
        counts['local_premise_probes'] += 1
        record['attempts'].append(dict(clause=clause, screen=screen))
        if screen['conflict'] is not None:
            record['selected'] = len(record['attempts']) - 1
            counts['local_guards_found'] += 1
            return dict(kind='guard', clause=list(clause), screen=deepcopy(screen)), record
    return None, record
