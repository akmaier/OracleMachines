#!/usr/bin/env python3
"""Adaptive, matched wide versus deep continuation of preserved case 16."""
from collections import Counter
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_nested_refinement import NestedRefinement, base

PARENT=Path('experiments/results/cnf-split-registry')
MODES=('flat','nested')


def all_coverage(h,registry,queries):
    selected=[];choices=[]
    for query in queries:
        flags=[h._load(k) is not None and base.compose(h,[k],registry,Counter())[0][0] for k in query['roots']]
        depth=next((d for d in (0,1) if flags[d]),None);choices.append(depth)
        if depth is not None:selected.append(query['roots'][depth])
    _,plan=base.compose(h,selected,registry,Counter());proof=base.expand(h,plan,selected,registry,Counter())
    return dict(selected_depths=choices,roots=selected,proof=proof,covered=len(selected))


def replay(path,protocol,result):
    before=base.sha(path);started=time.perf_counter();h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with (base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('acquisition')),
              patch.object(base.split,'discover_simplification',side_effect=AssertionError('fresh assumption'))):
            for key in base.rows(h):assert base.owner(h,key)._load(key) is not None
            evidence=[]
            for key,payload in h.db.execute(f'SELECT id,payload FROM {base.split.TABLE} ORDER BY rowid'):
                record=base.load_json(payload);assert base.split.record_key(record)==key
                base.split.verify(h,record,Counter());evidence.append(record)
            routes=base.routes_for(h,evidence);queries=base.load(protocol['queries']['path'])
            actual=all_coverage(h,routes,queries);assert actual==result['coverage']
            checked=base.split.verify_positive(h,actual['proof'],actual['roots'],evidence,Counter())
            return dict(patterns=len(base.rows(h)),pairs=len(evidence),covered=actual['covered'],
                original_bindings=len(queries),positive_steps=len(checked.justified),no_acquisition=True,
                seconds=time.perf_counter()-started)
    finally:h.close();assert base.sha(path)==before


def flat_batch(session,source,state_limit,pair_limit):
    tick=time.perf_counter();h=session.h;h.set_admission_budget(state_limit);h.counts=Counter()
    before=base.rows(h);old_counts=Counter(session.counts);operations=[];reason='pair_limit'
    variables=base.split.choices(h,source,session.counts,len({abs(l) for c in h._load(source)['cnf'] for l in c}))
    for _ in range(pair_limit):
        if session.coverage.closed()[0]:reason='closed';break
        variable=None
        for candidate in variables:
            identity=base.encode([source,candidate]);record=session.records.get(identity)
            if record is None or any(h._load(b['edge']['key']) is None for b in record['branches']):
                variable=candidate;break
        if variable is None:reason='candidates_exhausted';break
        operation=session.acquire(source,variable);operation['selected_depth']=0;operations.append(operation)
        if any(operation['pending']):reason='state_limit';break
    if session.coverage.closed()[0]:reason='closed'
    after=base.rows(h);fresh=set(after)-set(before)
    assert before.items()<=after.items() and fresh<=h.admitted and len(h.admitted)<=state_limit
    return dict(operations=operations,reason=reason,closed=session.coverage.closed()[0],entered=len(h.admitted),
        stored=len(fresh),probes=h.counts['probe_attempts'],admitted_ids=sorted(map(base.key_sha,h.admitted)),
        stored_ids=sorted(map(base.key_sha,fresh)),recognition_counts=dict(h.counts),
        selection_counts=dict(session.counts-old_counts),decisions=dict(session.decisions),seconds=time.perf_counter()-tick)


def stream(out,protocol,mode):
    out.mkdir();samples=[];target=base.load(protocol['target']['path']);cp=base.load(protocol['checkpoint']['path'])
    queries=base.load(protocol['queries']['path']);root=queries[target['case']]['roots'][0]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'h';tick=time.perf_counter();base.restore_archive(cp['archive'],path)
        h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        initial=base.rows(h)
        try:
            for key in initial:assert base.owner(h,key)._load(key) is not None
            session=NestedRefinement(h,root);initial_coverage=all_coverage(h,session.registry,queries)
            base.split.verify_positive(h,initial_coverage['proof'],initial_coverage['roots'],list(session.records.values()),Counter())
            assert initial_coverage['covered']==5
            initial_pairs=dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
            startup=time.perf_counter()-tick
            for batch in range(protocol['max_batches']):
                destination=out/f'batch-{batch}';destination.mkdir()
                if mode=='nested':result=session.batch(state_limit=protocol['state_limit'],pair_limit=protocol['pair_limit'])
                else:result=flat_batch(session,target['source'],protocol['state_limit'],protocol['pair_limit'])
                result.update(mode=mode,batch=batch,coverage=all_coverage(h,session.registry,queries),
                    patterns=len(base.rows(h)),pairs=len(session.records),registry=session.registry.statistics(),
                    pattern_digest=base.key_sha(base.encode(sorted(base.rows(h).items()))),
                    pair_digest=base.key_sha(base.encode(sorted(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}')))))
                assert initial.items()<=base.rows(h).items()
                assert initial_pairs.items()<=dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}')).items()
                result['archive']=base.archive(path,destination)
                result['cold']=replay(path,protocol,result)
                base.write(destination/'report.json',result)
                samples.append(dict(path=str(destination/'report.json'),sha256=base.sha(destination/'report.json')))
                print(base.encode(dict(mode=mode,batch=batch,closed=result['closed'],reason=result['reason'],
                    entered=result['entered'],stored=result['stored'],probes=result['probes'],
                    operations=len(result['operations']),covered=result['coverage']['covered'],seconds=result['seconds'])),flush=True)
                if result['closed'] or result['reason']=='candidates_exhausted':break
        finally:h.close()
    results=[base.load(s['path']) for s in samples]
    summary=dict(mode=mode,startup_seconds=startup,batches=len(samples),closed=results[-1]['closed'],
        covered=results[-1]['coverage']['covered'],entered=sum(r['entered'] for r in results),
        stored=sum(r['stored'] for r in results),probes=sum(r['probes'] for r in results),
        assumptions=sum(r['selection_counts'].get('bootstrap_fresh_assumptions',0) for r in results),
        operation_seconds=sum(r['seconds'] for r in results),cold_seconds=sum(r['cold']['seconds'] for r in results),
        compression_seconds=sum(r['archive']['seconds'] for r in results),
        pattern_digest=results[-1]['pattern_digest'],pair_digest=results[-1]['pair_digest'],
        database_bytes=results[-1]['archive']['database_bytes'],compressed_bytes=results[-1]['archive']['compressed_bytes'])
    base.write(out/'report.json',dict(summary=summary,samples=samples));return summary


def run(out):
    out.mkdir(exist_ok=False);target=base.load(PARENT/'next-discovery.json');cp=base.load(target['checkpoint']['path'])
    previous=base.load(PARENT/'validation.json');sources=dict(previous['source_fingerprints'])
    for p,d in sources.items():assert base.sha(p)==d,p
    sources=base.source_fingerprints(sources)
    for p in ('experiments/cnf_nested_refinement.py','experiments/compare_cnf_nested_refinement.py','solver/test_cnf_nested_refinement.py'):
        sources[p]=base.sha(p)
    binding=lambda p:dict(path=str(p),sha256=base.sha(p))
    protocol=dict(target=binding(PARENT/'next-discovery.json'),checkpoint=target['checkpoint'],
        queries=cp['queries'],options=base.OPTIONS,state_limit=128,pair_limit=16,max_batches=4,
        orders=[MODES,tuple(reversed(MODES))],source_fingerprints=sources,
        rationale='Adaptive case-16 continuation. Flat tries remaining source pivots; nested follows saved reductions and commits to one branch choice per unresolved frontier.',
        limitations=['Both arms share limits, not actual total work; up to 32 source assumptions per batch are separately charged.',
            'Nested favors fewer/smaller retained unresolved literals, then expands the smallest-support selected leaf. These heuristics are not guaranteed optimal.',
            'All candidates, budget failures and child states remain persisted. Coverage is not a SAT/UNSAT verdict.',
            'All full archives are preserved at every batch. Their cold replay, compression and common startup are reported separately from local expansion.'])
    base.write(out/'protocol.json',protocol);samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';summary=stream(dest,protocol,mode)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        a,b=[base.load(s['path'])['summary'] for s in samples if s['mode']==mode]
        for k in ('closed','covered','entered','stored','probes','assumptions','pattern_digest','pair_digest'):assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in ('closed','covered','entered','stored','probes','assumptions','batches','database_bytes','compressed_bytes')},
            **{'mean_'+k:(a[k]+b[k])/2 for k in ('startup_seconds','operation_seconds','cold_seconds','compression_seconds')}}
    base.write(out/'report.json',dict(protocol_sha256=base.sha(out/'protocol.json'),samples=samples,summary=summary))
    print(base.encode(summary),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
