"""Independent exhaustive semantics for each checked intermediate reduction."""
from collections import Counter
from itertools import product
from pathlib import Path
import json,random,time
from experiments import cnf_pair_feedback_buckets as k


def models(cnf):
    variables=sorted({abs(l) for c in cnf for l in c})
    return [dict(zip(variables,bits)) for bits in product((False,True),repeat=len(variables)) if all(any(dict(zip(variables,bits))[abs(l)]==(l>0) for l in c) for c in cnf)]


def main():
    rng=random.Random(2711271418);counts=Counter();records=[];began=time.perf_counter()
    limits={**k.DEFAULTS,'bag_limit':1,'depth_limit':0,'probe_limit':1,'continuation_limit':1,'pair_limit':8,'learn_limit':2}
    for i in range(240):
        n=rng.randrange(3,8);raw=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(4*n)]
        cnf,_=k.native.normalize(raw);before=models(cnf);counts['sources']+=1;counts['source_assignments']+=1<<n
        ref,diag,status,witness=k.discover_refinement(cnf,'feedback',limits,Counter());count=0
        if ref is not None:
            actual,got=k.check_refinement(cnf,ref,'feedback',limits,Counter());assert actual==status and got==witness
            current=cnf;maps=[]
            for rnd in ref['rounds']:
                ms=models(current);learned=k.joint.check(current,rnd['evidence'],pair_limit=8,learn_limit=2)
                assert all(k.native.holds(learned,m) for m in ms);counts['entailed_clauses']+=len(learned)
                augmented=k.relations.clean_quotient(current+learned,Counter());terminal=rnd['terminal'];k.prior.check_certificate(augmented,terminal)
                residual,data=k.terminal_transport(augmented,terminal,Counter());rs=models(residual);assert bool(ms)==bool(rs)
                maps.append(data)
                for m in rs:
                    for mapping in reversed(maps):m=k.lift_terminal(mapping,m)
                    assert k.native.holds(cnf,m);counts['lifted_residual_models']+=1
                count+=1;current=residual
            counts['rounds']+=count;counts[str(count)+'_round_'+status]+=1
        if status!='unresolved':assert (status=='sat')==bool(before)
        if witness is not None:assert k.native.holds(cnf,witness)
        records.append(dict(source=list(map(list,cnf)),rounds=count,status=status,satisfiable=bool(before)))
    result=dict(passed=True,counts=dict(counts),seconds=time.perf_counter()-began,seed=2711271418,records=records,scope='Outside measured cost. Exhaustive model enumeration separately checks every retained implication, existential equivalence of each prepared terminal and every residual model lifted through all preceding transports. No unrestricted efficiency claim.')
    Path(__file__).with_name('semantic-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(counts)


if __name__=='__main__':main()
