from collections import Counter
import json,time,sys
sys.path.insert(0,'.')
from experiments import cnf_hamming_repair as old
rows=json.load(open('experiments/results/cnf-hamming-repair/constructed-inputs.json'))
for row in rows:
 source=row['source'];seed=old.proposal(source);cnf=old.previous.capacity.canonical(source,Counter());names=seed['names'];model=dict(zip(names,seed['values']));occ={v:[] for v in names}
 for i,c in enumerate(cnf):
  for v in c:occ[abs(v)].append((i,v>0))
 sat=[sum(model[abs(v)]==(v>0) for v in c) for c in cnf];bad={i for i,n in enumerate(sat) if not n};used=set();nodes=0;t=time.perf_counter();best=len(bad)
 def flip(v):
  model[v]=not model[v]
  for i,positive in occ[v]:
   sat[i]+=1 if model[v]==positive else -1
   if sat[i]:bad.discard(i)
   else:bad.add(i)
 def dfs(keep):
  global nodes,best
  if nodes==20000:return None
  nodes+=1;best=min(best,len(bad))
  if not bad:return model.copy()
  choices=sorted((len(a:={abs(v) for v in cnf[i]}-used-keep),tuple(sorted(a)),i) for i in bad)
  if not choices[0][0]:return None
  def gain(v):return sum((1 if sat[i]==0 else 0) if model[v]!=positive else (-1 if sat[i]==1 else 0) for i,positive in occ[v])
  local=set(keep)
  for v in sorted(choices[0][1],key=lambda v:(-gain(v),v)):
   used.add(v);flip(v);ans=dfs(local);flip(v);used.remove(v)
   if ans is not None:return ans
   if nodes==20000:return None
   local.add(v)
  return None
 ans=dfs(set());print(row['id'],bool(ans),nodes,best,round(time.perf_counter()-t,4),flush=True)
