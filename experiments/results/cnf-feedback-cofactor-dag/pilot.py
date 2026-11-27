from pathlib import Path
from collections import Counter
import json,time,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import cnf_feedback_cofactor_dag as k
out=Path(__file__).resolve().parent;rows=json.loads((out/'development.json').read_text());report=[]
for row in rows:
 for depth,reuse in [(0,False),(2,False),(2,True)]:
  cc=Counter();t=time.perf_counter();r,history=k.discover(row['source'],cc,depth_limit=depth,reuse=reuse);elapsed=time.perf_counter()-t;k.validate(row['source'],r,Counter())
  item=dict(id=row['id'],depth=depth,reuse=reuse,status=r['status'],nodes=len(r['nodes']),seconds=elapsed,counts=dict(cc));report.append(item)
  print(json.dumps(item),flush=True)
  (out/f"{row['id']}-{depth}-{int(reuse)}.json").write_text(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')
(out/'pilot.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
