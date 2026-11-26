#!/usr/bin/env python3
"""Compare separate composition/search with one owned checked expansion."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b7_probe_cursor as prior,cnf_fused_b7_expansion as candidate
base=prior.base;old=prior.old;compact=prior.compact;bind=prior.bind;FIELDS=prior.FIELDS;c=candidate.c
PARENT=Path('experiments/results/cnf-b7-probe-cursor')
MODES=('split','fused_rebuild','fused')
FILES=('experiments/cnf_fused_b7_expansion.py','experiments/compare_cnf_fused_b7_expansion.py','solver/test_cnf_fused_b7_expansion.py')


def run(args,mode,counts):
    if mode=='split':
        closure=prior.compose(args,counts)
        return dict(closure=closure,result=c.discover(*args,closure,counts))
    if mode not in MODES:raise ValueError('Invalid expansion mode')
    return candidate.expand(*args,counts=counts,reuse_unchanged=mode=='fused')


def check(args,payload,counts):return c.validate(*args,payload['closure'],payload['result'],counts)


def pilot(out):
    out.mkdir();rows=[]
    for seed in base.load(PARENT/'remaining.json')['rows']:
        args=tuple(seed[k] for k in FIELDS);arms={}
        for mode in MODES:
            counts=Counter();payload=run(args,mode,counts);check(args,payload,Counter())
            arms[mode]=dict(payload=payload,counts=dict(counts))
        assert all(a['payload']==arms['split']['payload'] for a in arms.values())
        assert arms['fused']['payload']==dict(closure=seed['b6_cursor_feedback_closure'],result=seed['b7_probe_cursor'])
        rows.append(dict(target=seed['target'],event=seed['event'],arms=arms))
    compact(out/'pilot.json',dict(rows=rows));(out/'pilot-source.py').write_bytes(Path(FILES[0]).read_bytes())


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json');p=base.load(PARENT/'protocol.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),seeds=old.binding(PARENT/'remaining.json'),
        old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES),list(reversed(MODES))],
        limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),limitations=[
        'Replay of the same eighteen exposed expansion inputs from the B7 checkpoint, not additional search or held-out coverage. All three arms must reproduce the same parent closures and B7 results on this corpus.',
        'Split independently prepares for composition and discovery. Fused rebuild validates once but reconstructs every bank/closure. Fused also reuses the bank, closure trace, residual view and checked schedule on empty checked B6 failure sets.',
        'All original source, guard, earlier-layer, closure, full program, cursor-binding and failure checks precede the internal handoff. Caller inputs are privately copied. No externally supplied prepared token or verified flag is accepted.',
        'For an unchanged bank the optimized API may retain any valid existing closure trace. An alternate trace can produce a different valid portable result than scan-based recomputation; exact result equality is claimed for the measured canonical-closure corpus, not arbitrary trace reorderings.',
        'Original B6 result must be unresolved; contradictory composition is explicitly rejected for separate feedback handling. No B7 native compiler or new authority record is introduced.',
        'Census charges source-prefix reconstruction, complete expansion including recognition and copies, final serialization/reload and full independent checking. Startup/input loading, historical acquisition and final audit are additional.',
        'Each new probe still pays full residual-clause initialization. Complete scan-based composition on changed banks lies outside the occurrence-probe budget. Exact binding serialization and final independent validation remain charged.',
        'The parent open export and both discovery histories are referenced unchanged, not duplicated into another remaining file. Census artifacts still increase experiment storage. No lifetime memory or unrestricted-SAT bound is claimed.']))


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=prior.inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==ref['saved_source'] and hints==ref['saved_templates']
        args=(state['local'],hints,*(ref[k] for k in FIELDS[2:]));counts=Counter();tick=time.perf_counter();payload=run(args,mode,counts);elapsed=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'cursor-{ref["event"]}.json';compact(path,payload);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();check(args,cold,vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,counts=dict(counts),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,expansion_seconds=elapsed,persistence_seconds=persistence,verification_seconds=verification,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows));base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','expansion_seconds','persistence_seconds','verification_seconds','record_bytes')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter()))))


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
