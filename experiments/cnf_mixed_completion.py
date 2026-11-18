"""Lift a mixed two-CNF model from the live conditioned residual.

Uniform completion keeps priority. On its failure, SCC solving is restricted
to binary residuals. A model is checked against the whole raw premise before
native publication. A negative condition is retained as diagnostic evidence;
it never substitutes for a parent refutation. Candidate budgets are unchanged.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_residual_dag import propagate, restrict, holds, two_cnf
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
    record = dict(baseline=None, fixed=[], ranks=[], candidates=[], attempts=[], selected=None, exposed=None, binary_filter=None, completions=[], positive_selected=None)
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
        premise_cnf, premise_names, premise_root = solver._canonical(stronger)
        values, unit_trace, unit_conflict = propagate(premise_cnf, counts)
        remaining = () if unit_conflict is not None else restrict(premise_cnf, values, counts)
        screen = dict(root=premise_root, trace=unit_trace, conflict=unit_conflict,
                      residual_literals=sum(map(len, remaining)))
        counts['local_premise_probes'] += 1
        record['attempts'].append(dict(clause=clause, screen=screen))
        if screen['conflict'] is not None:
            record['selected'] = len(record['attempts']) - 1
            counts['local_guards_found'] += 1
            return dict(kind='guard', clause=list(clause), screen=deepcopy(screen)), record
        counts['inline_completion_checks'] += 1
        counts['inline_completion_clauses'] += len(remaining)
        false_valid = true_valid = binary_residual = True
        counts['mixed_recognition_clauses'] += len(remaining)
        for residual_clause in remaining:
            binary_residual &= len(residual_clause) <= 2
            negative = positive = False
            for literal in residual_clause:
                counts['inline_completion_literal_visits'] += 1
                negative |= literal < 0; positive |= literal > 0
            false_valid &= negative; true_valid &= positive
        detail = dict(index=len(record['attempts'])-1, residual_literals=sum(map(len, remaining)),
                      false_valid=false_valid, true_valid=true_valid)
        record['completions'].append(detail)
        if not false_valid and not true_valid:
            detail['two_cnf'] = binary_residual
            if not binary_residual:
                continue
            counts['mixed_scc_calls'] += 1
            local = Counter()
            residual_model, proof = two_cnf(remaining, local)
            counts['mixed_scc_implication_edges'] += local['implication_edges']
            detail['mixed'] = dict(model=None if residual_model is None else sorted(residual_model.items()),
                                   proof=deepcopy(proof), metrics=dict(local))
            if residual_model is None:
                counts['mixed_negative_conditions'] += 1
                # This branch alone cannot decide the parent. Keep probing.
                continue
            residual_variables = {abs(l) for c in remaining for l in c}
            if (set(residual_model) != residual_variables or set(residual_model) & set(values)
                    or any(type(v) is not int or type(bit) is not bool for v, bit in residual_model.items())):
                raise ValueError('Malformed mixed residual model')
            merged = {**values, **residual_model}
            model = {name: merged.get(i+1, False) for i, name in enumerate(premise_names)}
            model = {name: model.get(name, False) for name in names}
            counts['mixed_model_variables'] += len(model)
            counts['mixed_model_literals'] += sum(map(len, stronger))
            if not holds(stronger, model):
                raise ValueError('Mixed model fails target or assumption')
            counts['mixed_positive_models'] += 1
            record['positive_selected'] = len(record['attempts'])-1
            return dict(kind='positive-model', root=root, model=[[v, bit] for v, bit in model.items()]), record
        fill = not false_valid; detail['fill'] = fill
        model = {name: values.get(i+1, fill) for i, name in enumerate(premise_names)}
        model = {name: model.get(name, False) for name in names}
        counts['inline_completion_model_variables'] += len(model)
        counts['inline_completion_model_literals'] += sum(map(len, stronger))
        # Fresh propagation is only a candidate generator: validate the actual
        # source witness, and let native publication independently check it again.
        if not holds(stronger, model):
            raise ValueError('Inline model fails target or assumption')
        counts['inline_completion_models'] += 1
        record['positive_selected'] = len(record['attempts'])-1
        return dict(kind='positive-model', root=root, model=[[v, bit] for v, bit in model.items()]), record
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
    if choice['kind'] == 'positive-model':
        record['reason'] = ('mixed-positive-model' if 'mixed' in record['discovery']['completions'][-1]
                            else 'inline-positive-model')
        return choice, record
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
    """Retain guarded negative results and prefix fallback after early positive stopping."""
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
