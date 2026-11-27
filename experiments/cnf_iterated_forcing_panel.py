"""Frozen unlabelled controls for repeated binary-forcing closure."""
import random
from experiments.cnf_fresh_seed_panel import parity_prism


def cascade(rounds,broken=False,opposed=False):
    """Each derived x exposes the next three-edge forcing path."""
    clauses=[]
    for i in range(rounds):
        x,a,b=3*i+1,3*i+2,3*i+3
        gate=[] if i==0 else [-(x-3)]
        clauses.extend([gate+[x,a],gate+[-a,b],gate+[-b,x]])
    if broken:clauses.remove(([] if rounds==1 else [-(3*rounds-5)])+[-(3*rounds),3*rounds-2])
    if opposed:clauses.append([-(3*rounds-2),3*rounds+1,3*rounds+2])
    return clauses


def panel():
    rng=random.Random(2711270903);rows=[];desc={}
    def three(n):return [[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(round(4.2*n))]
    def add(family,size,variant,source):
        variables=sorted({abs(l) for c in source for l in c});names=variables[:];rng.shuffle(names)
        rename={v:(7013+41*w)*rng.choice((-1,1)) for v,w in zip(variables,names)}
        cnf=[[(1 if l>0 else -1)*rename[abs(l)] for l in c] for c in source]
        for c in cnf:rng.shuffle(c)
        rng.shuffle(cnf);key=f'i{len(rows):02d}';rows.append(dict(id=key,source=cnf));desc[key]=dict(family=family,size=size,variant=variant)
    for n in (15,19,23):
        for i in range(2):add('random_three',n,str(i),three(n))
    for rounds in (2,4,6):
        core=three(3*rounds+3)
        add('forcing_cascade',rounds,'complete',core+cascade(rounds))
        add('forcing_cascade',rounds,'deleted_terminal_edge',core+cascade(rounds,broken=True))
    for r in (8,10,12):
        for odd in (False,True):add('parity_prism',3*r,'odd' if odd else 'even',parity_prism(r,odd))
    for rounds in (3,5,7):
        # Wide clauses force no initial units; after the chain, opposing the
        # last three x variables yields a conflict. A deleted edge is a SAT control.
        source=cascade(rounds)+[[-(3*rounds-2),-(3*rounds-5),-(3*rounds-8)]]
        add('guarded_chain',rounds,'opposed',source)
        add('guarded_chain',rounds,'deleted_middle_clause',source[:4]+source[5:])
    rng.shuffle(rows)
    for row in rows[:4]:
        key=row['id']+'r';rows.append(dict(id=key,source=[[(19*abs(l)+13)*(1 if l>0 else -1) for l in reversed(c)] for c in reversed(row['source'])]));desc[key]={**desc[row['id']],'repeat_of':row['id']}
    return rows,desc
