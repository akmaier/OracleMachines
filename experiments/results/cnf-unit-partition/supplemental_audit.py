"""Retained illustrative source and a search-order counterexample, without tuning."""
from collections import Counter
from itertools import product
from pathlib import Path
import random,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import cnf_unit_partition as e
from experiments.compare_cnf_unit_partition import load,write,binding
out=Path(__file__).parent
source=[[1],[-1,2],[-2]]
seed=dict(format=e.prior.previous.FORMAT,names=[1,2],values=[True,False])
counts=Counter();result=e.search(source,seed,counts)
assert result['diagnostic']['expanded']==1 and result['exclusion']
assert counts['unit_forced_keeps'] and counts['unit_forced_flips']
assert e.check_exclusion(source,result['exclusion'])['answer'] is False
example=dict(source=source,seed=seed,result=result,counts=dict(counts))
rng=random.Random(202611280305);regression=None
for index in range(1000):
    source=[[rng.choice((-1,1))*v for v in rng.sample(range(1,7),3)] for _ in range(rng.randrange(10,31))]
    seed=e.prior.proposal(source)
    a=e.prior.search(source,seed,len(seed['names']),node_limit=20000,record=True)
    b=e.search(source,seed)
    if b['diagnostic']['expanded']>a['diagnostic']['expanded']:
        truth=any(all(any(values[abs(v)-1]==(v>0) for v in c) for c in source) for values in product((False,True),repeat=6))
        assert bool(a['witness'])==bool(b['witness'])==truth
        if truth:
            e.prior.previous.check(source,a['witness']);e.prior.previous.check(source,b['witness'])
        else:
            e.prior.check_exclusion(source,a['exclusion']);e.check_exclusion(source,b['exclusion'])
        regression=dict(index=index,source=source,seed=seed,prior=a,propagated=b,truth=truth)
        break
write(out/'supplemental-examples.json',dict(keep_and_flip=example,ordering_regression=regression,searched=index+1,scope='Illustration and deliberately searched counterexample, not held-out coverage. Ordering comparison uses the prior full-support partition kernel, not the matched boundary/export baseline.'))
a=load(out/'semantic-audit-final.json');b=load(out/'semantic-audit-reproduced.json');assert a==b
write(out/'supplemental-checks.json',dict(passed=True,semantic_reproduction_equal=True,semantic=binding(out/'semantic-audit-reproduced.json'),examples=binding(out/'supplemental-examples.json'),queries=a['counts']['queries'],sat=a['counts']['sat_queries'],unsat=a['counts']['unsat_queries'],one_state_unknown=a['counts']['one_state_unknown'],guarded_sat_reuses=a['checked_reuses'],stale_sat_witnesses_rejected=a['invalidated_witnesses']))
print('Counterexample:', None if regression is None else (regression['index'],regression['prior']['diagnostic'],regression['propagated']['diagnostic']))
