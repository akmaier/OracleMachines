#!/usr/bin/env python3
"""Truth, equivalence, admission and proof-preservation checks."""
from collections import Counter
from itertools import combinations,product
from pathlib import Path
from unittest.mock import patch
import random,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_admitted_learning as s
from experiments.audit_cnf_selective_learning import models


def expected(target,proof,limit):
    base=set(s.e.prior.canonical(target,Counter()));latest={}
    for i,entry in enumerate(proof['derivations']):
        clause=tuple(entry[2])
        if clause not in base:latest[clause]=i
    return [latest[c] for c in sorted(latest,key=lambda c:(len(c),-latest[c]))[:limit]]


def semantics(out):
    c2=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2))];c3=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2),(0,3,-3))]
    inputs=[('two',[c for i,c in enumerate(c2) if mask>>i&1]) for mask in range(512)]
    inputs += [('three',list(cs)) for n in range(4) for cs in combinations(c3,n)]
    rng=random.Random(202611280707);fresh=[];counts=Counter()
    for _ in range(128):
        names=rng.sample(range(11,1000),rng.randrange(4,8));source=[[rng.choice((-1,1))*v for v in rng.sample(names,rng.randrange(2,4))] for _ in range(rng.randrange(8,21))];source += [source[0],source[0]+[source[0][0]],[names[0],-names[0]]];inputs.append(('fresh',source));fresh.append(source)
    for kind,source in inputs:
        old,_=s.e.prior.prior.solve(source);base=s.e.prior.canonical(source,Counter());counts[kind+'_parents']+=1
        targets=[list(map(list,base[:i]+base[i+1:])) for i in range(len(base))] if kind=='two' else [[list(c) for c in base[1:]]]
        targets += [source+[[-1001,1003],[-1003]],[]]
        for target in targets:
            knowledge,_=s.e.prior.transport(source,old,target);truth=models(target);counts['targets']+=1
            for limit in (0,1,128):
                with patch.object(s.e.prior.prior,'search',side_effect=AssertionError):chosen=s.e.admit(target,knowledge,clause_limit=limit)
                assert chosen==expected(target,knowledge,limit);assert len(chosen)<=limit;counts['admission_checks']+=1
                augmented=target+[knowledge['derivations'][i][2] for i in chosen];assert models(augmented)==truth;counts['model_set_equalities']+=1
                result,diag=s.e.expand(target,knowledge,clause_limit=limit)
                assert result['derivations'][:len(knowledge['derivations'])]==knowledge['derivations']
                with patch.object(s.e,'expand',side_effect=AssertionError),patch.object(s.e.prior.prior,'search',side_effect=AssertionError):assert s.check(target,result)['answer']==bool(truth)
                counts[result['kind']]+=1
            bounded,_=s.e.expand(target,knowledge,node_limit=0);assert s.check(target,bounded)['answer']==(False if knowledge['kind']=='unsat' else None);counts['bounded_unknown']+=knowledge['kind']!='unsat'
    s.write(out/'semantic-audit.json',dict(passed=True,counts=dict(counts),fresh_inputs=fresh,scope='All two-variable clause sets/every single deletion, bounded three-variable sets and 128 fresh sparse mixtures. Budgets 0/1/128 each receive independent ranking, complete model-set equality, composed-answer and retained-prefix checks. All models are checked against original target clauses.'))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
