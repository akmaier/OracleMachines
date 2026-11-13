"""Exact affine equations plus at most one leftover clause.

Reuse checked Gaussian rows to construct a particular solution and a complete
nullspace basis. A single disjunction needs one compatible literal. Several
interacting leftover clauses are deliberately outside this recognized family.
Bitmasks use dense source variables; all source extraction and checking is paid.
"""
from collections import Counter
import copy
import hashlib

from experiments.cnf_affine_patterns import extract_affine, check_affine
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_variable_elimination import _source
from experiments.cnf_residual_dag import holds

FORMAT = 'affine-one-clause-v1'


def source(cnf, counts):
    if type(cnf) is not list or any(type(c) is not list for c in cnf):
        raise ValueError('Expected explicit CNF clauses')
    _source(cnf, counts)
    variables = {abs(l) for c in cnf for l in c}
    if variables != set(range(1, len(variables)+1)):
        raise ValueError('Affine masks require dense variables; normalize first')
    return len(variables)


def pivot_rows(affine):
    return sorted((r for r in affine['reductions'] if r['mask']),
        key=lambda r: r['mask'] & -r['mask'], reverse=True)


def make_space(n, affine, counts):
    """Back substitute checked triangular rows; do not redo elimination."""
    rows = pivot_rows(affine); pivots = {r['mask'] & -r['mask'] for r in rows}
    free = [1 << i for i in range(n) if 1 << i not in pivots]
    def solve(mask, homogeneous):
        for r in rows:
            counts['affine_space_backsub_rows'] += 1
            if ((r['mask'] & mask).bit_count() & 1) ^ (0 if homogeneous else r['rhs']):
                mask |= r['mask'] & -r['mask']
        return mask
    counts['affine_space_vectors_constructed'] += len(free)+1
    return dict(particular=solve(0, False), directions=[solve(bit, True) for bit in free])


def check_space(n, affine, space, counts):
    """Equation checks plus identity free coordinates prove a complete basis.

    The caller must first validate affine with check_affine on the exact CNF.
    Checked affine rows give rank r. The n-r independent homogeneous vectors
    span the kernel. Checking only some convenient directions would be unsound
    when claiming that every solution falsifies a literal.
    """
    if type(space) is not dict or set(space) != {'particular', 'directions'}:
        raise ValueError('Invalid affine-space certificate')
    if any(r['mask'] == 0 and r['rhs'] for r in affine['reductions']):
        raise ValueError('Inconsistent system has no affine solution space')
    rows = pivot_rows(affine); pivots = {r['mask'] & -r['mask'] for r in rows}
    free = [1 << i for i in range(n) if 1 << i not in pivots]; free_mask = sum(free)
    particular = space['particular']; directions = space['directions']
    valid_mask = lambda m: type(m) is int and m >= 0 and m.bit_length() <= n
    if (not valid_mask(particular) or particular & free_mask or type(directions) is not list
            or len(directions) != len(free) or any(not valid_mask(v) for v in directions)):
        raise ValueError('Missing, invalid or noncanonical affine vectors')
    for bit, vector in zip(free, directions, strict=True):
        if vector & free_mask != bit: raise ValueError('Nullspace free coordinates are not an identity basis')
    for equation in affine['equations']:
        mask = sum(1 << (v-1) for v in equation['variables'])
        if ((mask & particular).bit_count() & 1) != equation['rhs']:
            raise ValueError('Particular solution violates an equation')
        for vector in directions:
            if (mask & vector).bit_count() & 1: raise ValueError('Direction is not in the nullspace')
            counts['affine_space_kernel_equation_checks'] += 1
        counts['affine_space_particular_equation_checks'] += 1
    counts['affine_space_vectors_checked'] += len(directions)+1


def model(mask, n):
    return {v: bool(mask & (1 << (v-1))) for v in range(1, n+1)}


def discover(cnf, counts=None, *, affine=None, space=None):
    counts = Counter() if counts is None else counts; n = source(cnf, counts)
    if affine is None: affine = extract_affine(cnf, counts)
    else: counts['affine_clause_reused_extractions'] += 1
    summary = check_affine(cnf, affine, counts)
    if summary['leftover_clauses'] > 1:
        counts['affine_clause_outside_family'] += 1; return None
    if summary['inconsistent']:
        index = next(i for i,r in enumerate(affine['reductions']) if r['mask'] == 0 and r['rhs'] == 1)
        decision = dict(kind='linear_conflict', row=index)
    else:
        if space is None: space = make_space(n, affine, counts)
        else: counts['affine_clause_reused_spaces'] += 1
        check_space(n, affine, space, counts)
        particular = space['particular']; candidate = particular; repair = None
        ids = affine['leftovers']; clause = cnf[ids[0]] if ids else None
        if clause is not None and not holds([clause], model(particular, n)):
            candidate = None
            for lit in clause:
                bit = 1 << (abs(lit)-1)
                for i, vector in enumerate(space['directions']):
                    counts['affine_clause_direction_queries'] += 1
                    if vector & bit:
                        candidate = particular ^ vector; repair = i; break
                if candidate is not None: break
        decision = dict(kind='space', space=space, sat=candidate is not None, repair=repair, model=candidate)
    proof = dict(format=FORMAT, cnf=cnf, affine=affine, decision=decision)
    check_certificate(proof, expected_cnf=cnf, counts=counts)
    return copy.deepcopy(proof)


def check_certificate(proof, *, expected_cnf=None, counts=None):
    counts = Counter() if counts is None else counts
    if type(proof) is not dict or set(proof) != {'format', 'cnf', 'affine', 'decision'} or proof['format'] != FORMAT:
        raise ValueError('Invalid affine-clause certificate')
    cnf = proof['cnf']; n = source(cnf, counts)
    if expected_cnf is not None and encode(cnf) != encode(expected_cnf):
        raise ValueError('Affine-clause proof belongs to another exact source')
    affine = proof['affine']; summary = check_affine(cnf, affine, counts)
    if summary['leftover_clauses'] > 1: raise ValueError('More than one leftover clause')
    d = proof['decision']
    if type(d) is not dict or 'kind' not in d: raise ValueError('Missing affine decision')
    if d['kind'] == 'linear_conflict':
        if set(d) != {'kind', 'row'} or type(d['row']) is not int or not 0 <= d['row'] < len(affine['reductions']):
            raise ValueError('Invalid conflict row')
        row = affine['reductions'][d['row']]
        if row['mask'] != 0 or row['rhs'] != 1: raise ValueError('Row is not a contradiction')
        return dict(sat=False, model=None, variables=n, rank=summary['rank'], leftover_clauses=summary['leftover_clauses'])
    if d['kind'] != 'space' or set(d) != {'kind', 'space', 'sat', 'repair', 'model'} or type(d['sat']) is not bool:
        raise ValueError('Invalid affine-space decision')
    check_space(n, affine, d['space'], counts)
    particular = d['space']['particular']; directions = d['space']['directions']; repair = d['repair']
    if d['sat']:
        if repair is not None and (type(repair) is not int or not 0 <= repair < len(directions)):
            raise ValueError('Invalid repairing direction')
        expected = particular if repair is None else particular ^ directions[repair]
        if type(d['model']) is not int or d['model'] != expected or not holds(cnf, model(expected, n)):
            raise ValueError('Affine repair does not satisfy the complete source')
        result_model = model(expected, n); counts['affine_clause_model_literals'] += sum(map(len, cnf))
    else:
        if d['model'] is not None or repair is not None or len(affine['leftovers']) != 1:
            raise ValueError('Missing falsified single-clause obstruction')
        clause = cnf[affine['leftovers'][0]]
        for lit in clause:
            bit = 1 << (abs(lit)-1)
            if bool(particular & bit) == (lit > 0) or any(vector & bit for vector in directions):
                raise ValueError('Clause has a compatible literal')
            counts['affine_clause_fixed_literal_checks'] += 1
        result_model = None
    counts['affine_clause_decisions_checked'] += 1
    return dict(sat=d['sat'], model=result_model, variables=n, rank=summary['rank'], leftover_clauses=summary['leftover_clauses'])


def record_key(record):
    return hashlib.sha256(encode(record).encode()).hexdigest()


def attach(h, routes, record, counts):
    if type(record) is not dict or set(record) != {'source', 'proof'} or type(record['source']) is not str:
        raise ValueError('Invalid affine family route')
    node = h._load(record['source'])
    if node is None: raise ValueError('Missing affine route source')
    result = check_certificate(record['proof'], expected_cnf=node['cnf'], counts=counts)
    item = (dict(kind='affine_clause', id=record_key(record)), [])
    if item not in routes.by_source[record['source']]: routes.by_source[record['source']].append(item)
    return result
