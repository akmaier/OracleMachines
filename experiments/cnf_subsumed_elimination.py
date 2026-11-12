"""Checked retained-clause subsumption as a fallback for bounded elimination.

Only a clause that survives the pivot elimination may justify an omitted
resolvent. Complete pair enumeration and explicit source indices are checked
independently of the discovery index. Earlier elimination choices run first.
"""
from collections import defaultdict

from experiments.cnf_variable_elimination import VariableEliminationInventory, _limit, _source
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds


def discover_subsumed(cnf, counts, *, pair_limit=64, candidate_limit=64):
    _limit(pair_limit); _limit(candidate_limit)
    clauses = _source(cnf, counts); positions = defaultdict(list); anchors = defaultdict(list)
    for i, c in enumerate(clauses):
        anchors[min(c) if c else None].append(i)
        for lit in c: positions[lit].append(i)
        counts['subsumed_index_literals'] += len(c)
    variables = sorted({abs(l) for l in positions},
                       key=lambda v: (len(positions[v]) * len(positions[-v]), v))
    original = set(clauses); best = None; witness = dict(variable=None, omissions=[])
    counts['subsumed_candidate_budget_skips'] += max(0, len(variables) - candidate_limit)
    for variable in variables[:candidate_limit]:
        positive, negative = positions[variable], positions[-variable]
        pairs = len(positive) * len(negative)
        if pairs > pair_limit:
            counts['subsumed_pair_budget_skips'] += 1
            continue
        counts['subsumed_candidates_tested'] += 1
        removed = positive + negative; old_literals = sum(len(clauses[i]) for i in removed)
        added = set(); added_literals = 0; omissions = []; growing = False
        for a in positive:
            for b in negative:
                counts['subsumed_discovery_pairs'] += 1
                counts['subsumed_discovery_pair_literals'] += len(clauses[a]) + len(clauses[b])
                result = (clauses[a] - {variable}) | (clauses[b] - {-variable})
                if any(-lit in result for lit in result): continue
                if result in original or result in added: continue
                reason = None
                for anchor in [None] + sorted(result):
                    for i in anchors.get(anchor, ()):
                        c = clauses[i]; counts['subsumed_subset_tests'] += 1
                        counts['subsumed_subset_test_literal_bound'] += len(c)
                        if variable not in c and -variable not in c and len(c) <= len(result) and c <= result:
                            reason = i; break
                    if reason is not None: break
                if reason is not None:
                    omissions.append([a, b, reason]); counts['subsumed_discovery_omissions'] += 1
                    continue
                added.add(result); added_literals += len(result)
                if len(added) > len(removed) or added_literals > old_literals:
                    growing = True; break
            if growing: break
        if growing:
            counts['subsumed_growth_rejections'] += 1
            continue
        score = (added_literals - old_literals, len(added) - len(removed), pairs, variable)
        if best is None or score < best:
            best = score; witness = dict(variable=variable, omissions=omissions)
    counts['subsumed_discoveries'] += 1
    return witness


def check_subsumed(cnf, certificate, counts, *, pair_limit=64):
    _limit(pair_limit); _source(cnf, counts)
    if type(certificate) is not dict or set(certificate) != {'variable', 'omissions'}:
        raise ValueError('Invalid subsumed elimination fields')
    variable, omissions = certificate['variable'], certificate['omissions']
    if type(omissions) is not list:
        raise ValueError('Invalid omission list')
    if variable is None:
        if omissions: raise ValueError('Omissions without a pivot')
        return None
    if type(variable) is not int or variable <= 0:
        raise ValueError('Invalid subsumed elimination pivot')
    positive, negative, retained_ids = [], [], set()
    for i, c in enumerate(cnf):
        counts['subsumed_check_source_literals'] += len(c)
        if variable in c: positive.append(i)
        elif -variable in c: negative.append(i)
        else: retained_ids.add(i)
    if not positive and not negative: raise ValueError('Pivot absent')
    if len(positive) * len(negative) > pair_limit: raise ValueError('Opposing-pair cap exceeded')
    reasons = {}
    for item in omissions:
        if type(item) is not list or len(item) != 3 or any(type(i) is not int for i in item):
            raise ValueError('Invalid omission reference')
        a, b, r = item
        if a not in positive or b not in negative or r not in retained_ids or (a, b) in reasons:
            raise ValueError('Omission must reference a unique pair and a retained source clause')
        reasons[a, b] = r
    retained = {tuple(sorted(cnf[i])) for i in retained_ids}
    for a in positive:
        for b in negative:
            counts['subsumed_checked_pairs'] += 1
            counts['subsumed_checked_pair_literals'] += len(cnf[a]) + len(cnf[b])
            result = {l for l in cnf[a] if l != variable}
            result.update(l for l in cnf[b] if l != -variable)
            if any(-l in result for l in result):
                if (a, b) in reasons: raise ValueError('Tautological pair needs no omission witness')
                continue
            if (a, b) in reasons:
                reason = cnf[reasons[a, b]]
                counts['subsumed_check_reason_literals'] += len(reason)
                if any(l not in result for l in reason): raise ValueError('Reason does not subsume resolvent')
                counts['subsumed_checked_omissions'] += 1
            else:
                retained.add(tuple(sorted(result)))
    target = tuple(sorted(retained))
    if len(target) > len(cnf) or sum(map(len, target)) > sum(map(len, cnf)):
        raise ValueError('Subsumed elimination increases clauses or literals')
    counts['subsumed_checked_steps'] += 1
    return target


def lift_subsumed(cnf, certificate, child_model, counts, *, pair_limit=64):
    target = check_subsumed(cnf, certificate, counts, pair_limit=pair_limit)
    if target is None: raise ValueError('No subsumed elimination to lift')
    support = {abs(l) for c in target for l in c}
    if (type(child_model) is not dict or
            any(type(v) is not int or v <= 0 or type(b) is not bool for v, b in child_model.items()) or
            not support <= child_model.keys() or not holds(target, child_model)):
        raise ValueError('Invalid subsumed elimination child model')
    model = {abs(l): False for c in cnf for l in c}
    model.update((v, child_model[v]) for v in support)
    x = certificate['variable']
    model[x] = any(x in c and not any(model[abs(l)] == (l > 0) for l in c if l != x) for c in cnf)
    counts['subsumed_lift_source_literals'] += sum(map(len, cnf))
    if not holds(cnf, model): raise ValueError('Subsumed lift violates source')
    return model


class SubsumedEliminationInventory(VariableEliminationInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['terminal_subsumed_elimination'] = 'retained-source-clause-fallback-v1'

    def _discover_profile(self, cnf, depth, profile, groups):
        node = super()._discover_profile(cnf, depth, profile, groups)
        if node['kind'] != 'unresolved': return node
        proof = discover_subsumed(cnf, self.counts, pair_limit=self.config['elimination_pair_limit'],
                                   candidate_limit=self.config['elimination_candidate_limit'])
        target = check_subsumed(cnf, proof, self.counts, pair_limit=self.config['elimination_pair_limit'])
        node['subsumed_elimination'] = proof
        if target is not None:
            edge = self._edge(target, depth)
            node.update(kind='eliminate', edge=edge, summary=self._summary([edge]))
            self.counts['subsumed_rewrites'] += 1
        return node

    def _check_profile(self, key, node, cnf, profile, groups):
        if 'subsumed_elimination' not in node:
            if node.get('kind') == 'unresolved': raise ValueError('Missing subsumed fallback proposal')
            return super()._check_profile(key, node, cnf, profile, groups)
        old = {k: v for k, v in node.items() if k not in ('subsumed_elimination', 'edge')}
        old.update(kind='unresolved', summary=dict(closed=False, unresolved_leaves=1,
                                                  unresolved_literals=profile['shape']['literals']))
        super()._check_profile(key, old, cnf, profile, groups)
        target = check_subsumed(cnf, node['subsumed_elimination'], self.counts,
                               pair_limit=self.config['elimination_pair_limit'])
        if target is None:
            if node['kind'] != 'unresolved' or set(node) != set(old) | {'subsumed_elimination'}:
                raise ValueError('Null subsumed proposal must remain unresolved')
            summary = old['summary']
        else:
            if self.config['elimination_candidate_limit'] == 0: raise ValueError('Elimination disabled')
            if node['kind'] != 'eliminate' or set(node) != set(old) | {'subsumed_elimination', 'edge'}:
                raise ValueError('Invalid subsumed elimination edge')
            self._check_edge(node['edge'], target, node['depth'])
            summary = self._summary([node['edge']])
        if encode(node['summary']) != encode(summary): raise ValueError('Invalid subsumed summary')

    def lift(self, key, child_model):
        node = self._load(key)
        if node['kind'] != 'eliminate' or 'subsumed_elimination' not in node:
            return super().lift(key, child_model)
        names = node['edge']['names']
        if type(child_model) is not dict or any(type(child_model.get(i)) is not bool for i in range(1, len(names)+1)):
            raise ValueError('Invalid canonical subsumed model')
        model = {v: child_model[i] for i, v in enumerate(names, 1)}
        return lift_subsumed(node['cnf'], node['subsumed_elimination'], model, self.counts,
                             pair_limit=self.config['elimination_pair_limit'])
