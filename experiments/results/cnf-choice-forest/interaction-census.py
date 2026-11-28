#!/usr/bin/env python3
"""Post-freeze diagnosis of the five previously retained nonclique cases.

Independent source partition and cycle-rank computation; no solver/kernel calls.
Not used to select, tune, or omit any benchmark input or result.
"""
from itertools import combinations
from pathlib import Path
import hashlib
import json
import sys

base=Path(__file__).resolve().parent
rows=json.loads((base/'panel.json').read_text())
results=[]
for row in rows:
    if row['id'] not in ('e012','e013','e014','e015','e031'): continue
    clauses=sorted({tuple(sorted(set(c))) for c in row['source'] if not any(-v in c for v in c)})
    used=set(); demands=[]
    for c in sorted(clauses,key=lambda c:(-len(c),c)):
        names={abs(v) for v in c}
        if len(c)>=3 and not used.intersection(names): demands.append(c); used.update(names)
    owner={v:i for i,d in enumerate(demands) for v in d}; graph={i:set() for i in range(len(demands))}
    for c in clauses:
        if c in demands: continue
        assert len(c)==2 and all(-v in owner for v in c)
        a,b=(owner[-v] for v in c)
        if a!=b: graph[a].add(b); graph[b].add(a)
    def measure(cut):
        vertices=set(graph)-set(cut); edges=sum(len(graph[i]&vertices) for i in vertices)//2
        unseen=set(vertices); components=[]
        while unseen:
            todo=[min(unseen)]; unseen.remove(todo[0]); size=0
            while todo:
                node=todo.pop(); size+=1; found=graph[node]&unseen; unseen-=found; todo+=sorted(found)
            components.append(size)
        return dict(vertices=len(vertices),edges=edges,components=len(components),largest_component=max(components,default=0),cycle_rank=edges-len(vertices)+len(components))
    best=[]
    for n in range(3):
        choices=[(measure(cut)['cycle_rank'],cut,measure(cut)) for cut in combinations(sorted(graph),n)]
        rank,cut,m=min(choices)
        best.append(dict(cutset_size=n,candidates=len(choices),minimum_cycle_rank=rank,witness=list(cut),remaining=m))
    results.append(dict(id=row['id'],demands=len(demands),base=measure([]),best_by_size=best))
assert len(results)==5
out=dict(scope='Exhaustive cuts of size 0, 1 and 2 for the fixed proposed demand description. Cycle rank is E-V+components, not runtime or treewidth. No statement about other descriptions or original Boolean model uniqueness.',
         panel_sha256=hashlib.sha256((base/'panel.json').read_bytes()).hexdigest(),
         script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),cases=results)
(base/(sys.argv[1] if len(sys.argv)>1 else 'interaction-census.json')).write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
