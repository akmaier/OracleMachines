#!/usr/bin/env python3
"""Fresh reference processes and exact input/model transport, separate from timing."""
from collections import Counter
from pathlib import Path
import json,resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_boundary_transfer as s
from experiments import cnf_hamming_repair as portfolio
from experiments import cnf_verified_operators as verified


def row_source(out,key):
    row=next(row for row in s.bound(s.load(out/'protocol.json')['panel']) if row['id']==key)
    assert s.sha(row['raw']['path'])==row['raw']['sha256']
    cnf,_=s.parse_dimacs(Path(row['raw']['path']).read_text());assert cnf==row['source']
    return cnf


def worker(out,key,mode):
    started=time.perf_counter();source=row_source(out,key);counts=Counter();proof=None
    if mode=='portfolio':
        with verified.installed(bank:=verified.VerifiedOperators()):proof,diag=portfolio.pipeline(source,counts)
        discovered=time.perf_counter();got=portfolio.check_pipeline(source,proof,counts);reason=None;version=None
    elif mode=='z3':
        import z3
        context=z3.Context();names=sorted({abs(v) for c in source for v in c});variables={v:z3.Bool('v'+str(v),ctx=context) for v in names}
        solver=z3.Solver(ctx=context);solver.set(timeout=10000,random_seed=0)
        solver.add(*[z3.Or(*[variables[abs(v)] if v>0 else z3.Not(variables[-v]) for v in c]) if c else z3.BoolVal(False,ctx=context) for c in source])
        result=solver.check();reason=solver.reason_unknown() if result==z3.unknown else None;version=z3.get_version_string()
        proof=None
        if result==z3.sat:
            model=solver.model();proof=dict(format=s.e.previous.FORMAT,names=names,values=[z3.is_true(model.eval(variables[v],model_completion=True)) for v in names])
        discovered=time.perf_counter()
        got=s.e.previous.check(source,proof,counts) if proof else dict(answer=False if result==z3.unsat else None,model=None)
        diag=dict(statistics=str(solver.statistics()))
    else:raise ValueError(mode)
    ended=time.perf_counter()
    return dict(id=key,mode=mode,result=got,proof=proof,diagnostic=diag,counts=dict(counts),version=version,reason=reason,input_and_solve_seconds=discovered-started,checking_seconds=ended-discovered,worker_seconds=ended-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


def references(out):
    dest=out/'references';dest.mkdir();records=[]
    for row in s.source_rows(s.load(out/'protocol.json')):
        for mode in ('portfolio','z3'):
            started=time.perf_counter();log=dest/(row['id']+'-'+mode+'.json')
            try:
                proc=subprocess.run([sys.executable,__file__,'worker',str(out),row['id'],mode],capture_output=True,text=True,timeout=30,check=True)
                result=json.loads(proc.stdout);result['process_seconds']=time.perf_counter()-started;result['stderr']=proc.stderr
            except subprocess.TimeoutExpired as exc:
                result=dict(id=row['id'],mode=mode,timeout=True,process_seconds=time.perf_counter()-started,result=dict(answer=None,model=None),stdout=str(exc.stdout),stderr=str(exc.stderr))
            s.write(log,result);records.append(dict(**s.binding(log),id=row['id'],mode=mode));print(row['id'],mode,result['result']['answer'],round(result['process_seconds'],3),flush=True)
    s.write(out/'references.json',dict(records=records,scope='Each call starts a fresh process. Reference costs are separate from paired workflows; Z3 negative outputs are trusted reference claims, not project refutations.'))


def inputs(out):
    p=s.load(out/'protocol.json');rows=s.source_rows(p);byid={r['id']:r for r in rows};desc=s.bound(p['descriptions']);counts=Counter()
    for row in rows:
        kind=desc[row['id']]['kind'];counts[kind]+=1
        if kind=='edit':
            expected=[c[:] for c in byid[desc[row['id']]['original']]['source'][1:]];next(c for c in reversed(expected) if c)[0]*=-1
            assert expected==row['source'] and desc[row['id']]['publisher_answer'] is None
    for transport in s.bound(p['transports']):
        original=byid[transport['original']]['source'];mapping={int(v):w for v,w in transport['mapping'].items()}
        assert set(mapping)=={abs(v) for c in original for v in c} and len({abs(w) for w in mapping.values()})==len(mapping)
        assert [[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in reversed(original)]==byid[transport['id']]['source']
    assert counts==dict(original=24,edit=6,**{'signed-permutation':6})
    s.write(out/'input-audit.json',dict(passed=True,counts=dict(counts),panel=p['panel'],transports=p['transports'],scope='Bijective signed substitutions preserve satisfiability symbolically; edited labels remain unknown until reference/checking.'))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='worker':print(s.encode(worker(out,sys.argv[3],sys.argv[4])))
    else:globals()[action](out)
