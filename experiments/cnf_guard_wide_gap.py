#!/usr/bin/env python3
"""A checked guard graph can be SAT while it excludes a wider source clause.

This is a separation example for recognizers, not an implemented cover policy
or evidence of an advantage over ordinary SAT search.
"""
from collections import Counter
from itertools import product
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_conditional_unit_support import check_template
from experiments.cnf_guard_closure_solver import transport_short
from experiments.cnf_guard_context_solver import ContextGuardClosureSolver
from experiments.cnf_binary_clause_cover import inspect
from experiments import compare_cnf_bootstrap as base


def evidence():
    guards=[tuple(sorted((-v,sign*(v+3)))) for v in (1,2,3) for sign in (-1,1)]
    gadgets=[tuple(sorted(tuple(sorted(cl+(sign*(i+7),))) for sign in (-1,1))) for i,cl in enumerate(guards)]
    source=tuple(sorted(tuple(cl for g in gadgets for cl in g)+((1,2,3),)))
    assert native.normalize(source)[0]==source
    templates=[conditional_unit(g,[[abs(l),l<0] for l in cl],Counter()) for g,cl in zip(gadgets,guards)]
    parent=dict(cnf=source,mapping={v:v for v in range(1,13)},fixed={})
    checks=Counter();hints=[]
    for t,cl in zip(templates,guards):
        assert check_template(t)<=set(source)
        h=transport_short(source,t,t['assumptions'],parent,checks)
        assert h is not None and tuple(h['clause'])==cl;hints.append(h)
    graph=sorted({tuple(h['clause']) for h in hints});model,proof=native.two_cnf(graph,Counter())
    assert proof is None and model is not None and native.holds(graph,model)
    assert not native.holds([(1,2,3)],model)
    paths=[]
    for v in (1,2,3):
        path=[[v+3,graph.index(tuple(sorted((-v,v+3))))],[-v,graph.index(tuple(sorted((-v,-v-3))))]]
        current=v
        for nxt,cid in path:assert graph[cid]==tuple(sorted((-current,nxt)));current=nxt
        assert current==-v;paths.append(dict(literal=v,path=path))
    assert inspect(source,Counter())==(None,None)
    solver=ContextGuardClosureSolver(templates=templates)
    try:
        solver.guard_source=source;solver.closure_counts=Counter();solver.closure_records=None;solver.guard_parents=[parent]
        assert solver._guard_closure(source) is None;gate=dict(solver.closure_counts)
        assert gate.get('context_preparations',0)==0
    finally:solver.close()
    assignments=0;models=0
    for bits in product((False,True),repeat=12):
        assignments+=1;models+=native.holds(source,dict(enumerate(bits,1)))
    assert assignments==4096 and models==0
    return dict(source=[list(cl) for cl in source],variables=12,clauses=13,templates=templates,hints=hints,
        graph=[list(cl) for cl in graph],graph_model=sorted([v,b] for v,b in model.items()),
        covered_source_clause=[1,2,3],paths=paths,truth_assignments_checked=assignments,models=models,
        current_guard_gate=gate,transport_checks=dict(checks),
        limitations=[
            'The current learned-guard SCC gate and original-binary cover recognizer both miss this source, although the whole CNF is UNSAT. No complete-solver failure or new complexity result is claimed.',
            'The six guard templates are deliberately supplied. Automatic acquisition and origin costs remain open.',
            'Each source-clause literal has a checked path to its negation in the augmented graph. Their supports must be compiled under strengthened branch contexts before a new native clause-cover policy can be used.',
            'Do not pass synthetic guard-edge indices to a native checker as if they indexed actual source clauses. No new live policy, runtime advantage or native authority records are produced here.'])


if __name__=='__main__':
    out=Path(sys.argv[1]);base.write(out,dict(source_implementation=dict(path=__file__,sha256=base.sha(__file__)),evidence=evidence()))
