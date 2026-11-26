#!/usr/bin/env python3
"""Compare B11 restart, matched fresh, exact reuse and continuing B10."""
from collections import Counter
from pathlib import Path
import resource, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shared_b10_preparation as prior, cnf_b11_probe_cursor as candidate
base=prior.base; old=prior.old; compact=prior.compact; bind=prior.bind
PARENT=Path('experiments/results/cnf-shared-b10-preparation')
MODES=('b10', 'restart', 'matched', 'reuse')
FILES=('experiments/cnf_b11_probe_cursor.py', 'experiments/compare_cnf_b11_probe_cursor.py', 'solver/test_cnf_b11_probe_cursor.py')


def arguments(row):
    return (*prior.prior.arguments(row),old.bound(row['b10_result']))


def options(row):
    return dict(**prior.prior.options(row),next_closure=row['b10_feedback_closure'])


def prepare(out):
    assert not (out/'protocol.json').exists()
    cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items(): assert base.sha(f)==h, f
    seeds=cp['shared_b10_preparation']['remaining']
    base.write(out/'protocol.json', dict(parent=old.binding(PARENT/'checkpoint.json'), parent_manifest=old.binding(PARENT/'manifest.json'),
        parent_protocol=old.binding(PARENT/'protocol.json'), seeds=seeds, targets=sorted({r['target'] for r in prior.prior.load_frontier(seeds)}),
        pilot=old.binding(out/'pilot.json'), pilot_source=old.binding(out/'pilot-source.py'), comparison_pilot=old.binding(out/'b10-comparison-pilot.json'),
        source_fingerprints={**cp['source_fingerprints'], **{f:base.sha(f) for f in FILES}},
        orders=[list(MODES),list(reversed(MODES))], limits=dict(probe_limit=64,work_limit=262144,trace_limit=256), limitations=[
        'Fourteen exposed unresolved inputs. B11 composes checked B10 failures; no arbitrary-SAT or held-out coverage claim.',
        'B10 source histories use shared B8 preparation independently in discovery and checking. No trusted state crosses calls.',
        'Reuse imports B10 completions only for equal source-derived banks, full closure traces and trace bounds. Every failed assumption keeps its original-bank proof. Open completions are scheduling hints, never SAT authority.',
        'Matched fresh adds reusable completions to its probe budget and scales occurrence allowance; equality is checked for this workload, not guaranteed for arbitrary interrupted probes.',
        'Fixed-budget restart and continuing B10 are distinct coverage/cost comparisons, not matched controls. Stronger banks may restart and miss implications reached by an older unfinished schedule.',
        'Two isolated opposite-order repetitions charge reconstruction, owned recognition/preparation, search, independent cold checking and serialization/reload. Loading/startup, acquisition, pilots and final audits are additional; feedback and export are measured separately.',
        'New individual and combined closures use independently checked B11 and continued B10 failures. No native certificate or compiler is added. Neither exhaustion nor unresolved status certifies SAT.',
        'The new overlay references the entire immutable parent frontier and both result sets. All older histories and certificates remain; lifetime storage grows.']))


def inputs(p,target):
    source,ts,pairs,events=prior.inputs(old.bound(p['parent_protocol']),target)
    rows={r['event']:r for r in prior.prior.load_frontier(p['seeds']) if r['target']==target}
    return source,ts,[(ref,rows[ref['event']]) for ref,_ in pairs if ref['event'] in rows],events


def search(args,row,mode,counts,limits):
    if mode=='b10':
        return candidate.shared.discover(*args[:-1],**prior.prior.options(row),cursor=args[-1]['cursor'],counts=counts,**limits)
    return candidate.discover(*args,**options(row),policy=mode,counts=counts,**limits)


def check(args,row,mode,result,counts):
    if mode=='b10':
        return candidate.shared.validate(*args[:-1],**prior.prior.options(row),result=result,counts=counts)
    return candidate.validate(*args,**options(row),result=result,counts=counts)


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json'); source,ts,pairs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref,seed in pairs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']]
        assert list(map(list,state['local']))==seed['final_source'] and hints==seed['templates']
        args=(state['local'],hints,*arguments(seed)[2:])
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
    overlay=old.bound(binding);seeds={(r['target'],r['event']):r for r in prior.prior.load_frontier(overlay['parent'])}
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
