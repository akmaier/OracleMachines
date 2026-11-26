"""Combine independently checked B8/B9 failures and probe the resulting B10 bank.

Proof origins keep their original banks. Exact no-change comparison permits
schedule reuse, but open completions never certify SAT or semantic exhaustion.
"""
from copy import deepcopy
import json
from experiments import cnf_b9_probe_cursor as prior

engine = prior.engine
FORMAT = 'cnf-b10-probe-cursor-v1'
POLICY = 'b10-wide-occurrence-order-complement-first-v1'


def prepare(*inputs, closure, feedback_closure, joint_closure, counts, trace_limit=256):
    if len(inputs) != 21 or type(trace_limit) is not int or trace_limit < 1:
        raise ValueError('B10 requires B9 inputs, its result, a B8 comparison and a positive trace bound')
    owned, cl, fc, jc = deepcopy((inputs, closure, feedback_closure, joint_closure))
    prepared = prior.validate(*owned[:19], closure=cl, feedback_closure=fc,
                              result=owned[19], counts=counts)
    lower = prior.shared.validate(*owned[:18], closure=cl, result=owned[20], counts=counts)
    if any(owned[i]['program']['status'] != 'unresolved' for i in (19, 20)):
        raise ValueError('Unresolved B8 and B9 histories required')
    if lower != prepared[:19]:
        raise ValueError('B8 comparison changed the original bank or provenance')
    entries = dict(zip(prepared[19], prepared[20]))
    for kind, program in (('b8_comparison_probe', owned[20]['program']),
                          ('b9_probe', owned[19]['program'])):
        for i, row in enumerate(program['probes']):
            clause = (-row['assumption'],)
            counts['b10_exclusions'] += 1
            if clause not in entries:
                entries[clause] = dict(kind=kind, index=i)
                counts['b10_added_units'] += 1
    clauses = tuple(sorted(entries))
    prepared = (*prepared, clauses, [entries[cl] for cl in clauses])
    fixed = engine.prior.check_closure(clauses, jc, counts)
    bank, ids = engine.prior.residual_bank(clauses, fixed, counts)
    active = {abs(lit) for clause in bank for lit in clause}
    order = tuple(lit for lit in engine.frozen.roots(prepared[0]) if abs(lit) in active)
    binding = json.dumps([POLICY, prepared[0], clauses, jc, order, trace_limit],
                         sort_keys=True, separators=(',', ':'))
    counts['b10_binding_bytes'] += len(binding.encode())
    counts['b10_compare_literals'] += sum(map(len, prepared[19])) + sum(map(len, clauses))
    same = (prepared[19] == clauses and fc == jc
            and owned[19]['program']['trace_limit'] == trace_limit)
    view = (*prepared[:15], clauses, prepared[22])
    return prepared, view, bank, ids, order, binding, same, owned[19], jc


def _load(view, order, binding, cursor, counts, trace_limit):
    if cursor is not None:
        if type(cursor) is not dict or cursor.get('format') != FORMAT:
            raise ValueError('Invalid B10 cursor format')
        cursor = deepcopy(cursor)
        cursor['format'] = engine.FORMAT
    return engine.load(view, order, binding, cursor, counts, trace_limit)


def discover(*inputs, closure, feedback_closure, joint_closure, counts,
             policy='reuse', cursor=None, probe_limit=64, work_limit=262144, trace_limit=256):
    if policy not in ('restart', 'matched', 'reuse') or any(
            type(v) is not int or v < 1 for v in (probe_limit, work_limit, trace_limit)):
        raise ValueError('Invalid B10 search options')
    prepared, view, bank, ids, order, binding, same, history, cl = prepare(
        *inputs, closure=closure, feedback_closure=feedback_closure,
        joint_closure=joint_closure, counts=counts, trace_limit=trace_limit)
    if cursor is None and same and policy == 'matched':
        extra = len(history['cursor']['completed'])
        probe_limit += extra
        work_limit *= 1 + (extra + 63) // 64
    if cursor is None and same and policy == 'reuse':
        cursor = deepcopy(history['cursor'])
        cursor.update(format=FORMAT, binding=binding)
        counts['b10_imported_completed'] += len(cursor['completed'])
        counts['b10_imported_cursors'] += 1
    elif cursor is None:
        counts['b10_fresh_cursors'] += 1
    else:
        counts['b10_continued_cursors'] += 1
    state = _load(view, order, binding, cursor, counts, trace_limit)
    result = prior.prior._search(bank, ids, binding, cl['units'], state, counts,
                                 probe_limit, work_limit, trace_limit)
    result['cursor']['format'] = FORMAT
    return result


def validate(*inputs, closure, feedback_closure, joint_closure, result, counts):
    saved = deepcopy(result)
    program = prior.shared._header(saved)
    prepared, view, _, _, order, binding, _, _, _ = prepare(
        *inputs, closure=closure, feedback_closure=feedback_closure,
        joint_closure=joint_closure, counts=counts, trace_limit=program['trace_limit'])
    state = _load(view, order, binding, saved['cursor'], counts, program['trace_limit'])
    engine.prior.check_program(prepared[0], prepared[21], program, counts)
    if program != engine._program(state[4], state[6], program['trace_limit'], program['reason']):
        raise ValueError('B10 program disagrees with cursor')
    return prepared
