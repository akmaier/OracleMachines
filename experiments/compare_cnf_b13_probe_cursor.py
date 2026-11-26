#!/usr/bin/env python3
"""Compare joint B13 expansion with continuation of both B12 schedules."""
from collections import Counter
from pathlib import Path
import resource, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b12_progress_order as prior, cnf_b13_probe_cursor as candidate
base=prior.base; old=prior.old; compact=prior.compact; bind=prior.bind
PARENT=Path('experiments/results/cnf-shared-b12-preparation')
MODES=('source', 'unseen', 'reuse', 'matched')
FILES=('experiments/cnf_b13_probe_cursor.py', 'experiments/compare_cnf_b13_probe_cursor.py', 'solver/test_cnf_b13_probe_cursor.py')


def arguments(row):
    return (*prior.arguments(row),*(old.bound(row[f]) for f in ('b12_source_result','b12_unseen_result','b11_continuation_result')))


def options(row):
    return dict(**prior.options(row),combined_closure=row['b12_joint_closure'])


def prepare(out):
    assert not (out/'protocol.json').exists()
    cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items(): assert base.sha(f)==h, f
    seeds=cp['shared_b12_preparation']['remaining']
    base.write(out/'protocol.json', dict(parent=old.binding(PARENT/'checkpoint.json'), parent_manifest=old.binding(PARENT/'manifest.json'),
        parent_protocol=cp['b12_progress_order']['protocol'], seeds=seeds, targets=sorted({r['target'] for r in prior.load_frontier(seeds)}),
        pilot=old.binding(out/'pilot.json'), pilot_source=old.binding(out/'pilot-source.py'),
        source_fingerprints={**cp['source_fingerprints'], **{f:base.sha(f) for f in FILES}},
        orders=[list(MODES),list(reversed(MODES))], limits=dict(probe_limit=64,work_limit=262144,trace_limit=256), limitations=[
        'Fourteen exposed unresolved inputs. Joint B13 expansion is compared with continuing both B12 policies; no held-out or efficient arbitrary-SAT coverage claim.',
        'B12 source and unseen results and B11 continuation retain independent original-bank proof checks. One owned common B12 preparation supports all three; different policy and trace bindings remain distinct.',
        'B13 uses deterministic source order. Exact clause-bank, full closure trace and trace-bound equality permits importing only the checked source-order B12 cursor. On changed banks every assumption is freshly probed.',
        'Matched replaces imported completions with fresh extra probe/work allowance. The complete result must equal reuse on this workload. Open completions never certify SAT or semantic exhaustion.',
        'Both B12 continuations have the same additional 64-probe allowance as B13 reuse. Combining their discoveries costs both budgets; it is not a single-budget comparison.',
        'Two isolated opposite-order repetitions charge reconstruction, owned preparation, recognition, discovery, persistence/reload and cold checking. Startup/loading, acquisition, pilots, native compilation and final lineage auditing are additional.',
        'Feedback diagnostics retain old-bank proof provenance and all prior histories. A contradiction would require native source-only reconstruction before counting a new certified root.',
        'No persistent trusted state is passed between discovery and checking. New experiment files increase retained space; no production default or lifetime-space bound changes.']))



def inputs(p,target):
    source,ts,pairs,events=prior.inputs(old.bound(p['parent_protocol']),target)
    rows={r['event']:r for r in prior.load_frontier(p['seeds']) if r['target']==target}
    return source,ts,[(ref,rows[ref['event']]) for ref,_ in pairs if ref['event'] in rows],events


def search(args,row,mode,counts,limits):
    if mode in ('source','unseen'):
        return candidate.shared.discover(*args[:24],**prior.options(row),ordering=mode,
            cursor=args[24 if mode=='source' else 25]['cursor'],counts=counts,**limits)
    return candidate.discover(*args,**options(row),policy=mode,counts=counts,**limits)


def check(args,row,mode,result,counts):
    if mode in ('source','unseen'):
        return candidate.shared.validate(*args[:24],**prior.options(row),ordering=mode,result=result,counts=counts)
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
    overlay=old.bound(binding);seeds={(r['target'],r['event']):r for r in prior.load_frontier(overlay['parent'])}
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
