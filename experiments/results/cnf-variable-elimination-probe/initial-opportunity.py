from collections import Counter
import gzip,hashlib,json,sqlite3,tempfile,shutil,time
from pathlib import Path
from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.compare_cnf_retained_plans import sha
p=Path('experiments/results/cnf-prepared-probes-full/report.json');r=json.loads(p.read_text());old=next(x for x in r['results'] if x['mode']=='reuse')
leaves={};origins={};counts=Counter();start=time.perf_counter()
with tempfile.TemporaryDirectory() as tmp:
 dbpath=Path(tmp)/'a.db'
 with gzip.open(old['archive_path'],'rb') as src,dbpath.open('wb') as dst:shutil.copyfileobj(src,dst)
 assert sha(dbpath)==old['database_sha256']
 db=sqlite3.connect(f'file:{dbpath}?mode=ro',uri=True);h=PreparedProbeInventory(**r['options'])
 for i,row in enumerate(old['records']):
  if row['summary']['closed']:continue
  _,_,key=h._canonical(r['cases'][i]['source'],r['options']['max_depth'])
  assert hashlib.sha256(key.encode()).hexdigest()==row['root_sha256']
  stack=[key];seen=set();origins[i]=set()
  while stack:
   k=stack.pop()
   if k in seen:continue
   seen.add(k);n=json.loads(db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(k,)).fetchone()[0])
   if n['kind']=='unresolved':
    digest=hashlib.sha256(k.encode()).hexdigest();leaves[digest]=n['cnf'];origins[i].add(digest)
   elif n['kind']=='retained_plan':stack.append(n['reference'])
   elif n['kind']=='and':stack.extend(e['key'] for e in n['edges'])
   elif n['kind']=='or':stack.extend(e['key'] for e in n['alternatives'][n['selected']]['edges'])
   elif 'edge' in n:stack.append(n['edge']['key'])
 h.close();db.close()
rows=[]
for key,cnf in leaves.items():
 cs=[frozenset(c) for c in cnf];support=sorted({abs(l) for c in cs for l in c});candidates=[]
 for v in support:
  pos=[c-{v} for c in cs if v in c];neg=[c-{-v} for c in cs if -v in c];pairs=len(pos)*len(neg)
  counts['variables']+=1;counts['pair_count_'+str(min(pairs//16,10)*16)]+=1
  if pairs>64:counts['pair_budget_exceeded']+=1;continue
  keep={c for c in cs if v not in c and -v not in c};res=set()
  for a in pos:
   for b in neg:
    c=a|b
    if not any(-l in c for l in c):res.add(c)
  target=keep|res;dl=sum(map(len,target))-sum(map(len,cs));dm=len(target)-len(cs)
  candidates.append(dict(variable=v,pairs=pairs,added=len(res-keep),removed=len(pos)+len(neg),clause_delta=dm,literal_delta=dl))
 rows.append(dict(key_sha256=key,cnf=cnf,candidates=candidates,eligible=[x for x in candidates if x['clause_delta']<=0 and x['literal_delta']<=0]))
result=dict(input_report_sha256=sha(p),archive_sha256=old['database_sha256'],origins={str(k):sorted(v) for k,v in origins.items()},rows=rows,counts=dict(counts),seconds=time.perf_counter()-start)
Path('experiments/results/cnf-variable-elimination-probe/raw-opportunity.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
print('sources',len(origins),'leaves',len(rows),'lits',sum(sum(map(len,x['cnf'])) for x in rows),'eligible_leaves',sum(bool(x['eligible']) for x in rows),'variables',sum(len(x['eligible']) for x in rows),'counts',counts)
print('best',[(i,min(x['eligible'],key=lambda a:(a['literal_delta'],a['pairs'],a['variable']))) for i,x in enumerate(rows) if x['eligible']][:20])
