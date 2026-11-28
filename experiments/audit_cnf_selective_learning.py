#!/usr/bin/env python3
"""Independent truth, proof-path survival, target references and guarded edits."""
from collections import Counter
from itertools import product,combinations
from pathlib import Path
from unittest.mock import patch
import random,subprocess,sys,time,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_selective_learning as s


def models(source):
    names=sorted({abs(v) for c in source for v in c})
    return [dict(zip(names,vs)) for vs in product((False,True),repeat=len(names)) if all(any(dict(zip(names,vs))[abs(v)]==(v>0) for v in c) for c in source)]


def expected_survival(source,proof,target):
    base=s.e.canonical(source,Counter());present=set(s.e.canonical(target,Counter()));support=[{c} for c in base];keep=[]
    for i,(start,steps,_) in enumerate(proof['derivations']):
        needed=set(support[start])
        for _,parent in steps:needed.update(support[parent])
        support.append(needed)
        if needed<=present:keep.append(i)
    return keep


def semantics(out):
    c2=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2))];counts=Counter();fresh=[];rng=random.Random(202611280610)
    inputs=[('two',[c for i,c in enumerate(c2) if mask>>i&1]) for mask in range(512)]
    c3=[list(v for v in x if v) for x in product((0,1,-1),(0,2,-2),(0,3,-3))]
    inputs += [('three',list(cs)) for n in range(4) for cs in combinations(c3,n)]
    for _ in range(128):
        names=rng.sample(range(11,1000),rng.randrange(4,8));source=[[rng.choice((-1,1))*v for v in rng.sample(names,rng.randrange(2,4))] for _ in range(rng.randrange(8,21))];source += [source[0],source[0]+[source[0][0]],[names[0],-names[0]]];fresh.append(source);inputs.append(('fresh',source))
    for kind,source in inputs:
        proof,_=s.e.prior.solve(source);base=s.e.canonical(source,Counter());counts[kind+'_parents']+=1
        targets=[list(map(list,base[:i]+base[i+1:])) for i in range(len(base))] if kind=='two' else [[list(c) for c in base[1:]]]
        targets += [source+[[-1001,1003],[-1003]],[]]
        for target in targets:
            expected=expected_survival(source,proof,target)
            with patch.object(s.e.prior,'solve',side_effect=AssertionError),patch.object(s.e.prior,'search',side_effect=AssertionError):known,diag=s.e.transport(source,proof,target)
            assert diag['retained_indices']==expected;truth=models(target);counts['targets']+=1
            for _,_,clause in known['derivations']:
                assert all(any(m[abs(v)]==(v>0) for v in clause) for m in truth);counts['retained_semantic_checks']+=1;counts['satisfying_extensions_checked']+=len(truth)
            if known['kind']=='unsat':assert not truth;counts['retained_refutations']+=1
            result,diag=s.e.expand(target,known);assert s.check(target,result)['answer']==bool(truth);counts[result['kind']]+=1
            bounded,_=s.e.expand(target,known,node_limit=0)
            assert s.check(target,bounded)['answer']==(False if known['kind']=='unsat' else None);counts['bounded_unknown']+=known['kind']!='unsat'
    s.write(out/'semantic-audit.json',dict(passed=True,counts=dict(counts),fresh_inputs=fresh,scope='Every two-variable clause set with every single-clause deletion, plus bounded three-variable sets and 128 fresh sparse signed mixtures. Additions and empty targets included. Independent explicit premise-set unions validate the linear proof-path filter; truth tables validate retained clauses and all composed answers.'))


def transports(out):
    rows=s.source_rows(s.load(out/'protocol.json'));records=[];dest=out/'transport';dest.mkdir(exist_ok=True)
    for row in rows:
        counts=Counter();begin=time.perf_counter();source,proof=s.parent_data(row,counts)
        with patch.object(s.e.prior,'solve',side_effect=AssertionError),patch.object(s.e.prior,'search',side_effect=AssertionError):known,diag=s.e.transport(source,proof,row['source'],counts)
        elapsed=time.perf_counter()-begin
        assert diag['retained_indices']==expected_survival(source,proof,row['source'])
        try:s.e.prior.transport_knowledge(source,proof,row['source'])
        except ValueError as exc:rejected=str(exc)=='Missing source premise for knowledge reuse'
        else:rejected=False
        assert rejected
        s.write(dest/(row['id']+'.json'),dict(proof=known,survival=diag,counts=dict(counts),seconds=elapsed,whole_guard_rejected=rejected))
        records.append(dict(**s.binding(dest/(row['id']+'.json')),id=row['id'],parent_id=row['parent_id'],kind=row['kind'],original=len(proof['derivations']),retained=len(known['derivations']),discarded=len(diag['discarded_indices']),status=known['kind'],seconds=elapsed))
    s.write(out/'transport.json',dict(records=records,scope='Independent audit, outside matched timing. Old whole-collection guards reject all 32 targets. No search in selective transport; explicit transitive premise sets independently validate exactly which supplied derivations survive.'))


def references(out):
    dest=out/'references';dest.mkdir(exist_ok=True);records=[]
    for row in s.source_rows(s.load(out/'protocol.json')):
        start=time.perf_counter();proc=subprocess.run([sys.executable,'experiments/audit_cnf_boundary_transfer.py','worker',str(out),row['id'],'z3'],capture_output=True,text=True,timeout=30,check=True);result=json.loads(proc.stdout);result.update(process_seconds=time.perf_counter()-start,stderr=proc.stderr)
        s.write(dest/(row['id']+'.json'),result);records.append(dict(**s.binding(dest/(row['id']+'.json')),id=row['id']));print(row['id'],result['result']['answer'],flush=True)
    s.write(out/'references.json',dict(records=records,scope='Fresh Z3 processes, separate from comparisons. Models source checked, negative answers trusted references until independently certified.'))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
