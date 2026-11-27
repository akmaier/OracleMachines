"""Frozen mixed controls for binary relations after cofactor unit closure."""
import random
from experiments.cnf_fresh_seed_panel import parity_prism
from experiments.cnf_closed_bucket_panel import forced_guard


def panel():
    rng=random.Random(2711270641);rows=[];desc={}
    def random_three(n):
        return [[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(4.2*n))]
    def add(family,size,variant,source):
        variables=sorted({abs(l) for c in source for l in c});names=variables[:];rng.shuffle(names)
        rename={v:(4001+31*w)*rng.choice((-1,1)) for v,w in zip(variables,names)}
        cnf=[[(1 if l>0 else -1)*rename[abs(l)] for l in c] for c in source]
        for c in cnf:rng.shuffle(c)
        rng.shuffle(cnf);key=f'v{len(rows):02d}';rows.append(dict(id=key,source=cnf));desc[key]=dict(family=family,size=size,variant=variant)
    for n in (13,17,21):
        for i in range(2):add('random_three',n,str(i),random_three(n))
    for n in (9,13,17):
        core=random_three(n);aliases=[1]+[(-1 if i%2 else 1)*(n+i) for i in range(1,7)]
        spread=[[(rng.choice(aliases) if l>0 else -rng.choice(aliases)) if abs(l)==1 else l for l in c] for c in core]
        implications=[c for a in aliases[1:] for c in ([-1,a],[1,-a])]
        for edited in (False,True):add('signed_alias_guard',n,'delete_implication' if edited else 'complete',forced_guard(spread+(implications[1:] if edited else implications),n+6))
    for r in (6,8,10):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    for n in (10,14,18):
        wide=random_three(n);chain=[c for i in range(1,n) for c in ([-i,i+1],[i,-i-1])]
        for odd in (False,True):
            closing=[[n,1],[-n,-1]] if odd else [[-n,1],[n,-1]]
            add('binary_cycle_mixture',n,'inconsistent' if odd else 'consistent',wide+chain+closing)
    rng.shuffle(rows)
    for row in rows[:4]:
        key=row['id']+'r';rows.append(dict(id=key,source=[[(13*abs(l)+5)*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(row['source'])]));desc[key]={**desc[row['id']],'repeat_of':row['id']}
    return rows,desc
