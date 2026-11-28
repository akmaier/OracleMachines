#!/usr/bin/env python3
"""Exhaustive and adversarial semantic audit of unit-closed partitions."""
from collections import Counter
from itertools import combinations,product
from pathlib import Path
from unittest.mock import patch
import random,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_unit_partition as e
from experiments.compare_cnf_boundary_transfer import load,write


def audit():
    counts=Counter();fresh=[];rng=random.Random(202611280305)
    clauses2=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2))]
    clauses3=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2),(0,3,-3))]
    inputs=[('two', [c for i,c in enumerate(clauses2) if mask>>i&1]) for mask in range(512)]
    inputs += [('three',list(cs)) for n in range(4) for cs in combinations(clauses3,n)]
    for _ in range(128):
        names=rng.sample(range(11,900),rng.randrange(3,8));source=[]
        for _ in range(rng.randrange(5,24)):
            source.append([rng.choice((-1,1))*v for v in rng.sample(names,rng.randrange(1,min(4,len(names))+1))])
        source += [source[0], source[0]+[source[0][0]],[names[0],-names[0]]]
        inputs.append(('fresh',source));fresh.append(source)
    reuses=invalidated=0
    for kind,source in inputs:
        counts[kind+'_inputs']+=1;names=sorted({abs(v) for c in source for v in c})
        assignments=list(product((False,True),repeat=len(names)))
        holds=lambda values:all(any(dict(zip(names,values))[abs(v)]==(v>0) for v in c) for c in source)
        truth=any(holds(values) for values in assignments)
        seeds=assignments if kind=='two' else (assignments[0],assignments[-1])
        for values in seeds:
            seed=dict(format=e.prior.previous.FORMAT,names=names,values=list(values));result=e.search(source,seed)
            assert (result['witness'] is not None)==truth;counts['queries']+=1
            if truth:assert e.prior.previous.check(source,result['witness'])['answer'];counts['sat_queries']+=1
            else:
                with patch.object(e,'search',side_effect=AssertionError('Discovery in checker')):
                    assert e.check_exclusion(source,result['exclusion'])==dict(answer=False,model=None)
                counts['unsat_queries']+=1
        bounded=e.discover(source,node_limit=1)
        if bounded['diagnostic']['reason']=='budget':assert bounded['witness'] is None and bounded['exclusion'] is None;counts['one_state_unknown']+=1
        if kind=='fresh' and truth:
            proof=result['witness'];v=proof['names'][0];value=proof['values'][0];lit=v if value else -v
            assert e.prior.previous.check(source+[[lit]],proof)['answer'];reuses+=1
            try:e.prior.previous.check(source+[[-lit]],proof)
            except ValueError:invalidated+=1
            else:raise AssertionError('Stale witness')
    # Recheck the earlier planted panel independently; truth witnesses are audit-only.
    constructed=[]
    for row in load('experiments/results/cnf-hamming-repair/constructed-inputs.json'):
        r=e.discover(row['source']);assert r['witness'] and e.prior.previous.check(row['source'],r['witness'])['answer']
        constructed.append(dict(id=row['id'],diagnostic=r['diagnostic']))
    return dict(passed=True,counts=dict(counts),fresh_inputs=fresh,checked_reuses=reuses,invalidated_witnesses=invalidated,constructed=constructed,scope='All 512 two-variable clause subsets with every seed; all three-variable CNFs with at most three distinct clauses with all-false/all-true seeds; 128 fresh sparse signed edited cases with two seeds. Truth stays outside discovery. Prior constructed panel remains separately denominated.')


if __name__=='__main__':write(Path(sys.argv[1]),audit())
