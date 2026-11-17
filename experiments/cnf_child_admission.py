"""Optional local guards whose remaining child is known or unit-refuted.

Recognition changes policy only. Checked native publication and guard-chain
composition remain the authority. A rejected candidate leaves the archive intact.
"""
from collections import Counter
from experiments.cnf_local_guard import probe as local_probe
from experiments.cnf_residual_dag import restrict
from experiments.cnf_partition_screen import screen_branch


def select(solver, source, variable_limit=4, counts=None):
    if type(variable_limit) is not int or variable_limit < 0:
        raise ValueError('Expected a nonnegative variable bound')
    counts = Counter() if counts is None else counts
    record = dict(reason=None, discovery=None, proposal=None, child=None)
    if not variable_limit:
        record['reason'] = 'disabled'
        return None, record
    cnf, _, root = solver._canonical(source)
    if solver._read(root, cnf, purpose='admission_target') is not None:
        record['reason'] = 'known-target'
        return None, record
    counts['admission_family_clauses'] += len(cnf)
    counts['admission_family_literal_visits'] += sum(map(len, cnf))
    two = horn = dual = True
    for clause in cnf:
        positive = sum(l > 0 for l in clause)
        two &= len(clause) <= 2
        horn &= positive <= 1
        dual &= len(clause) - positive <= 1
    family = 'two-cnf' if two else 'horn' if horn else 'dual-horn' if dual else None
    if family:
        record['reason'] = 'native-' + family
        return None, record
    # Existing deletion-guard certificates exclude tautological source clauses.
    # The native fallback handles them; a normalized key alone cannot establish
    # eligibility for that stricter source-bound interface.
    for clause in source:
        counts['admission_source_literal_visits'] += len(clause)
        literals = set(clause)
        if any(-l in literals for l in literals):
            record['reason'] = 'tautological-source'
            return None, record
    choice, record['discovery'] = local_probe(solver, source, variable_limit, counts)
    record['proposal'] = choice
    if choice is None:
        record['reason'] = 'no-proposal'
        return None, record
    if choice['kind'] == 'terminal':
        record['reason'] = 'terminal-target'
        return choice, record
    target = restrict(source, {abs(l): l < 0 for l in choice['clause']}, counts)
    cnf, _, root = solver._canonical(target)
    known = solver._read(root, cnf, purpose='admission_child') is not None
    screen = None if known else screen_branch(solver, target, counts)
    counts['admission_child_lookups'] += 1
    counts['admission_child_probes'] += int(not known)
    record['child'] = dict(root=root, known=known, screen=screen)
    if known or screen['conflict'] is not None:
        record['reason'] = 'known-child' if known else 'unit-conflict-child'
        return dict(**choice, child=record['child']), record
    record['reason'] = 'nonterminal-child'
    return None, record
