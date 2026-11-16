"""Controlled, distinct CNF preimages of saved joins; no new SAT inference rule.

Replace a clause A or B by (A or x) and (B or not x), with fresh x. Complete
elimination of x reconstructs the original clause. A paired edit removes a
different clause and therefore breaks that specified image. The production
solver receives only the resulting CNF, never the construction witness.
"""
from collections import Counter
import random
from experiments.cnf_variable_elimination import check_elimination


def parent_case(cnf, clause_index, variant, *, edited=False):
    clauses = [list(c) for c in cnf]
    if type(variant) is not int or not 0 <= variant < 3:
        raise ValueError('Expected one of three fixed variants')
    if len(clauses) < 2 or not 0 <= clause_index < len(clauses) or len(clauses[clause_index]) < 2:
        raise ValueError('Need a splittable clause and a distinct edit clause')
    n = max(abs(l) for c in clauses for l in c)
    fresh = (5, 10*(n//2)+5, 10*n+5)[variant]
    mapped = [[10*l for l in c] for c in clauses]
    original = mapped[clause_index]
    cut = 1 if variant != 2 else len(original)-1
    edit_index = (clause_index+1) % len(mapped)
    image = [c for i,c in enumerate(mapped) if not edited or i != edit_index]
    source = [c for i,c in enumerate(mapped) if i != clause_index and (not edited or i != edit_index)]
    source += [original[:cut]+[fresh], original[cut:]+[-fresh]]
    rng = random.Random(1009*clause_index+37*variant+int(edited))
    for clause in source:
        rng.shuffle(clause)
    rng.shuffle(source)
    return dict(source=source, witness_variable=fresh, expected_image=image,
                split_clause=clause_index, removed_clause=edit_index if edited else None)


def check_image(h, source, variable, expected_key, counts=None):
    counts = Counter() if counts is None else counts
    image = check_elimination(source, dict(variable=variable), counts,
                              pair_limit=h.config['elimination_pair_limit'])
    actual = h._canonical(image, 0)[2]
    if actual != expected_key:
        raise ValueError('Elimination image does not match the claimed saved join')
    return actual
