#!/usr/bin/env python3
"""Reuse the B13 schema with extended B12 histories; compare old-bank searches."""
from collections import Counter
from itertools import permutations
from pathlib import Path
import resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b12_cold_batch as prior,compare_cnf_b13_probe_cursor as frozen
base=prior.base;old=prior.old;compact=prior.compact;bind=prior.bind;c=frozen.candidate
PARENT=Path('experiments/results/cnf-b12-cold-batch')
MODES=('continue','fresh','strengthen')
CASES=((37,39),(67,63))
FILES=('experiments/compare_cnf_b13_strengthened_histories.py','solver/test_cnf_b13_strengthened_histories.py')


def arguments(row,mode):
    args=frozen.arguments(row)
    if mode=='strengthen':
        return (*args[:24],old.bound(row['b12_batch_source_result']),old.bound(row['b12_batch_unseen_result']),args[26])
    if mode not in ('continue','fresh'):raise ValueError('Invalid comparison mode')
    return args


def options(row,mode):
    kw=frozen.options(row)
    if mode=='strengthen':kw=dict(kw,combined_closure=row['b12_batch_joint_closure'])
    return kw


def search(args,row,mode,counts,limits):
    cursor=old.bound(row['b13_result'])['cursor'] if mode=='continue' else None
    return c.discover(*args,**options(row,mode),cursor=cursor,policy='restart',counts=counts,**limits)


def check(args,row,mode,result,counts):
    return c.validate(*args,**options(row,mode),result=result,counts=counts)


def prepare(out):
    assert not (out/'protocol.json').exists()
    cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        parent_protocol=cp['b12_cold_batch']['protocol'],seeds=cp['b12_cold_batch']['remaining'],targets=[37,67],cases=[list(k) for k in CASES],
        pilot=old.binding(out/'pilot.json'),source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        orders=[list(x) for x in permutations(MODES)],limits=dict(probe_limit=320,work_limit=1310720,trace_limit=256),limitations=[
        'Exploratory follow-up on the two exposed changed cases selected by the parent closure gains. The other twelve open cases are retained unchanged, not repeatedly searched.',
        'The initial pilot used 64 and 320 probes: the declared timing census uses the latter to finish these fixed-bank schedules. It is not held-out evidence or a 64-probe comparison.',
        'Strengthen replaces the two B12 histories in the existing B13 schema with their checked completed extensions. No B14 layer, new proof format or production solver is added.',
        'The shared B13 constructor checks each extension on its original B12 bank. Its supplied complete closure is checked on the reconstructed augmented bank. No discovery authority enters cold checking.',
        'Changed-bank cursors are restarted. Continue uses the old B13 cursor on the original bank; fresh restarts the same original bank. Each gets at most 320 additional probes and 1310720 occurrence work, with trace bound 256.',
        'All six mode permutations run in separate processes before heavy checks, charging source reconstruction, preparation/discovery, every exported proof, serialization/reload and independent cold checking.',
        'Mode timing excludes startup/input loading, historical acquisition, pilots, joint-feedback composition, native compilation and final lineage audit; those remain additional costs.',
        'Combining different arms consumes all their budgets and original-bank proof checks. New failed assumptions or unit closures do not count as new native root certificates.',
        'Open completions retain their honest-production assumption and cannot establish SAT. Exhaustion concerns only this bank, policy and trace bound.',
        'Retain both old and strengthened schedules and all previous native results. Evidence space grows; no uniform arbitrary-SAT acquisition or space bound follows.']))


def inputs(p,target):
    source,ts,pairs,events=prior.inputs(old.bound(p['parent_protocol']),target)
    rows={(r['target'],r['event']):r for r in prior.prior.load_frontier(p['seeds'])}
    return source,ts,[(ref,rows[target,ref['event']]) for ref,_ in pairs if (target,ref['event']) in CASES],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,pairs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref,seed in pairs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==seed['final_source'] and hints==seed['templates']
        args=(state['local'],hints,*arguments(seed,mode)[2:]);cc=Counter();tick=time.perf_counter()
        result=search(args,seed,mode,cc,p['limits']);discovery=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'result-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);size=path.stat().st_size;persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();check(args,seed,mode,cold,vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,counts=dict(cc),verification_counts=dict(vc),reconstruction_counts=dict(rc),
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
    overlay=old.bound(binding);seeds={(r['target'],r['event']):r for r in prior.prior.load_frontier(overlay['parent'])};rows=[];seen=set()
    for delta in overlay['rows']:
        key=delta['target'],delta['event']
        if key not in seeds or key in seen or (set(delta)&set(seeds[key]))-{'target','event'}:raise ValueError('Invalid frontier overlay')
        seen.add(key);rows.append(dict(seeds[key],**delta))
    if seen!=seeds.keys():raise ValueError('Incomplete frontier overlay')
    return rows


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census':census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:globals()[action](out)
