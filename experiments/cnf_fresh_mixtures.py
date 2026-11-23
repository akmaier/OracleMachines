"""Fresh fixed-seed larger mixtures, frozen before any solver observations.

Labels never enter search. No instance is selected or rejected by solver output.
The expansion cap bounds native acquisitions, not total work, memory or time.
"""
from itertools import product
import random,time

FAMILIES=('random-three','parity-bridge','gated-horn','graph-colouring','disjoint-mix','shared-mix')
SIZES=(36,60)
LIMIT=256
BUDGET_MESSAGE='Residual expansion budget exhausted; no verdict'


def generate(family,size,sample,*,seed=202611231956):
    if family not in FAMILIES or type(size) is not int or size<12 or size%6 or sample not in (0,1):
        raise ValueError('Invalid larger-mixture configuration')
    rng=random.Random(seed+104729*FAMILIES.index(family)+1009*size+97*sample)
    def clause(variables):return [v if rng.randrange(2) else -v for v in rng.sample(list(variables),3)]
    def random_three(variables):return [clause(variables) for _ in range(round(4.25*len(variables)))]
    def gated(variables):
        gate=variables[-1];out=[]
        for _ in range(2*len(variables)):
            a,b,c=rng.sample(variables[:-1],3);out.append([-a,-b,c,gate])
            a,b,c=rng.sample(variables[:-1],3);out.append([a,b,-c,-gate])
        out.extend([[variables[0],gate],[-variables[1],-gate]])
        return out
    variables=list(range(1,size+1))
    if family=='random-three':source=random_three(variables)
    elif family=='parity-bridge':
        source=[]
        for _ in range(size-2):
            support=rng.sample(variables,3);rhs=rng.randrange(2)
            source.extend([[-v if b else v for v,b in zip(support,bits)]
                           for bits in product((False,True),repeat=3) if sum(bits)%2!=rhs])
        source.extend(clause(variables) for _ in range(size//2))
    elif family=='gated-horn':source=gated(variables)
    elif family=='graph-colouring':
        vertices=size//3;source=[[3*v+c+1 for c in range(3)] for v in range(vertices)]
        source.extend([[-(3*v+a+1),-(3*v+b+1)] for v in range(vertices) for a in range(3) for b in range(a+1,3)])
        for v in range(vertices):
            for w in range(v+1,vertices):
                if rng.random()<(0.18,0.32)[sample]:source.extend([[-(3*v+c+1),-(3*w+c+1)] for c in range(3)])
    else:
        half=size//2;left=variables[:half]
        right=variables[half:] if family=='disjoint-mix' else [1,2]+variables[half:size-2]
        source=random_three(left)+gated(right)
    # Hide the construction's variable order without changing its support.
    labels=rng.sample(range(100,100+37*size),size)
    source=[[labels[abs(l)-1]*(1 if l>0 else -1) for l in c] for c in source]
    for c in source:rng.shuffle(c)
    rng.shuffle(source)
    # A fixed edit deletes one clause and adds one signed width-three clause.
    # In disjoint-mix it explicitly bridges the two originally disjoint supports.
    if family=='disjoint-mix':selected=[labels[0],labels[size//2],labels[-1]]
    else:selected=rng.sample(sorted({abs(l) for c in source for l in c}),3)
    edited=[list(c) for c in source[1:]]+[[v if rng.randrange(2) else -v for v in selected]]
    # Monotone relabeling and order reversal preserve the exact canonical key.
    repeated=[[((2*abs(l)+1)*(1 if l>0 else -1)) for l in reversed(c)] for c in reversed(source)]
    return source,edited,repeated


def catalog():
    cases=[]
    for size in SIZES:
        for family in FAMILIES:
            for sample in (0,1):
                start=len(cases)
                for variant,source in zip(('base','edit','repeat'),generate(family,size,sample)):
                    cases.append(dict(case=len(cases),family=family,size=size,sample=sample,
                                      variant=variant,base_case=start,source=source))
    return cases


def attempt(solver,source):
    tick=time.perf_counter()
    try:result=solver.solve(source)
    except RuntimeError as error:
        if str(error)!=BUDGET_MESSAGE:raise
        return dict(status='unresolved',result=None,metrics=dict(solver.counts),
                    reason=BUDGET_MESSAGE,solve_seconds=time.perf_counter()-tick)
    return dict(status='sat' if result['answer'] else 'unsat',result=result,
                metrics=result['metrics'],reason=None,solve_seconds=time.perf_counter()-tick)
