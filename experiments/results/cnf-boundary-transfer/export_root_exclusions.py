"""Post-transfer proof export; replay only a completed full-support root search.

This follow-up was chosen after observing discarded root exclusions. It is not
part of the frozen transfer comparison. A fresh boundary run and any proof replay
share the same 20000-state total; other conditional exclusions stay local.
"""
from collections import Counter
from itertools import product
from pathlib import Path
import gzip,resource,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
from experiments import compare_cnf_boundary_transfer as s
FORMAT='cnf-exported-root-result-v1'


def discover(source,counts=None):
    counts=Counter() if counts is None else counts
    result=s.e.repair(source,counts);diagnostic=dict(boundary=result['diagnostic'],replay=None,total_states=result['diagnostic']['expanded'])
    if result['witness'] is not None:
        proof=dict(format=FORMAT,kind='sat',certificate=result['witness'])
    elif result['diagnostic']['prefix']['reason']=='radius-exhausted':
        # Prefix radius covers every source variable; no local proof is promoted.
        cap=result['diagnostic']['prefix']['expanded'];assert cap<=s.e.PREFIX_LIMIT and not result['evidence']['rounds']
        seed=s.e.proposal(source,counts)
        replay=s.e.previous_search.search(source,seed,len(seed['names']),counts,node_limit=cap,record=True)
        assert replay['diagnostic']['expanded']==cap and replay['diagnostic']['reason']=='radius-exhausted'
        diagnostic['replay']=replay['diagnostic'];diagnostic['total_states']+=cap
        proof=dict(format=FORMAT,kind='unsat',certificate=replay['exclusion'])
    else:proof=dict(format=FORMAT,kind='unknown',certificate=None)
    assert diagnostic['total_states']<=s.e.NODE_LIMIT
    check(source,proof,counts)
    return proof,result['evidence'],diagnostic


def check(source,proof,counts=None):
    counts=Counter() if counts is None else counts
    if type(proof) is not dict or set(proof)!={'format','kind','certificate'} or proof['format']!=FORMAT:raise ValueError('Invalid exported root result')
    if proof['kind']=='sat':return s.e.previous.check(source,proof['certificate'],counts)
    if proof['kind']=='unsat':
        result=s.e.previous_search.check_exclusion(source,proof['certificate'],counts)
        if not result['global_unsat']:raise ValueError('Root exclusion does not cover full support')
        return dict(answer=False,model=None)
    if proof['kind']=='unknown' and proof['certificate'] is None:
        s.e.previous.capacity.canonical(source,counts);return dict(answer=None,model=None)
    raise ValueError('Invalid exported conclusion')


def audit(out):
    universe=[list(v for v in pair if v) for pair in product((0,1,-1),(0,2,-2))];counts=Counter()
    for mask in range(512):
        source=[c for j,c in enumerate(universe) if mask>>j&1];names=sorted({abs(v) for c in source for v in c})
        truth=any(all(any(dict(zip(names,values))[abs(v)]==(v>0) for v in c) for c in source) for values in product((False,True),repeat=len(names)))
        proof,evidence,diag=discover(source);assert check(source,proof)['answer']==truth;s.e.check_evidence(source,evidence)
        counts['sat' if truth else 'unsat']+=1
        assert diag['total_states']<=20000
    source=[[1],[2]];seed=s.e.proposal(source);seed['values']=[False,False]
    partial=s.e.previous_search.search(source,seed,1,record=True)['exclusion']
    try:check(source,dict(format=FORMAT,kind='unsat',certificate=partial))
    except ValueError:pass
    else:raise AssertionError('Partial ball promoted')
    s.write(out/'export-audit.json',dict(passed=True,exhaustive_inputs=512,counts=dict(counts),partial_ball_rejected=True,script=s.binding(__file__)))


def run(out):
    dest=out/'root-export';dest.mkdir();started=time.perf_counter();p=s.load(out/'protocol.json');rows=s.source_rows(p);cases=[];proofs=[];evidences=[];total=Counter();phases=Counter()
    for row in rows:
        counts=Counter();start=time.perf_counter();proof,ev,diag=discover(row['source'],counts);acquisition=time.perf_counter()-start;discovery_counts=dict(counts)
        start=time.perf_counter();got=check(row['source'],proof,counts);s.e.check_evidence(row['source'],ev,counts);checking=time.perf_counter()-start
        start=time.perf_counter();s.write(dest/(row['id']+'.json'),proof);writing=time.perf_counter()-start
        proofs.append(proof);evidences.append(ev);total.update(counts);phases.update(dict(acquisition_seconds=acquisition,checking_seconds=checking,writing_seconds=writing))
        cases.append(dict(id=row['id'],status=proof['kind'],result=got,diagnostic=diag,counts=dict(counts),discovery_counts=discovery_counts,acquisition_seconds=acquisition,checking_seconds=checking))
    start=time.perf_counter();s.write(dest/'discovery.json',evidences);phases['writing_seconds']+=time.perf_counter()-start
    start=time.perf_counter();warm=Counter()
    for row,ev in zip(s.source_rows(p),s.load(dest/'discovery.json')):check(row['source'],s.load(dest/(row['id']+'.json')),warm);s.e.check_evidence(row['source'],ev,warm)
    warm_seconds=time.perf_counter()-start;start=time.perf_counter();cold=Counter()
    for _ in range(2):
        for row,ev in zip(s.source_rows(p),s.load(dest/'discovery.json')):check(row['source'],s.load(dest/(row['id']+'.json')),cold);s.e.check_evidence(row['source'],ev,cold)
    cold_seconds=time.perf_counter()-start;start=time.perf_counter();(dest/'combined.json.gz').write_bytes(gzip.compress(s.encode(dict(proofs=proofs,evidence=evidences)).encode(),mtime=0));persistence_seconds=time.perf_counter()-start
    s.write(out/'root-export.json',dict(script=s.binding(__file__),policy=s.binding(out/'export-policy.json'),scope='Single post-transfer follow-up, no matched speedup claim. Fresh boundary acquisition plus repeated full root proof generation is charged. No search changes or local-to-global promotion.',cases=cases,counts=dict(total),warm_counts=dict(warm),cold_counts=dict(cold),phases=dict(phases),warm_seconds=warm_seconds,cold_seconds=cold_seconds,persistence_seconds=persistence_seconds,complete_seconds=time.perf_counter()-started,proof_bytes=sum((dest/(r['id']+'.json')).stat().st_size for r in rows),evidence_bytes=(dest/'discovery.json').stat().st_size,combined_gzip_bytes=(dest/'combined.json.gz').stat().st_size,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
