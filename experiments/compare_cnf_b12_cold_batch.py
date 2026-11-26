#!/usr/bin/env python3
"""Compare separate cold B12 checks with one independently owned validation batch."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import resource, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b12_continuation_batch as prior, cnf_b12_cold_batch as candidate
base=prior.base; old=prior.old; compact=prior.compact; bind=prior.bind
PARENT=Path('experiments/results/cnf-b12-continuation-batch')
MODES=('source_separate', 'source_batch', 'unseen_separate', 'unseen_batch')
FILES=('experiments/cnf_b12_cold_batch.py', 'experiments/compare_cnf_b12_cold_batch.py', 'solver/test_cnf_b12_cold_batch.py')


def arguments(row):return prior.arguments(row)


def options(row):return prior.options(row)


def saved_cursor(row,ordering):
    return old.bound(row['b12_'+ordering+'_continuation_result'])['cursor']


def prepare(out):
    assert not (out/'protocol.json').exists()
    cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items(): assert base.sha(f)==h, f
    seeds=cp['b12_continuation_batch']['remaining']
    base.write(out/'protocol.json', dict(parent=old.binding(PARENT/'checkpoint.json'), parent_manifest=old.binding(PARENT/'manifest.json'),
        parent_protocol=cp['b12_continuation_batch']['protocol'], seeds=seeds, targets=sorted({r['target'] for r in prior.load_frontier(seeds)}),
        pilot=old.binding(out/'pilot.json'), pilot_source=old.binding(out/'pilot-source.py'),
        source_fingerprints={**cp['source_fingerprints'], **{f:base.sha(f) for f in FILES}},
        orders=[list(MODES[i:]+MODES[:i]) for i in range(4)], limits=dict(rounds=3,probe_limit=64,work_limit=262144,trace_limit=256), limitations=[
        'Replay all saved rounds for fourteen exposed cases and both B12 orders. Discovery is the same continuation batch in both arms; this run adds no coverage or new implications.',
        'Separate calls the current shared-B12 validator for each cold-reloaded snapshot. Batch privately owns portable inputs and snapshots, prepares once and independently checks every snapshot.',
        'One source, closure, ordering policy and trace bound per batch. Mixed trace bounds are explicitly rejected and must be checked separately. Exact bindings reject changed sources, closures and policies.',
        'Each snapshot retains a full cursor replay, failed-proof check and program/cursor agreement check. No prepared state or authority is passed from discovery, or between separate validation calls.',
        'Validation certifies the supplied snapshots individually; it does not assert a search budget or a consecutive-round relationship. The audit separately verifies equality with the previously preserved rounds.',
        'Four balanced rotating mode orders run before heavy tests. Charge reconstruction, preparation, discovery, copying, serialization/reload and independent cold checking. Startup/loading, acquisition, pilots, native compilation and final lineage audits are additional.',
        'Every result, clause bank, provenance and search counter must equal the parent checkpoint. Single-snapshot cases may regress because no preparation can be shared.',
        'All prior frontiers, proofs and native results are unchanged. This is an optional replay optimization, not a production default, new native certificate or unrestricted resource bound. Retained evidence space grows.']))



def inputs(p,target):
    source,ts,pairs,events=prior.inputs(old.bound(p['parent_protocol']),target)
    rows={r['event']:r for r in prior.load_frontier(p['seeds']) if r['target']==target}
    return source,ts,[(ref,rows[ref['event']]) for ref,_ in pairs if ref['event'] in rows],events


def search(args,row,mode,counts,limits):
    ordering=mode.split('_',1)[0]
    return prior.candidate.continue_rounds(*args,**options(row),cursor=saved_cursor(row,ordering),ordering=ordering,counts=counts,**limits)


def check(args,row,mode,results,counts):
    ordering,arm=mode.split('_',1)
    if arm=='batch':return candidate.validate_many(*args,**options(row),ordering=ordering,results=results,counts=counts)
    prepared=[candidate.prior.validate(*args,**options(row),ordering=ordering,result=r,counts=counts) for r in results]
    assert all(p==prepared[0] for p in prepared)
    return prepared[0]


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,pairs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref,seed in pairs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==seed['final_source'] and hints==seed['templates']
        args=(state['local'],hints,*arguments(seed)[2:]);cc=Counter();tick=time.perf_counter()
        results=search(args,seed,mode,cc,p['limits']);discovery=time.perf_counter()-tick
        tick=time.perf_counter();bindings=[];cold=[];size=0
        for i,r in enumerate(results):
            path=dest/f'result-{ref["event"]}-round-{i}.json';compact(path,r);cold.append(base.load(path));bindings.append(old.binding(path));size+=path.stat().st_size
        persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();check(args,seed,mode,cold,vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],results=bindings,counts=dict(cc),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,discovery_seconds=discovery,persistence_seconds=persistence,verification_seconds=verification,record_bytes=size))
    compact(dest/'events.json',dict(rows=rows));base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','record_bytes')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        **{k:dict(sum((Counter(r[k]) for r in rows),Counter())) for k in ('counts','reconstruction_counts','verification_counts')}))


def run_census(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'census-{target}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'census',str(out),str(dest),str(target),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),target=target,mode=mode,repeat=repeat))
        print(base.encode(dict(completed_target=target)),flush=True)
    base.write(out/'censuses.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census': census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else: globals()[action](out)
