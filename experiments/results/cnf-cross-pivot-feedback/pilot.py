from collections import Counter
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_conditioned_saturation as s,cnf_cross_pivot_feedback as k,cnf_cross_pivot_feedback_native as c
out=Path('experiments/results/cnf-cross-pivot-feedback');parent=Path('experiments/results/cnf-conditioned-saturation');protocol=s.base.load(parent/'protocol.json');reports=[]
for name in ('61-0','61-50','67-0'):
 case=s.old.bound(protocol['cases'][name]);cc=Counter();t=time.perf_counter();seed=s.seed(case,cc);full=k.collect(seed[29],s.base.load(parent/f'census-conditioned-0/{name}.json')['trials'],cc,order_source=seed[0]);small=k.compact(seed[29],full,cc,order_source=seed[0]);prep=time.perf_counter()-t
 s.compact(out/f'pilot-{name}-full.json',full);s.compact(out/f'pilot-{name}-compact.json',small)
 report=dict(name=name,status=small['status'],full_lemmas=len(full['lemmas']),compact_lemmas=len(small['lemmas']),preparation_seconds=prep,preparation_counts=dict(cc))
 print(s.base.encode(report),flush=True)
 if small['status']=='refuted':
  cc=Counter();t=time.perf_counter()
  with tempfile.TemporaryDirectory() as td:
   db=Path(td)/'db';solver=c.native.ResidualSolver(db)
   try:
    root=c.compile_extension(solver,case['source'],case['templates'],case['prefix'],*case['inputs'][2:],case['search'],summary=small,counts=cc,**case['options']);assert root==case['root'];tables=s.old.tables(solver.db)
   finally:solver.close()
   solve=time.perf_counter()-t;result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'));_,readers=s.previous.audit(db,[dict(source=case['source'])],[result]);dest=out/f'pilot-{name}';dest.mkdir();archive=s.base.archive(db,dest)
  report.update(solve_seconds=solve,complete_seconds=time.perf_counter()-t,records=sum(map(len,tables.values())),record_bytes=sum(len(a.encode())+len(b.encode()) for rows in tables.values() for a,b in rows.items()),counts=dict(cc),archive=archive,readers=readers)
  print(s.base.encode({k:v for k,v in report.items() if k in ('name','solve_seconds','complete_seconds','records','record_bytes')}),flush=True)
 reports.append(report)
s.base.write(out/'pilot.json',dict(rows=reports))
