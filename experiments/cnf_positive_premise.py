"""Recover a full SAT witness from an already retained positive premise screen.

This optional policy scans the previous selector's saved attempts only when it
would otherwise acquire a fallback. It neither extends the candidate budget nor
claims that the negative-probe filter preserves all positive opportunities.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_binary_probe import select as previous_select
from experiments.cnf_residual_dag import restrict, holds


def recover_premise_model(solver, source, attempt, counts=None):
    """Check the trace of source AND assumption, then transport its model."""
    counts = Counter() if counts is None else counts
    clause = attempt['clause']; screen = attempt['screen']
    if (type(clause) is not list or len(clause) != 1
            or type(clause[0]) is not int or not clause[0]):
        raise ValueError('Expected a single-literal assumption')
    _, names, root = solver._canonical(source)
    if abs(clause[0]) not in names:
        raise ValueError('Assumption variable is outside target')
    stronger = [list(c) for c in source] + [list(clause)]
    counts['positive_premise_literals_copied'] += sum(map(len, stronger))
    cnf, premise_names, premise_root = solver._canonical(stronger)
    if screen['root'] != premise_root or screen['conflict'] is not None:
        raise ValueError('Unbound positive premise')
    if type(screen['trace']) is not list:
        raise ValueError('Invalid premise unit trace')
    fixed = {}
    for step in screen['trace']:
        if type(step) is not list or len(step) != 2:
            raise ValueError('Invalid premise unit trace')
        literal, cid = step
        if (type(literal) is not int or not literal or type(cid) is not int
                or not 0 <= cid < len(cnf) or abs(literal) in fixed):
            raise ValueError('Invalid premise unit trace')
        reason = cnf[cid]
        counts['positive_premise_reason_literals'] += len(reason)
        if (any(abs(l) in fixed and fixed[abs(l)] == (l > 0) for l in reason)
                or [l for l in reason if abs(l) not in fixed] != [literal]):
            raise ValueError('Unforced premise literal')
        fixed[abs(literal)] = literal > 0
    # residual_literals is only a selection hint, never a certificate.
    if restrict(cnf, fixed, counts):
        raise ValueError('Premise is not positive-terminal')
    model = {name: fixed.get(i + 1, False) for i, name in enumerate(premise_names)}
    model = {name: model.get(name, False) for name in names}
    counts['positive_premise_model_literals'] += sum(map(len, stronger))
    if not holds(stronger, model):
        raise ValueError('Lifted model fails target or assumption')
    counts['positive_premise_models'] += 1
    return dict(kind='positive-model', root=root, model=[[v, bit] for v, bit in model.items()])


def select(solver, source, variable_limit=4, counts=None):
    """Use a checked saved premise model before fresh fallback acquisition."""
    counts = Counter() if counts is None else counts
    choice, trace = previous_select(solver, source, variable_limit, counts)
    discovery = trace['discovery']
    if discovery is None or (choice is not None and choice['kind'] != 'fallback-trace'):
        return choice, trace
    for index, attempt in enumerate(discovery['attempts']):
        counts['positive_premise_attempts_scanned'] += 1
        screen = attempt['screen']
        if screen['conflict'] is not None or screen['residual_literals'] != 0:
            continue
        recovered = recover_premise_model(solver, source, attempt, counts)
        if choice is not None:
            counts['fallback_trace_reuses'] -= 1
            counts['fallback_forced_variables'] -= len(discovery['fixed'])
        trace['previous_reason'] = trace['reason']; trace['reason'] = 'positive-premise-model'
        trace['positive_premise_attempt'] = index
        trace['positive_model'] = deepcopy(recovered)
        return recovered, trace
    return choice, trace
