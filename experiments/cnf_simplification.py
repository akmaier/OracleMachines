"""Checked unit/pure simplification exposing structure in arbitrary residuals.

Unit propagation reuses the existing discovery routine. Pure rounds inspect
the entire current residual, including all couplings. Independent replay checks
reasons, polarities and the exact child; erased assignments are retained for
model lifting. These are standard SAT reductions, not new tractability results.
"""
from experiments.cnf_affine_projection import ProjectionPatternInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds, propagate, restrict


def discover_simplification(cnf, counts, *, units=True, pure=True):
    assigned, trace, conflict = propagate(cnf, counts) if units else ({}, [], None)
    rounds = []
    if conflict is None and pure:
        current = restrict(cnf, assigned, counts)
        while True:
            literals = {lit for clause in current for lit in clause}
            counts['pure_discovery_literal_visits'] += sum(map(len, current))
            chosen = sorted((lit for lit in literals if -lit not in literals), key=abs)
            if not chosen:
                break
            rounds.append(chosen)
            current = restrict(current, {abs(lit): lit > 0 for lit in chosen}, counts)
    return dict(units=trace, conflict=conflict, pure_rounds=rounds)


def check_simplification(cnf, certificate, counts, *, units=True, pure=True):
    """Replay local reasons independently of propagation and pure discovery.

Unit reasons refer to the complete original node CNF. Pure absence is checked
in the *whole current residual*, never just in one selected tractable part.
The final residual is reconstructed directly, without trusting restrict().
"""
    if set(certificate) != {'units', 'conflict', 'pure_rounds'}:
        raise ValueError('Invalid simplification certificate fields')
    assigned = {}
    for lit, cid in certificate['units']:
        if (not units or type(lit) is not int or not lit or type(cid) is not int or
                not 0 <= cid < len(cnf) or abs(lit) in assigned):
            raise ValueError('Invalid unit reason index')
        clause = cnf[cid]
        if lit not in clause or any(abs(other) not in assigned or assigned[abs(other)] == (other > 0)
                                    for other in clause if other != lit):
            raise ValueError('Non-forced unit assignment')
        assigned[abs(lit)] = lit > 0
        counts['simplification_unit_check_literals'] += len(clause)
    conflict = certificate['conflict']
    if conflict is not None:
        if (not units or type(conflict) is not int or not 0 <= conflict < len(cnf) or
                certificate['pure_rounds'] or any(abs(lit) not in assigned or assigned[abs(lit)] == (lit > 0)
                                                for lit in cnf[conflict])):
            raise ValueError('Invalid unit conflict')
        counts['simplification_unit_check_literals'] += len(cnf[conflict])
        return ((),), assigned
    # A direct scan reconstructs restriction and checks discovery's fixed point.
    current = []
    for clause in cnf:
        counts['simplification_reconstruction_literals'] += len(clause)
        if any(abs(lit) in assigned and assigned[abs(lit)] == (lit > 0) for lit in clause):
            continue
        residual = tuple(lit for lit in clause if abs(lit) not in assigned)
        if units and len(residual) <= 1:
            raise ValueError('Incomplete unit fixed point')
        current.append(residual)
    for chosen in certificate['pure_rounds']:
        if not pure or not chosen or any(type(lit) is not int or not lit for lit in chosen):
            raise ValueError('Invalid pure round')
        polarities = {}
        for clause in current:
            for lit in clause:
                counts['simplification_pure_check_literals'] += 1
                polarities[abs(lit)] = polarities.get(abs(lit), 0) | (1 if lit > 0 else 2)
        expected = [v if sign == 1 else -v for v, sign in sorted(polarities.items()) if sign != 3]
        if encode(chosen) != encode(expected) or any(abs(lit) in assigned for lit in chosen):
            raise ValueError('Incomplete or impure assignment round')
        assigned.update((abs(lit), lit > 0) for lit in chosen)
        selected = set(chosen)
        # Opposite signs were excluded globally: pure steps only delete clauses.
        current = [clause for clause in current if not selected.intersection(clause)]
    if pure:
        remaining = {lit for clause in current for lit in clause}
        counts['simplification_pure_check_literals'] += sum(map(len, current))
        if any(-lit not in remaining for lit in remaining):
            raise ValueError('Incomplete pure fixed point')
    counts['verified_simplifications'] += 1
    return tuple(current), assigned


class SimplifyingPatternInventory(ProjectionPatternInventory):
    def __init__(self, *args, simplify_units=True, simplify_pure=True, **kwargs):
        if type(simplify_units) is not bool or type(simplify_pure) is not bool:
            raise ValueError('Simplification policies must be Boolean')
        super().__init__(*args, **kwargs)
        self.config.update(pattern_extension='unit-pure-discovery-v1',
                           simplify_units=simplify_units, simplify_pure=simplify_pure)

    def _profile(self, cnf):
        profile = super()._profile(cnf)
        if any(v == 'recognized' for v in profile['outcomes'].values()):
            profile['simplification'] = dict(status='already_recognized')
        else:
            options = dict(units=self.config['simplify_units'], pure=self.config['simplify_pure'])
            certificate = discover_simplification(cnf, self.counts, **options)
            target, assigned = check_simplification(cnf, certificate, self.counts, **options)
            profile['simplification'] = dict(status='ready' if assigned or certificate['conflict'] is not None else 'fixed_point',
                certificate=certificate, unit_assignments=len(certificate['units']),
                pure_assignments=sum(map(len, certificate['pure_rounds'])),
                residual_variables=len({abs(lit) for c in target for lit in c}),
                residual_clauses=len(target), residual_literals=sum(map(len, target)))
        return profile

    @staticmethod
    def _uses_simplification(profile, groups):
        return len(groups) <= 1 and profile['simplification']['status'] == 'ready'

    def _simplified(self, cnf, profile):
        return check_simplification(cnf, profile['simplification']['certificate'], self.counts,
                                   units=self.config['simplify_units'], pure=self.config['simplify_pure'])

    def _discover_profile(self, cnf, depth, profile, groups):
        if not self._uses_simplification(profile, groups):
            return super()._discover_profile(cnf, depth, profile, groups)
        target, _ = self._simplified(cnf, profile)
        edge = self._edge(target, depth)
        self.counts['simplification_rewrites'] += 1
        return dict(cnf=[list(c) for c in cnf], depth=depth, profile=profile,
                    kind='simplify', edge=edge, summary=self._summary([edge]))

    def _check_profile(self, key, node, cnf, profile, groups):
        if not self._uses_simplification(profile, groups):
            return super()._check_profile(key, node, cnf, profile, groups)
        if set(node) != {'cnf', 'depth', 'profile', 'kind', 'edge', 'summary'} or node['kind'] != 'simplify':
            raise ValueError('Missing checked simplification')
        target, _ = self._simplified(cnf, profile)
        if not {abs(lit) for c in target for lit in c} < {abs(lit) for c in cnf for lit in c}:
            raise ValueError('Simplification must strictly reduce variable support')
        self._check_edge(node['edge'], target, node['depth'])
        if encode(node['summary']) != encode(self._summary([node['edge']])):
            raise ValueError('Invalid simplification coverage summary')

    def lift(self, key, child_model):
        node = self._load(key)
        if node['kind'] != 'simplify':
            return super().lift(key, child_model)
        child = self._load(node['edge']['key'])
        if (any(i not in child_model or type(child_model[i]) is not bool for i in range(1, len(node['edge']['names'])+1))
                or not holds(child['cnf'], child_model)):
            raise ValueError('Invalid simplified child model')
        _, assigned = self._simplified(node['cnf'], node['profile'])
        result = {abs(lit): False for c in node['cnf'] for lit in c}
        result.update(assigned)
        result.update((v, child_model[i]) for i, v in enumerate(node['edge']['names'], 1))
        if not holds(node['cnf'], result):
            raise ValueError('Lift violates unsimplified source')
        return result
