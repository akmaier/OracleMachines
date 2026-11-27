"""Independent exhaustive and adversarial checks of signed-choice SAT proposals."""
from collections import Counter
from itertools import combinations, product
from pathlib import Path
from unittest.mock import patch
import json, random, time
from experiments import cnf_choice_witness as e
from experiments.audit_cnf_capacity_core import satisfiable, encode_domains


def audit(out):
    started=time.perf_counter();counts=Counter();missed=[];fresh=[]
    def inspect(source,category,retain=False):
        answer=satisfiable(source);proof,diag=e.discover(source)
        counts[category+'_inputs']+=1;counts[category+('_sat' if answer else '_unsat')]+=1
        if proof is not None:
            assert answer
            with patch.object(e.native,'solve_matching',side_effect=AssertionError('cold matching')):
                assert e.check(source,json.loads(json.dumps(proof)))['answer'] is True
            counts[category+'_certified']+=1
        for attempt in diag['attempts']:
            if attempt['strict_choice_class']:
                counts['strict_attempts']+=1
                if attempt['reason']!='matching-admission':
                    assert answer==(attempt['reason']=='checked-model')
        record=dict(source=source,satisfiable=answer,proof=proof,diagnostic=diag)
        if retain:fresh.append(record)
        if answer and proof is None and category.startswith('domain'):missed.append(record)
    for n,bound in ((2,9),(3,3)):
        clauses=[[s*v for v,s in enumerate(signs,1) if s] for signs in product((-1,0,1),repeat=n)]
        for k in range(bound+1):
            for source in combinations(clauses,k):inspect(list(source),'cnf'+str(n))
    for capacity in (2,3):
        for domains in product(range(1<<capacity),repeat=3):
            inspect(encode_domains(domains,capacity),'domain'+str(capacity))
    rng=random.Random(2711272155)
    for _ in range(1000):
        n=rng.randrange(1,7)
        source=[[rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),rng.randrange(1,n+1))] for _ in range(rng.randrange(1,20))]
        inspect(source,'random')
    for i in range(64):
        # New signed domain shapes and controlled source edits, all within
        # explicit truth-table reach. Never provide this metadata to discovery.
        source=encode_domains([rng.randrange(1,8) for _ in range(3)],3)
        if i%4==1:source.pop(rng.randrange(len(source)))
        if i%4==2:source[rng.randrange(len(source))][0]*=-1
        if i%4==3:source += [[1,-3,8],[-2,5]]
        names=sorted({abs(v) for c in source for v in c});ids=rng.sample(range(51,10000),len(names))
        mapping={v:ids[j]*rng.choice((-1,1)) for j,v in enumerate(names)}
        source=[[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in source];rng.shuffle(source)
        inspect(source,'fresh',True)
    nonclique=[[1,2,3],[4,5,6]]+[[-i,-(i+1)] for i in range(1,6)]
    inspect(nonclique,'nonclique',True)
    invalidated=0;reused=0
    for r in fresh:
        if r['proof'] is None:continue
        got=e.check(r['source'],r['proof']);v=next(iter(got['model']));literal=v if got['model'][v] else -v
        assert e.check(r['source']+[[literal]],r['proof'])['answer'];reused+=1
        try:e.check(r['source']+[[-literal]],r['proof'])
        except ValueError:invalidated+=1
        else:raise AssertionError('stale witness accepted')
    result=dict(passed=True,counts=dict(counts),fresh_records=fresh,missed_satisfiable_domains=missed,checked_reuses=reused,invalidated_witnesses=invalidated,seconds=time.perf_counter()-started,scope='Independent explicit truth tables, not matching, determine truth. Strict-class diagnostics are checked against truth; no-matching on noncliques is not UNSAT. Fixed fresh seed and policy; not representative generalization.')
    Path(out).mkdir(exist_ok=True);(Path(out)/'semantic-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(passed=True,counts=dict(counts),reuses=reused,invalidations=invalidated,missed_domains=len(missed))))


if __name__=='__main__':
    import sys
    audit(sys.argv[1])
