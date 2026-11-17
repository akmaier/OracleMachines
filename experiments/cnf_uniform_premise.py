"""Complete saved conditioned residuals with checked uniform assignments.

After consistent unit closure, all-false covers Horn residuals and all-true
covers dual-Horn residuals. The direct sign test also accepts broader CNFs.
Failure is inconclusive. The prior candidate budget and accepted choices stay.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_positive_premise import select as previous_select
from experiments.cnf_residual_dag import restrict, holds


def complete_premise(solver, source, attempt, counts=None):
    """Check a saved premise trace, then try both uniform residual models."""
    counts = Counter() if counts is None else counts
    clause = attempt['clause']; screen = attempt['screen']
    if (type(clause) is not list or len(clause) != 1
            or type(clause[0]) is not int or not clause[0]):
        raise ValueError('Expected a single-literal assumption')
    _, names, root = solver._canonical(source)
    if abs(clause[0]) not in names:
        raise ValueError('Assumption variable is outside target')
    stronger = [list(c) for c in source] + [list(clause)]
    counts['uniform_premise_literals_copied'] += sum(map(len, stronger))
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
        counts['uniform_premise_reason_literals'] += len(reason)
        if (any(abs(l) in fixed and fixed[abs(l)] == (l > 0) for l in reason)
                or [l for l in reason if abs(l) not in fixed] != [literal]):
            raise ValueError('Unforced premise literal')
        fixed[abs(literal)] = literal > 0
    # Reconstruct rather than trusting a residual-length or family label.
    residual = restrict(cnf, fixed, counts)
    counts['uniform_premise_recognition_clauses'] += len(residual)
    false_valid = true_valid = True
    for reason in residual:
        negative = positive = False
        for literal in reason:
            counts['uniform_premise_recognition_literal_visits'] += 1
            negative |= literal < 0; positive |= literal > 0
        false_valid &= negative; true_valid &= positive
    description = dict(residual_literals=sum(map(len, residual)),
        false_valid=false_valid, true_valid=true_valid)
    if not false_valid and not true_valid:
        counts['uniform_premise_misses'] += 1
        return None, description
    fill = not false_valid
    description['fill'] = fill
    model = {name: fixed.get(i + 1, fill) for i, name in enumerate(premise_names)}
    model = {name: model.get(name, False) for name in names}
    counts['uniform_premise_model_literals'] += sum(map(len, stronger))
    if not holds(stronger, model):
        raise ValueError('Lifted model fails target or assumption')
    counts['uniform_premise_models'] += 1
    return dict(kind='positive-model', root=root, model=[[v, bit] for v, bit in model.items()]), description


def select(solver, source, variable_limit=4, counts=None):
    counts = Counter() if counts is None else counts
    choice, trace = previous_select(solver, source, variable_limit, counts)
    discovery = trace['discovery']
    if (discovery is None or not discovery['attempts']
            or (choice is not None and choice['kind'] != 'fallback-trace')):
        return choice, trace
    diagnostics = dict(attempts=[], selected=None)
    trace['uniform_premise'] = diagnostics
    for index, attempt in enumerate(discovery['attempts']):
        counts['uniform_premise_attempts_scanned'] += 1
        if attempt['screen']['conflict'] is not None:
            continue
        recovered, description = complete_premise(solver, source, attempt, counts)
        diagnostics['attempts'].append(dict(index=index, **description))
        if recovered is None: continue
        if choice is not None:
            counts['fallback_trace_reuses'] -= 1
            counts['fallback_forced_variables'] -= len(discovery['fixed'])
        diagnostics['selected'] = index
        trace['previous_reason'] = trace['reason']; trace['reason'] = 'uniform-premise-model'
        trace['positive_model'] = deepcopy(recovered)
        return recovered, trace
    return choice, trace
