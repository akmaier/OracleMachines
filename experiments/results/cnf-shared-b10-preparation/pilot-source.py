"""Share B8 preparation inside one independently checked B10 call.

The original B8, comparison B8 and B9 histories keep their own bindings and
proof checks. Inputs are privately copied; no trusted state crosses calls.
"""
from copy import deepcopy
import json
from experiments import cnf_b10_probe_cursor as prior

b9 = prior.prior
shared = b9.shared
b8 = shared.prior
engine = prior.engine


def _check(module, view, clauses, order, binding, result, counts):
    program = shared._header(result)
    state = module._load(view, order, binding, result['cursor'], counts,
                         program['trace_limit'])
    engine.prior.check_program(view[0], clauses, program, counts)
    if program != engine._program(state[4], state[6], program['trace_limit'],
                                  program['reason']):
        raise ValueError('Source program disagrees with cursor')
    if program['status'] != 'unresolved':
        raise ValueError('Unresolved source histories required')
    counts['shared_b10_histories_checked'] += 1


def _prepare(inputs, closure, feedback_closure, joint_closure, counts, trace_limit):
    if len(inputs) != 21 or type(trace_limit) is not int or trace_limit < 1:
        raise ValueError('B10 requires 21 inputs and a positive trace bound')
    original, upper, comparison = (shared._header(inputs[i]) for i in (18, 19, 20))
    prepared, view, _, _, order, binding = shared._prepare(
        inputs[:18], closure, counts, original['trace_limit'])
    counts['shared_b10_prefix_preparations'] += 1
    _check(b8, view, prepared[17], order, binding, inputs[18], counts)
    # Trace bounds affect a history's binding, not its source-derived B8 bank,
    # closure, residual order or provenance. Check both histories independently.
    if comparison['trace_limit'] == original['trace_limit']:
        comparison_binding = binding
        counts['shared_b10_bindings_reused'] += 1
    else:
        comparison_binding = shared._binding(
            b8.POLICY, prepared[0], prepared[17], closure, order,
            comparison['trace_limit'], counts)
    _check(b8, view, prepared[17], order, comparison_binding, inputs[20], counts)

    entries = dict(zip(prepared[17], prepared[18]))
    for i, row in enumerate(original['probes']):
        clause = (-row['assumption'],)
        counts['b9_exclusions'] += 1
        if clause not in entries:
            entries[clause] = dict(kind='joint_probe', index=i)
            counts['b9_added_units'] += 1
    clauses = tuple(sorted(entries))
    prepared = (*prepared, clauses, [entries[cl] for cl in clauses])
    fixed = engine.prior.check_closure(clauses, feedback_closure, counts)
    bank, _ = engine.prior.residual_bank(clauses, fixed, counts)
    active = {abs(lit) for clause in bank for lit in clause}
    order = tuple(lit for lit in engine.frozen.roots(prepared[0]) if abs(lit) in active)
    binding = shared._binding(b9.POLICY, prepared[0], clauses, feedback_closure,
                              order, upper['trace_limit'], counts)
    _check(b9, (*prepared[:15], clauses, prepared[20]), clauses, order, binding,
           inputs[19], counts)

    for kind, program in (('b8_comparison_probe', comparison), ('b9_probe', upper)):
        for i, row in enumerate(program['probes']):
            clause = (-row['assumption'],)
            counts['b10_exclusions'] += 1
            if clause not in entries:
                entries[clause] = dict(kind=kind, index=i)
                counts['b10_added_units'] += 1
    clauses = tuple(sorted(entries))
    prepared = (*prepared, clauses, [entries[cl] for cl in clauses])
    fixed = engine.prior.check_closure(clauses, joint_closure, counts)
    bank, ids = engine.prior.residual_bank(clauses, fixed, counts)
    active = {abs(lit) for clause in bank for lit in clause}
    order = tuple(lit for lit in engine.frozen.roots(prepared[0]) if abs(lit) in active)
    binding = json.dumps([prior.POLICY, prepared[0], clauses, joint_closure,
                          order, trace_limit], sort_keys=True, separators=(',', ':'))
    counts['b10_binding_bytes'] += len(binding.encode())
    counts['b10_compare_literals'] += sum(map(len, prepared[19])) + sum(map(len, clauses))
    same = (prepared[19] == clauses and feedback_closure == joint_closure
            and upper['trace_limit'] == trace_limit)
    return prepared, (*prepared[:15], clauses, prepared[22]), bank, ids, order, binding, same


def discover(*inputs, closure, feedback_closure, joint_closure, counts,
             policy='reuse', cursor=None, probe_limit=64, work_limit=262144,
             trace_limit=256):
    if policy not in ('restart', 'matched', 'reuse') or any(
            type(v) is not int or v < 1 for v in (probe_limit, work_limit, trace_limit)):
        raise ValueError('Invalid B10 search options')
    owned, cl, fc, jc, saved = deepcopy((inputs, closure, feedback_closure, joint_closure, cursor))
    counts['shared_b10_owned_copies'] += 1
    prepared, view, bank, ids, order, binding, same = _prepare(
        owned, cl, fc, jc, counts, trace_limit)
    if saved is None and same and policy == 'matched':
        extra = len(owned[19]['cursor']['completed'])
        probe_limit += extra
        work_limit *= 1 + (extra + 63) // 64
    if saved is None and same and policy == 'reuse':
        saved = deepcopy(owned[19]['cursor'])
        saved.update(format=prior.FORMAT, binding=binding)
        counts['b10_imported_completed'] += len(saved['completed'])
        counts['b10_imported_cursors'] += 1
    elif saved is None:
        counts['b10_fresh_cursors'] += 1
    else:
        counts['b10_continued_cursors'] += 1
    state = prior._load(view, order, binding, saved, counts, trace_limit)
    result = b8._search(bank, ids, binding, jc['units'], state, counts,
                        probe_limit, work_limit, trace_limit)
    result['cursor']['format'] = prior.FORMAT
    return result


def validate(*inputs, closure, feedback_closure, joint_closure, result, counts):
    owned, cl, fc, jc, saved = deepcopy((inputs, closure, feedback_closure, joint_closure, result))
    counts['shared_b10_owned_copies'] += 1
    program = shared._header(saved)
    prepared, view, _, _, order, binding, _ = _prepare(
        owned, cl, fc, jc, counts, program['trace_limit'])
    state = prior._load(view, order, binding, saved['cursor'], counts, program['trace_limit'])
    engine.prior.check_program(prepared[0], prepared[21], program, counts)
    if program != engine._program(state[4], state[6], program['trace_limit'], program['reason']):
        raise ValueError('B10 program disagrees with cursor')
    return prepared
