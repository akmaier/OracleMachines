"""Replay entailed clauses across a checked conditioning/projection path.

Each premise is proved on the original formula, before any clause is added.
Conditioning restricts the clause; existential projection retains it only if
every remaining variable survives. A disappearing literal is never just erased.
This is a portable positive fact, not a coverage plan or a SAT/UNSAT answer.
"""
from collections import Counter

from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.cnf_binary_paths import check_binary_paths
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_exhaustion import check_clear_attempts
from experiments.cnf_residual_dag import normalize, restrict
from experiments.cnf_simplification import check_simplification
from experiments.cnf_variable_elimination import _source

FORMAT = 'source-lemma-transport-v1'


def formula(cnf, counts):
    if type(cnf) is not list or any(type(c) is not list for c in cnf):
        raise ValueError('Expected an explicit CNF')
    _source(cnf, counts)


def source_lemmas(cnf, attempts, lemmas, counts):
    """Check conditional units, without trusting a learning-policy verdict."""
    formula(cnf, counts)
    if type(attempts) is not list or type(lemmas) is not list:
        raise ValueError('Invalid lemma evidence')
    if len({encode(a) for a in attempts}) != len(attempts):
        raise ValueError('Duplicate source trace')
    check_clear_attempts(cnf, attempts, counts)
    used = set(); seen = set(); result = []
    for item in lemmas:
        if (type(item) is not dict or set(item) != {'attempt', 'unit', 'clause'}
                or type(item['attempt']) is not int or not 0 <= item['attempt'] < len(attempts)
                or type(item['unit']) is not int):
            raise ValueError('Invalid lemma reason')
        attempt = attempts[item['attempt']]; units = attempt['certificate']['units']
        if not 0 <= item['unit'] < len(units):
            raise ValueError('Missing conditional unit')
        x = attempt['variable'] * (1 if attempt['value'] else -1)
        lit = units[item['unit']][0]; clause = tuple(sorted((-x, lit)))
        if (abs(x) == abs(lit) or encode(item['clause']) != encode(clause)
                or clause in seen):
            raise ValueError('Unproved or duplicate source lemma')
        used.add(item['attempt']); seen.add(clause); result.append(clause)
        counts['transport_source_lemmas'] += 1
    if used != set(range(len(attempts))):
        raise ValueError('Unused source trace')
    return result


def check_certificate(certificate, *, expected_source=None, expected_target=None, counts=None):
    counts = Counter() if counts is None else counts
    if (type(certificate) is not dict
            or set(certificate) != {'format', 'source', 'attempts', 'lemmas', 'steps'}
            or certificate['format'] != FORMAT or type(certificate['steps']) is not list):
        raise ValueError('Invalid transport certificate')
    current = certificate['source']
    if expected_source is not None and encode(current) != encode(expected_source):
        raise ValueError('Transport evidence belongs to another source')
    clauses = source_lemmas(current, certificate['attempts'], certificate['lemmas'], counts)
    active = [(i, c) for i, c in enumerate(clauses)]; transcript = []
    for step in certificate['steps']:
        if type(step) is not dict or 'kind' not in step:
            raise ValueError('Missing transport step kind')
        common = {'kind', 'names', 'target'}; kind = step['kind']; fixed = {}
        if kind == 'condition':
            if set(step) != common | {'attempt'}:
                raise ValueError('Invalid conditioning fields')
            attempt = step['attempt']; check_clear_attempts(current, [attempt], counts)
            fixed = {attempt['variable']: attempt['value']}
            raw, closure = check_simplification(restrict(current, fixed, counts),
                attempt['certificate'], counts, pure=False)
            fixed.update(closure)
        elif kind == 'eliminate':
            if set(step) != common | {'certificate', 'pair_limit', 'clause_growth_limit'}:
                raise ValueError('Invalid projection fields')
            raw = check_additive_elimination(current, step['certificate'], counts,
                pair_limit=step['pair_limit'], clause_growth_limit=step['clause_growth_limit'])
            if raw is None:
                raise ValueError('Projection requires an eliminated variable')
        elif kind == 'binary_paths':
            if set(step) != common | {'certificate', 'root_limit'}:
                raise ValueError('Invalid binary-path fields')
            raw = check_binary_paths(current, step['certificate'], counts, root_limit=step['root_limit'])
        else:
            raise ValueError('Unsupported transport step')
        target, names = normalize(raw, counts)
        formula(step['target'], counts)
        if encode(step['names']) != encode(names) or encode(step['target']) != encode(target):
            raise ValueError('Incorrect target formula or variable binding')
        rename = {v: i for i, v in enumerate(names, 1)}
        retained = []; satisfied = []; lost = []
        for index, clause in active:
            counts['transport_clause_literals'] += len(clause)
            if any(abs(l) in fixed and fixed[abs(l)] == (l > 0) for l in clause):
                satisfied.append(index); continue
            residual = tuple(l for l in clause if abs(l) not in fixed)
            if any(abs(l) not in rename for l in residual):
                lost.append(index); continue
            mapped = tuple(sorted(rename[abs(l)] * (1 if l > 0 else -1) for l in residual))
            retained.append((index, mapped))
        transcript.append(dict(kind=kind, satisfied=satisfied, lost_support=lost,
            retained=[i for i, _ in retained]))
        active = retained; current = [list(c) for c in target]
        counts['transport_checked_steps'] += 1
    if expected_target is not None and encode(current) != encode(expected_target):
        raise ValueError('Transport evidence belongs to another target')
    explicit = {tuple(sorted(c)) for c in current}
    survivors = sorted({c for _, c in active})
    additions = [c for c in survivors if c not in explicit]
    return dict(target=current, survivors=[list(c) for c in survivors],
        additions=[list(c) for c in additions], transcript=transcript)


def checked_augmentation(certificate, target, counts=None):
    """Bind to the actual expansion leaf before appending any retained lemma."""
    result = check_certificate(certificate, expected_target=target, counts=counts)
    return tuple(tuple(c) for c in target) + tuple(tuple(c) for c in result['additions'])
