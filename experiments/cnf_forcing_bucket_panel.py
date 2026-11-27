"""Frozen controls for one-way binary forcing and shared path edges."""
import random
from experiments.cnf_fresh_seed_panel import parity_prism


def funnel(n,positive=False):
    starts=[-v if positive else v for v in range(1,n//3+1)];h=list(range(n+1,n+5))
    return [[-v,h[0]] for v in starts]+[[-a,b] for a,b in zip(h,h[1:])]+[[-h[-1],-v] for v in starts]


def panel():
    rng=random.Random(2711270747);rows=[];desc={}
    def random_three(n,planted=False):
        result=[]
        for _ in range(round(4.2*n)):
            c=[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)]
            if planted and all(l<0 for l in c):c[0]=-c[0]
            result.append(c)
        return result
    def add(family,size,variant,source):
        variables=sorted({abs(l) for c in source for l in c});names=variables[:];rng.shuffle(names)
        rename={v:(6007+37*w)*rng.choice((-1,1)) for v,w in zip(variables,names)}
        cnf=[[(1 if l>0 else -1)*rename[abs(l)] for l in c] for c in source]
        for c in cnf:rng.shuffle(c)
        rng.shuffle(cnf);key=f'w{len(rows):02d}';rows.append(dict(id=key,source=cnf));desc[key]=dict(family=family,size=size,variant=variant)
    for n in (14,18,22):
        for i in range(2):add('random_three',n,str(i),random_three(n))
    for n in (10,14,18):
        core=random_three(n);edges=funnel(n);broken=[c for c in edges if c!=[-n-2,n+3]]
        add('forcing_funnel',n,'complete',core+edges);add('forcing_funnel',n,'deleted_middle_edge',core+broken)
    for r in (7,9,11):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    for n in (11,15,19):
        source=random_three(n,True)+funnel(n,True)
        add('planted_forcing_funnel',n,'consistent',source);add('planted_forcing_funnel',n,'opposed_clause',source+[[-1,-2,-3]])
    rng.shuffle(rows)
    for row in rows[:4]:
        key=row['id']+'r';rows.append(dict(id=key,source=[[(17*abs(l)+11)*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(row['source'])]));desc[key]={**desc[row['id']],'repeat_of':row['id']}
    return rows,desc
