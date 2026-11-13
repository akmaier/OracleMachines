from collections import Counter,defaultdict,deque
from pathlib import Path
import sys,tempfile,json,time
sys.path.insert(0,str(Path.cwd()))
from experiments.compare_cnf_trace_reuse import restore_checkpoint,read_archive
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_trace_reuse import source_attempts
from experiments.cnf_probe_learning import learning_batch,augment
from experiments.cnf_probe_equivalence import discover_equivalence_probes,check_equivalence_probes
p=Path('experiments/results/cnf-trace-reuse/report.json');result=[]
with tempfile.TemporaryDirectory() as td:
 tmp=Path(td);r,old=restore_checkpoint(p,tmp/'h',tmp);h=BudgetedInventory(tmp/'h',**r['options']);h.set_admission_budget(0)
 for row in read_archive(r['opportunities']):
  source=row['source'];cnf=h._load(source)['cnf'];a,refs=source_attempts(h,source,Counter());g=defaultdict(set)
  for c in cnf:
   if len(c)==2:g[-c[0]].add(c[1]);g[-c[1]].add(c[0])
  for attempt in a:
   x=attempt['variable']*(1 if attempt['value'] else -1)
   for l,_ in attempt['certificate']['units']:g[x].add(l);g[-l].add(-x)
  reach={}
  for x in sorted({s*abs(l) for c in cnf for l in c for s in (-1,1)}):
   seen=set();todo=[x]
   while todo:
    y=todo.pop()
    if y in seen:continue
    seen.add(y);todo.extend(g[y]-seen)
   reach[x]=seen
  forced=sorted(x for x in reach if -x in reach[x]);eq=sorted((x,y) for x in reach if x>0 for y in reach[x] if abs(y)>x and x in reach[y])
  batch=learning_batch(cnf,a,16,Counter());expanded=augment(cnf,batch)
  c=Counter();probes=discover_equivalence_probes(expanded,4,c);check_equivalence_probes(expanded,probes,4,Counter())
  result.append(dict(source=source,cases=row['cases'],forced=forced,equivalences=eq,batch=batch,augmented=probes,counts=dict(c)))
 h.close()
Path('/tmp/oraclemachines-graph-diagnostic.json').write_text(json.dumps(result))
print(json.dumps(dict(sources=len(result),graph_forced=[(x['cases'],x['forced']) for x in result if x['forced']],graph_eq=[(x['cases'],x['equivalences']) for x in result if x['equivalences']],augmented=Counter(x['augmented']['status'] for x in result),augmented_gains=[(x['cases'],x['augmented']['status']) for x in result if x['augmented']['status']!='clear'])))
