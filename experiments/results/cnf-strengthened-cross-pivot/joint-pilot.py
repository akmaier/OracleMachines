from collections import Counter
from pathlib import Path
import sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_cross_pivot_feedback as s
out=Path('experiments/results/cnf-strengthened-cross-pivot');case=s.base.load(out/'pilot-case.json');summary=s.base.load(out/'pilot-summary.json');p=s.prior.seed(case,Counter());_,order,bank=s.joint.validate(p[29],summary,Counter(),order_source=p[0]);parts=s.base.load(out/'pilot-partitions.json')
cc=Counter();t=time.perf_counter();result=s.joint.collect(bank,parts,cc,order_source=order);small=s.joint.compact(bank,result,cc,order_source=order)
s.compact(out/'pilot-joint-full.json',result);s.compact(out/'pilot-joint-compact.json',small)
s.base.write(out/'joint-pilot.json',dict(seconds=time.perf_counter()-t,status=result['status'],lemmas=len(result['lemmas']),compact_lemmas=len(small['lemmas']),counts=dict(cc)))
print(s.base.encode(s.base.load(out/'joint-pilot.json')))
