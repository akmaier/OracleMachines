from collections import Counter
import json,sys,time
sys.path.insert(0,'.')
from experiments import cnf_partition_repair as old
records=json.load(open('experiments/results/cnf-partition-repair/near-models.json'))['records']
for record in records:
 snap=[s for s in record['snapshots'] if s['expanded']<=10000][-1];source=old.previous.capacity.canonical(record['source'],Counter());names=record['seed']['names'];seed=dict(zip(names,snap['values']));bad=[c for c in source if not any(seed[abs(l)]==(l>0) for l in c)];selected={abs(l) for c in bad for l in c};budget=10000
 print('ID',record['id'],flush=True)
 for j in range(10):
  active=[c for c in source if not any(abs(l) not in selected and seed[abs(l)]==(l>0) for l in c)]
  local=old.previous.capacity.canonical([[l for l in c if abs(l) in selected] for c in active],Counter());ns=sorted({abs(l) for c in local for l in c});proposal=dict(format=old.previous.FORMAT,names=ns,values=[seed[v] for v in ns]);r=old.search(local,proposal,len(ns),node_limit=budget,record=True);budget-=r['diagnostic']['expanded'];print(j,len(selected),len(active),r['diagnostic'],flush=True)
  if r['witness'] or r['diagnostic']['reason']=='budget':break
  referenced=set()
  for node in r['exclusion']['nodes'].values():
   if 'clause' in node:referenced.add(node['clause'])
   elif 'blocked' in node:referenced.add(node['blocked'])
   else:referenced.update(node['packing'])
  parents={tuple(c):[] for c in local}
  for c in active:parents[tuple(l for l in c if abs(l) in selected)].append(c)
  before=len(selected);extra=set()
  for i in referenced:
   c=min(parents[local[i]],key=lambda c:(sum(abs(l) not in selected for l in c),c));extra.update(abs(l) for l in c)
  selected.update(extra)
  if len(selected)==before:break
