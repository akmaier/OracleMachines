#!/usr/bin/env python3
"""Compare repeated B12 continuation calls with one privately prepared batch."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import resource, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b13_probe_cursor as prior, cnf_b12_continuation_batch as candidate
base=prior.base; old=prior.old; compact=prior.compact; bind=prior.bind
PARENT=Path('experiments/results/cnf-b13-probe-cursor')
MODES=('source_separate', 'source_batch', 'unseen_separate', 'unseen_batch')
FILES=('experiments/cnf_b12_continuation_batch.py', 'experiments/compare_cnf_b12_continuation_batch.py', 'solver/test_cnf_b12_continuation_batch.py')


def arguments(row):return prior.prior.arguments(row)


def options(row):return prior.prior.options(row)


def saved_cursor(row,ordering):
    return old.bound(row['b12_'+ordering+'_continuation_result'])['cursor']


def prepare(out):
    assert not (out/'protocol.json').exists()
    cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items(): assert base.sha(f)==h, f
    seeds=cp['b13_probe_cursor']['remaining']
    base.write(out/'protocol.json', dict(parent=old.binding(PARENT/'checkpoint.json'), parent_manifest=old.binding(PARENT/'manifest.json'),
        parent_protocol=cp['b13_probe_cursor']['protocol'], seeds=seeds, targets=sorted({r['target'] for r in prior.load_frontier(seeds)}),
        pilot=old.binding(out/'pilot.json'), pilot_source=old.binding(out/'pilot-source.py'),
        source_fingerprints={**cp['source_fingerprints'], **{f:base.sha(f) for f in FILES}},
        orders=[list(MODES[i:]+MODES[:i]) for i in range(4)], limits=dict(rounds=3,probe_limit=64,work_limit=262144,trace_limit=256), limitations=[
        'Fourteen exposed unresolved cases, both B12 orders. At most three additional 64-probe rounds per order, with equal per-round budgets in both implementations.',
        'Separate calls the current shared-B12 discovery API each round. Batch owns inputs once and prepares the identical bank once; each round reloads its portable cursor and retains its own index build and budget.',
        'Never reuse a stopped mutable queue: the search may have popped an uncompleted root. Portable completed history reconstructs the exact next root and promotion.',
        'Stop on refutation, generated complete reason or zero completed progress. Every exported snapshot is copied and cold checked separately through the existing B12 validator in both arms.',
        'Four balanced rotating mode orders run before heavy tests. Charge reconstruction, owned preparation, recognition, cursor reload, search, snapshot copying, persistence/reload and per-snapshot cold checking.',
        'Startup/input loading, acquisition, pilots, native compilation, feedback composition and final lineage audits are additional. A multi-round or multi-order union consumes all its constituent budgets.',
        'Open completions remain scheduling hints. Exhausting both B12 orders does not solve SAT and does not exhaust other stronger-bank searches.',
        'New implications and both histories are retained without a new native certificate or production default. No persistent trusted state or unrestricted resource bound; evidence increases lifetime storage.']))



def inputs(p,target):
    source,ts,pairs,events=prior.inputs(old.bound(p['parent_protocol']),target)
    rows={r['event']:r for r in prior.load_frontier(p['seeds']) if r['target']==target}
    return source,ts,[(ref,rows[ref['event']]) for ref,_ in pairs if ref['event'] in rows],events


def search(args,row,mode,counts,limits):
    ordering,arm=mode.split('_',1); saved=saved_cursor(row,ordering)
    if arm=='batch':return candidate.continue_rounds(*args,**options(row),cursor=saved,ordering=ordering,counts=counts,**limits)
    results=[]
    for _ in range(limits['rounds']):
        before=len(saved['completed'])
        result=candidate.prior.discover(*args,**options(row),cursor=saved,ordering=ordering,counts=counts,
            **{k:v for k,v in limits.items() if k!='rounds'})
        results.append(deepcopy(result))
        if result['program']['status']=='refuted' or result['program']['reason']=='complete' or len(result['cursor']['completed'])==before:break
        saved=result['cursor']
    return results


def check(args,row,mode,results,counts):
    ordering=mode.split('_',1)[0]
    return [candidate.prior.validate(*args,**options(row),ordering=ordering,result=r,counts=counts) for r in results]


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


def load_frontier(binding):
    overlay=old.bound(binding);seeds={(r['target'],r['event']):r for r in prior.load_frontier(overlay['parent'])}
    rows=[];seen=set()
    for delta in overlay['rows']:
        key=delta['target'],delta['event']
        if key not in seeds or key in seen or (set(delta)&set(seeds[key]))-{'target','event'}:
            raise ValueError('Invalid frontier overlay')
        seen.add(key);rows.append(dict(seeds[key],**delta))
    if seen!=seeds.keys(): raise ValueError('Incomplete frontier overlay')
    return rows


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census': census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else: globals()[action](out)
