"""Reuse a saved unit prefix after optional discovery declines a new guard.

This does not admit the rejected guard. It publishes the original target using
its baseline trace and ordinary solving of the remaining residual. Residual
acquisition retains its unrestricted cost and existing expansion budget.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_propagated_reuse import select as previous_select


def select(solver, source, variable_limit=4, counts=None):
    counts = Counter() if counts is None else counts
    choice, trace = previous_select(solver, source, variable_limit, counts)
    discovery = trace['discovery']
    if choice is not None or discovery is None or not discovery['fixed']:
        return choice, trace
    baseline = discovery['baseline']
    if baseline['conflict'] is not None:
        raise ValueError('Terminal target must have been selected before fallback')
    trace['fallback_reason'] = trace['reason']
    trace['reason'] = 'retained-prefix'
    counts['fallback_trace_reuses'] += 1
    counts['fallback_forced_variables'] += len(discovery['fixed'])
    return dict(kind='fallback-trace', screen=deepcopy(baseline)), trace
