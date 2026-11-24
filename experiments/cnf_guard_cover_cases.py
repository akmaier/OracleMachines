"""Controlled wide-clause covers; deliberately provisioned origin templates."""
from collections import Counter
from experiments import cnf_residual_dag as native
from experiments.cnf_stopped_support import conditional_unit
from experiments.cnf_guard_interactions import local_hints


def family(width=3, rename=None, edit=None):
    if type(width) is not int or width < 3:
        raise ValueError('Width at least three required')
    mapping = rename or {v: v for v in range(1, 4*width+1)}
    assert set(mapping) == set(range(1, 4*width+1))
    assert {abs(v) for v in mapping.values()} == set(mapping)
    def transform(clause):
        return tuple(sorted(mapping[abs(l)] * (1 if l > 0 else -1) for l in clause))
    guards = [tuple(sorted((-v, sign*(v+width)))) for v in range(1, width+1) for sign in (-1, 1)]
    gadgets = [tuple(sorted(transform(cl+(sign*(2*width+i+1),)) for sign in (-1, 1))) for i, cl in enumerate(guards)]
    wide = transform(tuple(range(1, width+1)))
    source = tuple(sorted(tuple(cl for g in gadgets for cl in g)+(wide,)))
    templates = [conditional_unit(g, [[abs(l), l < 0] for l in transform(cl)], Counter()) for g, cl in zip(gadgets, guards)]
    if edit == 'delete_support':
        source = tuple(cl for cl in source if cl != gadgets[0][0])
    elif edit == 'delete_wide':
        source = tuple(cl for cl in source if cl != wide)
    elif edit == 'flip_wide':
        source = tuple(sorted(tuple(cl for cl in source if cl != wide)+(tuple(sorted((-wide[0],)+wide[1:])),)))
    elif edit is not None:
        raise ValueError('Unknown edit')
    assert native.normalize(source)[0] == source
    event = dict(root=native.token(source, Counter()), mapping=[[v, v] for v in sorted(mapping)], fixed=[])
    local, hints, whole = local_hints(source, templates, event, Counter())
    assert whole and local == source
    graph = sorted({tuple(h['clause']) for h in hints})
    model, proof = native.two_cnf(graph, Counter())
    assert model is not None and proof is None
    return source, templates, hints, graph, model
