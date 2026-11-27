"""Frozen controls for unit closure and shared post-closure residuals."""
import random
from experiments.cnf_fresh_seed_panel import parity_prism


def forced_guard(core,n):
    # Either guard value forces the other variable, leaving precisely core.
    s,x=n+1,n+2
    return [[s,x],[-s,-x]]+[c+guard for c in core for guard in ([s,-x],[-s,x])]


def panel():
    rng=random.Random(2711270542);rows=[];desc={}
    def random_three(n,planted=False):
        result=[]
        for _ in range(round(4.2*n)):
            c=[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)]
            if planted and all(l<0 for l in c):c[0]=-c[0]
            result.append(c)
        return result
    def add(family,size,variant,source):
        variables=sorted({abs(l) for c in source for l in c});names=variables[:];rng.shuffle(names)
        rename={v:(2503+29*w)*rng.choice((-1,1)) for v,w in zip(variables,names)}
        cnf=[[(1 if l>0 else -1)*rename[abs(l)] for l in c] for c in source]
        for c in cnf:rng.shuffle(c)
        rng.shuffle(cnf);key=f'u{len(rows):02d}';rows.append(dict(id=key,source=cnf));desc[key]=dict(family=family,size=size,variant=variant)
    for n in (12,15,19,23):
        for i in range(2):add('random_three',n,str(i),random_three(n))
    for n in (10,14,18):
        source=forced_guard(random_three(n),n)
        add('forced_guard',n,'complete',source)
        add('forced_guard',n,'delete_forcing_clause',source[1:])
    for r in (5,7,9):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    for n in (16,24):
        core=random_three(n,True)
        for positive in (False,True):add('conditioned_planted',n,str(positive),forced_guard(core+[[v if positive else -v] for v in range(1,5)],n))
    rng.shuffle(rows)
    for row in rows[:4]:
        key=row['id']+'r';rows.append(dict(id=key,source=[[(11*abs(l)+7)*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(row['source'])]));desc[key]={**desc[row['id']],'repeat_of':row['id']}
    return rows,desc
