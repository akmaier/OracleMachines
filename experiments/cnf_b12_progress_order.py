"""Combine B10/B11 failures and compare source order with unseen-first B12 search.

Proof origins keep their original banks. Exact no-change comparison permits
schedule reuse, but open completions never certify SAT or semantic exhaustion.
"""
from copy import deepcopy
import json
from experiments import cnf_b11_probe_cursor as prior

engine = prior.engine
FORMAT = 'cnf-b12-progress-order-v1'
POLICY = 'b12-progress-order-complement-first-v1'


def prepare(*inputs, closure, feedback_closure, joint_closure, next_closure, latest_closure, counts, trace_limit=256, ordering='unseen'):
    if len(inputs) != 24 or type(trace_limit) is not int or trace_limit < 1:
        raise ValueError('B12 requires 24 inputs and a positive trace bound')
    if ordering not in ('source','unseen'): raise ValueError('Invalid B12 ordering')
    owned, cl, fc, jc, nc, lc = deepcopy((inputs, closure, feedback_closure, joint_closure, next_closure, latest_closure))
    prepared = prior.validate(*owned[:22], closure=cl, feedback_closure=fc, joint_closure=jc, next_closure=nc,
                              result=owned[22], counts=counts)
    lower = prior.shared.validate(*owned[:21], closure=cl, feedback_closure=fc, joint_closure=jc, result=owned[23], counts=counts)
    if any(owned[i]['program']['status'] != 'unresolved' for i in (22, 23)):
        raise ValueError('Unresolved B10 and B11 histories required')
    if lower != prepared[:23]:
        raise ValueError('B10 comparison changed the original bank or provenance')
    entries = dict(zip(prepared[23], prepared[24]))
    for kind, program in (('b10_comparison_probe', owned[23]['program']),
                          ('b11_probe', owned[22]['program'])):
        for i, row in enumerate(program['probes']):
            clause = (-row['assumption'],)
            counts['b12_exclusions'] += 1
            if clause not in entries:
                entries[clause] = dict(kind=kind, index=i)
                counts['b12_added_units'] += 1
    clauses = tuple(sorted(entries))
    prepared = (*prepared, clauses, [entries[cl] for cl in clauses])
    fixed = engine.prior.check_closure(clauses, lc, counts)
    bank, ids = engine.prior.residual_bank(clauses, fixed, counts)
    active = {abs(lit) for clause in bank for lit in clause}
    order = tuple(lit for lit in engine.frozen.roots(prepared[0]) if abs(lit) in active)
    same = (prepared[23] == clauses and nc == lc
            and owned[22]['program']['trace_limit'] == trace_limit)
    # On a changed bank, old completions affect priority only. None is imported
    # as a new-bank completion; the suffix still contains every active literal.
    if ordering == 'unseen' and not same:
        seen = set(owned[22]['cursor']['completed']) | set(owned[23]['cursor']['completed'])
        counts['b12_hint_slots'] += len(owned[22]['cursor']['completed']) + len(owned[23]['cursor']['completed'])
        fresh = tuple(lit for lit in order if lit not in seen)
        old = tuple(lit for lit in order if lit in seen)
        order = fresh + old
        counts['b12_unseen_priority_literals'] += len(fresh)
        counts['b12_deferred_literals'] += len(old)
    binding = json.dumps([POLICY, ordering, prepared[0], clauses, lc, order, trace_limit],
                         sort_keys=True, separators=(',', ':'))
    counts['b12_binding_bytes'] += len(binding.encode())
    counts['b12_compare_literals'] += sum(map(len, prepared[23])) + sum(map(len, clauses))
    view = (*prepared[:15], clauses, prepared[26])
    return prepared, view, bank, ids, order, binding, same, owned[22], lc



def _load(view, order, binding, cursor, counts, trace_limit):
    if cursor is not None:
        if type(cursor) is not dict or cursor.get('format') != FORMAT:
            raise ValueError('Invalid B12 cursor format')
        cursor = deepcopy(cursor)
        cursor['format'] = engine.FORMAT
    return engine.load(view, order, binding, cursor, counts, trace_limit)


def discover(*inputs, closure, feedback_closure, joint_closure, next_closure, latest_closure, counts,
             policy='reuse', cursor=None, probe_limit=64, work_limit=262144, trace_limit=256, ordering='unseen'):
    if policy not in ('restart', 'matched', 'reuse') or any(
            type(v) is not int or v < 1 for v in (probe_limit, work_limit, trace_limit)):
        raise ValueError('Invalid B12 search options')
    prepared, view, bank, ids, order, binding, same, history, cl = prepare(
        *inputs, closure=closure, feedback_closure=feedback_closure,
        joint_closure=joint_closure, next_closure=next_closure, latest_closure=latest_closure,
        counts=counts, trace_limit=trace_limit, ordering=ordering)
    if cursor is None and same and policy == 'matched':
        extra = len(history['cursor']['completed'])
        probe_limit += extra
        work_limit *= 1 + (extra + 63) // 64
    if cursor is None and same and policy == 'reuse':
        cursor = deepcopy(history['cursor'])
        cursor.update(format=FORMAT, binding=binding)
        counts['b12_imported_completed'] += len(cursor['completed'])
        counts['b12_imported_cursors'] += 1
    elif cursor is None:
        counts['b12_fresh_cursors'] += 1
    else:
        counts['b12_continued_cursors'] += 1
    state = _load(view, order, binding, cursor, counts, trace_limit)
    result = prior.shared.b8._search(bank, ids, binding, cl['units'], state, counts,
                                 probe_limit, work_limit, trace_limit)
    result['cursor']['format'] = FORMAT
    return result


def validate(*inputs, closure, feedback_closure, joint_closure, next_closure, latest_closure, result, counts, ordering='unseen'):
    saved = deepcopy(result)
    program = prior.shared.shared._header(saved)
    prepared, view, _, _, order, binding, _, _, _ = prepare(
        *inputs, closure=closure, feedback_closure=feedback_closure,
        joint_closure=joint_closure, next_closure=next_closure, latest_closure=latest_closure,
        counts=counts, trace_limit=program['trace_limit'], ordering=ordering)
    state = _load(view, order, binding, saved['cursor'], counts, program['trace_limit'])
    engine.prior.check_program(prepared[0], prepared[25], program, counts)
    if program != engine._program(state[4], state[6], program['trace_limit'], program['reason']):
        raise ValueError('B12 program disagrees with cursor')
    return prepared
