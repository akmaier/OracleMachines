import json,time
p=json.load(open('experiments/results/cnf-choice-witness/gap-diagnostics.json'))['remaining_random']
s=p['source'];seed=p['rejected_candidates'][0]['candidate'];names=seed['names'];init=dict(zip(names,seed['values']))
occ={v:[] for v in names}
for i,c in enumerate(s):
 for l in c:occ[abs(l)].append((i,l>0))
for radius in (10,12,14,16,20,50):
 model=init.copy();sat=[sum(model[abs(l)]==(l>0) for l in c) for c in s];bad={i for i,n in enumerate(sat) if not n};used=set();seen=set();nodes=0;budget=100000;best=len(bad);t=time.perf_counter()
 def flip(v):
  model[v]=not model[v]
  for i,positive in occ[v]:
   sat[i]+=1 if model[v]==positive else -1
   if sat[i]:bad.discard(i)
   else:bad.add(i)
 def dfs():
  global nodes,best
  if nodes>=budget:return None
  key=frozenset(used)
  if key in seen:return None
  seen.add(key);nodes+=1;best=min(best,len(bad))
  if not bad:return model.copy()
  rem=radius-len(used)
  if rem<=0:return None
  candidates=sorted(({abs(l) for l in s[i]}-used for i in bad),key=lambda x:(len(x),tuple(sorted(x))))
  if not candidates[0]:return None
  packing=set();lower=0
  for cs in candidates:
   if not cs&packing:packing.update(cs);lower+=1
  if lower>rem:return None
  def gain(v):
   return sum((1 if sat[i]==0 else 0) if model[v]!=positive else (-1 if sat[i]==1 else 0) for i,positive in occ[v])
  for v in sorted(candidates[0],key=lambda v:(-gain(v),v)):
   used.add(v);flip(v);ans=dfs();flip(v);used.remove(v)
   if ans is not None:return ans
  return None
 ans=dfs();print(radius,nodes,best,time.perf_counter()-t, None if ans is None else sum(ans[v]!=init[v] for v in names),flush=True)
