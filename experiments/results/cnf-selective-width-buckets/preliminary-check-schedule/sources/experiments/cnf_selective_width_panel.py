"""Frozen feedback controls: random CNFs, hidden pairs, deleted conflicts and parity."""
import random
from experiments.cnf_fresh_seed_panel import parity_prism


def hidden_pair(offset):
    x,y,a,b,c,d=range(offset+1,offset+7)
    return [[-x,-y,a],[-x,-y,b],[-a,-b,c],[-a,-b,d],[-c,-d]]


def panel():
    rng=random.Random(2711271519);rows=[];desc={}
    def three(n):return [[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(4.26*n))]
    def add(family,size,variant,source):
        vs=sorted({abs(l) for c in source for l in c});ns=vs[:];rng.shuffle(ns)
        rename={v:(37003+67*w)*rng.choice((-1,1)) for v,w in zip(vs,ns)}
        cnf=[[(1 if l>0 else -1)*rename[abs(l)] for l in c] for c in source]
        for c in cnf:rng.shuffle(c)
        rng.shuffle(cnf);key=f'w{len(rows):02d}';rows.append(dict(id=key,source=cnf));desc[key]=dict(family=family,size=size,variant=variant)
    for n in (32,40,48):
        for i in range(2):add('random_three',n,str(i),three(n))
    for n in (30,38,46):
        core=three(n);links=[[-(n+1),1,2],[-(n+2),-3,4]]
        add('hidden_binary',n,'complete',core+hidden_pair(n)+links)
        add('hidden_binary',n,'deleted_conflict',core+hidden_pair(n)[:-1]+links)
    for r in (13,15,17):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    rng.shuffle(rows)
    for r in rows[:4]:
        key=r['id']+'r';rows.append(dict(id=key,source=[[(31*abs(l)+19)*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(r['source'])]));desc[key]={**desc[r['id']],'repeat_of':r['id']}
    return rows,desc
