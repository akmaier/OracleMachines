"""Search the checked B9 bank, reusing B8 schedules only on exact equality.

Open completions remain scheduling hints, never satisfiability certificates.
All failed probes retain their original bank and are checked before reuse.
"""
from copy import deepcopy
import json
from experiments import cnf_shared_joint_preparation as shared

prior = shared.prior
engine = prior.c
FORMAT = 'cnf-b9-probe-cursor-v1'
POLICY = 'b9-wide-occurrence-order-complement-first-v1'


def prepare(*inputs, closure, feedback_closure, counts, trace_limit=256):
    if len(inputs) != 19 or type(trace_limit) is not int or trace_limit < 1:
        raise ValueError('B9 requires joint inputs, B8 result and positive trace bound')
    owned, cl, new_cl = deepcopy((inputs, closure, feedback_closure))
    prepared = shared.validate(*owned[:-1], closure=cl, result=owned[-1], counts=counts)
    if owned[-1]['program']['status'] != 'unresolved':
        raise ValueError('Unresolved B8 history required')
    entries = dict(zip(prepared[17], prepared[18]))
    for i, row in enumerate(owned[-1]['program']['probes']):
        clause = (-row['assumption'],)
        counts['b9_exclusions'] += 1
        if clause not in entries:
            entries[clause] = dict(kind='joint_probe', index=i)
            counts['b9_added_units'] += 1
    clauses = tuple(sorted(entries))
    prepared = (*prepared, clauses, [entries[cl] for cl in clauses])
    fixed = engine.prior.check_closure(clauses, new_cl, counts)
    bank, ids = engine.prior.residual_bank(clauses, fixed, counts)
    active = {abs(lit) for clause in bank for lit in clause}
    order = tuple(lit for lit in engine.frozen.roots(prepared[0]) if abs(lit) in active)
    binding = json.dumps([POLICY, prepared[0], clauses, new_cl, order, trace_limit],
                         sort_keys=True, separators=(',', ':'))
    counts['b9_binding_bytes'] += len(binding.encode())
    counts['b9_compare_literals'] += sum(map(len, prepared[17])) + sum(map(len, clauses))
    same = (prepared[17] == clauses and cl == new_cl
            and owned[-1]['program']['trace_limit'] == trace_limit)
    view = (*prepared[:15], clauses, prepared[20])
    return prepared, view, bank, ids, order, binding, same, owned[-1], new_cl


def _load(view, order, binding, cursor, counts, trace_limit):
    if cursor is not None:
        if type(cursor) is not dict or cursor.get('format') != FORMAT:
            raise ValueError('Invalid B9 cursor format')
        cursor = deepcopy(cursor)
        cursor['format'] = engine.FORMAT
    return engine.load(view, order, binding, cursor, counts, trace_limit)


def discover(*inputs, closure, feedback_closure, counts, policy='reuse', cursor=None,
             probe_limit=64, work_limit=262144, trace_limit=256):
    if policy not in ('restart', 'matched', 'reuse') or any(
            type(v) is not int or v < 1 for v in (probe_limit, work_limit, trace_limit)):
        raise ValueError('Invalid B9 search options')
    prepared, view, bank, ids, order, binding, same, history, cl = prepare(
        *inputs, closure=closure, feedback_closure=feedback_closure,
        counts=counts, trace_limit=trace_limit)
    if cursor is None and same and policy == 'matched':
        extra = len(history['cursor']['completed'])
        probe_limit += extra
        work_limit *= 1 + (extra + 63) // 64
    if cursor is None and same and policy == 'reuse':
        cursor = deepcopy(history['cursor'])
        cursor.update(format=FORMAT, binding=binding)
        counts['b9_imported_completed'] += len(cursor['completed'])
        counts['b9_imported_cursors'] += 1
    elif cursor is None:
        counts['b9_fresh_cursors'] += 1
    else:
        counts['b9_continued_cursors'] += 1
    state = _load(view, order, binding, cursor, counts, trace_limit)
    result = prior._search(bank, ids, binding, cl['units'], state, counts,
                           probe_limit, work_limit, trace_limit)
    result['cursor']['format'] = FORMAT
    return result


def validate(*inputs, closure, feedback_closure, result, counts):
    saved = deepcopy(result)
    program = shared._header(saved)
    prepared, view, _, _, order, binding, _, _, _ = prepare(
        *inputs, closure=closure, feedback_closure=feedback_closure,
        counts=counts, trace_limit=program['trace_limit'])
    state = _load(view, order, binding, saved['cursor'], counts, program['trace_limit'])
    engine.prior.check_program(prepared[0], prepared[19], program, counts)
    if program != engine._program(state[4], state[6], program['trace_limit'], program['reason']):
        raise ValueError('B9 program disagrees with cursor')
    return prepared
