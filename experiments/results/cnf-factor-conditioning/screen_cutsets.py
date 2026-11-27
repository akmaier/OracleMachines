"""Diagnostic static cutsets; no new root authority or matched timing claim."""
from pathlib import Path
from itertools import combinations,product
from collections import Counter
import json,time
from experiments import compare_cnf_factor_clause_width as s
out=Path(__file__).parent;parent=s.base.load('experiments/results/cnf-factor-refinement/panel.json');records=[]
for row in parent:
 _,cnf,names,factors,active,spent=s.f.checked_prefix(row['source'],row['prefix'],Counter())
 proof=s.base.load(Path('experiments/results/cnf-factor-refinement/clause4-0')/(row['id']+'.json'));s.f.check_prefix(row['source'],row['prefix'],proof)
 raw=[c for e in proof['entries'] for c in e['certificate']['clauses']];variables=sorted({abs(v) for c in raw for v in c});graph={v:set() for v in variables}
 for c in raw:
  for a,b in combinations(map(abs,c),2):graph[a].add(b);graph[b].add(a)
 chosen=[]
 for _ in range(4):
  v=min(graph,key=lambda v:(-len(graph[v]),v));chosen.append(v)
  for u in graph[v]:graph[u].discard(v)
  del graph[v]
 for depth in range(5):
  work=spent;branches=[];start=time.perf_counter()
  for values in product((False,True),repeat=depth):
   assignment=dict(zip(chosen[:depth],values));child=[ [l for l in c if abs(l) not in assignment] for c in raw if not any(assignment.get(abs(l))==(l>0) for l in c if abs(l) in assignment)]
   if work>=262144:branches.append(dict(values=values,status='unresolved',reason='global-budget'));continue
   p,d=s.continuation.bucket.discover(child,bag_limit=9,work_limit=262144-work);got=s.continuation.bucket.check_certificate(child,p);work+=d['spent']
   if got['model'] is not None:
    model={v:False for v in variables};model.update(got['model']);model.update(assignment);assert s.continuation.native.holds(raw,model);lifted=s.f.restore_prefix(cnf,names,row['prefix'],factors,model,s.continuation.bucket);assert s.continuation.native.holds(row['source'],lifted)
   branches.append(dict(values=values,status=p['status'],steps=len(p['steps']),diagnostic=d))
  rec=dict(id=row['id'],depth=depth,cutset=chosen[:depth],branches=branches,reserved_work=work,seconds=time.perf_counter()-start);records.append(rec);print(row['id'],depth,rec['cutset'],Counter(b['status'] for b in branches),work,flush=True)
s.base.write(out/'cutset-screen.json',dict(records=records,scope='Diagnostic from saved independently checked exact covers. Child bucket certificates checked and all discovered models restored through original prefix; no new full-root or matched total-cost claim. Selection is graph-degree only, label-blind.'))
