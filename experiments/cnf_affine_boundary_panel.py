"""Frozen connected hidden-dimension controls and transfer cases; labels withheld."""
from itertools import product
import random
from experiments.cnf_fresh_seed_panel import cube, parity_prism


def parity(variables, rhs):
    return [[-v if b else v for v,b in zip(variables,bits)]
            for bits in product((0,1),repeat=len(variables)) if sum(bits)%2!=rhs]


def hidden_pairs(pairs, sat):
    # The seven-variable core has a unique all-false assignment before its bridge.
    core=cube(4)[1:]+[[l+4 if l>0 else l-4 for l in cl] for cl in cube(3)[1:]]
    core += [[1,-5 if sat else 5]]
    for i in range(pairs):core += parity((1,8+2*i,9+2*i),0)
    return core


def panel():
    rng=random.Random(2711270136);rows=[];descriptions={}
    def add(family,size,variant,raw):
        variables=sorted({abs(l) for c in raw for l in c});permuted=variables[:];rng.shuffle(permuted)
        mapping={v:(503+17*w)*rng.choice((-1,1)) for v,w in zip(variables,permuted)}
        source=[[(1 if l>0 else -1)*mapping[abs(l)] for l in c] for c in raw]
        for c in source:rng.shuffle(c)
        rng.shuffle(source);key=f'b{len(rows):02d}';rows.append(dict(id=key,source=source))
        descriptions[key]=dict(family=family,size=size,variant=variant)
    for k in (0,1,3,6):
        for sat in (False,True):add('connected_hidden_pairs',k,'positive' if sat else 'negative',hidden_pairs(k,sat))
    for r in (4,6,10):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    for n in (8,11,14):
        for i in range(2):add('random_three',n,str(i),[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(4.2*n))])
    # Destroy one complete parity half and add a clause crossing an internal pair.
    for k in (1,3,6):
        raw=hidden_pairs(k,True);add('crossing_edit',k,'added',raw+[[8,-9,2]])
    raw=parity_prism(6,True);add('parity_deletion',18,'first_clause_removed',raw[1:])
    rng.shuffle(rows)
    # Exact repetition is a separate stream stratum, not independent coverage.
    for row in rows[:4]:
        key=row['id']+'r';rows.append(dict(id=key,source=[[((abs(l)*2+1)*(1 if l>0 else -1)) for l in reversed(c)] for c in reversed(row['source'])]));descriptions[key]={**descriptions[row['id']], 'repeat_of':row['id']}
    return rows,descriptions
