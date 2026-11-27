"""Independent full truth tables and mutated partial programs on a warmed bank."""
from collections import Counter
from copy import deepcopy
from itertools import product
from pathlib import Path
import random,time
from experiments import cnf_verified_operators as v
from experiments.compare_cnf_verified_operators import base
out=Path(__file__).parent


def program(source,pivot):
    cnf,_=v.native.normalize(source);ids=[i for i,c in enumerate(cnf) if pivot in map(abs,c)]
    if not ids:return None
    boundary=sorted({abs(x) for i in ids for x in cnf[i]}-{pivot});bits=choices=0
    for row in range(1<<len(boundary)):
        assignment={x:bool(row>>i&1) for i,x in enumerate(boundary)};feasible=[]
        for value in (False,True):
            assignment[pivot]=value
            if all(any(assignment[abs(l)]==(l>0) for l in cnf[i]) for i in ids):feasible.append(value)
        if feasible:bits|=1<<row;choices|=int(feasible[0])<<row
    # Full boundary support is valid even if some coordinates are inessential.
    return dict(format=v.FORMAT,cnf=list(map(list,cnf)),reduce=True,limits=dict(bag_limit=8,work_limit=262144),steps=[dict(variable=pivot,inputs=ids,scope=boundary,bits=bits,choices=choices)],status='unresolved',model=None)


def outcome(source,proof,bank,counts):
    try:return dict(accepted=True,result=v.check_certificate(source,proof,counts,session=bank))
    except ValueError:return dict(accepted=False)


def main():
    start=time.perf_counter();rng=random.Random(2711271658);bank=v.VerifiedOperators();counts=Counter();records=[]
    clauses=[[s*(i+1) for i,s in enumerate(signs) if s] for signs in product((-1,0,1),repeat=2)]
    sources=[[c for i,c in enumerate(clauses) if mask>>i&1] for mask in range(1<<len(clauses))]
    for _ in range(180):
        n=rng.randrange(3,7);sources.append([[x*rng.choice((-1,1)) for x in rng.sample(range(1,n+1),rng.randrange(1,min(n,3)+1))] for _ in range(3*n)])
    for index,source in enumerate(sources):
        canonical,_=v.native.normalize(source)
        for pivot in sorted({abs(l) for c in canonical for l in c}):
            proof=program(canonical,pivot);v.LEGACY_CHECK(canonical,proof);got=outcome(canonical,proof,bank,counts);assert got['accepted'];counts['valid_programs']+=1
            assert outcome(canonical,proof,bank,counts)['accepted'];counts['repeated_programs']+=1
            mutations=[]
            for field in ('bits','choices'):
                bad=deepcopy(proof);bad['steps'][0][field]^=1;mutations.append((field,bad))
            bad=deepcopy(proof);bad['steps'][0]['inputs']=bad['steps'][0]['inputs'][:-1];mutations.append(('missing-input',bad))
            bad=deepcopy(proof);bad['steps'][0]['scope'].append(999);mutations.append(('extra-coordinate',bad))
            bad=deepcopy(proof);bad['cnf'].append([999]);mutations.append(('wrong-source',bad))
            for kind,bad in mutations:
                try:v.LEGACY_CHECK(canonical,bad);expected=True
                except ValueError:expected=False
                actual=outcome(canonical,bad,bank,counts)['accepted'];assert expected==actual and not actual
                counts['rejected_'+kind]+=1
            records.append(dict(source_index=index,source=list(map(list,canonical)),pivot=pivot,proof=proof))
    counts['sources']=len(sources)
    base.write(out/'semantic-audit.json',dict(passed=True,counts=dict(counts),cache=bank.stats(),records=records,seconds=time.perf_counter()-start,scope='Separate from matched cost. Independently evaluate source clauses for every local pivot assignment; warm exact operator bank then mutate relation bits, choice bits, incident inputs, coordinates and source binding. Compare every rejection with the unchanged legacy checker. Explicit full boundary scope tests valid nonminimal support.'))
    print(dict(counts))


if __name__=='__main__':main()
