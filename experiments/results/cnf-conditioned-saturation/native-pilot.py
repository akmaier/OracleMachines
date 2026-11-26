from collections import Counter
from pathlib import Path
import tempfile,time,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_bootstrap
from experiments import compare_cnf_probe_saturation as s,cnf_conditioned_saturation as k,cnf_conditioned_saturation_native as c
out=Path(__file__).parent;r=next(r for r in s.base.load(out/'pilot.json')['rows'] if (r['target'],r['event'])==(28,17))
u=s.parent.prior;source,ts,refs,events=u.prior.inputs(s.old.bound(s.base.load(s.parent.PARENT/'protocol.json')['parent_protocol']),28);ref=next(ref for ref,_ in refs if ref['event']==17);cc=Counter();source,templates,tail=u.bind(source,ts,ref,events[17],cc)
case=dict(source=source,templates=templates,prefix=ref['program'],inputs=r['args'],options=r['options'],search=r['search'],root=ref['root'])
partition=k.discover(r['seed'],r['trials'][-1]['pivot'],Counter(),order_source=r['order_source']);assert partition['status']=='refuted';case['partition']=partition;s.parent.compact(out/'pilot-case.json',case)
cc=Counter();start=time.perf_counter()
with tempfile.TemporaryDirectory() as td:
 path=Path(td)/'db';solver=c.native.ResidualSolver(path)
 try:
  tick=time.perf_counter();root=c.compile_extension(solver,source,templates,ref['program'],*r['args'][2:],r['search'],partition=partition,counts=cc,**r['options']);solve=time.perf_counter()-tick;tables=s.old.tables(solver.db)
 finally:solver.close()
 result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'));assert root==case['root']
 actual,readers=s.previous.audit(path,[dict(source=source)],[result]);assert actual==tables
 archive=s.base.archive(path,out)
s.base.write(out/'native-pilot.json',dict(result=result,counts=dict(cc),solve_seconds=solve,complete_seconds=time.perf_counter()-start,archive=archive,readers=readers,record_bytes=sum(len(k.encode())+len(v.encode()) for t in tables.values() for k,v in t.items()),records=sum(map(len,tables.values()))))
print(s.base.encode(dict(seconds=time.perf_counter()-start,solve=solve,records=sum(map(len,tables.values())))),flush=True)
