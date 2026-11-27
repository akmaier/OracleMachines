"""Frozen transfer panel for conditioning before complete bucket elimination."""
import random
from experiments.cnf_fresh_seed_panel import parity_prism
from experiments.cnf_semantic_bucket_panel import repeated_gates


def panel():
    rng=random.Random(2711270333);rows=[];desc={}
    def random_three(n):
        return [[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(4.2*n))]
    def add(family,size,variant,source):
        variables=sorted({abs(l) for c in source for l in c});names=variables[:];rng.shuffle(names)
        rename={v:(1231+19*w)*rng.choice((-1,1)) for v,w in zip(variables,names)}
        cnf=[[(1 if l>0 else -1)*rename[abs(l)] for l in c] for c in source]
        for c in cnf:rng.shuffle(c)
        rng.shuffle(cnf);key=f'c{len(rows):02d}';rows.append(dict(id=key,source=cnf));desc[key]=dict(family=family,size=size,variant=variant)
    for n in (10,13,17,21):
        for i in range(2):add('random_three',n,str(i),random_three(n))
    for n in (10,12,16):
        core=random_three(n);guard=n+1;twins=[c+[s*guard] for c in core for s in (-1,1)]
        add('guarded_twins',n,'complete',twins)
        add('guarded_twins',n,'delete_one_clause',twins[:-1])
    for r in (4,6,8):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    for n in (6,12):
        for oppose in (False,True):
            source=repeated_gates(n,True)+[[3]]
            if oppose:source += [[-(3*n)]]
            add('linked_gates',n,'opposed_output' if oppose else 'positive_output',source)
    rng.shuffle(rows)
    for r in rows[:4]:
        key=r['id']+'r';rows.append(dict(id=key,source=[[(5*abs(l)+3)*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(r['source'])]));desc[key]={**desc[r['id']],'repeat_of':r['id']}
    return rows,desc
