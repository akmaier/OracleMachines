"""Share immutable B12 preparation across bounded rounds in one owned call.

Each round reloads its portable cursor. In particular, a stopped search may
have popped an uncompleted root; its mutated queue must never be handed on.
The exported results use the existing B12 format and independent cold checker.
"""
from copy import deepcopy
from experiments import cnf_shared_b12_preparation as prior


def continue_rounds(*inputs, closure, feedback_closure, joint_closure, next_closure,
                    latest_closure, cursor, counts, rounds=3, ordering='source',
                    probe_limit=64, work_limit=262144, trace_limit=256):
    if cursor is None or any(type(v) is not int or v < 1 for v in
                            (rounds, probe_limit, work_limit, trace_limit)):
        raise ValueError('A saved B12 cursor and positive round bounds are required')
    owned, cl, fc, jc, nc, lc, saved = deepcopy((inputs, closure, feedback_closure,
        joint_closure, next_closure, latest_closure, cursor))
    counts['batch_owned_copies'] += 1
    prepared, view, bank, ids, order, binding, _ = prior._prepare(
        owned, cl, fc, jc, nc, lc, counts, trace_limit, ordering)
    counts['batch_prefix_preparations'] += 1
    results = []
    for _ in range(rounds):
        state = prior.prior._load(view, order, binding, saved, counts, trace_limit)
        before = len(state[3])
        counts['b12_continued_cursors'] += 1
        result = prior.shared.b8._search(bank, ids, binding, lc['units'], state,
                                        counts, probe_limit, work_limit, trace_limit)
        result['cursor']['format'] = prior.prior.FORMAT
        # Independent snapshots avoid aliasing across exported rounds or back
        # into the caller's supplied histories and cursor.
        results.append(deepcopy(result))
        counts['batch_rounds'] += 1
        if (result['program']['status'] == 'refuted'
                or result['program']['reason'] == 'complete'
                or len(result['cursor']['completed']) == before):
            break
        saved = result['cursor']
    return results
