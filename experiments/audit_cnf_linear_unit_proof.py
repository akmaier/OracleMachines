"""Independent small-case truth and proof-conversion audit."""
from collections import Counter
from itertools import combinations,product
from pathlib import Path
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_linear_unit_proof as e
from experiments.compare_cnf_linear_unit_proof import load,write


def audit():
    counts=Counter();two=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2))]
    three=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2),(0,3,-3))]
    inputs=[('two',[c for i,c in enumerate(two) if m>>i&1]) for m in range(512)]
    inputs += [('three',list(cs)) for n in range(4) for cs in combinations(three,n)]
    inputs += [('edited',x) for x in load('experiments/results/cnf-unit-partition/semantic-audit-final.json')['fresh_inputs']]
    for kind,source in inputs:
        counts[kind+'_inputs']+=1;names=sorted({abs(v) for c in source for v in c});assignments=list(product((False,True),repeat=len(names)))
        truth=any(all(any(dict(zip(names,vs))[abs(v)]==(v>0) for v in c) for c in source) for vs in assignments)
        seeds=assignments if kind=='two' else (assignments[0],assignments[-1])
        for values in seeds:
            seed=dict(format=e.prior.prior.previous.FORMAT,names=names,values=list(values));r=e.prior.search(source,seed);counts['queries']+=1
            assert bool(r['witness'])==truth
            if truth:e.prior.prior.previous.check(source,r['witness']);counts['sat']+=1
            else:
                p=e.pack(source,r['exclusion']);reverse=dict(r['exclusion'],nodes=dict(reversed(list(r['exclusion']['nodes'].items()))));assert e.pack(source,reverse)==p
                with patch.object(e,'pack',side_effect=AssertionError),patch.object(e.prior,'search',side_effect=AssertionError),patch.object(e.prior,'check_exclusion',side_effect=AssertionError):
                    assert e.check_exclusion(source,p)==dict(answer=False,model=None)
                counts['unsat']+=1
                broken=dict(p,nodes=p['nodes'][:-1])
                try:e.check_exclusion(source,broken)
                except ValueError:counts['truncations_rejected']+=1
                else:raise AssertionError('Truncated proof accepted')
    return dict(passed=True,counts=dict(counts),scope='Every seed on all two-variable clause sets; two seeds on three-variable CNFs with at most three clauses and on the preserved 128 sparse edited sources. Truth is exhaustively evaluated outside discovery; conversion order and independent checking are verified.')


if __name__=='__main__':write(Path(sys.argv[1]),audit())
