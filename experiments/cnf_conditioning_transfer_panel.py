"""Second synthetic transfer panel, frozen before conditioning development."""
import random
from experiments.cnf_fresh_seed_panel import cube,parity_prism,truth


def panel():
    rng=random.Random(2711270101);rows=[];descriptions={}
    def add(family,size,variant,source):
        variables=sorted({abs(l) for cl in source for l in cl});names=variables[:];rng.shuffle(names)
        mapping={v:(211+11*w)*rng.choice((-1,1)) for v,w in zip(variables,names)}
        cnf=[[(1 if l>0 else -1)*mapping[abs(l)] for l in cl] for cl in source]
        for cl in cnf:rng.shuffle(cl)
        rng.shuffle(cnf);key=f'h{len(rows):02d}';rows.append(dict(id=key,source=cnf))
        descriptions[key]=dict(family=family,size=size,variant=variant)
    for n in (4,5,6):
        for deleted in (False,True):add('clause_cube',n,'deleted' if deleted else 'full',cube(n)[int(deleted):])
    for r in (3,4,5):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    for n in (8,11,14):
        for i in range(2):
            add('random_3cnf',n,str(i),[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(4.2*n))])
    for n in (4,5,6):
        source=cube(n)[1:]+[[l+n if l>0 else l-n for l in cl] for cl in cube(3)[1:]]
        for flipped in (False,True):add('bridge_mixture',n+3,'flipped' if flipped else 'bridge',source+[[1,-(n+1) if flipped else n+1]])
    rng.shuffle(rows);return rows,descriptions
