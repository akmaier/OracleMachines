"""Independent source/cofactor truth audit; outside matched stage timings."""
from pathlib import Path
from collections import Counter
from itertools import product
from unittest.mock import patch
import gzip,hashlib,json,random,time
from experiments import cnf_factor_conditioning as f
from experiments.compare_cnf_factor_conditioning import base,old


def main(out):
    rng=random.Random(2711271927);sources=[]
    clauses=[[s*v for v,s in enumerate(signs,1) if s] for signs in product((-1,0,1),repeat=2)]
    for bits in range(512):sources.append(dict(kind='exhaustive-two',source=[c for i,c in enumerate(clauses) if bits>>i&1],cut_limit=2))
    for i in range(40):
        n=6+i%3;source=[[v*rng.choice((-1,1)) for v in rng.sample(range(1,n+1),3)] for _ in range(3*n)]
        sources.append(dict(kind='seeded',source=source,cut_limit=4))
        perm=rng.sample(range(11,11+n),n);signs=[rng.choice((-1,1)) for _ in range(n)]
        sources.append(dict(kind='signed-permutation',source=[[perm[abs(v)-1]*signs[abs(v)-1]*(1 if v>0 else -1) for v in c] for c in reversed(source)],cut_limit=4))
        edited=source[1:]+[[-v for v in source[0]]]+([[n+1],[-(n+1),n+2]] if i%2 else [[1,2],[-1,-2]])
        sources.append(dict(kind='edit-or-disjoint-mixture',source=edited,cut_limit=4))
    base.write(out/'audit-inputs.json',dict(seed=2711271927,records=sources,scope='Unlabelled independent finite semantic audit, not held-out workload performance. Prefixes may be deliberately left open after a checked terminal.'))
    records=[];counts=Counter();start=time.perf_counter()
    for item in sources:
        source=item['source'];prefix,_=f.bucket.discover(source,bag_limit=3,work_limit=256);prefix.update(status='unresolved',model=None);prefix['limits']['work_limit']=65536
        cert,diag=f.discover(source,prefix,cut_limit=item['cut_limit']);got=f.check(source,prefix,cert)
        names=sorted({abs(v) for c in source for v in c});truth=any(f.native.holds(source,dict(zip(names,values))) for values in product((False,True),repeat=len(names)))
        if got['answer'] is not None:assert got['answer']==truth
        if got['answer']:assert f.native.holds(source,got['model'])
        raw=[c for e in cert['entries'] for c in e['certificate']['clauses']];variables=sorted({abs(v) for c in raw for v in c})
        for branch in cert['branches']:
            fixed=dict(zip(cert['cutset'],branch['values']));residual=f.cofactor(raw,fixed,Counter());free=[v for v in variables if v not in fixed]
            for values in product((False,True),repeat=len(free)):
                model=dict(zip(free,values));assert f.native.holds(residual,model)==f.native.holds(raw,{**model,**fixed});counts['cofactor_assignments']+=1
        with patch.object(f.bucket,'discover',side_effect=AssertionError('cold discovery')),patch.object(f.covers,'discover',side_effect=AssertionError('cold cover')),patch.object(f,'cutset',side_effect=AssertionError('cold heuristic')):assert f.check(source,prefix,json.loads(json.dumps(cert)))==got
        counts[item['kind']]+=1;counts[cert['status']]+=1;counts['branches']+=len(cert['branches']);counts['prefix_steps']+=len(prefix['steps'])
        records.append(dict(source=source,prefix=prefix,proof=cert,diagnostic=diag,truth=truth,result=got))
    payload=base.encode(records).encode();path=out/'semantic-audit-certificates.json.gz';path.write_bytes(gzip.compress(payload,mtime=0))
    result=dict(passed=True,counts=dict(counts),seconds=time.perf_counter()-start,inputs=old.binding(out/'audit-inputs.json'),archive=old.binding(path),uncompressed_sha256=hashlib.sha256(payload).hexdigest(),scope='Independent direct truth labels and every cofactor assignment; all source/prefix and SAT witnesses checked, cold replay with discovery/ranking disabled. No generalization or timing inference.')
    base.write(out/'semantic-audit.json',result);print(base.encode(result))


if __name__=='__main__':
    import sys
    main(Path(sys.argv[1]))
