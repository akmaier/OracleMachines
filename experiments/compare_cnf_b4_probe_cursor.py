#!/usr/bin/env python3
"""Fresh B4 probe bindings: all open cases versus changed banks/closures."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cursor_feedback as prior,cnf_b4_probe_cursor as candidate
base=prior.base;old=prior.old;compact=prior.compact
PARENT=Path('experiments/results/cnf-direct-unit-closure')
SEEDS=Path('experiments/results/cnf-cursor-feedback')
MODES=('all','changed')
FIELDS=('final_source','templates','seed','closure','new','next_closure','third','feedback_closure','probe_cursor','cursor_feedback_closure')
FILES=('experiments/cnf_b4_probe_cursor.py','experiments/compare_cnf_b4_probe_cursor.py','solver/test_cnf_b4_probe_cursor.py')


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');p=base.load(SEEDS/'protocol.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        seeds=old.binding(SEEDS/'remaining-closures.json'),seed_protocol=old.binding(SEEDS/'protocol.json'),old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],
        pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),
        limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),orders=[list(MODES),list(reversed(MODES))],
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},limitations=[
        'Same29 exposed unresolved B4 cases; no holdout. Both arms reconstruct and check all earlier provenance and closures. All probes every case; changed skips10 exactly unchanged B3/B4 bank-and-assignment pairs.',
        'New cursors bind the exact B4 bank, source, closure, order, policy and trace limit. Old B3 history supplies checked implications but never skips candidates in B4. Open history remains trusted scheduling data, not a SAT or exhaustive-proof certificate.',
        'Per searched case:64 new assumptions,262144 occurrence visits,256 proof steps including the closure prefix. Index construction, per-probe initialization, preparation, checking and persistence are additionally charged in counters/timings. No global linear-work claim.',
        'Two opposite-order isolated repetitions per target. Complete census includes source-prefix reconstruction, discovery, JSON write/reload, semantic cold checking and reporting; startup/input loading, earlier acquisition and final audit are additional.',
        'No direct refutations observed. Saved B4 failure traces have checked provenance but are not native whole-root certificates. No new cumulative records or native archives, production changes or broader coverage claim.',
        'Skipping unchanged cases is a heuristic policy. A preserved counterexample shows missed refutation; equality of observed failures on this sample is not a general coverage guarantee.',
        'Exact bindings duplicate full content. Retained histories and growing proof layers remain unbounded; no unrestricted SAT or P-versus-NP conclusion.']))


def inputs(p,target):
    source,ts,refs,events=prior.inputs(p,target)
    saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    return source,ts,[dict(ref,cursor_feedback_closure=saved[ref['event']]['cursor_feedback_closure']) for ref in refs],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=prior.bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']]
        assert list(map(list,state['local']))==ref['saved_source'] and hints==ref['saved_templates']
        args=(state['local'],hints,*(ref[k] for k in FIELDS[2:]))
        c=Counter();tick=time.perf_counter();result=candidate.discover(*args,c,policy=mode,**p['limits']);discovery=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'cursor-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();candidate.validate(*args,cold,vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,counts=dict(c),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,discovery_seconds=discovery,persistence_seconds=persistence,verification_seconds=verification,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','record_bytes')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter()))))


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
    if action=='census':census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:globals()[action](out)
