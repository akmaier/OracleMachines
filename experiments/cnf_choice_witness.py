"""Checked SAT proposals from signed choices and conservative resource groups.

A matching is only a proposal. Every original clause must accept the complete
assignment. Failed matching, failed recognition and rejected models prove nothing.
The pre-existing capacity/expansion portfolio remains the fallback.
"""
from collections import Counter
from experiments import cnf_capacity_core as capacity
from experiments import cnf_residual_dag as native

FORMAT = 'cnf-choice-witness-v1'
MATCHING_ALLOWANCE = 300000


def check(source, proof, counts=None):
    counts = Counter() if counts is None else counts
    capacity.canonical(source, counts)  # Validate raw input, including tautologies.
    names = sorted({abs(v) for clause in source for v in clause})
    if (type(proof) is not dict or set(proof) != {'format', 'names', 'values'}
            or proof['format'] != FORMAT or type(proof['names']) is not list
            or any(type(v) is not int for v in proof['names']) or proof['names'] != names
            or type(proof['values']) is not list or len(proof['values']) != len(names)
            or any(type(v) is not bool for v in proof['values'])):
        raise ValueError('Invalid complete choice witness')
    model = dict(zip(names, proof['values']))
    for clause in source:
        counts['witness_clause_checks'] += 1
        counts['witness_literal_charge'] += len(clause)
        if not any(model[abs(v)] == (v > 0) for v in clause):
            raise ValueError('Choice witness violates original source')
    return dict(answer=True, model=model)


def discover(source, counts=None, *, matching_allowance=MATCHING_ALLOWANCE):
    """Try wide-first, then all-clause disjoint-variable demands.

    Connected conflict components are conservative capacity-one groups even when
    not cliques. This may miss models but cannot authorize a false SAT answer.
    D*E reserves an upper bound on the unchanged matching helper's edge visits.
    Source scans, grouping, sorting, copying and full witness checks are extra.
    """
    counts = Counter() if counts is None else counts
    if type(matching_allowance) is not int or matching_allowance < 0:
        raise ValueError('Invalid matching allowance')
    clauses = capacity.canonical(source, counts)
    names = sorted({abs(v) for clause in source for v in clause})
    attempts = []; remaining = matching_allowance
    if () in clauses:
        return None, dict(reason='empty-clause', attempts=[], reserved=0)
    for minimum_width in (3, 1):
        demands = []; used_variables = set(); choices = set()
        for clause in sorted(clauses, key=lambda c: (-len(c), c)):
            counts['choice_selection_literal_charge'] += len(clause)
            variables = {abs(v) for v in clause}
            if len(clause) >= minimum_width and not used_variables.intersection(variables):
                demands.append(clause); choices.update(clause); used_variables.update(variables)
        graph = {v: set() for v in choices}; demand_set = set(demands); uncovered = []
        for clause in clauses:
            counts['choice_classification_clause_visits'] += 1
            if clause in demand_set:
                continue
            if len(clause) == 2 and all(-v in choices for v in clause):
                a, b = (-v for v in clause); graph[a].add(b); graph[b].add(a)
            else:
                uncovered.append(clause)
        groups = []; owner = {}
        for start in sorted(choices):
            if start in owner:
                continue
            index = len(groups); owner[start] = index; group = []; pending = [start]
            while pending:
                v = pending.pop(); group.append(v)
                counts['choice_component_edge_visits'] += len(graph[v])
                for w in sorted(graph[v]):
                    if w not in owner:
                        owner[w] = index; pending.append(w)
            groups.append(sorted(group))
        cliques = all(len(graph[v]) == len(group)-1 for group in groups for v in group)
        domains = {}
        for i, clause in enumerate(demands):
            domains[i] = {}
            for v in clause:
                domains[i].setdefault(owner[v], v)
        edge_bound = len(domains) * sum(len(d) for d in domains.values())
        diagnostic = dict(minimum_width=minimum_width, demands=len(demands),
                          groups=len(groups), choice_variables=len(used_variables),
                          unclassified_clauses=len(uncovered), clique_components=cliques,
                          strict_choice_class=not uncovered and cliques,
                          matching_bound=edge_bound)
        attempts.append(diagnostic)
        if edge_bound > remaining:
            diagnostic['reason'] = 'matching-admission'; continue
        remaining -= edge_bound; counts['choice_reserved_matching_visits'] += edge_bound
        before = counts['matching_domain_edge_visits']
        selected, obstruction = native.solve_matching(domains, counts)
        assert counts['matching_domain_edge_visits'] - before <= edge_bound
        if obstruction is not None:
            diagnostic['reason'] = 'no-conservative-matching'; continue
        model = {v: False for v in names}
        for v in choices:
            model[abs(v)] = v < 0  # Unselected signed choice is false.
        for v in selected:
            model[abs(v)] = v > 0
        proof = dict(format=FORMAT, names=names, values=[model[v] for v in names])
        try:
            check(source, proof, counts)
        except ValueError:
            diagnostic['reason'] = 'source-rejects-model'; continue
        diagnostic['reason'] = 'checked-model'
        return proof, dict(reason='sat', attempts=attempts,
                           reserved=matching_allowance-remaining)
    return None, dict(reason='no-checked-model', attempts=attempts,
                      reserved=matching_allowance-remaining)


def pipeline(source, counts=None, *, enabled=True):
    counts = Counter() if counts is None else counts
    if type(enabled) is not bool:
        raise ValueError('Invalid choice policy')
    diagnostic = None
    if enabled:
        proof, diagnostic = discover(source, counts)
        if proof is not None:
            return dict(kind='choice', proof=proof), dict(choice=diagnostic)
    proof, prior = capacity.pipeline(source, counts)
    return dict(kind='previous', proof=proof), dict(choice=diagnostic, previous=prior)


def check_pipeline(source, proof, counts=None):
    if type(proof) is not dict or set(proof) != {'kind', 'proof'}:
        raise ValueError('Invalid choice pipeline certificate')
    if proof['kind'] == 'choice':
        return check(source, proof['proof'], counts)
    if proof['kind'] == 'previous':
        return capacity.check_pipeline(source, proof['proof'], counts)
    raise ValueError('Invalid choice certificate kind')
