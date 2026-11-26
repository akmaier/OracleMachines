#!/usr/bin/env python3
"""Charge preparation, continuation, final persistence and cold recovery."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b6_probe_cursor as prior,cnf_prepared_b6_search as candidate
base=prior.base;old=prior.old;c=candidate.candidate;compact=prior.compact;FIELDS=prior.FIELDS
PARENT=Path('experiments/results/cnf-b6-probe-cursor')
MODES=('single','chunks','prepared')
FILES=('experiments/cnf_prepared_b6_search.py','experiments/compare_cnf_prepared_b6_search.py','solver/test_cnf_prepared_b6_search.py')


def advance(args,history,mode,counts):
    if mode not in MODES:raise ValueError('Invalid arm')
    cursor=history['cursor'];steps=0;start=time.perf_counter();session=None;construction=0.0
    if mode=='prepared':
        session=candidate.PreparedB6Search(*args,counts=counts,cursor=cursor);construction=time.perf_counter()-start
    for _ in range(1 if mode=='single' else 8):
        steps+=1;limit=64 if mode=='single' else 8
        result=session.advance(counts,probe_limit=limit) if session is not None else c.discover(*args,counts,cursor=cursor,probe_limit=limit)
        cursor=result['cursor']
        if result['program']['reason']!='probe_limit':break
    return result,steps,time.perf_counter()-start,construction


def pilot(out):
    out.mkdir();rows=[];composed=[]
    for row in base.load(PARENT/'remaining.json')['rows']:
        args=[row[k] for k in FIELDS];arms={}
        for mode in MODES:
            counts=Counter();result,steps,_,_=advance(args,row['b6_probe_cursor'],mode,counts);c.validate(*args,result,Counter())
            arms[mode]=dict(result=result,counts=dict(counts),steps=steps)
        assert arms['single']['result']==arms['chunks']['result']==arms['prepared']['result']
        rows.append(dict(target=row['target'],event=row['event'],arms=arms))
        counts=Counter();prepared=c.validate(*args,row['b6_probe_cursor'],counts)
        bank=tuple(sorted(set(prepared[13])|{(-p['assumption'],) for p in row['b6_probe_cursor']['program']['probes']}))
        fixed,trace,conflict=c.native.propagate(bank,counts);assert conflict is None
        closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
        assert c.prior.check_closure(bank,closure,counts)==fixed
        extra=set(fixed)-dict(row['b5_cursor_feedback_closure']['assignment']).keys()
        composed.append(dict(row,b6_composition_closure=closure,b6_composition_added_variables=sorted(extra),b6_composition_counts=dict(counts)))
    compact(out/'pilot.json',dict(rows=rows));compact(out/'composition-diagnostic.json',dict(rows=composed,scope='All nine parent failures composed and checked on B7. No contradiction. Diagnostic only; no B7 native compiler or new B7 search.'))
    (out/'pilot-source.py').write_bytes(Path(FILES[0]).read_bytes())


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');p=base.load(PARENT/'protocol.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        seeds=old.binding(PARENT/'remaining.json'),old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],
        pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),diagnostic=old.binding(out/'composition-diagnostic.json'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES),list(reversed(MODES))],
        limits=dict(chunk_size=8,chunks=8,single_size=64,work_per_call=262144,trace_limit=256),limitations=[
        'Eighteen exposed B6 cases, including six already exhausted literal orders. The nine parent failures were composed diagnostically first: no contradiction and ten new assignments. No holdout.',
        'All arms reconstruct the source prefix once and continue the identical retained B6 cursor. Single takes one64-probe call. Chunks and prepared take at most eight8-probe calls, stopping immediately on complete/refuted/budget status.',
        'Each call allows262144 occurrence visits and256 trace steps. Chunked arms can spend more total work allowance; observed propagation and final results must match the single arm. Earlier acquisition is excluded.',
        'Prepared owns a deep copy of the original inputs, validates once, retains the exact binding, fixed closure prefix, residual index and live scheduling state, then drops unused proof layers. Public results are deep copies. Same-process private state is trusted; reflection or concurrent mutation is outside contract.',
        'A changed input, closure or trace allowance requires a new checked session. Portable cursor imports and cold recovery validate original inputs and history; no process-global digest-only cache or native proof bypass.',
        'Census charges source reconstruction, construction/copying, all calls, final serialization/reload, full semantic verification and a new cold session construction. Startup/loading, prior acquisition, pilot diagnostic and final audit are additional.',
        'Cold recovery and one uninterrupted pass are controls; warm chunk savings do not imply a cold or single-pass advantage. Per-probe initialization, proof copying, provenance and lifetime storage remain.',
        'All old histories and diagnostic closures remain; new cursors are appended, not overwritten. No production default, native authority table or unrestricted SAT bound changes.']))


def inputs(p,target):
    source,ts,refs,events=prior.inputs(p,target);saved={r['event']:r for r in old.bound(p['seeds'])['rows'] if r['target']==target}
    return source,ts,[dict(r,b6_probe_cursor=saved[r['event']]['b6_probe_cursor']) for r in refs],events


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=prior.prior.bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==ref['saved_source'] and hints==ref['saved_templates']
        args=(state['local'],hints,*(ref[k] for k in FIELDS[2:]));counts=Counter()
        result,steps,elapsed,construction=advance(args,ref['b6_probe_cursor'],mode,counts)
        tick=time.perf_counter();path=dest/f'cursor-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();c.validate(*args,cold,vc);verification=time.perf_counter()-tick
        recover=Counter();tick=time.perf_counter();candidate.PreparedB6Search(*args,counts=recover,cursor=cold['cursor']);recovery=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,steps=steps,counts=dict(counts),verification_counts=dict(vc),recovery_counts=dict(recover),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,continuation_seconds=elapsed,construction_seconds=construction,persistence_seconds=persistence,verification_seconds=verification,recovery_seconds=recovery,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows));base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','continuation_seconds','construction_seconds','persistence_seconds','verification_seconds','recovery_seconds','record_bytes','steps')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,counts=dict(sum((Counter(r['counts']) for r in rows),Counter()))))


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
