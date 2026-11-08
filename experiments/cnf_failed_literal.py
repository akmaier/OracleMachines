"""Optional bounded failed-literal discovery with independently checked reasons.

This is standard look-ahead, not a new SAT class. Only a unit-conflict trace
licenses a forced opposite literal. No-conflict probes are retained but imply
neither satisfiability nor nonmembership in any family. Budgets are per residual.
"""
from collections import Counter

from experiments.cnf_fused_conditioning import FusedShortestClauseInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import components, holds, restrict
from experiments.cnf_simplification import discover_simplification, check_simplification


def probe_choices(cnf, limit, counts):
    frequencies = Counter(abs(lit) for clause in cnf if len(clause) == 2 for lit in clause)
    counts['probe_ranking_literal_visits'] += sum(map(len, cnf))
    return sorted(frequencies, key=lambda v: (-frequencies[v], v))[:limit]


def discover_probes(cnf, limit, counts):
    attempts = []
    for variable in probe_choices(cnf, limit, counts):
        for value in (False, True):
            branch = restrict(cnf, {variable: value}, counts)
            certificate = discover_simplification(branch, counts, pure=False)
            attempts.append(dict(variable=variable, value=value, certificate=certificate))
            counts['probe_attempts'] += 1
            if certificate['conflict'] is not None:
                # Carry the opposite assumption and its closure directly to the
                # final child, without a second full intermediate node.
                retained = restrict(cnf, {variable: not value}, counts)
                closure = discover_simplification(retained, counts, pure=False)
                counts['probe_forced_values'] += 1
                return dict(status='forced', attempts=attempts, closure=closure)
    return dict(status='clear', attempts=attempts)


def check_probes(cnf, result, limit, counts):
    """Check deterministic attempt order and reasons without rerunning search.

The reason sequence need not be the unique sequence emitted by propagation;
each reason and every claimed no-conflict fixed point is independently checked.
"""
    forced = result.get('status') == 'forced'
    if (result.get('status') not in ('clear', 'forced') or
            set(result) != ({'status', 'attempts', 'closure'} if forced else {'status', 'attempts'})):
        raise ValueError('Invalid probe fields')
    expected = [(v, b) for v in probe_choices(cnf, limit, counts) for b in (False, True)]
    attempts = result['attempts']
    if not isinstance(attempts, list) or len(attempts) > len(expected) or (forced and not attempts):
        raise ValueError('Invalid probe count')
    for i, (attempt, (variable, value)) in enumerate(zip(attempts, expected)):
        if (set(attempt) != {'variable', 'value', 'certificate'} or
                type(attempt['variable']) is not int or attempt['variable'] != variable or
                type(attempt['value']) is not bool or attempt['value'] != value):
            raise ValueError('Invalid probe order or assumption')
        branch = restrict(cnf, {variable: value}, counts)
        certificate = attempt['certificate']
        check_simplification(branch, certificate, counts, pure=False)
        conflict = certificate['conflict'] is not None
        if conflict != (forced and i == len(attempts)-1):
            raise ValueError('Invalid probe stop or forced-value claim')
        counts['verified_probe_attempts'] += 1
    if not forced:
        if len(attempts) != len(expected):
            raise ValueError('Omitted unsuccessful probe')
        return cnf, {}
    last = attempts[-1]
    fixed = {last['variable']: not last['value']}
    target, closure_fixed = check_simplification(restrict(cnf, fixed, counts),
                                                result['closure'], counts, pure=False)
    fixed.update(closure_fixed)
    if not {abs(lit) for c in target for lit in c} < {abs(lit) for c in cnf for lit in c}:
        raise ValueError('Probe closure must strictly reduce support')
    return target, fixed


class FailedLiteralInventory(FusedShortestClauseInventory):
    def __init__(self, *args, probe_limit=4, **kwargs):
        if type(probe_limit) is not int or not 0 <= probe_limit <= 64:
            raise ValueError('probe_limit must be an integer between 0 and 64')
        super().__init__(*args, **kwargs)
        self.config.update(probing='binary-frequency-failed-literal-v1', probe_limit=probe_limit)

    def _probe_enabled(self, profile, groups):
        return (self.config['probe_limit'] > 0 and len(groups) <= 1 and
                not any(v == 'recognized' for v in profile['outcomes'].values()) and
                not self._uses_simplification(profile, groups) and
                not self._uses_projection(profile, groups))

    def _discover_probes(self, cnf):
        return discover_probes(cnf, self.config['probe_limit'], self.counts)

    def _check_probes(self, cnf, result):
        return check_probes(cnf, result, self.config['probe_limit'], self.counts)

    @staticmethod
    def _uses_probe(profile):
        return profile['probing']['status'] == 'forced'

    def _profile(self, cnf):
        profile = super()._profile(cnf)
        groups = components(cnf, self.counts) if self.config['decompose'] else [cnf]
        profile['probing'] = (self._discover_probes(cnf)
                              if self._probe_enabled(profile, groups) else dict(status='skipped'))
        return profile

    def _check(self, key, node):
        # The base checker rediscovering the complete profile would rerun every
        # probe. Recompute ordinary recognition, then replay saved probe reasons.
        depth = node.get('depth')
        if type(depth) is not int or not 0 <= depth <= self.config['max_depth']:
            raise ValueError('Invalid remaining depth')
        cnf, _, actual = self._canonical(node['cnf'], depth)
        if actual != key or node['cnf'] != [list(c) for c in cnf]:
            raise ValueError('Invalid canonical identity')
        profile = super()._profile(cnf)
        groups = components(cnf, self.counts) if self.config['decompose'] else [cnf]
        saved = node['profile'].get('probing', {})
        if self._probe_enabled(profile, groups):
            self._check_probes(cnf, saved)
        elif saved != dict(status='skipped'):
            raise ValueError('Probing overrides an earlier recognition/reduction')
        profile['probing'] = saved
        if encode(profile) != encode(node['profile']):
            raise ValueError('Invalid pattern certificate')
        self._check_profile(key, node, cnf, profile, groups)
        self.counts['verified_pattern_nodes'] += 1

    def _discover_profile(self, cnf, depth, profile, groups):
        if not self._uses_probe(profile):
            return super()._discover_profile(cnf, depth, profile, groups)
        target, _ = self._check_probes(cnf, profile['probing'])
        edge = self._edge(target, depth)
        self.counts['probe_rewrites'] += 1
        return dict(cnf=[list(c) for c in cnf], depth=depth, profile=profile,
                    kind='probe', edge=edge, summary=self._summary([edge]))

    def _check_profile(self, key, node, cnf, profile, groups):
        if not self._uses_probe(profile):
            return super()._check_profile(key, node, cnf, profile, groups)
        if set(node) != {'cnf', 'depth', 'profile', 'kind', 'edge', 'summary'} or node['kind'] != 'probe':
            raise ValueError('Missing checked probe rewrite')
        target, _ = self._check_probes(cnf, profile['probing'])
        self._check_edge(node['edge'], target, node['depth'])
        if encode(node['summary']) != encode(self._summary([node['edge']])):
            raise ValueError('Invalid probe coverage summary')

    def lift(self, key, child_model):
        node = self._load(key)
        if node['kind'] != 'probe':
            return super().lift(key, child_model)
        edge = node['edge']; child = self._load(edge['key'])
        if (any(i not in child_model or type(child_model[i]) is not bool for i in range(1, len(edge['names'])+1))
                or not holds(child['cnf'], child_model)):
            raise ValueError('Invalid probed child model')
        _, fixed = self._check_probes(node['cnf'], node['profile']['probing'])
        model = {abs(lit): False for c in node['cnf'] for lit in c}
        model.update(fixed)
        model.update((v, child_model[i]) for i, v in enumerate(edge['names'], 1))
        if not holds(node['cnf'], model):
            raise ValueError('Lift violates probe source')
        return model
