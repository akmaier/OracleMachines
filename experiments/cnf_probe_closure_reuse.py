"""Delta-check a saved unit fixed point before reusing its proof by reference.

Only an append-only, independently justified batch is eligible. Original probe
proofs are checked first. Restriction preserves the old clause prefix, so reason
indices remain valid. An active added clause or a new assumption uses the full
old probe pass. This policy changes proof representation, not probe budgets.
"""
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_equivalence import discover_equivalence_probes, check_equivalence_probes
from experiments.cnf_probe_learning import ProbeLearningInventory, learning_batch, augment
from experiments.cnf_residual_dag import restrict
from experiments.cnf_simplification import discover_simplification, check_simplification


def batch_inactive(attempt, batch, counts):
    """A previously validated nonconflicting unit closure needs only this delta.

    This is a fixed-point test, not a stand-alone proof checker. Duplicate
    literal semantics agree with the existing scan propagator; inputs/batches
    here are normalized, non-tautological clauses with distinct variables.
    """
    certificate = attempt['certificate']
    if certificate['conflict'] is not None or certificate['pure_rounds']:
        return False
    assigned = {attempt['variable']: attempt['value']}
    assigned.update((abs(lit), lit > 0) for lit, _ in certificate['units'])
    counts['reuse_assignment_entries'] += 1 + len(certificate['units'])
    for addition in batch:
        unassigned = 0
        satisfied = False
        for lit in addition['clause']:
            counts['reuse_delta_literal_visits'] += 1
            value = assigned.get(abs(lit))
            if value is None:
                unassigned += 1
            elif value == (lit > 0):
                satisfied = True
                break
        if not satisfied and unassigned < 2:
            counts['reuse_active_batches'] += 1
            return False
    return True


def expand_references(continuation, attempts):
    """Materialize aliases only; checking the source and delta is separate."""
    expanded = dict(continuation, attempts=[])
    for attempt in continuation['attempts']:
        copy = dict(attempt)
        certificate = attempt['certificate']
        if 'reuse' in certificate:
            index = certificate['reuse']
            if (set(certificate) != {'reuse'} or type(index) is not int or
                    not 0 <= index < len(attempts)):
                raise ValueError('Invalid original probe reference')
            original = attempts[index]
            if (attempt['variable'] != original['variable'] or
                    attempt['value'] != original['value']):
                raise ValueError('Reused probe has a different assumption')
            copy['certificate'] = original['certificate']
        expanded['attempts'].append(copy)
    return expanded


def discover_reuse_probes(cnf, probe_limit, learn_limit, counts, *, _select_batch=learning_batch):
    original = discover_equivalence_probes(cnf, probe_limit, counts)
    if original['status'] != 'clear':
        return original
    batch = _select_batch(cnf, original['attempts'], learn_limit, counts)
    if not batch:
        return original
    augmented = augment(cnf, batch)
    saved = {(a['variable'], a['value']): (i, a) for i, a in enumerate(original['attempts'])}

    def discover_attempt(variable, value):
        previous = saved.get((variable, value))
        if previous is not None and batch_inactive(previous[1], batch, counts):
            counts['reused_continuation_probes'] += 1
            return previous[1]['certificate']
        counts['fresh_continuation_probes' if previous is None else 'active_continuation_probes'] += 1
        return discover_simplification(restrict(augmented, {variable: value}, counts), counts, pure=False)

    before = counts['probe_attempts']
    continuation = discover_equivalence_probes(augmented, probe_limit, counts,
                                               _discover_attempt=discover_attempt)
    counts['learning_continuation_probe_attempts'] += counts['probe_attempts'] - before
    for attempt in continuation['attempts']:
        previous = saved.get((attempt['variable'], attempt['value']))
        if previous is not None and attempt['certificate'] is previous[1]['certificate']:
            attempt['certificate'] = dict(reuse=previous[0])
    success = continuation['status'] != 'clear'
    counts['learning_successes' if success else 'learning_inconclusive'] += 1
    counts['learning_clauses_proposed'] += len(batch)
    return dict(status='learned' if success else 'learning_clear', attempts=original['attempts'],
                batch=batch, continuation=continuation)


def check_reuse_probes(cnf, result, probe_limit, learn_limit, counts, *, _select_batch=learning_batch):
    if result.get('status') not in ('learned', 'learning_clear'):
        target, fixed = check_equivalence_probes(cnf, result, probe_limit, counts)
        if result['status'] == 'clear' and _select_batch(cnf, result['attempts'], learn_limit, counts):
            raise ValueError('Omitted local-learning attempt')
        return target, fixed
    if set(result) != {'status', 'attempts', 'batch', 'continuation'}:
        raise ValueError('Invalid local-learning fields')
    # All original reasons and fixed points are checked before selecting a batch
    # or consulting a reference. The selector is code, never certificate input.
    check_equivalence_probes(cnf, dict(status='clear', attempts=result['attempts']), probe_limit, counts)
    expected = _select_batch(cnf, result['attempts'], learn_limit, counts)
    if not expected or encode(result['batch']) != encode(expected):
        raise ValueError('Invalid learning batch or source reason')
    augmented = augment(cnf, expected)
    expanded = expand_references(result['continuation'], result['attempts'])
    saved = {(a['variable'], a['value']): a for a in result['attempts']}

    def check_attempt(variable, value, certificate):
        previous = saved.get((variable, value))
        if previous is not None and certificate is previous['certificate']:
            if not batch_inactive(previous, expected, counts):
                raise ValueError('Added clause invalidates reused fixed point')
            counts['verified_reused_probes'] += 1
        else:
            check_simplification(restrict(augmented, {variable: value}, counts), certificate, counts, pure=False)

    target, fixed = check_equivalence_probes(augmented, expanded, probe_limit, counts,
                                             _check_attempt=check_attempt)
    success = expanded['status'] != 'clear'
    if (result['status'] == 'learned') != success:
        raise ValueError('Invalid learning outcome')
    counts['verified_learning_attempts'] += 1
    if not success:
        return cnf, {}
    if not {abs(l) for c in target for l in c} < {abs(l) for c in cnf for l in c}:
        raise ValueError('Learned continuation must strictly reduce support')
    return target, fixed


class ProbeClosureReuseInventory(ProbeLearningInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['probe_closure_reuse'] = 'checked-inactive-batch-reference-v1'

    def _discover_probes(self, cnf):
        return discover_reuse_probes(cnf, self.config['probe_limit'], self.config['learn_limit'], self.counts)

    def _check_probes(self, cnf, result):
        return check_reuse_probes(cnf, result, self.config['probe_limit'], self.config['learn_limit'], self.counts)
