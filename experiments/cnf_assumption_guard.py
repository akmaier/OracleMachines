"""Bounded single-clause probes with checked publication of a forced guard.

Candidates are proposals, not certificates. A unit refutation of T AND C forces
every model of T to falsify C. The remaining restricted target still needs solving.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_clause_deletion_guard import FORMAT, clause_set, check_guard
from experiments.cnf_partition_screen import screen_branch, publish_screened_branch


def probe(solver, source, candidates, limit=2, counts=None):
    if type(limit) is not int or limit < 0 or type(candidates) is not list:
        raise ValueError('Expected a finite candidate list and nonnegative probe bound')
    counts = Counter() if counts is None else counts
    trace = dict(baseline=None, attempts=[], selected=None)
    if not limit:
        return None, trace
    baseline = screen_branch(solver, source, counts)
    trace['baseline'] = baseline
    counts['assumption_baseline_probes'] += 1
    if baseline['conflict'] is not None:
        counts['assumption_terminal_targets'] += 1
        return dict(kind='terminal', screen=deepcopy(baseline)), trace
    members = clause_set(source, counts)
    variables = {abs(l) for c in members for l in c}
    seen = set()
    for raw in candidates[:limit]:
        counts['assumption_candidates_examined'] += 1
        clause = next(iter(clause_set([raw], counts)))
        reason = ('empty' if not clause else 'contained' if clause in members else
                  'outside' if not {abs(l) for l in clause} <= variables else
                  'duplicate' if clause in seen else None)
        seen.add(clause)
        entry = dict(clause=list(clause), skipped=reason, screen=None)
        trace['attempts'].append(entry)
        if reason:
            continue
        stronger = [list(c) for c in source] + [list(clause)]
        counts['assumption_premise_literals_copied'] += sum(map(len, stronger))
        screen = screen_branch(solver, stronger, counts)
        counts['assumption_premise_probes'] += 1
        entry['screen'] = screen
        if screen['conflict'] is not None:
            trace['selected'] = len(trace['attempts']) - 1
            counts['assumption_guards_found'] += 1
            return dict(kind='guard', clause=list(clause), screen=deepcopy(screen)), trace
    return None, trace


def publish_guard(solver, source, choice, counts=None):
    """Publish only the retained conflict trace; never solve a probe residual."""
    counts = Counter() if counts is None else counts
    if choice['kind'] != 'guard' or choice['screen']['conflict'] is None:
        raise ValueError('A checked-conflict candidate is required')
    members = clause_set(source, counts)
    clause = next(iter(clause_set([choice['clause']], counts)))
    if (not clause or clause in members or
            not {abs(l) for l in clause} <= {abs(l) for c in members for l in c}):
        raise ValueError('Expected a nonempty missing clause in target coordinates')
    stronger = [list(c) for c in source] + [list(clause)]
    child = publish_screened_branch(solver, stronger, choice['screen'])
    if child['answer'] is not False:
        raise ValueError('A guard premise must be negative')
    guard = dict(format=FORMAT, stronger=stronger, stronger_root=child['root'], removed_clause=list(clause))
    fixed, target = check_guard(solver, source, guard, counts)
    return guard, fixed, target, child
