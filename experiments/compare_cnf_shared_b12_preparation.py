#!/usr/bin/env python3
"""Isolate common-prefix validation in joint discovery and cold checking."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b12_progress_order as prior,cnf_shared_b12_preparation as candidate
base=prior.base;old=prior.old;compact=prior.compact;bind=prior.bind
PARENT=Path('experiments/results/cnf-b12-progress-order')
ARMS=('separate','shared_discovery','shared_both')
MODES=tuple(order+'_'+arm for order in ('source','unseen') for arm in ARMS)
FILES=('experiments/cnf_shared_b12_preparation.py','experiments/compare_cnf_shared_b12_preparation.py','solver/test_cnf_shared_b12_preparation.py')


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');seeds=prior.prior.load_frontier(old.bound(cp['b12_progress_order']['protocol'])['seeds'])
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),parent_protocol=old.binding(PARENT/'protocol.json'),
        seeds=old.bound(cp['b12_progress_order']['protocol'])['seeds'],remaining=cp['b12_progress_order']['remaining'],targets=sorted({r['target'] for r in seeds}),pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES),list(reversed(MODES))],limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),limitations=[
        'Fourteen exposed unresolved B12 inputs, both source and unseen orderings. Exact replay optimization, not additional coverage or held-out performance.',
        'Separate is frozen B12. Shared discovery changes discovery only; shared both prepares independently again for cold validation. No prepared state crosses calls.',
        'Original B10, comparison B10 and B11 retain independent exact bindings, schedules and original-bank proof checking. Common B10 prefix/provenance/closure preparation is shared within an owned call.',
        'Different history trace bounds receive distinct bindings. Common bank, provenance and residual order are independent of the bound. Ownership copies precede preparation.',
        'Every pilot and timed result must equal its preserved B12 result. Final audit uses the frozen full validator and the independent B12 bank/provenance reconstruction on every result.',
        'Two isolated opposite-order repetitions charge reconstruction, ownership, preparation, search, serialization/reload and cold checking. Startup/input loading, acquisition, pilots, native compilation and final lineage auditing are additional.',
        'Order policies, allowances, origin choices, trace ordering and serialized formats are unchanged. Open completions remain scheduling hints; exhaustion is never SAT.',
        'The B12 remaining overlay, both complementary proof sets, native archives and reference tables stay unchanged. New diagnostics add storage. No production default, unrestricted efficiency or lifetime-space bound changes.']))



def inputs(p,target):
    source,ts,pairs,events=prior.inputs(old.bound(p['parent_protocol']),target)
    saved={r['event']:r for r in prior.prior.load_frontier(p['seeds']) if r['target']==target}
    return source,ts,[(ref,saved[ref['event']]) for ref,_ in pairs if ref['event'] in saved],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    ordering,arm=mode.split('_',1)
    discovery=candidate.prior if arm=='separate' else candidate
    checker=candidate if arm=='shared_both' else candidate.prior
    for ref,seed in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==seed['final_source'] and hints==seed['templates']
        args=(state['local'],hints,*prior.arguments(seed)[2:]);kw=dict(**prior.options(seed),ordering=ordering);cc=Counter();tick=time.perf_counter()
        result=discovery.discover(*args,**kw,counts=cc,**p['limits']);elapsed=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'result-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();checker.validate(*args,**kw,result=cold,counts=vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,counts=dict(cc),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,discovery_seconds=elapsed,persistence_seconds=persistence,verification_seconds=verification,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows));base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','record_bytes')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter())),verification_counts=dict(sum((Counter(r['verification_counts']) for r in rows),Counter()))))


def run_census(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'census-{target}-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'census',str(out),str(dest),str(target),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),target=target,mode=mode,repeat=repeat))
        print(base.encode(dict(completed_target=target)),flush=True)
    base.write(out/'censuses.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census':census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:globals()[action](out)
