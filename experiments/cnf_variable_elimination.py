"""Checked bounded Davis-Putnam elimination at unresolved structural leaves.

This established preprocessing rule preserves existential projection, not the
same models over all original variables. The checker enumerates every opposing
clause pair independently; model lifting restores the eliminated variable.
No polynomial closure of arbitrary SAT or Lean refinement is claimed.
"""
from collections import defaultdict

from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds


def _limit(value):
    if type(value) is not int or value < 0:
        raise ValueError('Elimination limits must be nonnegative integers')


def _source(cnf, counts):
    clauses = []
    for clause in cnf:
        if any(type(lit) is not int or not lit for lit in clause):
            raise ValueError('Invalid elimination source literal')
        items = frozenset(clause)
        if len(items) != len(clause) or any(-lit in items for lit in items):
            raise ValueError('Elimination requires normalized clauses')
        clauses.append(items)
        counts['elimination_validation_literals'] += len(clause)
    if len(set(clauses)) != len(clauses):
        raise ValueError('Elimination requires distinct clauses')
    return clauses


def discover_elimination(cnf, counts, *, pair_limit=64, candidate_limit=64):
    """Select one non-growing projection; null means no selected witness only."""
    _limit(pair_limit); _limit(candidate_limit)
    clauses = _source(cnf, counts)
    positions = defaultdict(list)
    for cid, clause in enumerate(clauses):
        for lit in clause:
            positions[lit].append(cid)
            counts['elimination_index_literals'] += 1
    variables = {abs(lit) for lit in positions}
    choices = sorted(variables, key=lambda v: (len(positions[v]) * len(positions[-v]), v))
    counts['elimination_candidate_variables'] += len(choices)
    if len(choices) > candidate_limit:
        counts['elimination_candidate_budget_skips'] += len(choices) - candidate_limit
    original = set(clauses); best = None
    for variable in choices[:candidate_limit]:
        positive, negative = positions[variable], positions[-variable]
        pairs = len(positive) * len(negative)
        if pairs > pair_limit:
            counts['elimination_pair_budget_skips'] += 1
            continue
        removed = positive + negative
        old_literals = sum(len(clauses[cid]) for cid in removed)
        added = set(); added_literals = 0; growing = False
        counts['elimination_candidates_tested'] += 1
        for a in positive:
            for b in negative:
                counts['elimination_discovery_pairs'] += 1
                counts['elimination_discovery_pair_literals'] += len(clauses[a]) + len(clauses[b])
                result = (clauses[a] - {variable}) | (clauses[b] - {-variable})
                if any(-lit in result for lit in result):
                    counts['elimination_tautological_pairs'] += 1
                    continue
                if result in original or result in added:
                    counts['elimination_duplicate_resolvents'] += 1
                    continue
                added.add(result); added_literals += len(result)
                if len(added) > len(removed) or added_literals > old_literals:
                    growing = True
                    break
            if growing:
                break
        if growing:
            counts['elimination_growth_rejections'] += 1
            continue
        score = (added_literals - old_literals, len(added) - len(removed), pairs, variable)
        if best is None or score < best:
            best = score
    counts['elimination_discoveries'] += 1
    return dict(variable=None if best is None else best[-1])


def check_elimination(cnf, certificate, counts, *, pair_limit=64):
    """Recompute all resolvents from the actual source, without discovery state."""
    _limit(pair_limit)
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
        counts['elimination_check_source_literals'] += len(clause)
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
            counts['elimination_checked_pairs'] += 1
            counts['elimination_checked_pair_literals'] += len(a) + len(b)
            result = set(a); result.update(b)
            if not any(-lit in result for lit in result):
                retained.add(tuple(sorted(result)))
    target = tuple(sorted(retained))
    if len(target) > len(cnf) or sum(map(len, target)) > sum(map(len, cnf)):
        raise ValueError('Elimination increases clauses or literal occurrences')
    counts['elimination_checked_steps'] += 1
    counts['elimination_checked_pure_steps' if not positive or not negative else 'elimination_checked_mixed_steps'] += 1
    return target


def lift_elimination(cnf, certificate, child_model, counts, *, pair_limit=64):
    target = check_elimination(cnf, certificate, counts, pair_limit=pair_limit)
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
    counts['elimination_lift_source_literals'] += sum(map(len, cnf))
    if not holds(cnf, model):
        raise ValueError('Elimination lift violates source')
    return model


class VariableEliminationInventory(PreparedProbeInventory):
    def __init__(self, *args, elimination_pair_limit=64, elimination_candidate_limit=64, **kwargs):
        _limit(elimination_pair_limit); _limit(elimination_candidate_limit)
        super().__init__(*args, **kwargs)
        self.config.update(terminal_elimination='complete-opposing-pairs-nongrowing-v1',
                           elimination_pair_limit=elimination_pair_limit,
                           elimination_candidate_limit=elimination_candidate_limit)

    def _discover_profile(self, cnf, depth, profile, groups):
        node = super()._discover_profile(cnf, depth, profile, groups)
        if node['kind'] != 'unresolved':
            return node
        proof = discover_elimination(cnf, self.counts, pair_limit=self.config['elimination_pair_limit'],
                                     candidate_limit=self.config['elimination_candidate_limit'])
        target = check_elimination(cnf, proof, self.counts, pair_limit=self.config['elimination_pair_limit'])
        node['elimination'] = proof
        if target is not None:
            edge = self._edge(target, depth)
            node.update(kind='eliminate', edge=edge, summary=self._summary([edge]))
            self.counts['elimination_rewrites'] += 1
        return node

    def _check_profile(self, key, node, cnf, profile, groups):
        if node.get('kind') not in ('eliminate', 'unresolved'):
            if 'elimination' in node:
                raise ValueError('Unexpected terminal elimination')
            return super()._check_profile(key, node, cnf, profile, groups)
        old = {k: v for k, v in node.items() if k not in ('elimination', 'edge')}
        old.update(kind='unresolved', summary=dict(closed=False, unresolved_leaves=1,
                                                  unresolved_literals=profile['shape']['literals']))
        super()._check_profile(key, old, cnf, profile, groups)
        if 'elimination' not in node:
            raise ValueError('Missing terminal elimination proposal')
        target = check_elimination(cnf, node['elimination'], self.counts,
                                   pair_limit=self.config['elimination_pair_limit'])
        if target is None:
            if node['kind'] != 'unresolved' or set(node) != set(old) | {'elimination'}:
                raise ValueError('Empty elimination witness must remain unresolved')
            summary = old['summary']
        else:
            if self.config['elimination_candidate_limit'] == 0:
                raise ValueError('Elimination discovery is disabled')
            if node['kind'] != 'eliminate' or set(node) != set(old) | {'elimination', 'edge'}:
                raise ValueError('Missing elimination edge')
            self._check_edge(node['edge'], target, node['depth'])
            summary = self._summary([node['edge']])
        if encode(node['summary']) != encode(summary):
            raise ValueError('Invalid elimination coverage summary')

    def lift(self, key, child_model):
        node = self._load(key)
        if node['kind'] != 'eliminate':
            return super().lift(key, child_model)
        edge = node['edge']
        if (type(child_model) is not dict or
                any(i not in child_model or type(child_model[i]) is not bool for i in range(1, len(edge['names']) + 1))):
            raise ValueError('Invalid canonical elimination model')
        original_names = {v: child_model[i] for i, v in enumerate(edge['names'], 1)}
        return lift_elimination(node['cnf'], node['elimination'], original_names, self.counts,
                                pair_limit=self.config['elimination_pair_limit'])
