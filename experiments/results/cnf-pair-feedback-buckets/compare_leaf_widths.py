"""Check whether width-nine opportunities already exist after only one pair batch."""
from collections import Counter
from pathlib import Path
import time
from experiments import compare_cnf_pair_feedback_buckets as s
base=s.base;k=s.k;old=s.old;out=Path(__file__).parent
records=[];summary=Counter();began=time.perf_counter();counts=Counter()
for row in base.load(out/'next-width-profile.json')['records']:
    current=old.bound(row['proof']);file=out/'base-0'/Path(row['proof']['path']).name;before=base.load(file)
    node=before['nodes'][row['node']];assert node['cnf']==current['nodes'][row['node']]['cnf']
    s.prior.k.check_certificate(before['cnf'],before,counts)
    final=node if node['refinement'] is None else node['refinement']['terminal']['nodes'][-1];cnf=tuple(map(tuple,final['cnf']))
    cc=Counter();start=time.perf_counter();cert,diag=k.bucket.discover(cnf,cc,**{**k.bucket.DEFAULTS,'bag_limit':9});got=k.bucket.check_certificate(cnf,cert,cc)
    if got['answer']:assert k.native.holds(cnf,got['model'])
    status=cert['status'];after=row['bucket-nine']['certificate']['status'];summary['one_round_'+status]+=1;summary['two_round_'+after]+=1;counts.update(cc)
    records.append(dict(id=row['id'],node=row['node'],one_round_proof=old.binding(file),two_round_proof=row['proof'],source=list(map(list,cnf)),certificate=cert,diagnostic=diag,counts=dict(cc),seconds=time.perf_counter()-start,two_round_status=after))
base.write(out/'leaf-width-comparison.json',dict(summary=dict(summary),records=records,counts=dict(counts),seconds=time.perf_counter()-began,scope='Post-hoc leaf-only width-nine comparison on the remaining feedback frontier. One-round opportunities must not be attributed to the second feedback round. Whole-root and total-cost comparisons are still required.'))
print(summary)
