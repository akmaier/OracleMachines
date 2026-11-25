"""Probe the second checked closure; skip unchanged banks as a search policy.

Every emitted conflict is checked against B2. Old failures remain proofs on B0,
and the next layer remains proofs on B1. An unchanged outcome is unresolved;
it is neither a SAT certificate nor a claim that further search cannot help.
"""
from collections import deque
from experiments import cnf_layered_feedback as layered

prior = layered.prior
frozen = layered.frozen


def prepare(source, templates, seed, closure, new, next_closure, counts):
    prepared = layered.prepare(source, templates, seed, closure, new, counts)
    fixed = prior.check_closure(prepared[5], next_closure, counts)
    return prepared, fixed


def unchanged(prepared, closure, fixed, counts):
    # Exact equality, not a signature or a variable-count heuristic.
    first, second = prepared[3], prepared[5]
    counts['schedule_bank_literal_slots'] += sum(map(len, first)) + sum(map(len, second))
    counts['schedule_assignment_slots'] += len(closure['assignment']) + len(fixed)
    return first == second and prior.fixed_pairs(closure['assignment']) == fixed


def discover(source, templates, seed, closure, new, next_closure, counts, *,
             policy='changed', probe_limit=64, work_limit=262144, trace_limit=256):
    if policy not in ('all', 'changed') or any(
            type(v) is not int or v < 1 for v in (probe_limit, work_limit, trace_limit)):
        raise ValueError('Invalid changed-closure probe bounds')
    prepared, fixed = prepare(source, templates, seed, closure, new, next_closure, counts)
    same = unchanged(prepared, closure, fixed, counts)
    if policy == 'changed' and same:
        counts['schedule_unchanged_skips'] += 1
        return dict(action='unchanged', program=None)
    counts['schedule_searched'] += 1
    source, bank = prepared[0], prepared[5]
    reduced, ids = prior.residual_bank(bank, fixed, counts)
    active = {abs(l) for cl in reduced for l in cl}
    queue = deque(l for l in frozen.roots(source) if abs(l) in active)
    prefix = next_closure['units']
    index = frozen.UnitIndex(reduced, counts)
    start = counts['probe_occurrence_visits']
    records, found, tested, promoted = [], {}, set(), None
    counts['closure_removed_variables'] += len(fixed)
    counts['closure_active_variables'] += len(active)

    def result(status, reason, terminal=None):
        return dict(action='searched', program=dict(
            status=status, reason=reason, mode='conditioned', probes=records,
            terminal=terminal, trace_limit=trace_limit))

    try:
        if len(prefix) > trace_limit:
            return result('unresolved', 'trace_limit')
        while queue or promoted is not None:
            priority = promoted is not None
            root = promoted if priority else queue.popleft()
            promoted = None
            if root in tested:
                counts['closure_duplicate_skips'] += 1
                continue
            if len(tested) >= probe_limit:
                return result('unresolved', 'probe_limit')
            tested.add(root)
            counts['probe_roots'] += 1
            counts['closure_promoted_probes' if priority else 'closure_base_probes'] += 1
            proof = index.probe(root, counts,
                lambda: work_limit - (counts['probe_occurrence_visits'] - start),
                trace_limit - len(prefix))
            if proof is None:
                continue
            proof = dict(units=[list(p) for p in prefix] + [
                [l, ids[cid]] for l, cid in proof['units']], conflict=ids[proof['conflict']])
            counts['closure_lifted_steps'] += len(prefix)
            records.append(dict(assumption=root, proof=proof))
            found[root] = len(records) - 1
            counts['probe_exclusions'] += 1
            if -root in found:
                return result('refuted', 'opposite_probes',
                              dict(low=found[-abs(root)], high=found[abs(root)]))
            if -root not in tested:
                promoted = -root
    except frozen.ProbeLimit as error:
        return result('unresolved', str(error))
    return result('unresolved', 'complete')


def validate(source, templates, seed, closure, new, next_closure, result, counts):
    prepared, fixed = prepare(source, templates, seed, closure, new, next_closure, counts)
    if type(result) is not dict or set(result) != {'action', 'program'}:
        raise ValueError('Invalid changed-closure result')
    if result['action'] == 'unchanged':
        if result['program'] is not None or not unchanged(prepared, closure, fixed, counts):
            raise ValueError('Changed bank cannot be skipped as unchanged')
    elif result['action'] == 'searched':
        program = result['program']
        prior.check_program(prepared[0], prepared[5], program, counts)
        if program['mode'] != 'conditioned' or any(
                abs(r['assumption']) in fixed for r in program['probes']):
            raise ValueError('Probe repeats a closure assignment')
    else:
        raise ValueError('Unknown changed-closure action')
    return prepared
