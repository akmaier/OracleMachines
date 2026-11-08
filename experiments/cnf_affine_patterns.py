"""Exact extraction of complete direct XOR encodings from normalized CNF.

Every clause belongs to an extracted equation or remains as a coupling clause.
The mixed representation is equivalent on *every assignment*, not merely
equisatisfiable. Discovery never enumerates unobserved assignments. This is an
optional analysis policy; the ordinary SAT solver and v1 inventory are unchanged.
"""
from collections import defaultdict

from experiments.cnf_pattern_inventory import FAMILIES, PatternInventory


AFFINE_FAMILIES = FAMILIES + ('explicit_affine', 'affine_conflict')


def complete_half(size, width):
    # size == 2**(width-1), without constructing a width-bit power for a sparse,
    # very wide clause. Width zero (an empty clause) is handled separately.
    return size > 0 and size.bit_length() == width and size & (size-1) == 0


def extract_affine(cnf, counts):
    groups = defaultdict(list)
    for cid, clause in enumerate(cnf):
        support = tuple(sorted(abs(lit) for lit in clause))
        forbidden = sum(lit < 0 for lit in clause) % 2
        groups[support, forbidden].append(cid)
        counts['affine_grouping_literals'] += len(clause)
    equations, leftovers = [], []
    for (support, forbidden), ids in sorted(groups.items()):
        if not support or complete_half(len(ids), len(support)):
            equations.append(dict(variables=list(support), rhs=1-forbidden, clauses=ids))
        else:
            leftovers.extend(ids)
    # Integer rows use the normalized formula's dense variable numbering.
    basis, reductions = {}, []
    for equation in equations:
        mask = sum(1 << (v-1) for v in equation['variables'])
        rhs, using = equation['rhs'], []
        while mask:
            pivot = mask & -mask
            if pivot not in basis:
                basis[pivot] = len(reductions)
                break
            previous = basis[pivot]
            using.append(previous)
            mask ^= reductions[previous]['mask']
            rhs ^= reductions[previous]['rhs']
            counts['affine_elimination_xors'] += 1
        reductions.append(dict(using=using, mask=mask, rhs=rhs))
    counts['affine_extracted_equations'] += len(equations)
    counts['affine_leftover_clauses'] += len(leftovers)
    return dict(equations=equations, leftovers=sorted(leftovers), reductions=reductions)


def check_affine(cnf, certificate, counts):
    """Check positive extraction and row operations without trusting grouping.

Complete, distinct sign patterns of one parity exclude exactly that half cube.
All clause IDs must occur exactly once. Row operations only use prior reduced
rows, giving an invertible triangular transformation of the equation system.
The caller separately enforces the deterministic discovery policy/profile.
"""
    if set(certificate) != {'equations', 'leftovers', 'reductions'}:
        raise ValueError('Invalid affine certificate fields')
    used, rows = set(), []
    for equation in certificate['equations']:
        if set(equation) != {'variables', 'rhs', 'clauses'}:
            raise ValueError('Invalid equation fields')
        variables, rhs, ids = equation['variables'], equation['rhs'], equation['clauses']
        if (any(type(v) is not int or v <= 0 for v in variables) or
                variables != sorted(set(variables)) or type(rhs) is not int or rhs not in (0, 1) or
                not ids or any(type(cid) is not int or not 0 <= cid < len(cnf) for cid in ids)):
            raise ValueError('Invalid equation domain')
        signs = set()
        for cid in ids:
            if cid in used:
                raise ValueError('Repeated source clause')
            used.add(cid)
            clause = cnf[cid]
            if sorted(abs(lit) for lit in clause) != variables or sum(lit < 0 for lit in clause) % 2 != 1-rhs:
                raise ValueError('Incorrect support or forbidden parity')
            signs.add(tuple(sorted(lit for lit in clause if lit < 0)))
            counts['affine_verification_literals'] += len(clause)
        valid_size = complete_half(len(signs), len(variables)) if variables else (len(signs) == 1 and rhs == 1)
        if len(signs) != len(ids) or not valid_size:
            raise ValueError('Incomplete or duplicated parity half')
        rows.append((sum(1 << (v-1) for v in variables), rhs))
    leftovers = certificate['leftovers']
    if any(type(cid) is not int for cid in leftovers) or leftovers != [i for i in range(len(cnf)) if i not in used]:
        raise ValueError('Omitted, repeated or reordered coupling clause')
    reductions = certificate['reductions']
    if len(reductions) != len(rows):
        raise ValueError('Missing row reduction')
    pivots = {}
    for i, ((mask, rhs), row) in enumerate(zip(rows, reductions)):
        if (set(row) != {'using', 'mask', 'rhs'} or type(row['mask']) is not int or type(row['rhs']) is not int):
            raise ValueError('Invalid reduced row')
        for previous in row['using']:
            if (type(previous) is not int or not 0 <= previous < i or not mask or
                    pivots.get(mask & -mask) != previous):
                raise ValueError('Invalid elimination dependency')
            mask ^= reductions[previous]['mask']
            rhs ^= reductions[previous]['rhs']
            counts['affine_verification_xors'] += 1
        if (mask, rhs) != (row['mask'], row['rhs']):
            raise ValueError('Invalid elimination result')
        if mask:
            pivot = mask & -mask
            if pivot in pivots:
                raise ValueError('Incomplete row elimination')
            pivots[pivot] = i
    counts['affine_verified_certificates'] += 1
    return dict(pure=not leftovers, inconsistent=any(row['mask'] == 0 and row['rhs'] == 1 for row in reductions),
                rank=len(pivots), equation_count=len(rows), leftover_clauses=len(leftovers),
                leftover_literals=sum(len(cnf[i]) for i in leftovers),
                interface_variables=sorted({abs(lit) for i in leftovers for lit in cnf[i]}.intersection(
                    {v for equation in certificate['equations'] for v in equation['variables']})))


class AffinePatternInventory(PatternInventory):
    """Versioned policy extending v1; old archive identities are left intact."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['pattern_extension'] = 'explicit-affine-v1'

    def _profile(self, cnf):
        profile = super()._profile(cnf)
        certificate = extract_affine(cnf, self.counts)
        summary = check_affine(cnf, certificate, self.counts)
        profile['outcomes'].update(explicit_affine='recognized' if summary['pure'] else 'excluded',
                                   affine_conflict='recognized' if summary['inconsistent'] else 'excluded')
        profile['evidence']['explicit_affine'] = certificate
        profile['evidence']['affine_conflict'] = summary
        profile['cell'] = ''.join(profile['outcomes'][name][0].upper() for name in AFFINE_FAMILIES)
        return profile
