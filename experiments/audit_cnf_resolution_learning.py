"""Exhaustive truth, learned-clause semantics and retained-panel checks."""
from collections import Counter
from itertools import combinations,product
from pathlib import Path
from unittest.mock import patch
import random,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import cnf_resolution_learning as e
from experiments.compare_cnf_linear_unit_proof import load,write


def audit():
    counts=Counter();fresh=[];rng=random.Random(202611280506)
    c2=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2))];c3=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2),(0,3,-3))]
    inputs=[('two',[c for i,c in enumerate(c2) if m>>i&1]) for m in range(512)]
    inputs += [('three',list(cs)) for n in range(4) for cs in combinations(c3,n)]
    for i in range(128):
        names=rng.sample(range(11,1000),rng.randrange(5,9));source=[]
        for _ in range(rng.randrange(15,37)):
            source.append([rng.choice((-1,1))*v for v in rng.sample(names,3 if i<64 else rng.randrange(2,5))])
        source += [source[0],source[0]+[source[0][0]],[names[0],-names[0]]];fresh.append(source);inputs.append(('fresh',source))
    for kind,source in inputs:
        counts[kind+'_inputs']+=1;names=sorted({abs(v) for c in source for v in c});assignments=list(product((False,True),repeat=len(names)))
        models=[dict(zip(names,vs)) for vs in assignments if all(any(dict(zip(names,vs))[abs(v)]==(v>0) for v in c) for c in source)]
        for vs in (assignments if kind=='two' else (assignments[0],assignments[-1])):
            seed=dict(format=e.prior.prior.previous.FORMAT,names=names,values=list(vs));p,d=e.search(source,seed);assert (p['kind']=='sat')==bool(models);counts['queries']+=1
            with patch.object(e,'search',side_effect=AssertionError),patch.object(e,'solve',side_effect=AssertionError):assert e.check_result(source,p)['answer']==bool(models)
            counts[p['kind']]+=1
            for entry in p['derivations']:
                assert all(any(m[abs(v)]==(v>0) for v in entry[2]) for m in models);counts['learned_semantics_checked']+=1;counts['satisfying_extensions_checked']+=len(models)
            limited,diag=e.search(source,seed,node_limit=2)
            if limited['kind']=='unknown':
                assert limited['conclusion'] is None and e.check_result(source,limited)['answer'] is None;counts['bounded_unknown']+=1
    retained={}
    for path in ('experiments/results/cnf-boundary-transfer/panel.json','experiments/results/cnf-hamming-repair/constructed-inputs.json'):
        records=[]
        for row in load(path):
            p,d=e.solve(row['source']);got=e.check_result(row['source'],p);assert got['answer'] is not None
            if 'constructed' in path:assert got['answer'] is True
            else:assert got['answer']==load('experiments/results/cnf-boundary-transfer/references/'+row['id']+'-z3.json')['result']['answer']
            records.append(dict(id=row['id'],kind=p['kind'],diagnostic=d))
        retained[path]=records
    return dict(passed=True,counts=dict(counts),fresh_inputs=fresh,retained=retained,scope='All two-variable clause sets/all seeds; bounded three-variable clause sets/two seeds; 128 fresh sparse signed duplicated/tautological mixtures/two seeds. Truth and every learned clause are checked by enumeration outside search. Prior panels remain separate.')


if __name__=='__main__':write(Path(sys.argv[1]),audit())
