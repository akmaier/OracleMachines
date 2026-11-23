from pathlib import Path
import sys,json
sys.path.insert(0,str(Path.cwd()))
from collections import Counter,deque
from experiments import compare_cnf_partition_preparation as study
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_targeted_backbone import inspect_targeted_backbone
from experiments.cnf_binary_backbone import inspect_backbones
from experiments.cnf_residual_dag import normalize,two_cnf
spec=study.base.load(study.PARENT.parent/'cnf-partition-preparation/next-target.json')['branch_candidate']
cnf,names=normalize(spec['source']);ids=[i for i,c in enumerate(cnf) if len(c)==2];g={}
for i in ids:
    a,b=cnf[i];g.setdefault(-a,[]).append((b,i));g.setdefault(-b,[]).append((a,i))
paths={}
for v in sorted({abs(l) for c in cnf for l in c}):
    for root in (v,-v):
        par={root:None};q=deque([root])
        while q and -root not in par:
            for to,cid in g.get(q.popleft(),[]):
                if to not in par:par[to]=(cid,None);q.append(to)
        if -root in par:paths[root]=len(par)
print('forced false roots',paths)
print('cover clauses',[(i,c) for i,c in enumerate(cnf) if all(l in paths for l in c)])
for name,fn in [('original',inspect_targeted_backbone),('binary1',lambda c,n:discover(c,n,policy='binary1')),('total4',lambda c,n:discover(c,n,policy='total4')),('all-cover',lambda c,n:discover(c,n,policy='binary1',root_limit=10000)),('partials',inspect_backbones)]:
    counts=Counter();p,cover,parts=fn(cnf,counts);print(name,p,cover,parts,dict(counts))
print('clausehist',dict(Counter(map(len,cnf))))
