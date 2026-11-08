"""Checked existential projection of explicit affine constraints onto couplings.

Projection eliminates only variables absent from the leftover clauses. Its
remaining equations are encoded as CNF within a deterministic literal budget;
an encoding-budget miss keeps the original formula and bounded fallback policy.
Every successful rewrite removes at least one variable and consumes no branch
depth. Full original records and failed analyses remain in the archive.
"""
import itertools

from experiments.cnf_affine_patterns import AffinePatternInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import holds


def equation_mask(equation):
    return sum(1 << (v-1) for v in equation['variables'])


def project_equations(equations, keep, counts):
    variables = {v for equation in equations for v in equation['variables']}
    internal = sorted(variables-set(keep))
    internal_mask = sum(1 << (v-1) for v in internal)
    basis, rows = {}, []
    for equation in equations:
        mask, rhs, using = equation_mask(equation), equation['rhs'], []
        while mask & internal_mask:
            remaining = mask & internal_mask
            pivot = remaining & -remaining
            if pivot not in basis:
                basis[pivot] = len(rows)
                break
            previous = basis[pivot];using.append(previous)
            mask ^= rows[previous]['mask'];rhs ^= rows[previous]['rhs']
            counts['projection_xors'] += 1
        rows.append(dict(mask=mask, rhs=rhs, using=using))
    seen, boundary = set(), []
    for i, row in enumerate(rows):
        pair = (row['mask'], row['rhs'])
        if not row['mask'] & internal_mask and pair != (0, 0) and pair not in seen:
            boundary.append(i);seen.add(pair)
    return dict(internal=internal, rows=rows, boundary=boundary)


def check_projection(equations, keep, certificate, counts):
    """Verify exact row equivalence and elimination of every internal pivot.

Internal pivot variables can be assigned in decreasing order. Nonpivot
internal variables are free; the remaining rows are necessary AND sufficient
constraints on keep. No equation with a surviving internal variable is silently
treated as a boundary constraint.
"""
    if set(certificate) != {'internal', 'rows', 'boundary'}:
        raise ValueError('Invalid projection certificate fields')
    internal = sorted({v for e in equations for v in e['variables']}-set(keep))
    if encode(certificate['internal']) != encode(internal):
        raise ValueError('Invalid eliminated variables')
    internal_mask = sum(1 << (v-1) for v in internal)
    rows = certificate['rows']
    if len(rows) != len(equations):
        raise ValueError('Missing projection equation')
    pivots = {}
    for i, (equation, row) in enumerate(zip(equations, rows)):
        if set(row) != {'mask', 'rhs', 'using'} or type(row['mask']) is not int or type(row['rhs']) is not int:
            raise ValueError('Invalid projection row')
        mask, rhs = equation_mask(equation), equation['rhs']
        for previous in row['using']:
            remaining = mask & internal_mask
            if (type(previous) is not int or not 0 <= previous < i or not remaining or
                    pivots.get(remaining & -remaining) != previous):
                raise ValueError('Invalid projection dependency')
            mask ^= rows[previous]['mask'];rhs ^= rows[previous]['rhs']
            counts['projection_verification_xors'] += 1
        if (mask, rhs) != (row['mask'], row['rhs']):
            raise ValueError('Incorrect projected row')
        remaining = mask & internal_mask
        if remaining:
            pivot = remaining & -remaining
            if pivot in pivots:
                raise ValueError('Incomplete internal elimination')
            pivots[pivot] = i
    seen, expected = set(), []
    for i, row in enumerate(rows):
        pair = (row['mask'], row['rhs'])
        if not row['mask'] & internal_mask and pair != (0, 0) and pair not in seen:
            expected.append(i);seen.add(pair)
    if encode(certificate['boundary']) != encode(expected):
        raise ValueError('Missing or duplicated boundary constraint')
    counts['verified_projections'] += 1


def row_variables(mask):
    variables = []
    while mask:
        bit = mask & -mask;variables.append(bit.bit_length());mask ^= bit
    return variables


def encode_boundary(certificate, budget, counts):
    """Budget charged before enumeration, including empty contradiction clauses."""
    widths = [certificate['rows'][i]['mask'].bit_count() for i in certificate['boundary']]
    total = 0
    for width in widths:
        if width > budget.bit_length():
            return None
        total += max(1, width)*(1 << max(width-1, 0))
        if total > budget:
            return None
    blocks = []
    for i in certificate['boundary']:
        row = certificate['rows'][i];variables = row_variables(row['mask'])
        clauses = [[-v if bit else v for v, bit in zip(variables, bits)]
                   for bits in itertools.product((0, 1), repeat=len(variables)) if sum(bits) % 2 != row['rhs']]
        counts['projection_encoded_literals'] += sum(map(len, clauses))
        blocks.append(clauses)
    return blocks


def check_boundary(certificate, blocks, counts):
    """Check generated half cubes without trusting the assignment enumerator."""
    if len(blocks) != len(certificate['boundary']):
        raise ValueError('Missing projected clause block')
    for i, clauses in zip(certificate['boundary'], blocks):
        row = certificate['rows'][i];variables = row_variables(row['mask'])
        width = len(variables)
        if len(clauses) != (1 << max(width-1, 0)) or (not width and row['rhs'] != 1):
            raise ValueError('Incomplete projected parity encoding')
        patterns = set()
        for clause in clauses:
            if (any(type(lit) is not int for lit in clause) or
                    sorted(abs(lit) for lit in clause) != variables or
                    sum(lit < 0 for lit in clause) % 2 == row['rhs']):
                raise ValueError('Incorrect projected sign pattern')
            patterns.add(tuple(sorted(clause)))
            counts['projection_encoding_check_literals'] += len(clause)
        if len(patterns) != len(clauses):
            raise ValueError('Duplicated projected sign pattern')


def lift_projection(equations, keep, certificate, model, counts):
    """Extend a feasible keep assignment; choose free internal variables false."""
    check_projection(equations, keep, certificate, counts)
    if any(v not in model or type(model[v]) is not bool for v in keep):
        raise ValueError('Missing Boolean boundary assignment')
    result = {v: model[v] for v in keep}
    result.update((v, False) for v in certificate['internal'])
    internal = set(certificate['internal'])
    pivots = []
    for row in certificate['rows']:
        variables = row_variables(row['mask']);owned = internal.intersection(variables)
        if owned:
            pivots.append((min(owned), row, variables))
        elif sum(result[v] for v in variables) % 2 != row['rhs']:
            raise ValueError('Infeasible boundary assignment')
    for pivot, row, variables in sorted(pivots, reverse=True):
        result[pivot] = bool(row['rhs'] ^ (sum(result[v] for v in variables if v != pivot) % 2))
        counts['projection_lifting_variables'] += len(variables)
    if not all(sum(result[v] for v in e['variables']) % 2 == e['rhs'] for e in equations):
        raise ValueError('Lift does not satisfy original equations')
    return result


class ProjectionPatternInventory(AffinePatternInventory):
    def __init__(self, *args, projection_budget=4096, **kwargs):
        if type(projection_budget) is not int or not 0 <= projection_budget <= 65536:
            raise ValueError('projection_budget must be an integer between 0 and 65536')
        super().__init__(*args, **kwargs)
        self.config.update(pattern_extension='affine-projection-v1', projection_budget=projection_budget)

    def _profile(self, cnf):
        profile = super()._profile(cnf)
        affine = profile['evidence']['explicit_affine']
        keep = sorted({abs(lit) for i in affine['leftovers'] for lit in cnf[i]})
        internal = {v for e in affine['equations'] for v in e['variables']}-set(keep)
        if not affine['leftovers'] or not internal or profile['evidence']['affine_conflict']['inconsistent']:
            profile['projection'] = dict(status='not_applicable')
            return profile
        certificate = project_equations(affine['equations'], keep, self.counts)
        check_projection(affine['equations'], keep, certificate, self.counts)
        blocks = encode_boundary(certificate, self.config['projection_budget'], self.counts)
        if blocks is not None:
            check_boundary(certificate, blocks, self.counts)
        profile['projection'] = dict(status='encoding_cap' if blocks is None else 'ready',
                                     keep=keep, certificate=certificate, blocks=blocks)
        return profile

    @staticmethod
    def _uses_projection(profile, groups):
        return (len(groups) <= 1 and profile['projection']['status'] == 'ready' and
                not any(v == 'recognized' for v in profile['outcomes'].values()))

    @staticmethod
    def _target(cnf, profile):
        return ([cnf[i] for i in profile['evidence']['explicit_affine']['leftovers']] +
                [clause for block in profile['projection']['blocks'] for clause in block])

    def _discover_profile(self, cnf, depth, profile, groups):
        if not self._uses_projection(profile, groups):
            return super()._discover_profile(cnf, depth, profile, groups)
        target = self._target(cnf, profile)
        edge = self._edge(target, depth)
        self.counts['projection_rewrites'] += 1
        return dict(cnf=[list(c) for c in cnf], depth=depth, profile=profile,
                    kind='project', edge=edge, summary=self._summary([edge]))

    def _check_profile(self, key, node, cnf, profile, groups):
        if not self._uses_projection(profile, groups):
            return super()._check_profile(key, node, cnf, profile, groups)
        if set(node) != {'cnf', 'depth', 'profile', 'kind', 'edge', 'summary'} or node['kind'] != 'project':
            raise ValueError('Missing exact projection rewrite')
        target = self._target(cnf, profile)
        if not set(abs(lit) for c in target for lit in c) < set(abs(lit) for c in cnf for lit in c):
            raise ValueError('Projection must strictly reduce variable support')
        self._check_edge(node['edge'], target, node['depth'])
        if encode(node['summary']) != encode(self._summary([node['edge']])):
            raise ValueError('Invalid projected coverage summary')

    def lift(self, key, child_model):
        node = self._load(key)
        if node['kind'] != 'project':
            raise ValueError('Expected projection node')
        child = self._load(node['edge']['key'])
        if not holds(child['cnf'], child_model):
            raise ValueError('Invalid child model')
        model = {v: child_model[i] for i, v in enumerate(node['edge']['names'], 1)}
        profile = node['profile'];projection = profile['projection']
        result = lift_projection(profile['evidence']['explicit_affine']['equations'],
                                 projection['keep'], projection['certificate'], model, self.counts)
        if not holds(node['cnf'], result):
            raise ValueError('Lift violates source CNF')
        return result
