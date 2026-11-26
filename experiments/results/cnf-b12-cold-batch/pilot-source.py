"""Independently cold-check B12 snapshots with one owned common preparation.

A batch has one source, closure, policy and trace bound. Every snapshot keeps
its own cursor replay, failed-proof check and program/cursor agreement check.
No prepared state or validation authority is accepted from discovery.
"""
from copy import deepcopy
from experiments import cnf_shared_b12_preparation as prior


def validate_many(*inputs, closure, feedback_closure, joint_closure, next_closure,
                  latest_closure, results, counts, ordering='source'):
    if type(results) not in (list, tuple) or not results:
        raise ValueError('A nonempty sequence of B12 snapshots is required')
    owned, cl, fc, jc, nc, lc, snapshots = deepcopy((inputs, closure,
        feedback_closure, joint_closure, next_closure, latest_closure, results))
    counts['cold_batch_owned_copies'] += 1
    programs = [prior.shared.shared._header(result) for result in snapshots]
    limit = programs[0]['trace_limit']
    if any(program['trace_limit'] != limit for program in programs):
        raise ValueError('Cold batch snapshots must share the trace bound')
    prepared, view, _, _, order, binding, _ = prior._prepare(
        owned, cl, fc, jc, nc, lc, counts, limit, ordering)
    counts['cold_batch_prefix_preparations'] += 1
    for result, program in zip(snapshots, programs):
        state = prior.prior._load(view, order, binding, result['cursor'], counts, limit)
        prior.engine.prior.check_program(prepared[0], prepared[25], program, counts)
        if program != prior.engine._program(state[4], state[6], limit, program['reason']):
            raise ValueError('B12 program disagrees with cursor')
        counts['cold_batch_snapshots_checked'] += 1
    return prepared
