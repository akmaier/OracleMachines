"""Retain an explicit ordering regression; never tune the measured policy."""
from pathlib import Path
from collections import Counter
import json,random
from experiments import cnf_partition_repair as e


def main(out):
    rng=random.Random(2811260202);record=None
    for index in range(10000):
        n=rng.randrange(4,9)
        source=[[rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),rng.randrange(2,min(n,4)+1))] for _ in range(rng.randrange(8,30))]
        seed=e.proposal(source);n=len(seed['names'])
        a=e.baseline.search(source,seed,n);b=e.search(source,seed,n)
        if a['witness'] is not None and b['diagnostic']['expanded']>a['diagnostic']['expanded']:
            cap=a['diagnostic']['expanded'];limited=e.search(source,seed,n,node_limit=cap)
            assert limited['witness'] is None and limited['diagnostic']['reason']=='budget'
            assert e.previous.check(source,a['witness'])['answer'] and e.previous.check(source,b['witness'])['answer']
            record=dict(index=index,source=source,seed=seed,baseline=a,partition=b,illustrative_cap=cap,partition_at_cap=limited)
            break
    Path(out,'ordering-regression.json').write_text(json.dumps(dict(seed=2811260202,record=record,scope='Post-hoc small adversarial search. A smaller illustrative cap demonstrates no universal ordering dominance; it never alters the frozen 20000-state panel policy.'),sort_keys=True,indent=2)+'\n')
    print(json.dumps(None if record is None else dict(index=index,baseline_states=a['diagnostic']['expanded'],partition_states=b['diagnostic']['expanded'],illustrative_cap=cap)))


if __name__=='__main__':
    import sys
    main(sys.argv[1])
