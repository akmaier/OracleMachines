from collections import Counter
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_cross_pivot_feedback as s
out=Path('experiments/results/cnf-strengthened-cross-pivot');parent=Path('experiments/results/cnf-cross-pivot-feedback');p=s.base.load(parent/'protocol.json');case=s.old.bound(p['cases']['61-50']);summary=s.old.bound(p['records']['61-50']['compact']);k=s.joint.k
cc=Counter();t=time.perf_counter();prepared=s.prior.seed(case,cc);_,order,bank=s.joint.validate(prepared[29],summary,cc,order_source=prepared[0]);prep=time.perf_counter()-t
s.compact(out/'pilot-case.json',case);s.compact(out/'pilot-summary.json',summary)
rows=[]
for name,clauses in (('old',prepared[29]),('strengthened',bank)):
 counts=Counter();t=time.perf_counter();result=k.discover(clauses,counts,order_source=order);elapsed=time.perf_counter()-t;k.validate(clauses,result,Counter(),order_source=order)
 s.compact(out/f'pilot-{name}.json',result);record=dict(mode=name,status=result['status'],reason=result['reason'],rounds=len(result['rounds']),seconds=elapsed,counts=dict(counts));rows.append(record);print(s.base.encode({key:v for key,v in record.items() if key!='counts'}),flush=True)
 if name=='strengthened' and result['status']!='refuted':
  fixed,_,_=k.native.propagate(bank,Counter());pivots=list(dict.fromkeys(abs(l) for l in k.frozen.roots(order) if abs(l) not in fixed))[:16];trials=[]
  for pivot in pivots:
   counts=Counter();t=time.perf_counter();part=s.joint.conditioned.discover(bank,pivot,counts,order_source=order);elapsed=time.perf_counter()-t
   s.joint.conditioned.validate(bank,part,Counter(),order_source=order);trials.append(part);print(s.base.encode(dict(pivot=pivot,status=part['status'],low=part['low']['reason'],high=part['high']['reason'],seconds=elapsed)),flush=True)
   if part['status']=='refuted':break
  s.compact(out/'pilot-partitions.json',trials)
s.base.write(out/'pilot.json',dict(preparation_seconds=prep,preparation_counts=dict(cc),rows=rows))
