"""Post-hoc next-step screen, excluded from matched acquisition and coverage."""
from collections import Counter
from pathlib import Path
import time
from experiments import compare_cnf_pair_feedback_buckets as s
base=s.base;k=s.k;old=s.old
out=Path(__file__).parent
counts=Counter();records=[];began=time.perf_counter();summary=Counter()
for row in base.load(out/'remaining-profile.json')['records']:
    cnf=tuple(map(tuple,row['source']));record=dict(id=row['id'],node=row['node'],proof=row['proof'],source=row['source']);summary['leaves']+=1
    for mode in ('repeat-preparation','bucket-nine'):
        start=time.perf_counter();cc=Counter()
        if mode=='repeat-preparation':
            p,d=k.prior.discover(cnf,cc,mode='restart',**{**k.prior.DEFAULTS,'depth_limit':0});got=k.prior.check_certificate(cnf,p,cc)
        else:
            p,d=k.bucket.discover(cnf,cc,**{**k.bucket.DEFAULTS,'bag_limit':9});got=k.bucket.check_certificate(cnf,p,cc)
        if got['answer']:assert k.native.holds(cnf,got['model'])
        summary[mode+'_'+p['status']]+=1;counts.update(cc);record[mode]=dict(certificate=p,diagnostic=d,counts=dict(cc),seconds=time.perf_counter()-start)
    records.append(record)
base.write(out/'next-width-profile.json',dict(summary=dict(summary),records=records,counts=dict(counts),seconds=time.perf_counter()-began,scope='Post-hoc leaf-only evidence on checked final residuals. No added root verdict, matched cost or production-policy claim. Compare unchanged width-eight preparation with a bare width-nine bucket; different scopes are explicitly charged.'))
print(summary)
