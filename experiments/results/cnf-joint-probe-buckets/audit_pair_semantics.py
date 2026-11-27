"""Untimed semantic audit, independent of propagation trace validation."""
from collections import Counter
from itertools import product
from pathlib import Path
import random,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments.compare_cnf_joint_probe_buckets import base,k

out=Path(__file__).parent;protocol=base.load(out/'protocol.json')
for f,h in protocol['source_fingerprints'].items():assert base.sha(f)==h,f
rng=random.Random(2711271319);summary=Counter();started=time.perf_counter()
for i in range(200):
    n=rng.randrange(3,8);source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),rng.randrange(2,min(n,4)+1))] for _ in range(2*n)]
    cnf,_=k.native.normalize(source);ev,diag=k.joint.discover(cnf,pair_limit=64,learn_limit=16);other,od=k.joint.discover(cnf,mode='restart',pair_limit=64,learn_limit=16)
    assert ev==other and diag==od;learned=k.joint.check(cnf,ev,pair_limit=64,learn_limit=16);models=0
    for bits in product((False,True),repeat=n):
        model=dict(enumerate(bits,1));summary['assignments_checked']+=1
        before=k.native.holds(cnf,model);after=k.native.holds(cnf+learned,model)
        assert before==after,(i,cnf,learned,model)
        models+=before
    summary.update(dict(cases=1,satisfiable=bool(models),learned_clauses=len(learned),prefixes=len(ev['prefixes'])))
assert summary['satisfiable']>50 and summary['learned_clauses']>0
base.write(out/'semantic-audit.json',dict(passed=True,summary=dict(summary),seconds=time.perf_counter()-started,scope='200 independent small random CNFs; enumerate all assignments and compare full model sets before/after learned clauses. Both acquisition modes must emit identical evidence. Untimed and separate from the matched panel.'))
print(base.encode(dict(summary)))
