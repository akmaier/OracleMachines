#!/usr/bin/env python3
"""Independent truth and exact trace checks for watched propagation."""
from collections import Counter
from itertools import combinations,product
from pathlib import Path
from unittest.mock import patch
import random,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_watched_learning as e
from experiments.compare_cnf_boundary_transfer import write


def audit(out):
    counts=Counter();fresh=[];rng=random.Random(202611280810)
    c2=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2))];c3=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2),(0,3,-3))]
    inputs=[('two',[c for i,c in enumerate(c2) if m>>i&1]) for m in range(512)]
    inputs += [('three',list(cs)) for n in range(4) for cs in combinations(c3,n)]
    for i in range(256):
        names=rng.sample(range(11,1000),rng.randrange(5,11));source=[[rng.choice((-1,1))*v for v in rng.sample(names,rng.randrange(2,5))] for _ in range(rng.randrange(25,66))]
        source += [source[0],source[0]+[source[0][0]],[names[0],-names[0]]]
        if i%4==0:source.append([names[-1]])
        inputs.append(('fresh',source));fresh.append(source)
    for kind,source in inputs:
        counts[kind+'_inputs']+=1;names=sorted({abs(v) for c in source for v in c});assignments=list(product((False,True),repeat=len(names)))
        models=[dict(zip(names,vs)) for vs in assignments if all(any(dict(zip(names,vs))[abs(v)]==(v>0) for v in c) for c in source)]
        for vs in (assignments if kind=='two' else (assignments[0],assignments[-1])):
            seed=dict(format=e.prior.prior.previous.FORMAT,names=names,values=list(vs))
            for cap in (0,2,20000):
                reference=e.baseline.search(source,seed,node_limit=cap);c=Counter();candidate=e.search(source,seed,c,node_limit=cap);assert reference==candidate,(kind,source,seed,cap,reference,candidate)
                proof,diag=candidate;counts['trace_equalities']+=1;counts[proof['kind']]+=1
                counts['watch_moves']+=c['watch_moves'];counts['backjumps']+=c['learning_nonchronological_jumps'];counts['stale_candidates']+=c['watch_stale_candidates'];counts['learned_duplicates']+=c['learning_duplicate_clauses']
                with patch.object(e,'search',side_effect=AssertionError),patch.object(e.baseline,'search',side_effect=AssertionError):got=e.check_result(source,proof)['answer']
                if got is not None:assert got==bool(models)
                if cap==20000:assert got is not None
                for _,_,clause in proof['derivations']:
                    assert all(any(m[abs(v)]==(v>0) for v in clause) for m in models);counts['learned_semantics_checked']+=1
            if kind=='fresh':
                old=reference[0]
                for target in (source[1:],source+[[-1001,names[0]],[1001]]):
                    a=e.selective.solve(source,old,target);b=e.solve(source,old,target);assert a==b;counts['edited_trace_equalities']+=1
                    knowledge,_=e.selective.transport(source,old,target);assert b[0]['derivations'][:len(knowledge['derivations'])]==knowledge['derivations']
    write(out/'semantic-audit.json',dict(passed=True,counts=dict(counts),fresh_inputs=fresh,scope='All two-variable clause sets/all seeds; three-variable clause sets of at most three clauses/two seeds; 256 sparse signed duplicate/tautological mixtures/two seeds. Budgets 0,2,20000 compare complete proof objects and diagnostics. Independent truth tables check every answer and learned consequence. Fresh mixtures receive deletion/shared-variable-addition composition comparisons; repeated seeds/budgets/edits are not independent samples.'))


if __name__=='__main__':audit(Path(sys.argv[1]))
