#!/usr/bin/env python3
"""A forced literal can expose binary conflict without covering any wide clause.

A separating example for the current recognizers, not a complete-solver failure,
new tractability claim or implemented iterative shortening policy.
"""
from collections import Counter
from itertools import product
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_guard_interactions import local_hints,binary_paths
from experiments.cnf_guard_clause_cover import discover
from experiments.cnf_guard_context_solver import ContextGuardClosureSolver
from experiments import compare_cnf_bootstrap as base


def evidence():
    guards=[(-1,2),(-2,-1)]
    gadgets=[tuple(sorted(tuple(sorted(cl+(sign*(i+3),))) for sign in (-1,1))) for i,cl in enumerate(guards)]
    wide=tuple(sorted(tuple(sorted((1,a*5,b*6))) for a,b in product((-1,1),repeat=2)))
    core=tuple(cl for g in gadgets for cl in g);source=tuple(sorted(core+wide))
    assert native.normalize(source)[0]==source
    templates=[conditional_unit(g,sorted([[abs(l),l<0] for l in cl]),Counter()) for g,cl in zip(gadgets,guards)]
    event=dict(root=native.token(source,Counter()),mapping=[[v,v] for v in range(1,7)],fixed=[])
    local,hints,whole=local_hints(source,templates,event,Counter());assert local==source and whole
    graph=sorted(tuple(h['clause']) for h in hints);model,proof=native.two_cnf(graph,Counter())
    assert proof is None and model is not None
    profile=binary_paths(graph,Counter());assert set(profile['paths'])=={-1}
    counts=Counter();assert discover(source,graph,model,counts) is None
    solver=ContextGuardClosureSolver(templates=templates)
    try:
        solver.guard_source=source;solver.closure_counts=Counter();solver.closure_records=None
        solver.guard_parents=[dict(cnf=source,mapping=dict(event['mapping']),fixed={})]
        assert solver._guard_closure(source) is None
    finally:solver.close()
    reduced,names=native.normalize(native.restrict_scan(source,{1:False},Counter()))
    reduced_model,reduced_proof=native.two_cnf(reduced,Counter());assert reduced_model is None and reduced_proof is not None
    cases=[]
    for mask in range(16):
        formula=tuple(sorted(core+tuple(cl for i,cl in enumerate(wide) if mask>>i&1)))
        models=[dict(enumerate(bits,1)) for bits in product((False,True),repeat=6) if native.holds(formula,dict(enumerate(bits,1)))]
        assert bool(models)==(mask!=15)
        cases.append(dict(wide_mask=mask,models=len(models)))
    return dict(source=source,templates=templates,hints=hints,graph=graph,graph_model=sorted([v,b] for v,b in model.items()),
        forced_literal=-1,path=profile['paths'][-1],cover_counts=dict(counts),conditioned_source=reduced,
        conditioned_names=names,binary_conflict=reduced_proof,truth_cases=cases,truth_assignments_checked=16*64,
        limitations=['The checked graph forces only not-x; no source clause is wholly excluded. Conditioning on not-x leaves all four binary sign patterns on y,z and is contradictory.',
                     'Templates are deliberately supplied. This motivates exact partial clause shortening with shared supports; it does not implement a live policy or show a speedup over ordinary solving.'])


if __name__=='__main__':
    base.write(Path(sys.argv[1]),dict(source=dict(path=__file__,sha256=base.sha(__file__)),evidence=evidence()))
