"""Truth-table checks and a checked minimum-distance diagnostic for repair."""
from collections import Counter
from itertools import combinations, product
from pathlib import Path
from unittest.mock import patch
import gzip, json, random, time
from experiments import cnf_hamming_repair as e


def write(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=2)+'\n')


def audit(out):
    out=Path(out);started=time.perf_counter();counts=Counter();fresh=[]
    rng=random.Random(2811260001)

    def inspect(source, category, *, all_seeds=False, retain=False):
        names=sorted({abs(v) for c in source for v in c})
        models=[values for values in product((False,True),repeat=len(names))
                if all(any(dict(zip(names,values))[abs(v)]==(v>0) for v in c) for c in source)]
        counts[category+'_inputs']+=1;counts[category+('_sat' if models else '_unsat')]+=1
        seeds=list(product((False,True),repeat=len(names))) if all_seeds else [tuple(e.proposal(source)['values'])]
        for initial in seeds:
            seed=dict(format=e.previous.FORMAT,names=names,values=list(initial))
            minimum=min((sum(a!=b for a,b in zip(initial,m)) for m in models),default=len(names)+1)
            for radius in range(len(names)+1):
                result=e.search(source,seed,radius,record=True)
                assert result['diagnostic']['reason']!='budget'
                counts['ball_queries']+=1
                with patch.object(e,'search',side_effect=AssertionError('checker invoked search')):
                    if minimum<=radius:
                        assert result['witness'] is not None and result['exclusion'] is None
                        got=e.previous.check(source,json.loads(json.dumps(result['witness'])))
                        assert got['answer'] and sum(got['model'][v]!=initial[j] for j,v in enumerate(names))<=radius
                        counts['sat_balls']+=1
                    else:
                        assert result['witness'] is None
                        got=e.check_exclusion(source,json.loads(json.dumps(result['exclusion'])))
                        assert got['no_model_within_radius'] and got['global_unsat']==(radius==len(names))
                        counts['excluded_balls']+=1
            limited=e.search(source,seed,len(names),node_limit=1,record=True)
            if limited['diagnostic']['reason']=='budget':
                assert limited['exclusion'] is None and limited['witness'] is None
                counts['budget_unknowns']+=1
        if retain:
            fresh.append(dict(source=source,satisfiable=bool(models),seed=seed,
                              minimum_distance=None if not models else minimum,result=result))

    for n,bound in ((2,9),(3,3)):
        clauses=[[s*v for v,s in enumerate(signs,1) if s] for signs in product((-1,0,1),repeat=n)]
        for k in range(bound+1):
            for source in combinations(clauses,k):inspect(list(source),'cnf'+str(n),all_seeds=n==2)
    for _ in range(1000):
        n=rng.randrange(1,7)
        source=[[rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),rng.randrange(n+1))] for _ in range(rng.randrange(16))]
        inspect(source,'random')
    old=json.loads(Path('experiments/results/cnf-choice-witness/semantic-audit.json').read_text())
    for record in old['missed_satisfiable_domains']:inspect(record['source'],'retained_domain')
    for i in range(64):
        n=rng.randrange(3,8)
        source=[[rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),rng.randrange(1,n+1))] for _ in range(rng.randrange(2,18))]
        if i%4==0:source += [[n+1,n+2],[-n-1,-n-2]]
        if i%4==1:source += [[1],[-1]]
        if i%4==2:source += [source[0],source[0]+[-source[0][0]]]
        if i%4==3:source[0][0]*=-1
        names=sorted({abs(v) for c in source for v in c});ids=rng.sample(range(100,10000),len(names))
        mapping={v:ids[j]*rng.choice((-1,1)) for j,v in enumerate(names)}
        source=[[mapping[abs(v)]*(1 if v>0 else -1) for v in c] for c in source];rng.shuffle(source)
        inspect(source,'fresh',retain=True)
    reuses=invalidated=0
    for r in fresh:
        w=r['result']['witness']
        if w is None or not w['names']:continue
        literal=w['names'][0]*(1 if w['values'][0] else -1)
        assert e.previous.check(r['source']+[[literal]],w)['answer'];reuses+=1
        try:e.previous.check(r['source']+[[-literal]],w)
        except ValueError:invalidated+=1
        else:raise AssertionError('stale repair witness accepted')
    result=dict(passed=True,counts=dict(counts),fresh_records=fresh,checked_reuses=reuses,
                invalidated_witnesses=invalidated,seconds=time.perf_counter()-started,
                scope='Explicit truth tables determine minimum distance independently. Ball exhaustion excludes only that radius; budget exhaustion remains unknown. Old domain misses and fresh mixtures are finite gate audits, not representative transfer.')
    write(out/'semantic-audit.json',result)
    print(json.dumps(dict(passed=True,counts=dict(counts),reuses=reuses,invalidations=invalidated)))


def distance(out):
    out=Path(out);started=time.perf_counter()
    old=json.loads(Path('experiments/results/cnf-choice-witness/gap-diagnostics.json').read_text())['remaining_random']
    source=old['source'];seed=e.proposal(source)
    assert seed==old['rejected_candidates'][0]['candidate']
    c=Counter();t=time.perf_counter();closed=e.search(source,seed,25,c,node_limit=100000,record=True)
    construction=time.perf_counter()-t;assert closed['diagnostic']['reason']=='radius-exhausted'
    write(out/'radius-25-exclusion.json',closed['exclusion'])
    proofs=[];times=[];cc=Counter()
    with patch.object(e,'search',side_effect=AssertionError('cold repair search')):
        for _ in range(2):
            t=time.perf_counter();p=json.loads((out/'radius-25-exclusion.json').read_text())
            got=e.check_exclusion(source,p,cc);assert not got['global_unsat'];times.append(time.perf_counter()-t);proofs.append(got)
    t=time.perf_counter();w=e.search(source,seed,26,c,node_limit=100000)
    witness_seconds=time.perf_counter()-t
    assert w['diagnostic']['distance']==26 and e.previous.check(source,w['witness'])['answer']
    write(out/'distance-26-witness.json',w['witness'])
    data=(out/'radius-25-exclusion.json').read_bytes();compressed=gzip.compress(data,mtime=0)
    (out/'radius-25-exclusion.json.gz').write_bytes(compressed)
    result=dict(passed=True,id=old['id'],source=source,seed=seed,minimum_distance=26,
                closed=closed['diagnostic'],witness=w['diagnostic'],construction_seconds=construction,
                witness_seconds=witness_seconds,cold_check_seconds=times,cold_results=proofs,
                counts=dict(c),cold_counts=dict(cc),exclusion_bytes=len(data),compressed_bytes=len(compressed),
                total_seconds=time.perf_counter()-started,
                scope='Supplementary exposed-case diagnosis at a larger explicit budget, outside paired timings. Excluding radius 25 plus a model at distance 26 certifies this seed-specific minimum. Neither lower radii nor the seed are general tractability claims.')
    write(out/'distance-diagnostic.json',result)
    print(json.dumps({k:result[k] for k in ('minimum_distance','closed','witness','construction_seconds','cold_check_seconds','exclusion_bytes','compressed_bytes')}))


if __name__=='__main__':
    import sys
    globals()[sys.argv[1]](sys.argv[2])
