#!/usr/bin/env python3
"""Truth-table audit of exact conditioning, incremental reuse and checked repair."""
from collections import Counter
from itertools import product
from pathlib import Path
import json,random,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_boundary_repair as e


def audit():
    counts=Counter(); fresh=[]; rng=random.Random(202611280102)
    universe=[list(lit for lit in pair if lit) for pair in product((0,1,-1),(0,2,-2))]
    inputs=[('exhaustive', [c for i,c in enumerate(universe) if mask>>i&1]) for mask in range(1<<len(universe))]
    for _ in range(64):
        names=rng.sample(range(7,900),rng.randrange(3,7)); source=[]
        for _ in range(rng.randrange(3,19)):
            c=[rng.choice((-1,1))*v for v in rng.sample(names,rng.randrange(1,min(4,len(names))+1))]
            source.append(c)
        source += [source[0], source[0]+[source[0][0]], [names[0],-names[0]]]
        inputs.append(('fresh',source));fresh.append(source)
    for kind,source in inputs:
        counts[kind+'_inputs']+=1; names=sorted({abs(v) for c in source for v in c})
        assignments=[dict(zip(names,vs)) for vs in product((False,True),repeat=len(names))]
        truth=lambda m:all(any(m[abs(v)]==(v>0) for v in c) for c in source)
        initials=assignments if kind=='exhaustive' else [assignments[0],assignments[-1]]
        subsets=[sorted(v for j,v in enumerate(names) if mask>>j&1) for mask in range(1<<len(names))] if kind=='exhaustive' else [[],names[:len(names)//2],names]
        for model in initials:
            seed=dict(format=e.previous.FORMAT,names=names,values=[model[v] for v in names])
            index=e.ConditionalIndex(source,seed)
            for k in range(len(names)+1):
                index.extend(names[:k]);assert index.snapshot()==e.cofactor(source,seed,names[:k]);counts['incremental_snapshots']+=1
            for selected in subsets:
                local,_=e.cofactor(source,seed,selected);s=e.local_seed(local,seed)
                result=e.previous_search.search(local,s,len(s['names']),record=True)
                feasible=any(truth(m) and all(m[v]==model[v] for v in names if v not in selected) for m in assignments)
                assert (result['witness'] is not None)==feasible;counts['conditional_queries']+=1
                if feasible:
                    lifted=dict(model);lifted.update(zip(result['witness']['names'],result['witness']['values']))
                    witness=dict(format=e.previous.FORMAT,names=names,values=[lifted[v] for v in names])
                    assert e.previous.check(source,witness)['answer'];counts['sat_contexts']+=1
                else:
                    proof=dict(format=e.CONDITIONAL,seed=seed,selected=selected,proof=result['exclusion'])
                    assert e.check_conditional(source,proof)==dict(outside_context_excluded=True);counts['excluded_contexts']+=1
        for cap in (1,8,100):
            got=e.repair(source,node_limit=cap,prefix_limit=cap//2)
            assert got['diagnostic']['expanded']<=cap;e.check_evidence(source,got['evidence']);counts['bounded_runs']+=1
            if got['witness']:assert e.previous.check(source,got['witness'])['answer'];counts['bounded_sat']+=1
    return dict(passed=True,counts=dict(counts),fresh_inputs=fresh,scope='All 512 subsets of the nine canonical clauses on two named variables; all actual-support seeds/free sets. 64 fresh sparse signed edited inputs use two seeds and three free sets. Truth assignments stay outside discovery.')


if __name__=='__main__':Path(sys.argv[1]).write_text(json.dumps(audit(),indent=2,sort_keys=True)+'\n')
