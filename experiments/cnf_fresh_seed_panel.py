"""Deterministic new CNFs; descriptions are never supplied to discovery.

This is a small synthetic transfer panel, not a representative SAT distribution.
Freeze the emitted inputs before collecting results or changing the compiler.
"""
from itertools import product
import random


def cube(n):
    return [list(row) for row in product(*[(i,-i) for i in range(1,n+1)])]


def parity_prism(r,odd):
    if r==2:
        edges=[(a,b) for a in range(4) for b in range(a+1,4)]
    else:
        edges=sorted({tuple(sorted((i,(i+1)%r))) for i in range(r)} |
                     {tuple(sorted((r+i,r+(i+1)%r))) for i in range(r)} |
                     {(i,r+i) for i in range(r)})
    clauses=[]
    for vertex in range(2*r):
        variables=[i+1 for i,e in enumerate(edges) if vertex in e]
        for bits in product((0,1),repeat=len(variables)):
            if sum(bits)%2 != int(odd and vertex==0):
                clauses.append([v if not b else -v for v,b in zip(variables,bits)])
    return clauses


def panel():
    rng=random.Random(2611270027);rows=[];descriptions={}
    def add(family,size,variant,source):
        # Hide generator order and polarity while preserving exact truth.
        variables=sorted({abs(l) for cl in source for l in cl})
        names=variables[:];rng.shuffle(names)
        mapping={v:(100+7*name)*rng.choice((-1,1)) for v,name in zip(variables,names)}
        cnf=[[(1 if l>0 else -1)*mapping[abs(l)] for l in cl] for cl in source]
        for cl in cnf:rng.shuffle(cl)
        rng.shuffle(cnf)
        key=f'p{len(rows):02d}';rows.append(dict(id=key,source=cnf))
        descriptions[key]=dict(family=family,size=size,variant=variant)
    for n in (3,4,5):
        for edited in (False,True):add('clause_cube',n,'one_clause_deleted' if edited else 'full',cube(n)[int(edited):])
    for n in (6,9,12):
        for trial in range(2):
            source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(4.2*n))]
            add('random_3cnf',n,str(trial),source)
    for n in (6,9,12):
        source=[[-i,i+1] for i in range(1,n)]+[[-n,1],[1]]
        for edited in (False,True):add('signed_implication_cycle',n,'opposed_unit' if edited else 'base',source+([[-n//2]] if edited else []))
    for r in (2,3,4):
        for odd in (False,True):add('parity_prism',3*r,'odd_charge' if odd else 'even_charge',parity_prism(r,odd))
    for n in (3,4,5):
        core=cube(n)[1:];offset=[[l+n if l>0 else l-n for l in cl] for cl in cube(3)[1:]]
        for shared in (False,True):
            # Sharing the first coordinate creates interaction without labels.
            mapping=lambda l: ((1 if l>0 else -1) if abs(l)==n+1 else l)
            source=core+([[mapping(l) for l in cl] for cl in offset] if shared else offset)
            add('mixed_components',n+3-int(shared),'shared_coordinate' if shared else 'disjoint',source)
    # Adversarial bridges and single-literal edits of the mixtures.
    for n in (3,4,5):
        core=cube(n)[1:];other=[[l+n if l>0 else l-n for l in cl] for cl in cube(3)[1:]]
        for flip in (False,True):
            add('mixture_edit',n+3,'bridge_flip' if flip else 'bridge',core+other+[[1,-(n+1) if flip else n+1]])
    rng.shuffle(rows)
    return rows,descriptions


def truth(source):
    """Independent exhaustive oracle for this small panel, outside timed solving."""
    names=sorted({abs(l) for cl in source for l in cl})
    for bits in product((False,True),repeat=len(names)):
        model=dict(zip(names,bits))
        if all(any(model[abs(l)]==(l>0) for l in cl) for cl in source):
            return dict(answer=True,model=sorted(map(list,model.items())))
    return dict(answer=False,model=None)
