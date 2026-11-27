"""Frozen symbolic preprocessing transfer inputs; descriptions are audit-only."""
import random
from experiments.cnf_fresh_seed_panel import parity_prism
from experiments.cnf_semantic_bucket_panel import repeated_gates


def panel():
    rng=random.Random(2711270440);rows=[];desc={}
    def random_three(n,planted=False):
        result=[]
        for _ in range(round(4.2*n)):
            c=[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)]
            if planted and all(l<0 for l in c):c[0]=-c[0]
            result.append(c)
        return result
    def guarded(core,n,levels):
        for v in range(n+1,n+levels+1):core=[c+[sign*v] for c in core for sign in (-1,1)]
        return core
    def add(family,size,variant,source):
        variables=sorted({abs(l) for c in source for l in c});names=variables[:];rng.shuffle(names)
        mapping={v:(1901+23*w)*rng.choice((-1,1)) for v,w in zip(variables,names)}
        cnf=[[(1 if l>0 else -1)*mapping[abs(l)] for l in c] for c in source]
        for c in cnf:rng.shuffle(c)
        rng.shuffle(cnf);key=f'y{len(rows):02d}';rows.append(dict(id=key,source=cnf));desc[key]=dict(family=family,size=size,variant=variant)
    for n in (11,14,18,22):
        for i in range(2):add('random_three',n,str(i),random_three(n))
    for n in (10,14,18):
        core=random_three(n)
        for levels in (1,2):add('guarded_core',n,str(levels),guarded(core,n,levels))
    for n in (10,14):
        core=guarded(random_three(n),n,2)
        add('edited_guard',n,'delete_one',core[:-1])
        edited=[c[:] for c in core];edited[-1][0]=-edited[-1][0]
        add('edited_guard',n,'flip_one',edited)
    for n in (14,22):
        core=random_three(n,True)
        for value in (False,True):add('planted_units',n,str(value),core+[[v if value else -v] for v in range(1,7)])
    for r in (4,6):
        source=parity_prism(r,True)+[[l+3*r if l>0 else l-3*r for l in c] for c in repeated_gates(3,True)]
        add('mixed_parity_gates',3*r,'bridge',source+[[-1,3*r+1]])
    rng.shuffle(rows)
    for row in rows[:4]:
        key=row['id']+'r';rows.append(dict(id=key,source=[[(7*abs(l)+5)*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(row['source'])]));desc[key]={**desc[row['id']],'repeat_of':row['id']}
    return rows,desc
