#!/usr/bin/env python3
"""Matched full-result cold checking plus continuation, with one shared prepare."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_prepared_b6_search as prior,cnf_checked_b6_restore as candidate
base=prior.base;old=prior.old;compact=prior.compact;FIELDS=prior.FIELDS;c=candidate.candidate;bind=prior.prior.prior.bind
PARENT=Path('experiments/results/cnf-prepared-b6-search')
MODES=('separate','shared')
FILES=('experiments/cnf_checked_b6_restore.py','experiments/compare_cnf_checked_b6_restore.py','solver/test_cnf_checked_b6_restore.py')


def recover(args,result,mode,counts):
    if mode=='shared':return candidate.restore(*args,result=result,counts=counts)
    if mode!='separate':raise ValueError('Invalid recovery arm')
    c.validate(*args,result,counts)
    return candidate.PreparedB6Search(*args,counts=counts,cursor=result['cursor'],trace_limit=result['program']['trace_limit'])


def pilot(out):
    out.mkdir();rows=[];diagnostic=[]
    for row in base.load(PARENT/'remaining.json')['rows']:
        args=tuple(row[k] for k in FIELDS);arms={}
        for mode in MODES:
            rc=Counter();session=recover(args,row['b6_prepared_cursor'],mode,rc);ac=Counter();result=session.advance(ac,probe_limit=8)
            c.validate(*args,result,Counter());arms[mode]=dict(result=result,restoration_counts=dict(rc),advance_counts=dict(ac))
        assert arms['separate']['result']==arms['shared']['result'] and arms['separate']['advance_counts']==arms['shared']['advance_counts']
        rows.append(dict(target=row['target'],event=row['event'],arms=arms))
        counts=Counter();prepared=c.validate(*args,row['b6_prepared_cursor'],counts)
        probes=row['b6_prepared_cursor']['program']['probes'];bank=tuple(sorted(set(prepared[13])|{(-p['assumption'],) for p in probes}))
        fixed,trace,conflict=c.native.propagate(bank,counts);assert conflict is None
        closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]));assert c.prior.check_closure(bank,closure,counts)==fixed
        extra=set(fixed)-dict(row['b5_cursor_feedback_closure']['assignment']).keys()
        diagnostic.append(dict(row,b6_composition_closure=closure,b6_composition_added_variables=sorted(extra),b6_composition_counts=dict(counts)))
    compact(out/'pilot.json',dict(rows=rows));compact(out/'composition-diagnostic.json',dict(rows=diagnostic,scope='All24 parent B6 failures composed into B7. No contradiction; seven changed closures gain25 assignments. No B7 native compilation or probing.'))
    (out/'pilot-source.py').write_bytes(Path(FILES[0]).read_bytes())


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');p=base.load(PARENT/'protocol.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),seeds=old.binding(PARENT/'remaining.json'),
        old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),diagnostic=old.binding(out/'composition-diagnostic.json'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES),list(reversed(MODES))],
        limits=dict(probe_limit=8,work_limit=262144,trace_limit=256),limitations=[
        'Eighteen exposed B6 cases. The24 parent failures were composed diagnostically first: no contradiction,25 new assignments in seven cases. No holdout.',
        'Both arms check the complete portable result, including its redundant program/terminal fields, and construct an owned session. Separate runs the existing validator and constructor. Shared validates once and internally transfers the checked schedule and bank.',
        'The shared path deep-copies caller input and the entire result before checking. It accepts no external verified flag, digest-only cache or prepared token. It allocates continuation state only after all original full-result checks pass.',
        'Each arm makes one eight-probe continuation with262144 occurrence visits and the saved trace bound. Final results and advancement counters must match exactly; open or exhausted states are not SAT.',
        'Census charges source-prefix reconstruction, full checking and restoration including copies, continuation, final serialization/reload and independent full semantic validation. Startup/input loading, prior acquisition, composition diagnostic and final audit are additional.',
        'This isolates one cold recovery plus a short continuation. It is not directly comparable to the previous64-probe/chunk experiment and does not claim a benefit over merely importing a cursor while ignoring the complete result contract.',
        'The returned object uses the frozen PreparedB6Search private layout. Input edits require a new checked session; reflection or concurrent private mutation is outside its ownership contract. Native compilers retain their full checks.',
        'All older histories and diagnostic closures remain. No production default, native authority records, unrestricted SAT theorem or lifetime-space bound changes.']))


def inputs(p,target):
    source,ts,refs,events=prior.inputs(p,target);saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    return source,ts,[dict(r,b6_prepared_cursor=saved[r['event']]['b6_prepared_cursor']) for r in refs],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==ref['saved_source'] and hints==ref['saved_templates']
        args=(state['local'],hints,*(ref[k] for k in FIELDS[2:]));counts=Counter();tick=time.perf_counter()
        session=recover(args,ref['b6_prepared_cursor'],mode,counts);restoration=time.perf_counter()-tick
        ac=Counter();tick=time.perf_counter();result=session.advance(ac,probe_limit=8);elapsed=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'cursor-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();c.validate(*args,cold,vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,restoration_counts=dict(counts),advance_counts=dict(ac),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,restoration_seconds=restoration,advance_seconds=elapsed,persistence_seconds=persistence,verification_seconds=verification,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows));base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','restoration_seconds','advance_seconds','persistence_seconds','verification_seconds','record_bytes')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        restoration_counts=dict(sum((Counter(r['restoration_counts']) for r in rows),Counter())),advance_counts=dict(sum((Counter(r['advance_counts']) for r in rows),Counter()))))


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
