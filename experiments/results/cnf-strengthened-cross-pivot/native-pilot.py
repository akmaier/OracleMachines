from collections import Counter
from pathlib import Path
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_cross_pivot_feedback as s,cnf_iterated_cross_pivot as k,cnf_iterated_cross_pivot_native as c
out=Path('experiments/results/cnf-strengthened-cross-pivot');case=s.base.load(out/'pilot-case.json');prepared=s.prior.seed(case,Counter());cc=Counter();t=time.perf_counter()
chain,searches=k.discover(prepared[29],cc,order_source=prepared[0]);small=k.compact(prepared[29],chain,cc,order_source=prepared[0]);k.validate(prepared[29],small,Counter(),order_source=prepared[0]);elapsed=time.perf_counter()-t
assert chain['levels'][0]==s.base.load(out/'pilot-summary.json');assert chain['levels'][1]==s.base.load(out/'pilot-joint-full.json');assert small['levels'][1]==s.base.load(out/'pilot-joint-compact.json')
s.compact(out/'pilot-chain-full.json',chain);s.compact(out/'pilot-chain-compact.json',small);s.compact(out/'pilot-searches.json',searches)
print(s.base.encode(dict(status=chain['status'],levels=len(chain['levels']),lemmas=[len(x['lemmas']) for x in chain['levels']],compact_lemmas=[len(x['lemmas']) for x in small['levels']],preparation_seconds=elapsed)),flush=True)
cc=Counter();t=time.perf_counter()
with tempfile.TemporaryDirectory() as td:
 db=Path(td)/'db';solver=c.native.ResidualSolver(db)
 try:
  root=c.compile_extension(solver,case['source'],case['templates'],case['prefix'],*case['inputs'][2:],case['search'],chain=small,counts=cc,**case['options']);assert root==case['root'];tables=s.old.tables(solver.db)
 finally:solver.close()
 solve=time.perf_counter()-t;result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'));_,readers=s.previous.audit(db,[dict(source=case['source'])],[result]);archive=s.base.archive(db,out)
report=dict(solve_seconds=solve,complete_seconds=time.perf_counter()-t,records=sum(map(len,tables.values())),record_bytes=sum(len(a.encode())+len(b.encode()) for rows in tables.values() for a,b in rows.items()),counts=dict(cc),archive=archive,readers=readers)
s.base.write(out/'native-pilot.json',report);print(s.base.encode({key:v for key,v in report.items() if key not in ('counts','readers')}),flush=True)
