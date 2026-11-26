#!/usr/bin/env python3
"""Isolate common-prefix validation in joint discovery and cold checking."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_probe_cursor as prior,cnf_shared_joint_preparation as candidate
base=prior.base;old=prior.old;compact=prior.compact;bind=prior.bind;FIELDS=prior.FIELDS
PARENT=Path('experiments/results/cnf-joint-probe-cursor')
MODES=('separate','shared_discovery','shared_both')
FILES=('experiments/cnf_shared_joint_preparation.py','experiments/compare_cnf_shared_joint_preparation.py','solver/test_cnf_shared_joint_preparation.py')


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');seeds=old.bound(cp['joint_probe_cursor']['remaining-closures'])['rows']
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),parent_protocol=old.binding(PARENT/'protocol.json'),
        seeds=cp['joint_probe_cursor']['remaining-closures'],targets=sorted({r['target'] for r in seeds}),pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES),list(reversed(MODES))],limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),limitations=[
        'Replay of sixteen currently unresolved cases, reproducing the already retained B8 search result; this is no new search frontier, refutation or held-out coverage.',
        'Separate is the current full discovery/checking route. Shared discovery changes only discovery; shared both uses fresh independent shared preparation again for cold validation. No checked state crosses the boundary between calls.',
        'Original B6, comparison B6 and upper B7 programs, exact bindings, deterministic schedules and proof reasons are all checked. Only their common B6 source/provenance/closure preparation is computed once inside a call.',
        'A differing comparison trace allowance gets a distinct exact binding. The bank, residual and order depend on the common original inputs and not on that allowance. Source and all payloads are privately copied before shared preparation.',
        'The sixteen-case pilot compares every returned prepared bank and result to the frozen implementation. Final audit always uses the frozen full validator, even for the shared-both arm.',
        'Two isolated opposite-order repetitions charge source-prefix reconstruction, discovery including ownership copies and recognition, serialization/reload, and independent full cold checking. Startup/input loading, historical acquisition, pilot and final audit are additional.',
        'Search engine, allowances, logical stages, origin choices and serialized formats are unchanged. Search counters and all results must match across arms. Exhaustion and open completion are not SAT.',
        'The parent open export and all native archives are referenced unchanged. New diagnostic artifacts still increase retained experiment storage. No production-default, native proof-rule, unrestricted-SAT or lifetime-space change.']))


def inputs(p,target):
    source,ts,pairs,events=prior.inputs(old.bound(p['parent_protocol']),target)
    saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    return source,ts,[(ref,saved[ref['event']]) for ref,_ in pairs if ref['event'] in saved],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    discovery=candidate.prior if mode=='separate' else candidate
    checker=candidate if mode=='shared_both' else candidate.prior
    for ref,seed in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==seed['final_source'] and hints==seed['templates']
        args=(state['local'],hints,*(seed[k] for k in FIELDS[2:]));cl=seed['joint_cursor_feedback_closure'];cc=Counter();tick=time.perf_counter()
        result=discovery.discover(*args,closure=cl,counts=cc,**p['limits']);elapsed=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'result-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();checker.validate(*args,closure=cl,result=cold,counts=vc);verification=time.perf_counter()-tick
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
