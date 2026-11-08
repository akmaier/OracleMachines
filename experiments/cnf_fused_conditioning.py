"""Exact conditioning edges carrying checked simplification traces.

The intermediate restricted CNF is reconstructed, not persisted as a new node
when the existing planner would immediately simplify it. Recognition and
component priority are unchanged. Full root/source records remain intact.
"""
from experiments.cnf_conditioning import shortest_balanced_choices
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import components, holds, normalize, restrict
from experiments.cnf_simplification import SimplifyingPatternInventory, check_simplification


class FusedConditioningInventory(SimplifyingPatternInventory):
    def __init__(self, *args, simplify_pure=False, **kwargs):
        super().__init__(*args, simplify_pure=simplify_pure, **kwargs)
        self.config['conditioning_edges'] = 'checked-closure-v1'

    def _prepared(self, cnf):
        profile = self._profile(cnf)
        groups = components(cnf, self.counts) if self.config['decompose'] else [cnf]
        return profile, groups

    def _conditioning_edge(self, cnf, variable, value, depth):
        raw = restrict(cnf, {variable: value}, self.counts)
        intermediate, names, key = self._canonical(raw, depth)
        existing = self._load(key)
        if existing is not None:
            if existing['kind'] != 'simplify':
                return dict(key=key, names=names)
            profile = existing['profile']
        else:
            profile, groups = self._prepared(intermediate)
            if not self._uses_simplification(profile, groups):
                # Reuse the just-computed profile rather than rediscovering it.
                self._record_node(key, self._discover_profile(intermediate, depth, profile, groups))
                return dict(key=key, names=names)
        target, _ = self._simplified(intermediate, profile)
        child = self._edge(target, depth)
        self.counts['fused_conditioning_edges'] += 1
        return dict(key=child['key'], names=[names[v-1] for v in child['names']],
                    closure=profile['simplification']['certificate'])

    def _check_conditioning_edge(self, edge, cnf, variable, value, depth):
        if 'closure' not in edge:
            super()._check_conditioning_edge(edge, cnf, variable, value, depth)
            if self._load(edge['key'])['kind'] == 'simplify':
                raise ValueError('Omitted conditioning closure')
            return
        if set(edge) != {'key', 'names', 'closure'}:
            raise ValueError('Invalid conditioning closure fields')
        intermediate, names = normalize(restrict(cnf, {variable: value}, self.counts), self.counts)
        profile, groups = self._prepared(intermediate)
        if (not self._uses_simplification(profile, groups) or
                encode(edge['closure']) != encode(profile['simplification']['certificate'])):
            raise ValueError('Invalid conditioning closure policy')
        target, _ = check_simplification(intermediate, edge['closure'], self.counts,
            units=self.config['simplify_units'], pure=self.config['simplify_pure'])
        if not {abs(lit) for c in target for lit in c} < {abs(lit) for c in intermediate for lit in c}:
            raise ValueError('Closure must strictly reduce support')
        _, local_names, key = self._canonical(target, depth)
        expected_names = [names[v-1] for v in local_names]
        if edge['key'] != key or encode(edge['names']) != encode(expected_names) or self._load(key) is None:
            raise ValueError('Invalid closure identity or source transport')
        self.counts['verified_fused_conditioning_edges'] += 1

    def lift_conditioned(self, key, attempt_index, value, child_model):
        """Lift any satisfying branch child through its assumption and reasons."""
        node = self._load(key)
        if (node['kind'] != 'or' or type(attempt_index) is not int or
                not 0 <= attempt_index < len(node['alternatives']) or type(value) is not bool):
            raise ValueError('Invalid conditioning lift request')
        attempt = node['alternatives'][attempt_index]
        variable = attempt['variable'];edge = attempt['edges'][int(value)]
        child = self._load(edge['key'])
        if (any(i not in child_model or type(child_model[i]) is not bool for i in range(1,len(edge['names'])+1))
                or not holds(child['cnf'], child_model)):
            raise ValueError('Invalid branch child model')
        result = {abs(lit): False for c in node['cnf'] for lit in c}
        result[variable] = value
        if 'closure' in edge:
            intermediate, names = normalize(restrict(node['cnf'], {variable:value}, self.counts), self.counts)
            _, fixed = check_simplification(intermediate, edge['closure'], self.counts,
                units=self.config['simplify_units'], pure=self.config['simplify_pure'])
            result.update((names[v-1], b) for v,b in fixed.items())
        result.update((v,child_model[i]) for i,v in enumerate(edge['names'],1))
        self.counts['conditioning_lift_literal_visits'] += sum(map(len,node['cnf']))
        if result[variable] != value or not holds(node['cnf'],result):
            raise ValueError('Lift violates conditioning source')
        return result


class FusedShortestClauseInventory(FusedConditioningInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['conditioning_policy'] = 'shortest-balanced-v1'

    def _choices(self, cnf):
        return shortest_balanced_choices(cnf, self.config['candidate_limit'], self.counts)
