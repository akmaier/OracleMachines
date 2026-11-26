from collections import Counter
from pathlib import Path
import cProfile,json,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import cnf_iterated_cross_pivot as k
from experiments.cnf_fresh_seed_panel import truth
out=Path(__file__).resolve().parent
rows=json.loads((out/'panel.json').read_text());results=[]
def run():
 for row in rows:
  cc=Counter();start=time.perf_counter();chain,search=k.discover(row['source'],cc);seconds=time.perf_counter()-start
  k.validate(row['source'],chain,Counter());oracle=truth(row['source']);assert chain['status']!='refuted' or not oracle['answer']
  results.append(dict(id=row['id'],status=chain['status'],reason=chain['reason'],seconds=seconds,counts=dict(cc),truth=oracle))
  (out/(row['id']+'-chain.json')).write_text(json.dumps(chain,sort_keys=True,separators=(',',':'))+'\n')
  print(row['id'],chain['status'],oracle['answer'],round(seconds,4),flush=True)
cProfile.run('run()',str(out/'baseline.pstats'))
(out/'baseline.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
print(Counter((x['status'],x['truth']['answer']) for x in results))
