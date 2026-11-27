"""Independent exhaustive source projection and reconstruction audit."""
from collections import Counter
from itertools import product,combinations
from pathlib import Path
import json,random,time
from experiments import cnf_bucket_continuation as k


def source_models(cnf):
    variables=sorted({abs(l) for c in cnf for l in c});result=[]
    for bits in product((False,True),repeat=len(variables)):
        model=dict(zip(variables,bits))
        if all(any(model[abs(l)]==(l>0) for l in c) for c in cnf):result.append(model)
    return result


def audit(cnf,proof,models,counts):
    # Reconstruct factors independently from the compact step records.
    factors=[]
    for clause in cnf:
        scope=sorted(abs(l) for l in clause);bits=0
        for row in range(1<<len(scope)):
            m={v:bool(row>>i&1) for i,v in enumerate(scope)}
            if any(m[abs(l)]==(l>0) for l in clause):bits|=1<<row
        factors.append(dict(scope=scope,bits=bits))
    active=set(range(len(factors)))
    for step in proof['steps']:
        active.difference_update(step['inputs']);active.add(len(factors));factors.append(dict(scope=step['scope'],bits=step['bits']))
    variables=sorted({v for i in active for v in factors[i]['scope']});expected={tuple(m[v] for v in variables) for m in models};actual=set()
    for values in product((False,True),repeat=len(variables)):
        m=dict(zip(variables,values));counts['factor_assignments']+=1
        if not all(factors[i]['bits']>>sum(int(m[v])<<j for j,v in enumerate(factors[i]['scope']))&1 for i in active):continue
        actual.add(values);full={v:False for c in cnf for v in map(abs,c)};full.update(m)
        for step in reversed(proof['steps']):
            boundary=sorted({v for i in step['inputs'] for v in factors[i]['scope']}-{step['variable']})
            row=sum(int(full[v])<<j for j,v in enumerate(boundary));full[step['variable']]=bool(step['choices']>>row&1)
        assert all(any(full[abs(l)]==(l>0) for l in c) for c in cnf);counts['reconstructed_models']+=1
    assert actual==expected


def main():
    rng=random.Random(2711271522);counts=Counter();records=[];began=time.perf_counter()
    for i in range(180):
        if i%2:
            n=rng.randrange(6,10);core=n-2
            source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,core+1),3)] for _ in range(4*core)]
            if i%30==1:
                n=6;source=[[v*sign for v,sign in zip(vs,signs)] for vs in combinations(range(1,5),3) for signs in product((-1,1),repeat=3)]
            source += [[1,n-1,n],[-1,-(n-1),n],[1,n-1,-n]]
        else:
            n=rng.randrange(4,9);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(3*n)]
        cnf,_=k.native.normalize(source);models=source_models(cnf);counts['sources']+=1;counts['source_assignments']+=1<<len({abs(l) for c in cnf for l in c})
        prefix,_=k.bucket.discover(cnf,bag_limit=3,work_limit=4096);audit(cnf,prefix,models,counts)
        record=dict(source=list(map(list,cnf)),prefix_status=prefix['status'])
        if prefix['status']=='unresolved':
            extension,diag,got=k.discover(cnf,prefix,mode='resume');restart=k.discover(cnf,prefix,mode='restart');assert (extension,diag,got)==restart
            combined={**prefix,'limits':{**prefix['limits'],'bag_limit':4},'steps':prefix['steps']+extension['steps'],'status':extension['status'],'model':extension['model']}
            audit(cnf,combined,models,counts);counts['continued']+=1;counts['reused_steps']+=len(prefix['steps']);counts['suffix_steps']+=len(extension['steps']);counts['continued_'+extension['status']]+=1
            if got['answer'] is not None:assert got['answer']==bool(models)
            record.update(status=extension['status'],prefix=prefix,extension=extension)
        records.append(record)
    assert counts['reused_steps']>0 and counts['continued_unsat']>0
    result=dict(passed=True,counts=dict(counts),seconds=time.perf_counter()-began,records=records,scope='Outside measured cost. Enumerate complete source models and each active-factor assignment; compare the exact existential projection and reconstruct every feasible active assignment through all old/new choices. Restart/resume records must match.')
    Path(__file__).with_name('semantic-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(counts)


if __name__=='__main__':main()
