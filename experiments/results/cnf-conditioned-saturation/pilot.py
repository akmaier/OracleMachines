from collections import Counter
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_bootstrap
from experiments import compare_cnf_sliced_saturation as latest
s=latest.parent;k=s.kernel
out=Path(__file__).parent;cp=s.base.load(latest.PARENT.parent/'cnf-sliced-saturation'/'checkpoint.json')
rows=s.load_frontier(cp['sliced_saturation']['remaining']);results=[]
for row in rows:
 args=s.parent.prior.arguments(row,'strengthen');kw=s.parent.prior.options(row,'strengthen');search=s.old.bound(row['b13_strength_result']);cc=Counter();tick=time.perf_counter()
 p=s.compiler.feedback.prepare(*args,search,**kw,counts=cc);seed=p[29]
 fixed,_,conflict=k.native.propagate(seed,cc);assert conflict is None
 order=list(dict.fromkeys(abs(l) for l in k.frozen.roots(p[0]) if abs(l) not in fixed));trials=[]
 for v in order[:16]:
  arms=[]
  for lit in (-v,v):
   sc=Counter();start=time.perf_counter();result=k.discover((*seed,(lit,)),sc,order_source=p[0],round_limit=8)
   k.validate((*seed,(lit,)),result,Counter(),order_source=p[0]);arms.append(dict(literal=lit,result=result,counts=dict(sc),seconds=time.perf_counter()-start))
  trials.append(dict(pivot=v,arms=arms))
  if all(a['result']['status']=='refuted' for a in arms):break
 result=dict(target=row['target'],event=row['event'],seed=list(map(list,seed)),order_source=list(map(list,p[0])),args=args,options=kw,search=search,order=order,trials=trials,seconds=time.perf_counter()-tick)
 results.append(result);s.base.write(out/'pilot.json',dict(rows=results))
 print(s.base.encode(dict(target=row['target'],event=row['event'],pivots=len(trials),refuted_pair=any(all(a['result']['status']=='refuted' for a in r['arms']) for r in trials),failed_arms=sum(a['result']['status']=='refuted' for r in trials for a in r['arms']),seconds=result['seconds'])),flush=True)
