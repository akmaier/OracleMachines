from collections import Counter
import json,sys,time
sys.path.insert(0,'.')
from experiments import cnf_partition_repair as old
records=json.load(open('experiments/results/cnf-partition-repair/near-models.json'))['records']
for record in records:
 print('ID',record['id'],'trace',[(s['expanded'],len(s['false_original'])) for s in record['snapshots']],flush=True)
 snaps=[s for s in record['snapshots'] if s['expanded']<=10000]
 snap=snaps[-1];s=record['source'];names=record['seed']['names'];seed=dict(zip(names,snap['values']));bad=[c for c in s if not any(seed[abs(l)]==(l>0) for l in c)];selected={abs(l) for c in bad for l in c};budget=10000
 for round in range(4):
  active=[c for c in s if not any(abs(l) not in selected and seed[abs(l)]==(l>0) for l in c)]
  local=[[l for l in c if abs(l) in selected] for c in active];ns=sorted({abs(l) for c in local for l in c});proposal=dict(format=old.previous.FORMAT,names=ns,values=[seed[v] for v in ns]);t=time.perf_counter();r=old.search(local,proposal,len(ns),node_limit=budget,record=True);budget-=r['diagnostic']['expanded'];print(round,len(selected),len(active),r['diagnostic'],round if False else time.perf_counter()-t,flush=True)
  if r['witness']:break
  if r['diagnostic']['reason']=='budget':break
  selected.update(abs(l) for c in active for l in c)
