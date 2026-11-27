"""Frozen controls for full-CNF failed-literal closure and shared indexes."""
import random
from experiments.cnf_fresh_seed_panel import parity_prism


def wide_failure(offset=0):
    x,a,b,c=[offset+i for i in range(1,5)]
    # Assuming x propagates a and b, then c and not c via wide clauses.
    return [[-x,a],[-x,b],[-a,-b,c],[-a,-b,-c]]


def panel():
    rng=random.Random(2711271005);rows=[];desc={}
    def three(n):return [[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(4.2*n))]
    def add(family,size,variant,source):
        vs=sorted({abs(l) for c in source for l in c});ns=vs[:];rng.shuffle(ns);rename={v:(8017+43*w)*rng.choice((-1,1)) for v,w in zip(vs,ns)}
        cnf=[[(1 if l>0 else -1)*rename[abs(l)] for l in c] for c in source]
        for c in cnf:rng.shuffle(c)
        rng.shuffle(cnf);key=f'f{len(rows):02d}';rows.append(dict(id=key,source=cnf));desc[key]=dict(family=family,size=size,variant=variant)
    for n in (16,20,24):
        for i in range(2):add('random_three',n,str(i),three(n))
    for n in (12,18,24):
        core=three(n);motifs=sum((wide_failure(j) for j in range(0,n-3,4)),[])
        add('wide_failed_mixture',n,'complete',core+motifs)
        add('wide_failed_mixture',n,'deleted_conflict_clause',core+motifs[:-1])
    for r in (9,11,13):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    for copies in (3,5,7):
        source=sum((wide_failure(4*j) for j in range(copies)),[])
        # Link modules by wide clauses; an opposing clause joins their forced values.
        source += [[4*j+1,-(4*(j+1)+1),4*j+4] for j in range(copies-1)]
        add('wide_modules',copies,'consistent',source)
        add('wide_modules',copies,'opposed',source+[[4*j+1 for j in range(copies)]])
    rng.shuffle(rows)
    for r in rows[:4]:
        key=r['id']+'r';rows.append(dict(id=key,source=[[(23*abs(l)+17)*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(r['source'])]));desc[key]={**desc[r['id']],'repeat_of':r['id']}
    return rows,desc
