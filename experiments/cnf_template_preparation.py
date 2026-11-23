"""Reuse one source-bound cofactor preparation during template publication.

The returned immutable preparation is descriptive, not a certificate accepted by
another publisher. Only this synchronous call constructs and publishes a proof;
the ordinary native verifier still checks the complete canonical target.
"""
from collections import Counter
from dataclasses import dataclass

from experiments.cnf_conditional_unit_support import fixed_pairs, match
from experiments.cnf_residual_dag import FORMAT, propagate, restrict


@dataclass(frozen=True, slots=True)
class PreparedQuery:
    source: tuple
    assignment: tuple
    target: tuple
    cnf: tuple
    names: tuple
    key: str


def prepare_and_publish(solver, source, template, context, counts=None):
    """Return (preparation, cached/template/None), with None requiring fallback.

    No caller-supplied canonical target or stale cross-query cache is trusted.
    Copying the source and validating the context are charged on every call,
    including cached roots and misses. Templates are checked once on a miss.
    """
    c = Counter() if counts is None else counts
    source = tuple(tuple(clause) for clause in source)
    c['preparation_copied_clauses'] += len(source)
    c['preparation_copied_literals'] += sum(map(len, source))
    fixed = fixed_pairs(context)
    c['preparation_assignment_pairs'] += len(fixed)
    target = restrict(source, fixed, c)
    local, names, key = solver._canonical(target)
    prepared = PreparedQuery(source, tuple(sorted(fixed.items())), target,
                             local, tuple(names), key)
    old = solver._read(key, local, purpose='conditional_query')
    if old is not None:
        return prepared, 'cached'
    if not match(source, template, c):
        return prepared, None
    assumptions = fixed_pairs(template['assumptions'])
    if any(fixed.get(v) != bit for v, bit in assumptions.items()):
        raise ValueError('Context does not extend template assumptions')
    if () in local:
        proof = dict(kind='empty')
    else:
        rename = {v: i + 1 for i, v in enumerate(names)}
        positions = {clause: i for i, clause in enumerate(local)}
        small = restrict(template['clauses'], fixed, c)
        ids = sorted({positions[tuple(sorted((1 if lit > 0 else -1)
                     * rename[abs(lit)] for lit in clause))] for clause in small})
        _, trace, conflict = propagate(tuple(local[i] for i in ids), c)
        if conflict is None:
            raise ValueError('Conditioned support did not refute by units')
        proof = dict(kind='units', trace=[[lit, ids[cid]] for lit, cid in trace],
                     conflict=ids[conflict])
    solver._store(key, dict(format=FORMAT, cnf=[list(clause) for clause in local],
                            answer=False, proof=proof))
    c['conditional_publications'] += 1
    c['shared_template_preparations'] += 1
    return prepared, 'template'
