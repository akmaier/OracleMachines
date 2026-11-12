"""Optional fixed additive clause growth after earlier elimination rules fail.

Every accepted step is exact existential projection with strictly smaller
support. With initial m clauses and n variables and fixed allowance d, one
elimination-only chain has at most n steps and at most m+d*n clauses per state.
No useful-pivot availability or whole-planner bound follows.
"""
from collections import defaultdict
from experiments.cnf_variable_elimination import _limit, _source
from experiments.cnf_clause_bound_elimination import ClauseBoundEliminationInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds


def discover_additive_elimination(cnf, counts, *, pair_limit=64, candidate_limit=64, clause_growth_limit=1):
    """Select one additive-clause-bounded projection; null means no selected witness only."""
    _limit(pair_limit); _limit(candidate_limit); _limit(clause_growth_limit)
    clauses = _source(cnf, counts)
    positions = defaultdict(list)
    for cid, clause in enumerate(clauses):
        for lit in clause:
            positions[lit].append(cid)
            counts['additive_elimination_index_literals'] += 1
    variables = {abs(lit) for lit in positions}
    choices = sorted(variables, key=lambda v: (len(positions[v]) * len(positions[-v]), v))
    counts['additive_elimination_candidate_variables'] += len(choices)
    if len(choices) > candidate_limit:
        counts['additive_elimination_candidate_budget_skips'] += len(choices) - candidate_limit
    original = set(clauses); best = None
    for variable in choices[:candidate_limit]:
        positive, negative = positions[variable], positions[-variable]
        pairs = len(positive) * len(negative)
        if pairs > pair_limit:
            counts['additive_elimination_pair_budget_skips'] += 1
            continue
        removed = positive + negative
        old_literals = sum(len(clauses[cid]) for cid in removed)
        added = set(); added_literals = 0; growing = False
        counts['additive_elimination_candidates_tested'] += 1
        for a in positive:
            for b in negative:
                counts['additive_elimination_discovery_pairs'] += 1
                counts['additive_elimination_discovery_pair_literals'] += len(clauses[a]) + len(clauses[b])
                result = (clauses[a] - {variable}) | (clauses[b] - {-variable})
                if any(-lit in result for lit in result):
                    counts['additive_elimination_tautological_pairs'] += 1
                    continue
                if result in original or result in added:
                    counts['additive_elimination_duplicate_resolvents'] += 1
                    continue
                added.add(result); added_literals += len(result)
                if len(added) > len(removed) + clause_growth_limit:
                    growing = True
                    break
            if growing:
                break
        if growing:
            counts['additive_elimination_growth_rejections'] += 1
            continue
        # Prefer the least clause growth so the budget-two local choice agrees
        # with budget one whenever the latter has an eligible candidate.
        score = (len(added) - len(removed), added_literals - old_literals, pairs, variable)
        if best is None or score < best:
            best = score
    counts['additive_elimination_discoveries'] += 1
    return dict(variable=None if best is None else best[-1])


def check_additive_elimination(cnf, certificate, counts, *, pair_limit=64, clause_growth_limit=1):
    """Recompute all resolvents from the actual source, without discovery state."""
    _limit(pair_limit); _limit(clause_growth_limit)
    _source(cnf, counts)
    if type(certificate) is not dict or set(certificate) != {'variable'}:
        raise ValueError('Invalid elimination certificate fields')
    variable = certificate['variable']
    if variable is None:
        # No selected witness is not a proof that no bounded elimination exists.
        return None
    if type(variable) is not int or variable <= 0:
        raise ValueError('Invalid elimination variable')
    positive, negative, retained = [], [], set()
    for clause in cnf:
        counts['additive_elimination_check_source_literals'] += len(clause)
        if variable in clause:
            positive.append(tuple(lit for lit in clause if lit != variable))
        elif -variable in clause:
            negative.append(tuple(lit for lit in clause if lit != -variable))
        else:
            retained.add(tuple(sorted(clause)))
    if not positive and not negative:
        raise ValueError('Eliminated variable absent from source')
    if len(positive) * len(negative) > pair_limit:
        raise ValueError('Elimination exceeds pair limit')
    for a in positive:
        for b in negative:
            counts['additive_elimination_checked_pairs'] += 1
            counts['additive_elimination_checked_pair_literals'] += len(a) + len(b)
            result = set(a); result.update(b)
            if not any(-lit in result for lit in result):
                retained.add(tuple(sorted(result)))
    target = tuple(sorted(retained))
    if len(target) > len(cnf) + clause_growth_limit:
        raise ValueError('Elimination exceeds additive clause budget')
    source_variables = {abs(l) for c in cnf for l in c}
    target_variables = {abs(l) for c in target for l in c}
    if not target_variables < source_variables or variable in target_variables:
        raise ValueError('Elimination must strictly reduce variable support')
    counts['additive_elimination_positive_clause_growth'] += max(0, len(target)-len(cnf))
    counts['additive_elimination_positive_literal_growth'] += max(0, sum(map(len, target))-sum(map(len, cnf)))
    counts['additive_elimination_checked_steps'] += 1
    counts['additive_elimination_checked_pure_steps' if not positive or not negative else 'additive_elimination_checked_mixed_steps'] += 1
    return target


def lift_additive_elimination(cnf, certificate, child_model, counts, *, pair_limit=64, clause_growth_limit=1):
    target = check_additive_elimination(cnf, certificate, counts, pair_limit=pair_limit, clause_growth_limit=clause_growth_limit)
    if target is None:
        raise ValueError('No elimination to lift')
    support = {abs(lit) for clause in target for lit in clause}
    if (type(child_model) is not dict or
            any(type(v) is not int or v <= 0 or type(b) is not bool for v, b in child_model.items()) or
            any(v not in child_model or type(child_model[v]) is not bool for v in support) or
            not holds(target, child_model)):
        raise ValueError('Invalid elimination child model')
    variable = certificate['variable']
    model = {abs(lit): False for clause in cnf for lit in clause}
    model.update((v, child_model[v]) for v in support)
    # Any unsatisfied positive tail forces x=true. Opposing unsatisfied tails
    # would falsify their resolvent, contradicting the checked target model.
    model[variable] = any(variable in clause and
                          not any(model[abs(lit)] == (lit > 0) for lit in clause if lit != variable)
                          for clause in cnf)
    counts['additive_elimination_lift_source_literals'] += sum(map(len, cnf))
    if not holds(cnf, model):
        raise ValueError('Elimination lift violates source')
    return model


class AdditiveEliminationInventory(ClauseBoundEliminationInventory):
    def __init__(self, *args, clause_growth_limit=1, **kwargs):
        _limit(clause_growth_limit)
        super().__init__(*args, **kwargs)
        self.config['terminal_additive_elimination'] = 'complete-pairs-additive-clause-fallback-v1'
        self.config['clause_growth_limit'] = clause_growth_limit

    def _discover_profile(self, cnf, depth, profile, groups):
        node = super()._discover_profile(cnf, depth, profile, groups)
        if node['kind'] != 'unresolved': return node
        proof = discover_additive_elimination(cnf, self.counts, pair_limit=self.config['elimination_pair_limit'],
                                   candidate_limit=self.config['elimination_candidate_limit'],
                                   clause_growth_limit=self.config['clause_growth_limit'])
        target = check_additive_elimination(cnf, proof, self.counts, pair_limit=self.config['elimination_pair_limit'],
                               clause_growth_limit=self.config['clause_growth_limit'])
        node['additive_elimination'] = proof
        if target is not None:
            edge = self._edge(target, depth)
            node.update(kind='eliminate', edge=edge, summary=self._summary([edge]))
            self.counts['additive_elimination_rewrites'] += 1
        return node

    def _check_profile(self, key, node, cnf, profile, groups):
        if 'additive_elimination' not in node:
            if node.get('kind') == 'unresolved': raise ValueError('Missing additive-clause fallback proposal')
            return super()._check_profile(key, node, cnf, profile, groups)
        old = {k: v for k, v in node.items() if k not in ('additive_elimination', 'edge')}
        old.update(kind='unresolved', summary=dict(closed=False, unresolved_leaves=1,
                                                  unresolved_literals=profile['shape']['literals']))
        super()._check_profile(key, old, cnf, profile, groups)
        target = check_additive_elimination(cnf, node['additive_elimination'], self.counts,
                               pair_limit=self.config['elimination_pair_limit'],
                               clause_growth_limit=self.config['clause_growth_limit'])
        if target is None:
            if node['kind'] != 'unresolved' or set(node) != set(old) | {'additive_elimination'}:
                raise ValueError('Null additive-clause proposal must remain unresolved')
            summary = old['summary']
        else:
            if self.config['elimination_candidate_limit'] == 0: raise ValueError('Elimination disabled')
            if node['kind'] != 'eliminate' or set(node) != set(old) | {'additive_elimination', 'edge'}:
                raise ValueError('Invalid additive-clause elimination edge')
            self._check_edge(node['edge'], target, node['depth'])
            summary = self._summary([node['edge']])
        if encode(node['summary']) != encode(summary): raise ValueError('Invalid additive-clause summary')

    def lift(self, key, child_model):
        node = self._load(key)
        if node['kind'] != 'eliminate' or 'additive_elimination' not in node:
            return super().lift(key, child_model)
        names = node['edge']['names']
        if type(child_model) is not dict or any(type(child_model.get(i)) is not bool for i in range(1, len(names)+1)):
            raise ValueError('Invalid canonical additive-clause model')
        model = {v: child_model[i] for i, v in enumerate(names, 1)}
        return lift_additive_elimination(node['cnf'], node['additive_elimination'], model, self.counts,
                             pair_limit=self.config['elimination_pair_limit'],
                               clause_growth_limit=self.config['clause_growth_limit'])
