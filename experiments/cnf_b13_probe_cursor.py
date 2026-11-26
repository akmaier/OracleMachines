"""Combine both checked B12 orders and B11 continuation before B13 search.

One owned common prefix supports three distinct original-bank history checks.
Open completions transfer only under exact bank, closure and bound equality.
"""
from copy import deepcopy
import json
from experiments import cnf_shared_b12_preparation as shared

engine = shared.engine
FORMAT = 'cnf-b13-probe-cursor-v1'
POLICY = 'b13-wide-occurrence-order-complement-first-v1'


def _binding(policy, source, clauses, closure, order, trace_limit, counts, ordering=None):
    fields = [policy, source, clauses, closure, order, trace_limit]
    if ordering is not None: fields.insert(1, ordering)
    result = json.dumps(fields, sort_keys=True, separators=(',', ':'))
    counts['b13_binding_bytes'] += len(result.encode())
    return result


def _prepare(inputs, cl, fc, jc, nc, lc, combined_closure, counts, trace_limit):
    if len(inputs) != 27 or type(trace_limit) is not int or trace_limit < 1:
        raise ValueError('B13 requires 27 inputs and a positive trace bound')
    source, unseen, continuation = (shared.shared.shared._header(inputs[i]) for i in (24, 25, 26))
    prepared, view, _, _, order, binding, _ = shared._prepare(
        inputs[:24], cl, fc, jc, nc, lc, counts, source['trace_limit'], 'source')
    counts['b13_prefix_preparations'] += 1
    shared._check(shared.prior, view, prepared[25], order, binding, inputs[24], counts)
    same_unseen = (prepared[23] == prepared[25] and nc == lc
                   and inputs[22]['program']['trace_limit'] == unseen['trace_limit'])
    unseen_order = order
    if not same_unseen:
        seen = set(inputs[22]['cursor']['completed']) | set(inputs[23]['cursor']['completed'])
        unseen_order = tuple(lit for lit in order if lit not in seen) + tuple(lit for lit in order if lit in seen)
        counts['b13_history_hint_slots'] += len(inputs[22]['cursor']['completed']) + len(inputs[23]['cursor']['completed'])
    unseen_binding = _binding(shared.prior.POLICY, prepared[0], prepared[25], lc,
                              unseen_order, unseen['trace_limit'], counts, ordering='unseen')
    shared._check(shared.prior, view, prepared[25], unseen_order, unseen_binding, inputs[25], counts)

    fixed = engine.prior.check_closure(prepared[23], nc, counts)
    lower_bank, _ = engine.prior.residual_bank(prepared[23], fixed, counts)
    active = {abs(lit) for clause in lower_bank for lit in clause}
    lower_order = tuple(lit for lit in engine.frozen.roots(prepared[0]) if abs(lit) in active)
    lower_binding = _binding(shared.b11.POLICY, prepared[0], prepared[23], nc,
                             lower_order, continuation['trace_limit'], counts)
    shared._check(shared.b11, (*prepared[:15], prepared[23], prepared[24]), prepared[23],
                  lower_order, lower_binding, inputs[26], counts)
    counts['b13_histories_checked'] += 3

    entries = dict(zip(prepared[25], prepared[26]))
    for kind, program in (('b12_source_probe', source), ('b12_unseen_probe', unseen),
                          ('b11_continuation_probe', continuation)):
        for i, row in enumerate(program['probes']):
            clause = (-row['assumption'],)
            counts['b13_exclusions'] += 1
            if clause not in entries:
                entries[clause] = dict(kind=kind, index=i)
                counts['b13_added_units'] += 1
    clauses = tuple(sorted(entries))
    prepared = (*prepared, clauses, [entries[clause] for clause in clauses])
    fixed = engine.prior.check_closure(clauses, combined_closure, counts)
    bank, ids = engine.prior.residual_bank(clauses, fixed, counts)
    active = {abs(lit) for clause in bank for lit in clause}
    order = tuple(lit for lit in engine.frozen.roots(prepared[0]) if abs(lit) in active)
    binding = _binding(POLICY, prepared[0], clauses, combined_closure, order, trace_limit, counts)
    counts['b13_compare_literals'] += sum(map(len, prepared[25])) + sum(map(len, clauses))
    same = (prepared[25] == clauses and lc == combined_closure
            and source['trace_limit'] == trace_limit)
    return prepared, (*prepared[:15], clauses, prepared[28]), bank, ids, order, binding, same


def discover(*inputs, closure, feedback_closure, joint_closure, next_closure,
             latest_closure, combined_closure, counts, policy='reuse', cursor=None,
             probe_limit=64, work_limit=262144, trace_limit=256):
    if policy not in ('restart', 'matched', 'reuse') or any(
            type(v) is not int or v < 1 for v in (probe_limit, work_limit, trace_limit)):
        raise ValueError('Invalid B13 search options')
    owned, cl, fc, jc, nc, lc, combined, saved = deepcopy((inputs, closure,
        feedback_closure, joint_closure, next_closure, latest_closure, combined_closure, cursor))
    counts['b13_owned_copies'] += 1
    prepared, view, bank, ids, order, binding, same = _prepare(
        owned, cl, fc, jc, nc, lc, combined, counts, trace_limit)
    if saved is None and same and policy == 'matched':
        extra = len(owned[24]['cursor']['completed'])
        probe_limit += extra
        work_limit *= 1 + (extra + 63) // 64
    if saved is None and same and policy == 'reuse':
        saved = deepcopy(owned[24]['cursor'])
        saved.update(format=FORMAT, binding=binding)
        counts['b13_imported_completed'] += len(saved['completed'])
        counts['b13_imported_cursors'] += 1
    elif saved is None:
        counts['b13_fresh_cursors'] += 1
    else:
        counts['b13_continued_cursors'] += 1
    state = _load(view, order, binding, saved, counts, trace_limit)
    result = shared.shared.b8._search(bank, ids, binding, combined['units'], state,
                                    counts, probe_limit, work_limit, trace_limit)
    result['cursor']['format'] = FORMAT
    return result


def _load(view, order, binding, cursor, counts, trace_limit):
    if cursor is not None:
        if type(cursor) is not dict or cursor.get('format') != FORMAT:
            raise ValueError('Invalid B13 cursor format')
        cursor = deepcopy(cursor)
        cursor['format'] = engine.FORMAT
    return engine.load(view, order, binding, cursor, counts, trace_limit)


def validate(*inputs, closure, feedback_closure, joint_closure, next_closure,
             latest_closure, combined_closure, result, counts):
    owned, cl, fc, jc, nc, lc, combined, saved = deepcopy((inputs, closure,
        feedback_closure, joint_closure, next_closure, latest_closure, combined_closure, result))
    counts['b13_owned_copies'] += 1
    program = shared.shared.shared._header(saved)
    prepared, view, _, _, order, binding, _ = _prepare(
        owned, cl, fc, jc, nc, lc, combined, counts, program['trace_limit'])
    state = _load(view, order, binding, saved['cursor'], counts, program['trace_limit'])
    engine.prior.check_program(prepared[0], prepared[27], program, counts)
    if program != engine._program(state[4], state[6], program['trace_limit'], program['reason']):
        raise ValueError('B13 program disagrees with cursor')
    return prepared
