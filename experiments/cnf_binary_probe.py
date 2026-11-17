"""Skip single-assumption unit probes without residual binary incidence.

Only unassigned variables in the original candidate prefix are considered.
After consistent unit closure, assigning a variable outside every binary clause
cannot create a new unit or empty clause. This changes discovery work, not the
selected successful proposal, publication rule or general SAT fallback.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_residual_dag import propagate, restrict
from experiments.cnf_partition_screen import screen_branch
from experiments.cnf_positive_child import recover_model


def cheap_family(cnf, counts=None):
    if counts is not None:
        counts['propagated_family_clauses'] += len(cnf)
        counts['propagated_family_literal_visits'] += sum(map(len, cnf))
    if not cnf or () in cnf: return 'constant'
    two = horn = dual = True
    for clause in cnf:
        positives = sum(l > 0 for l in clause)
        two &= len(clause) <= 2; horn &= positives <= 1; dual &= len(clause) - positives <= 1
    return 'two-cnf' if two else 'horn' if horn else 'dual-horn' if dual else None


def probe(solver, source, variable_limit=4, counts=None):
    if type(variable_limit) is not int or variable_limit < 0:
        raise ValueError('Expected a nonnegative variable bound')
    counts = Counter() if counts is None else counts
    record = dict(baseline=None, fixed=[], ranks=[], candidates=[], attempts=[], selected=None, exposed=None, binary_filter=None)
    if not variable_limit:
        return None, record
    cnf, names, root = solver._canonical(source)
    fixed, trace, conflict = propagate(cnf, counts)
    residual = () if conflict is not None else restrict(cnf, fixed, counts)
    baseline = dict(root=root, trace=trace, conflict=conflict, residual_literals=sum(map(len, residual)))
    record['baseline'] = baseline
    record['fixed'] = [[names[v - 1], bit] for v, bit in sorted(fixed.items())]
    counts['local_baseline_probes'] += 1
    if conflict is not None:
        counts['local_terminal_targets'] += 1
        return dict(kind='terminal', screen=deepcopy(baseline)), record
    if fixed:
        residual_cnf, _, residual_root = solver._canonical(residual)
        node = solver._read(residual_root, residual_cnf, purpose='propagated_residual')
        counts['propagated_residual_lookups'] += 1
        family = cheap_family(residual_cnf, counts) if node is None else None
        # Disabling native leaves must not silently enable general search here.
        if family != 'constant' and not solver.leaves:
            family = None
        exposed = dict(root=residual_root, known=node is not None,
                       answer=None if node is None else node['answer'], family=family)
        record['exposed'] = exposed
        if node is not None or family is not None:
            counts['propagated_residual_reuses' if node is not None else 'propagated_family_admissions'] += 1
            return dict(kind='propagated', screen=deepcopy(baseline), exposed=deepcopy(exposed)), record
    binary = Counter()
    counts['local_ranking_clause_visits'] += len(cnf)
    counts['local_ranking_literal_visits'] += sum(map(len, cnf))
    for c in cnf:
        if len(c) == 2:
            binary.update(abs(l) for l in c)
    remaining = set(range(1, len(names) + 1)) - set(fixed)
    ranked = sorted(remaining, key=lambda v: (-binary[v], names[v - 1]))
    record['ranks'] = [dict(variable=names[v - 1], binary_incidence=binary[v]) for v in ranked]
    record['candidates'] = [[sign * names[v - 1]] for v in ranked[:variable_limit] for sign in (-1, 1)]
    counts['binary_filter_clause_visits'] += len(residual)
    eligible = set()
    for c in residual:
        if len(c) == 2:
            counts['binary_filter_literal_visits'] += 2
            eligible.update(abs(l) for l in c)
    eligible_names = {names[v-1] for v in eligible}
    counts['binary_filter_name_transports'] += len(eligible)
    record['binary_filter'] = dict(variables=sorted(eligible_names), skipped=[])
    for clause in record['candidates']:
        if abs(clause[0]) not in eligible_names:
            record['binary_filter']['skipped'].append(list(clause))
            counts['binary_probe_skips'] += 1
            continue
        stronger = [list(c) for c in source] + [clause]
        counts['local_premise_literals_copied'] += sum(map(len, stronger))
        screen = screen_branch(solver, stronger, counts)
        counts['local_premise_probes'] += 1
        record['attempts'].append(dict(clause=clause, screen=screen))
        if screen['conflict'] is not None:
            record['selected'] = len(record['attempts']) - 1
            counts['local_guards_found'] += 1
            return dict(kind='guard', clause=list(clause), screen=deepcopy(screen)), record
    return None, record


def _select(solver, source, variable_limit=4, counts=None):
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
    family = cheap_family(cnf)
    if family == 'constant': family = 'two-cnf'
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
    choice, record['discovery'] = probe(solver, source, variable_limit, counts)
    record['proposal'] = choice
    if choice is None:
        record['reason'] = 'no-proposal'
        return None, record
    if choice['kind'] in ('terminal', 'propagated'):
        record['reason'] = ('terminal-target' if choice['kind'] == 'terminal' else
                            'known-propagated' if choice['exposed']['known'] else 'native-propagated')
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


def select(solver, source, variable_limit=4, counts=None):
    """Retain prefix fallback and whole-target model recovery after filtering."""
    counts = Counter() if counts is None else counts
    choice, trace = _select(solver, source, variable_limit, counts)
    discovery = trace['discovery']
    if choice is None and discovery is not None and discovery['fixed']:
        baseline = discovery['baseline']
        if baseline['conflict'] is not None:
            raise ValueError('Terminal target must have been selected before fallback')
        trace['fallback_reason'] = trace['reason']; trace['reason'] = 'retained-prefix'
        counts['fallback_trace_reuses'] += 1
        counts['fallback_forced_variables'] += len(discovery['fixed'])
        choice = dict(kind='fallback-trace', screen=deepcopy(baseline))
    child = trace['child']; screen = None if child is None else child['screen']
    if screen is not None and screen['conflict'] is None and screen['residual_literals'] == 0:
        recovered = recover_model(solver, source, trace['proposal'], screen, counts)
        if choice is not None and choice['kind'] == 'fallback-trace':
            counts['fallback_trace_reuses'] -= 1
            counts['fallback_forced_variables'] -= len(discovery['fixed'])
        trace['previous_reason'] = trace['reason']; trace['reason'] = 'positive-child-model'
        trace['positive_model'] = deepcopy(recovered)
        return recovered, trace
    return choice, trace
