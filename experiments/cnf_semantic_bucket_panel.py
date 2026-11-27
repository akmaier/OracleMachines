"""Frozen non-affine bucket controls and transfer inputs, with hidden labels."""
import random
from experiments.cnf_fresh_seed_panel import parity_prism


def repeated_gates(size, linked):
    # Existentially eliminating z from z <-> (a and b) gives the true relation.
    cnf=[]
    for i in range(size):
        a,b,z=3*i+1,3*i+2,3*i+3
        cnf += [[-z,a],[-z,b],[z,-a,-b]]
        if linked and i:cnf += [[-(3*(i-1)+3),a]]
    return cnf


def panel():
    rng=random.Random(2711270235);rows=[];desc={}
    def add(family,size,variant,source):
        variables=sorted({abs(l) for c in source for l in c});names=variables[:];rng.shuffle(names)
        mapping={v:(997+13*w)*rng.choice((-1,1)) for v,w in zip(variables,names)}
        cnf=[[(1 if l>0 else -1)*mapping[abs(l)] for l in c] for c in source]
        for c in cnf:rng.shuffle(c)
        rng.shuffle(cnf);key=f's{len(rows):02d}';rows.append(dict(id=key,source=cnf));desc[key]=dict(family=family,size=size,variant=variant)
    for n in (9,12,16,20):
        for i in range(2):add('random_three',n,str(i),[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(4.2*n))])
    for n in (4,8,16):
        for linked in (False,True):add('and_gates',n,'linked' if linked else 'disjoint',repeated_gates(n,linked))
    for r in (3,5,7):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    # Equivalent complete small relations represented with redundant syntax.
    for n in (4,8):
        source=repeated_gates(n,True)
        add('edited_gates',n,'opposed_output',source+[[3],[-(3*n)]])
        add('edited_gates',n,'delete_definition',source[:-1]+[[3],[-(3*n)]])
    rng.shuffle(rows)
    for r in rows[:4]:
        key=r['id']+'r';rows.append(dict(id=key,source=[[((3*abs(l)+1)*(1 if l>0 else -1)) for l in reversed(c)] for c in reversed(r['source'])]));desc[key]={**desc[r['id']],'repeat_of':r['id']}
    return rows,desc
