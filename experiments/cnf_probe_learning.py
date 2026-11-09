"""One bounded, checked local-learning round before another probe pass.

Only implications already proved by original-source unit traces may be added.
The pass excludes explicit duplicates and binary-path consequences, including
paths through earlier accepted clauses. Retain a child only when the next old
probe pass reduces support. Failed attempts remain evidence but do not recurse.
"""
from collections import defaultdict

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_equivalence import (
    ProbeEquivalenceInventory, discover_equivalence_probes, check_equivalence_probes)
from experiments.cnf_residual_dag import holds


def learning_batch(cnf, attempts, limit, counts):
    if not limit:
        return []
    graph = defaultdict(set)
    clauses = {tuple(c) for c in cnf}
    counts['learning_graph_literal_visits'] += sum(map(len, cnf))
    for clause in cnf:
        if len(clause) == 2:
            a, b = clause
            graph[-a].add(b); graph[-b].add(a)
    selected = []
    for ai, attempt in enumerate(attempts):
        assumption = attempt['variable'] * (1 if attempt['value'] else -1)
        for ui, (lit, _) in enumerate(attempt['certificate']['units']):
            counts['learning_candidate_visits'] += 1
            clause = tuple(sorted((-assumption, lit)))
            if clause in clauses:
                counts['learning_explicit_duplicates'] += 1
                continue
            seen, stack = set(), [assumption]
            while stack:
                v = stack.pop()
                if v in seen:
                    continue
                seen.add(v); counts['learning_reachability_vertices'] += 1
                counts['learning_reachability_edges'] += len(graph[v])
                stack.extend(graph[v] - seen)
            if lit in seen:
                counts['learning_binary_redundant'] += 1
                continue
            selected.append(dict(attempt=ai, unit=ui, clause=list(clause)))
            clauses.add(clause)
            a, b = clause
            graph[-a].add(b); graph[-b].add(a)
            if len(selected) == limit:
                return selected
    return selected


def augment(cnf, batch):
    # Preserve clause order so that continuation reasons have stable indices.
    return tuple(tuple(c) for c in cnf) + tuple(tuple(b['clause']) for b in batch)


def discover_learning_probes(cnf, probe_limit, learn_limit, counts):
    original = discover_equivalence_probes(cnf, probe_limit, counts)
    if original['status'] != 'clear':
        return original
    batch = learning_batch(cnf, original['attempts'], learn_limit, counts)
    if not batch:
        return original
    before = counts['probe_attempts']
    continuation = discover_equivalence_probes(augment(cnf, batch), probe_limit, counts)
    counts['learning_continuation_probe_attempts'] += counts['probe_attempts'] - before
    success = continuation['status'] != 'clear'
    counts['learning_successes' if success else 'learning_inconclusive'] += 1
    counts['learning_clauses_proposed'] += len(batch)
    return dict(status='learned' if success else 'learning_clear', attempts=original['attempts'],
                batch=batch, continuation=continuation)


def check_learning_probes(cnf, result, probe_limit, learn_limit, counts):
    if result.get('status') not in ('learned', 'learning_clear'):
        target, fixed = check_equivalence_probes(cnf, result, probe_limit, counts)
        if result['status'] == 'clear' and learning_batch(cnf, result['attempts'], learn_limit, counts):
            raise ValueError('Omitted local-learning attempt')
        return target, fixed
    if set(result) != {'status', 'attempts', 'batch', 'continuation'}:
        raise ValueError('Invalid local-learning fields')
    # Check all implications on the original source BEFORE trusting additions.
    # This disallows circular proofs using the newly learned clauses themselves.
    check_equivalence_probes(cnf, dict(status='clear', attempts=result['attempts']), probe_limit, counts)
    expected = learning_batch(cnf, result['attempts'], learn_limit, counts)
    if not expected or encode(result['batch']) != encode(expected):
        raise ValueError('Invalid learning batch or source reason')
    target, fixed = check_equivalence_probes(augment(cnf, expected), result['continuation'], probe_limit, counts)
    success = result['continuation']['status'] != 'clear'
    if (result['status'] == 'learned') != success:
        raise ValueError('Invalid learning outcome')
    counts['verified_learning_attempts'] += 1
    if not success:
        return cnf, {}
    if not {abs(l) for c in target for l in c} < {abs(l) for c in cnf for l in c}:
        raise ValueError('Learned continuation must strictly reduce support')
    return target, fixed


class ProbeLearningInventory(ProbeEquivalenceInventory):
    def __init__(self, *args, learn_limit=4, **kwargs):
        if type(learn_limit) is not int or not 0 <= learn_limit <= 16:
            raise ValueError('learn_limit must be an integer between 0 and 16')
        super().__init__(*args, **kwargs)
        self.config.update(probe_learning='one-batch-binary-path-filter-v1', learn_limit=learn_limit)

    def _discover_probes(self, cnf):
        return discover_learning_probes(cnf, self.config['probe_limit'], self.config['learn_limit'], self.counts)

    def _check_probes(self, cnf, result):
        return check_learning_probes(cnf, result, self.config['probe_limit'], self.config['learn_limit'], self.counts)

    @staticmethod
    def _uses_probe(profile):
        return profile['probing']['status'] in ('forced', 'common', 'equivalence', 'learned')

    def lift(self, key, child_model):
        node = self._load(key); result = node['profile']['probing']
        if (node['kind'] != 'probe' or result['status'] != 'learned' or
                result['continuation']['status'] != 'equivalence'):
            return super().lift(key, child_model)
        edge = node['edge']; child = self._load(edge['key'])
        if (any(i not in child_model or type(child_model[i]) is not bool
                for i in range(1, len(edge['names'])+1)) or not holds(child['cnf'], child_model)):
            raise ValueError('Invalid learned-equivalence child model')
        self._check_probes(node['cnf'], result)
        model = {abs(lit): False for c in node['cnf'] for lit in c}
        model.update((v, child_model[i]) for i, v in enumerate(edge['names'], 1))
        for variable, signed_rep in result['continuation']['witness']['mapping']:
            model[variable] = model[abs(signed_rep)] if signed_rep > 0 else not model[abs(signed_rep)]
        if not holds(node['cnf'], model):
            raise ValueError('Lift violates learned source')
        return model
