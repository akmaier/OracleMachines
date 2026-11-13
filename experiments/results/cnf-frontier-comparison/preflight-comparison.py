from collections import Counter
from pathlib import Path
import json,tempfile,time
from experiments.continue_cnf_probe_split import restore_checkpoint,routes_for
from experiments.continue_cnf_original_splits import select
from experiments.compare_cnf_trace_reuse import archive_json
from experiments.compare_cnf_probe_continuation import sha
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_learning_batch import selection
from experiments.cnf_pattern_inventory import encode
r={};total=time.perf_counter()
with tempfile.TemporaryDirectory() as td:
 tmp=Path(td);path=tmp/'history';t=time.perf_counter();parent,*evidence=restore_checkpoint(Path('experiments/results/cnf-probe-split/report.json'),path,tmp);r['restore_seconds']=time.perf_counter()-t
 t=time.perf_counter();before=sha(path);h=BudgetedInventory(path,**parent['options']);h.set_admission_budget(0);routes=routes_for(h,evidence);roots=[h.inspect(c['source'])['root']['key'] for c in parent['cases']];assert compose(h,roots,routes,Counter())[0]==parent['final_closed'];r['preparation_seconds']=time.perf_counter()-t
 c=Counter();t=time.perf_counter();chosen=select(h,routes,evidence,roots,parent['final_closed'],c);r['selection_seconds']=time.perf_counter()-t;r['selection_counts']=dict(c);r['selection']=chosen;source=chosen['leaf']['source']
 rows=[row for row in selection(h,routes,Counter()) if row['source']==source and row['reason']=='ready'];assert len(rows)==1;r['learning_selection']=rows[0]
 c=Counter();t=time.perf_counter();record,target=routes.learned_blocks.advance(h,rows[0]['base_sha256'],c);r['learning_seconds']=time.perf_counter()-t;r['learning_counts']=dict(c);r['learning_record']=record
 print(json.dumps(dict(cases=chosen['leaf']['selected_original_cases'],ranks=[row['rank'] for row in chosen['ranked']],learning_status=record['probing']['status'],learned_attempts=[(a['variable'],a['value']) for a in record['probing']['attempts']],learning_target_variables=len({abs(l) for c in target for l in c}))),flush=True)
 assert not h.admitted;h.close();assert sha(path)==before
r['total_seconds']=time.perf_counter()-total
Path('/tmp/oracle-frontier-comparison.json').write_text(encode(r)+'\n')
