"""Checked signed choices with at most two conditioned demand vertices.

After removing the supplied cutset the demand-interaction graph must be a
forest. Tables describe exact single-representative feasibility, not all Boolean
models. Unknown prefixes never authorize UNSAT. Recognition is incomplete.
"""
from collections import Counter
from itertools import combinations, islice, product
from experiments import cnf_choice_witness as prior

FORMAT = 'cnf-choice-forest-v1'
MAX_CUTSET = 2
RECOGNITION_LIMIT = 4096
PAIR_LIMIT = 50000


class Limit(Exception):
    pass


def layout(source, demands, counts):
    clauses = prior.capacity.canonical(source, counts)
    if type(demands) is not list:
        raise ValueError('Invalid demands')
    owner = {}; variables = set(); domains = []
    for i, row in enumerate(demands):
        if (type(row) is not list or not row or any(type(v) is not int or v == 0 for v in row)
                or tuple(row) not in clauses or len({abs(v) for v in row}) != len(row)
                or any(abs(v) in variables for v in row)):
            raise ValueError('Demands must be disjoint-variable source clauses')
        domains.append(tuple(row)); variables.update(abs(v) for v in row)
        owner.update((v, i) for v in row)
    demand_set = set(domains); graph = {i: set() for i in range(len(domains))}; conflicts = set()
    for clause in clauses:
        counts['forest_classification_clause_visits'] += 1
        if clause in demand_set:
            continue
        if len(clause) != 2 or any(-v not in owner for v in clause):
            raise ValueError('Unclassified source clause')
        a, b = (-v for v in clause); conflicts.add(tuple(sorted((a, b))))
        if owner[a] != owner[b]:
            graph[owner[a]].add(owner[b]); graph[owner[b]].add(owner[a])
    return domains, graph, conflicts


def forest(graph, cutset, counts):
    removed = set(cutset); parent = {}; order = []
    for root in sorted(graph):
        if root in removed or root in parent:
            continue
        parent[root] = None; pending = [root]
        while pending:
            node = pending.pop(); order.append(node)
            for other in sorted(graph[node]):
                counts['forest_graph_edge_visits'] += 1
                if other in removed or other == parent[node]:
                    continue
                if other in parent:
                    return None
                parent[other] = node; pending.append(other)
    return parent, order


def choose_cutset(graph, counts, limit, cap):
    attempts = 0
    for size in range(limit + 1):
        for cut in combinations(sorted(graph), size):
            if attempts == cap:
                return None, attempts, 'recognition-limit'
            attempts += 1
            tree = forest(graph, cut, counts)
            if tree is not None:
                return list(cut), attempts, 'forest'
    return None, attempts, 'no-cutset-at-allowed-size'


def compatible(a, b, conflicts, counts, remaining=None):
    if remaining is not None:
        if remaining[0] == 0:
            raise Limit()
        remaining[0] -= 1
    counts['forest_compatibility_tests'] += 1
    return tuple(sorted((a, b))) not in conflicts


def branch_data(domains, cutset, values, conflicts, counts, remaining=None):
    if any(not compatible(a, b, conflicts, counts, remaining) for a, b in combinations(values, 2)):
        return None
    return {i: [v for v in domain if all(compatible(v, chosen, conflicts, counts, remaining) for chosen in values)]
            for i, domain in enumerate(domains) if i not in cutset}


def children_of(parent):
    children = {i: [] for i in parent}
    for i, p in parent.items():
        if p is not None: children[p].append(i)
    return children


def tables(domains, cutset, values, conflicts, tree, counts, remaining):
    allowed = branch_data(domains, cutset, values, conflicts, counts, remaining)
    if allowed is None: return None
    parent, order = tree; children = children_of(parent); live = [[] for _ in domains]
    for node in reversed(order):
        for value in allowed[node]:
            if all(any(compatible(value, child_value, conflicts, counts, remaining) for child_value in live[child])
                   for child in children[node]):
                live[node].append(value)
    return live


def check(source, proof, counts=None):
    counts = Counter() if counts is None else counts
    clauses = prior.capacity.canonical(source, counts)
    if (type(proof) is not dict or set(proof) != {'format', 'empty', 'demands', 'cutset', 'branches'}
            or proof['format'] != FORMAT or type(proof['empty']) is not bool):
        raise ValueError('Invalid forest certificate')
    if proof['empty']:
        if () not in clauses or any(proof[k] != [] for k in ('demands', 'cutset', 'branches')):
            raise ValueError('Missing source empty clause')
        return dict(answer=False, model=None)
    domains, graph, conflicts = layout(source, proof['demands'], counts)
    cutset = proof['cutset']; branches = proof['branches']
    if (type(cutset) is not list or any(type(i) is not int or not 0 <= i < len(domains) for i in cutset)
            or cutset != sorted(set(cutset)) or len(cutset) > MAX_CUTSET or type(branches) is not list):
        raise ValueError('Invalid cutset or branches')
    tree = forest(graph, cutset, counts)
    if tree is None: raise ValueError('Residual demand graph contains a cycle')
    parent, order = tree; children = children_of(parent)
    roots = [node for node in order if parent[node] is None]
    total = 1
    for node in cutset: total *= len(domains[node])
    if len(branches) > total: raise ValueError('Too many branches')
    model = None
    for values, live in zip(islice(product(*(domains[i] for i in cutset)), len(branches)), branches):
        allowed = branch_data(domains, cutset, values, conflicts, counts)
        if allowed is None:
            if live is not None: raise ValueError('Conflicting cutset assignment needs a conflict row')
            continue
        if (type(live) is not list or len(live) != len(domains)
                or any(type(row) is not list or any(type(v) is not int for v in row) for row in live)
                or any(live[i] != [] for i in cutset)):
            raise ValueError('Invalid live tables')
        # Local equations use supplied child tables; acyclicity makes their
        # exact solution unique. Check both live and dead domain values.
        for node in order:
            expected = [value for value in allowed[node]
                        if all(any(compatible(value, other, conflicts, counts) for other in live[child])
                               for child in children[node])]
            if live[node] != expected: raise ValueError('Inexact live table')
        if model is None and all(live[node] for node in roots):
            selected = dict(zip(cutset, values))
            for node in order:
                p = parent[node]
                selected[node] = next(v for v in live[node] if p is None or compatible(v, selected[p], conflicts, counts))
            names = sorted({abs(v) for c in source for v in c}); assignment = {v: False for v in names}
            for domain in domains:
                for v in domain: assignment[abs(v)] = v < 0
            for v in selected.values(): assignment[abs(v)] = v > 0
            witness = dict(format=prior.FORMAT, names=names, values=[assignment[v] for v in names])
            model = prior.check(source, witness, counts)['model']
    if model is not None: return dict(answer=True, model=model)
    return dict(answer=False if len(branches) == total else None, model=None)


def discover(source, counts=None, *, cutset_limit=MAX_CUTSET,
             recognition_limit=RECOGNITION_LIMIT, pair_limit=PAIR_LIMIT):
    counts = Counter() if counts is None else counts
    for name, value in [('cutset', cutset_limit), ('recognition', recognition_limit), ('pair', pair_limit)]:
        if type(value) is not int or value < 0: raise ValueError('Invalid ' + name + ' limit')
    if cutset_limit > MAX_CUTSET: raise ValueError('Unsupported cutset size')
    clauses = prior.capacity.canonical(source, counts)
    if () in clauses:
        proof = dict(format=FORMAT, empty=True, demands=[], cutset=[], branches=[])
        return proof, dict(reason='empty-clause', attempts=[])
    attempts = []; remaining_recognition = recognition_limit
    for width in (3, 1):
        demands = []; used = set()
        for clause in sorted(clauses, key=lambda c: (-len(c), c)):
            counts['forest_selection_literal_charge'] += len(clause)
            names = {abs(v) for v in clause}
            if len(clause) >= width and not used.intersection(names):
                demands.append(list(clause)); used.update(names)
        attempt = dict(minimum_width=width, demands=len(demands)); attempts.append(attempt)
        try: domains, graph, conflicts = layout(source, demands, counts)
        except ValueError:
            attempt['reason'] = 'unclassified-clauses'; continue
        cutset, tested, reason = choose_cutset(graph, counts, cutset_limit, remaining_recognition)
        remaining_recognition -= tested
        attempt.update(reason=reason, tested_cutsets=tested, edges=sum(map(len, graph.values())) // 2)
        if cutset is None: continue
        tree = forest(graph, cutset, counts); remaining = [pair_limit]
        proof = dict(format=FORMAT, empty=False, demands=demands, cutset=cutset, branches=[])
        for values in product(*(domains[i] for i in cutset)):
            try: live = tables(domains, cutset, values, conflicts, tree, counts, remaining)
            except Limit:
                attempt['reason'] = 'pair-limit'; break
            proof['branches'].append(live)
        result = check(source, proof, counts)
        attempt.update(cutset=cutset, completed_branches=len(proof['branches']),
                       charged_pair_tests=pair_limit - remaining[0])
        return proof, dict(reason='sat' if result['answer'] is True else 'unsat' if result['answer'] is False else 'incomplete', attempts=attempts)
    return None, dict(reason='unrecognized', attempts=attempts)
