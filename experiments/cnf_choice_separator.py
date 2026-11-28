"""Exact elimination messages for signed choices, including cyclic groups.

Each message is the complete relation on a checked separator. Discovery is
bounded and incomplete; an empty checked message proves UNSAT, while a positive
verdict needs all messages and a raw-source model. Width remains explicit.
"""
from collections import Counter
from itertools import combinations, product
from math import prod
from experiments import cnf_choice_forest as prior

FORMAT = 'cnf-choice-separator-v1'
STATE_LIMIT = 200000
BAG_LIMIT = 65536
ORDER_LIMIT = 1000000


def min_fill(graph, counts, limit):
    graph = {v: set(neighbors) for v, neighbors in graph.items()}
    order = []; tested = 0
    while graph:
        scores = []
        for v in sorted(graph):
            missing = 0
            for a, b in combinations(sorted(graph[v]), 2):
                if tested == limit: return None
                tested += 1; counts['separator_order_pair_tests'] += 1
                missing += b not in graph[a]
            scores.append((missing, len(graph[v]), v))
        v = min(scores)[2]; neighbors = sorted(graph[v]); order.append(v)
        for a, b in combinations(neighbors, 2): graph[a].add(b); graph[b].add(a)
        for a in neighbors: graph[a].remove(v)
        del graph[v]
    return order


def plan(graph, order, counts):
    if (type(order) is not list or any(type(v) is not int for v in order)
            or sorted(order) != sorted(graph)):
        raise ValueError('Order must be a permutation of all demands')
    rank = {v: i for i, v in enumerate(order)}
    graph = {v: set(neighbors) for v, neighbors in graph.items()}
    separators = []; children = [[] for _ in order]
    for i, v in enumerate(order):
        sep = sorted(graph[v], key=rank.__getitem__); separators.append(sep)
        if sep: children[rank[sep[0]]].append(i)
        for a, b in combinations(sep, 2):
            counts['separator_plan_pair_visits'] += 1
            graph[a].add(b); graph[b].add(a)
        for a in sep: graph[a].remove(v)
        del graph[v]
    # The elimination construction proves edge coverage and running
    # intersection. Check the message scope containment explicitly as well.
    for i, v in enumerate(order):
        bag = {v, *separators[i]}
        if any(not set(separators[c]) <= bag for c in children[i]):
            raise ValueError('Child separator escapes parent bag')
    return separators, children


def local_ok(v, value, assignment, sep, children, separators, relations, conflicts, counts):
    counts['separator_candidate_assignments'] += 1
    if any(not prior.compatible(value, assignment[w], conflicts, counts) for w in sep): return False
    assignment[v] = value
    for child in children:
        counts['separator_message_lookups'] += 1
        if tuple(assignment[w] for w in separators[child]) not in relations[child]: return False
    return True


def make_table(i, domains, order, separators, children, relations, conflicts, counts):
    v = order[i]; sep = separators[i]; rows = []
    for values in product(*(domains[w] for w in sep)):
        assignment = dict(zip(sep, values))
        if any(local_ok(v, value, assignment, sep, children[i], separators, relations, conflicts, counts)
               for value in domains[v]): rows.append(list(values))
    return rows


def check(source, proof, counts=None):
    counts = Counter() if counts is None else counts
    clauses = prior.prior.capacity.canonical(source, counts)
    if (type(proof) is not dict or set(proof) != {'format','empty','demands','order','tables'}
            or proof['format'] != FORMAT or type(proof['empty']) is not bool):
        raise ValueError('Invalid separator certificate')
    if proof['empty']:
        if () not in clauses or any(proof[k] != [] for k in ('demands','order','tables')):
            raise ValueError('Missing source empty clause')
        return dict(answer=False, model=None)
    domains, graph, conflicts = prior.layout(source, proof['demands'], counts)
    order = proof['order']; separators, children = plan(graph, order, counts)
    tables = proof['tables']
    if type(tables) is not list or len(tables) > len(order): raise ValueError('Invalid table prefix')
    relations = []; empty = False
    for i, rows in enumerate(tables):
        if (type(rows) is not list or any(type(row) is not list or any(type(v) is not int for v in row) for row in rows)):
            raise ValueError('Invalid relation rows')
        # Unlike the constructor, verification checks every separator tuple
        # against a supplied relation, including its omitted/dead tuples.
        relation = {tuple(row) for row in rows}; expected_order = []
        v = order[i]; sep = separators[i]
        for values in product(*(domains[w] for w in sep)):
            assignment = dict(zip(sep, values))
            feasible = any(local_ok(v, value, assignment, sep, children[i], separators, relations, conflicts, counts)
                           for value in domains[v])
            if feasible != (values in relation): raise ValueError('Inexact separator relation')
            if feasible: expected_order.append(list(values))
        if rows != expected_order: raise ValueError('Noncanonical or foreign relation rows')
        relations.append(relation); empty |= not rows
    if empty: return dict(answer=False, model=None)
    if len(tables) != len(order): return dict(answer=None, model=None)
    selected = {}
    for i in reversed(range(len(order))):
        v = order[i]; sep = separators[i]
        selected[v] = next(value for value in domains[v]
                          if local_ok(v, value, selected, sep, children[i], separators, relations, conflicts, counts))
    names = sorted({abs(v) for c in source for v in c}); model = {v:False for v in names}
    for domain in domains:
        for v in domain: model[abs(v)] = v < 0
    for v in selected.values(): model[abs(v)] = v > 0
    witness = dict(format=prior.prior.FORMAT, names=names, values=[model[v] for v in names])
    return prior.prior.check(source, witness, counts)


def discover(source, counts=None, *, state_limit=STATE_LIMIT, bag_limit=BAG_LIMIT, order_limit=ORDER_LIMIT):
    counts = Counter() if counts is None else counts
    for value in (state_limit, bag_limit, order_limit):
        if type(value) is not int or value < 0: raise ValueError('Invalid limit')
    clauses = prior.prior.capacity.canonical(source, counts)
    if () in clauses:
        return dict(format=FORMAT,empty=True,demands=[],order=[],tables=[]), dict(reason='empty-clause',attempts=[])
    attempts = []; order_start = counts['separator_order_pair_tests']
    for width in (3, 1):
        demands = []; used = set()
        for clause in sorted(clauses, key=lambda c:(-len(c),c)):
            counts['separator_selection_literal_charge'] += len(clause)
            names = {abs(v) for v in clause}
            if len(clause) >= width and not used.intersection(names): demands.append(list(clause)); used.update(names)
        attempt = dict(minimum_width=width, demands=len(demands)); attempts.append(attempt)
        try: domains, graph, conflicts = prior.layout(source, demands, counts)
        except ValueError:
            attempt['reason'] = 'unclassified-clauses'; continue
        order = min_fill(graph, counts, order_limit - (counts['separator_order_pair_tests'] - order_start))
        if order is None:
            attempt['reason'] = 'order-limit'; break
        separators, children = plan(graph, order, counts)
        states = [len(domains[v])*prod(len(domains[w]) for w in separators[i]) for i,v in enumerate(order)]
        proof = dict(format=FORMAT,empty=False,demands=demands,order=order,tables=[])
        relations = []; reserved = 0; reason = 'complete'
        for i, charge in enumerate(states):
            if charge > bag_limit or reserved + charge > state_limit:
                reason = 'bag-limit' if charge > bag_limit else 'state-limit'; break
            reserved += charge; counts['separator_reserved_states'] += charge
            rows = make_table(i, domains, order, separators, children, relations, conflicts, counts)
            proof['tables'].append(rows); relations.append({tuple(row) for row in rows})
            if not rows: reason = 'empty-message'; break
        result = check(source, proof, counts)
        attempt.update(reason=reason,edges=sum(map(len,graph.values()))//2,
            maximum_separator_size=max(map(len,separators),default=0),
            maximum_bag_states=max(states,default=0),full_plan_states=sum(states),reserved_states=reserved,
            completed_messages=len(proof['tables']),retained_rows=sum(map(len,proof['tables'])))
        return proof,dict(reason='sat' if result['answer'] is True else 'unsat' if result['answer'] is False else 'incomplete',attempts=attempts)
    return None,dict(reason='unrecognized',attempts=attempts)
