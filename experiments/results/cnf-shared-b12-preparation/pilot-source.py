"""Share common B10 preparation within one owned, independently checked B12 call.

Original B10, comparison B10 and B11 histories retain their own bindings and
proof checks. No prepared object or validation authority survives the call.
"""
from copy import deepcopy
import json
from experiments import cnf_b12_progress_order as prior

b11 = prior.prior
shared = b11.shared
engine = prior.engine


def _check(module, view, clauses, order, binding, result, counts):
    program = shared.shared._header(result)
    state = module._load(view, order, binding, result['cursor'], counts,
                         program['trace_limit'])
    engine.prior.check_program(view[0], clauses, program, counts)
    if program != engine._program(state[4], state[6], program['trace_limit'],
                                  program['reason']):
        raise ValueError('Source program disagrees with cursor')
    if program['status'] != 'unresolved':
        raise ValueError('Unresolved source histories required')
    counts['shared_b12_histories_checked'] += 1


def _prepare(inputs, closure, feedback_closure, joint_closure, next_closure,
             latest_closure, counts, trace_limit, ordering):
    if len(inputs) != 24 or type(trace_limit) is not int or trace_limit < 1:
        raise ValueError('B12 requires 24 inputs and a positive trace bound')
    if ordering not in ('source', 'unseen'):
        raise ValueError('Invalid B12 ordering')
    original, upper, comparison = (shared.shared._header(inputs[i]) for i in (21, 22, 23))
    prepared, view, _, _, order, binding, _ = shared._prepare(
        inputs[:21], closure, feedback_closure, joint_closure, counts,
        original['trace_limit'])
    counts['shared_b12_prefix_preparations'] += 1
    _check(shared.prior, view, prepared[21], order, binding, inputs[21], counts)
    # Only the trace bound differs between these history bindings. The common
    # source-derived bank, provenance, closure and residual order are identical.
    if comparison['trace_limit'] == original['trace_limit']:
        comparison_binding = binding
        counts['shared_b12_bindings_reused'] += 1
    else:
        comparison_binding = shared.shared._binding(
            shared.prior.POLICY, prepared[0], prepared[21], joint_closure,
            order, comparison['trace_limit'], counts)
    _check(shared.prior, view, prepared[21], order, comparison_binding, inputs[23], counts)

    entries = dict(zip(prepared[21], prepared[22]))
    for i, row in enumerate(original['probes']):
        clause = (-row['assumption'],)
        counts['b11_exclusions'] += 1
        if clause not in entries:
            entries[clause] = dict(kind='b10_probe', index=i)
            counts['b11_added_units'] += 1
    clauses = tuple(sorted(entries))
    prepared = (*prepared, clauses, [entries[cl] for cl in clauses])
    fixed = engine.prior.check_closure(clauses, next_closure, counts)
    bank, _ = engine.prior.residual_bank(clauses, fixed, counts)
    active = {abs(lit) for clause in bank for lit in clause}
    order = tuple(lit for lit in engine.frozen.roots(prepared[0]) if abs(lit) in active)
    binding = shared.shared._binding(b11.POLICY, prepared[0], clauses, next_closure,
                                      order, upper['trace_limit'], counts)
    _check(b11, (*prepared[:15], clauses, prepared[24]), clauses, order, binding,
           inputs[22], counts)

    for kind, program in (('b10_comparison_probe', comparison), ('b11_probe', upper)):
        for i, row in enumerate(program['probes']):
            clause = (-row['assumption'],)
            counts['b12_exclusions'] += 1
            if clause not in entries:
                entries[clause] = dict(kind=kind, index=i)
                counts['b12_added_units'] += 1
    clauses = tuple(sorted(entries))
    prepared = (*prepared, clauses, [entries[cl] for cl in clauses])
    fixed = engine.prior.check_closure(clauses, latest_closure, counts)
    bank, ids = engine.prior.residual_bank(clauses, fixed, counts)
    active = {abs(lit) for clause in bank for lit in clause}
    order = tuple(lit for lit in engine.frozen.roots(prepared[0]) if abs(lit) in active)
    same = (prepared[23] == clauses and next_closure == latest_closure
            and upper['trace_limit'] == trace_limit)
    if ordering == 'unseen' and not same:
        seen = set(inputs[22]['cursor']['completed']) | set(inputs[23]['cursor']['completed'])
        counts['b12_hint_slots'] += len(inputs[22]['cursor']['completed']) + len(inputs[23]['cursor']['completed'])
        fresh = tuple(lit for lit in order if lit not in seen)
        old = tuple(lit for lit in order if lit in seen)
        order = fresh + old
        counts['b12_unseen_priority_literals'] += len(fresh)
        counts['b12_deferred_literals'] += len(old)
    binding = json.dumps([prior.POLICY, ordering, prepared[0], clauses, latest_closure,
                          order, trace_limit], sort_keys=True, separators=(',', ':'))
    counts['b12_binding_bytes'] += len(binding.encode())
    counts['b12_compare_literals'] += sum(map(len, prepared[23])) + sum(map(len, clauses))
    return prepared, (*prepared[:15], clauses, prepared[26]), bank, ids, order, binding, same


def discover(*inputs, closure, feedback_closure, joint_closure, next_closure,
             latest_closure, counts, policy='reuse', cursor=None, probe_limit=64,
             work_limit=262144, trace_limit=256, ordering='unseen'):
    if policy not in ('restart', 'matched', 'reuse') or any(
            type(v) is not int or v < 1 for v in (probe_limit, work_limit, trace_limit)):
        raise ValueError('Invalid B12 search options')
    owned, cl, fc, jc, nc, lc, saved = deepcopy((inputs, closure, feedback_closure,
        joint_closure, next_closure, latest_closure, cursor))
    counts['shared_b12_owned_copies'] += 1
    prepared, view, bank, ids, order, binding, same = _prepare(
        owned, cl, fc, jc, nc, lc, counts, trace_limit, ordering)
    if saved is None and same and policy == 'matched':
        extra = len(owned[22]['cursor']['completed'])
        probe_limit += extra
        work_limit *= 1 + (extra + 63) // 64
    if saved is None and same and policy == 'reuse':
        saved = deepcopy(owned[22]['cursor'])
        saved.update(format=prior.FORMAT, binding=binding)
        counts['b12_imported_completed'] += len(saved['completed'])
        counts['b12_imported_cursors'] += 1
    elif saved is None:
        counts['b12_fresh_cursors'] += 1
    else:
        counts['b12_continued_cursors'] += 1
    state = prior._load(view, order, binding, saved, counts, trace_limit)
    result = shared.b8._search(bank, ids, binding, lc['units'], state, counts,
                               probe_limit, work_limit, trace_limit)
    result['cursor']['format'] = prior.FORMAT
    return result


def validate(*inputs, closure, feedback_closure, joint_closure, next_closure,
             latest_closure, result, counts, ordering='unseen'):
    owned, cl, fc, jc, nc, lc, saved = deepcopy((inputs, closure, feedback_closure,
        joint_closure, next_closure, latest_closure, result))
    counts['shared_b12_owned_copies'] += 1
    program = shared.shared._header(saved)
    prepared, view, _, _, order, binding, _ = _prepare(
        owned, cl, fc, jc, nc, lc, counts, program['trace_limit'], ordering)
    state = prior._load(view, order, binding, saved['cursor'], counts, program['trace_limit'])
    engine.prior.check_program(prepared[0], prepared[25], program, counts)
    if program != engine._program(state[4], state[6], program['trace_limit'], program['reason']):
        raise ValueError('B12 program disagrees with cursor')
    return prepared
