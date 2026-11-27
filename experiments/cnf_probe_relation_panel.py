"""Frozen nonfolding failure/alias mixtures; labels never guide acquisition."""
import random
from experiments.cnf_fresh_seed_panel import parity_prism


def failure(offset):
    x,a,b,c,d=range(offset+1,offset+6)
    return [[-x,a],[-x,b],[-a,-b,c],[-a,-b,d],[-c,-d]]


def panel():
    rng=random.Random(2711271112);rows=[];desc={}
    def three(n):return [[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(4.2*n))]
    def add(family,size,variant,source):
        vs=sorted({abs(l) for c in source for l in c});ns=vs[:];rng.shuffle(ns)
        rename={v:(9011+47*w)*rng.choice((-1,1)) for v,w in zip(vs,ns)}
        cnf=[[(1 if l>0 else -1)*rename[abs(l)] for l in c] for c in source]
        for c in cnf:rng.shuffle(c)
        rng.shuffle(cnf);key=f'g{len(rows):02d}';rows.append(dict(id=key,source=cnf));desc[key]=dict(family=family,size=size,variant=variant)
    for n in (18,23,28):
        for i in range(2):add('random_three',n,str(i),three(n))
    for n in (13,18,23):
        core=three(n);motif=failure(n)
        links=[[n+1,1,-2],[-(n+2),3,4]]
        add('nonfolding_failure',n,'complete',core+motif+links)
        add('nonfolding_failure',n,'deleted_conflict',core+motif[:-1]+links)
    for n in (12,17,22):
        core=three(n);x=n+1;u=n+6;v=n+7
        clauses=core+failure(n)+[[x,-u,v],[x,u,-v],[-u,1,2],[v,-3,4]]
        add('probe_exposed_alias',n,'complete',clauses)
        # Deleting one direction leaves an implication, not an equivalence.
        add('probe_exposed_alias',n,'deleted_direction',clauses[:len(core)+6]+clauses[len(core)+7:])
    for r in (9,11,13):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    rng.shuffle(rows)
    for r in rows[:4]:
        key=r['id']+'r';rows.append(dict(id=key,source=[[(31*abs(l)+19)*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(r['source'])]));desc[key]={**desc[r['id']],'repeat_of':r['id']}
    return rows,desc
