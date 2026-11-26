#!/usr/bin/env python3
"""Compare B9 restart, matched fresh, exact reuse and continuing B8."""
from collections import Counter
from pathlib import Path
import resource, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_prepared_prefix_replay as prior, cnf_b9_probe_cursor as candidate
base=prior.base; old=prior.old; compact=prior.compact; FIELDS=prior.FIELDS
PARENT=Path('experiments/results/cnf-prepared-prefix-replay')
MODES=('b8', 'restart', 'matched', 'reuse')
FILES=('experiments/cnf_b9_probe_cursor.py', 'experiments/compare_cnf_b9_probe_cursor.py', 'solver/test_cnf_b9_probe_cursor.py')


def arguments(row):
    return (*(row[k] for k in FIELDS), row['joint_probe_cursor'])


def options(row):
    return dict(closure=row['joint_cursor_feedback_closure'], feedback_closure=row['joint_probe_feedback_closure'])


def prepare(out):
    assert not (out/'protocol.json').exists()
    cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items(): assert base.sha(f)==h, f
    seeds=cp['prepared_prefix_replay']['remaining']
    base.write(out/'protocol.json', dict(parent=old.binding(PARENT/'checkpoint.json'), parent_manifest=old.binding(PARENT/'manifest.json'),
        parent_protocol=old.binding(PARENT/'protocol.json'), seeds=seeds, targets=sorted({r['target'] for r in old.bound(seeds)['rows']}),
        pilot=old.binding(out/'pilot.json'), pilot_source=old.binding(out/'pilot-source.py'),
        source_fingerprints={**cp['source_fingerprints'], **{f:base.sha(f) for f in FILES}},
        orders=[list(MODES),list(reversed(MODES))], limits=dict(probe_limit=64,work_limit=262144,trace_limit=256), limitations=[
        'Sixteen exposed unresolved inputs. B9 composes the checked B8 failures; no arbitrary-SAT or held-out coverage claim.',
        'Reuse imports B8 completions only when exact source-derived bank, complete closure including trace order, and trace bound agree. Every source proof and retained failed assumption is checked. Open completions remain scheduling hints, not SAT certificates.',
        'Matched fresh adds imported completion count to its probe budget and scales its work allowance. Exact result equality is audited for these inputs, not guaranteed when budgets interrupt different individual probes.',
        'Restart uses the same fixed allowance without imported history; B8 continuation uses the older bank and is a separate coverage/cost comparison, not a matched control.',
        'Two isolated opposite-order repetitions charge current context source reconstruction, owned discovery/recognition, independent cold checking and result persistence/reload. Startup/input loading, pilot, historical acquisition, final lineage audit and separately measured feedback/export are additional.',
        'New feedback closures are derived from independently checked B9 failed assumptions. There is no new native compiler or native certificate in this checkpoint. Exhaustion and unresolved status are not SAT.',
        'The new frontier is an overlay referencing the immutable complete parent frontier. Loading verifies that binding. Prior B8 and new B9 histories both remain available. New artifacts still grow lifetime storage.']))


def inputs(p,target): return prior.inputs(old.bound(p['parent_protocol']),target)


def search(args,row,mode,counts,limits):
    if mode=='b8':
        return prior.search.discover(*args[:-1],closure=row['joint_cursor_feedback_closure'],
            cursor=row['joint_probe_cursor']['cursor'],counts=counts,**limits)
    return candidate.discover(*args,**options(row),policy=mode,counts=counts,**limits)


def check(args,row,mode,result,counts):
    if mode=='b8':
        return prior.search.validate(*args[:-1],closure=row['joint_cursor_feedback_closure'],result=result,counts=counts)
    return candidate.validate(*args,**options(row),result=result,counts=counts)


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json'); source,ts,pairs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref,seed in pairs:
        rc=Counter();tick=time.perf_counter();_,_,state=prior.candidate.bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']]
        assert list(map(list,state['local']))==seed['final_source'] and hints==seed['templates']
        args=(state['local'],hints,*(seed[k] for k in FIELDS[2:]),seed['joint_probe_cursor'])
        cc=Counter();tick=time.perf_counter();result=search(args,seed,mode,cc,p['limits']);discovery=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'result-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();check(args,seed,mode,cold,vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,counts=dict(cc),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,discovery_seconds=discovery,persistence_seconds=persistence,verification_seconds=verification,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
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
    overlay=old.bound(binding);seeds={(r['target'],r['event']):r for r in old.bound(overlay['parent'])['rows']}
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
