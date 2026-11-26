#!/usr/bin/env python3
"""Compose current B6 failures and compare changed-bank discovery with exact reuse."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_checked_b6_restore as prior,cnf_b7_probe_cursor as candidate
base=prior.base;old=prior.old;compact=prior.compact;bind=prior.bind;c=candidate
PARENT=Path('experiments/results/cnf-checked-b6-restore')
FIELDS=(*prior.FIELDS,'b6_checked_restore_cursor')
MODES=('base','restart','matched','reuse')
FILES=('experiments/cnf_b6_cursor_feedback.py','experiments/cnf_b7_probe_cursor.py','experiments/compare_cnf_b7_probe_cursor.py','solver/test_cnf_b7_probe_cursor.py')


def compose(args,counts):
    prepared=c.feedback.prepare(*args,counts)
    fixed,trace,conflict=c.native.propagate(prepared[15],counts)
    if conflict is not None:raise ValueError('Composition refutation needs a separate native-compilation checkpoint')
    closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
    assert c.prior.check_closure(prepared[15],closure,counts)==fixed
    return closure


def search(args,closure,mode,counts):
    if mode=='base':return c.feedback.cursor.discover(*args[:-1],counts,cursor=args[-1]['cursor'],probe_limit=64)
    if mode not in MODES:raise ValueError('Invalid census arm')
    # Matched work allowance is only expanded for an exact importable bank.
    # Both fresh controls must reproduce the reused frontier when extended.
    extra=0
    if mode=='matched':
        p,*_=c.prepare(*args,closure,counts)
        if c.equivalent(p,args[-2],closure,args[-1],256,counts):extra=len(args[-1]['cursor']['completed'])
    return c.discover(*args,closure,counts,policy='reuse' if mode=='reuse' else 'restart',probe_limit=64+extra,work_limit=262144*(1+(extra+63)//64))


def check(args,closure,result,mode,counts):
    if mode=='base':return c.feedback.cursor.validate(*args[:-1],result,counts)
    return c.validate(*args,closure,result,counts)


def pilot(out):
    out.mkdir();rows=[]
    for seed in base.load(PARENT/'remaining.json')['rows']:
        args=tuple(seed[k] for k in FIELDS);cc=Counter();closure=compose(args,cc);arms={}
        for mode in MODES:
            counts=Counter();result=search(args,closure,mode,counts);check(args,closure,result,mode,Counter())
            arms[mode]=dict(result=result,counts=dict(counts))
        assert arms['matched']['result']==arms['reuse']['result']
        added=sorted(set(dict(closure['assignment']))-dict(args[-2]['assignment']).keys())
        rows.append(dict(target=seed['target'],event=seed['event'],closure=closure,composition_counts=dict(cc),additional_variables=added,arms=arms))
    compact(out/'pilot.json',dict(rows=rows));(out/'pilot-source.py').write_bytes(Path(FILES[1]).read_bytes())
    print(base.encode([dict(target=r['target'],event=r['event'],added=len(r['additional_variables']),arms={m:dict(status=a['result']['program']['status'],reason=a['result']['program']['reason'],failures=len(a['result']['program']['probes']),probes=a['counts'].get('probe_roots',0),imported=a['counts'].get('b7_imported_completed',0)) for m,a in r['arms'].items()}) for r in rows]))


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');p=base.load(PARENT/'protocol.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),seeds=old.binding(PARENT/'remaining.json'),
        old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES),list(reversed(MODES))],
        limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),limitations=[
        'Eighteen exposed cases, no held-out speed or recognition claim. All 25 current B6 failures are composed first; composition adds 26 assignments in seven cases and no contradiction.',
        'Base continues the old B6 frontier. Restart probes the new B7 bank from scratch for 64 assumptions. Matched extends fresh search to the reused frontier on exact bank/closure/trace-bound matches. Reuse imports only such matches; changed inputs start fresh.',
        'Matched also pays an extra eligibility preparation and comparison to size its allowance. Report this overhead separately: its end-to-end time is not a pure measure of repeated probe cost.',
        'Composition is a complete scan-based checked fixed point and is charged in B7 arms, outside the bounded occurrence-probe budget. Prior acquisition, startup/input loading and final audit are additional.',
        'Each census charges source-prefix reconstruction, composition, discovery, serialization/reload, and independent checking including closure and every prior proof layer. Counts and all regressions are retained.',
        'Completed open assumptions are scheduling history, not SAT certificates; trusted exhaustive coverage is not inferred from imported history. Every failed assumption is independently checked before use.',
        'This checkpoint adds checked B7 search but no native B7 compiler or production default. No new authority records or cumulative table changes. Arbitrary-SAT complexity and lifetime-space bounds remain open.']))


def inputs(p,target):
    source,ts,refs,events=prior.inputs(p,target);saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    return source,ts,[dict(r,b6_checked_restore_cursor=saved[r['event']]['b6_checked_restore_cursor']) for r in refs],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==ref['saved_source'] and hints==ref['saved_templates']
        args=(state['local'],hints,*(ref[k] for k in FIELDS[2:]));cc=Counter();tick=time.perf_counter();closure=None if mode=='base' else compose(args,cc);composition=time.perf_counter()-tick
        counts=Counter();tick=time.perf_counter();result=search(args,closure,mode,counts);discovery=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'cursor-{ref["event"]}.json';compact(path,dict(closure=closure,result=result));cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();check(args,cold['closure'],cold['result'],mode,vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,composition_counts=dict(cc),counts=dict(counts),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,composition_seconds=composition,discovery_seconds=discovery,persistence_seconds=persistence,verification_seconds=verification,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows));base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','composition_seconds','discovery_seconds','persistence_seconds','verification_seconds','record_bytes')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter())),composition_counts=dict(sum((Counter(r['composition_counts']) for r in rows),Counter()))))


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
