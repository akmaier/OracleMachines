#!/usr/bin/env python3
"""Measure one local proof context per source event, with unchanged search."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shared_joint_preparation as prior,cnf_prepared_prefix_replay as candidate
base=prior.base;old=prior.old;compact=prior.compact;FIELDS=prior.FIELDS;search=prior.candidate
PARENT=Path('experiments/results/cnf-shared-joint-preparation');MODES=('frozen','context')
FILES=('experiments/cnf_prepared_prefix_replay.py','experiments/compare_cnf_prepared_prefix_replay.py','solver/test_cnf_prepared_prefix_replay.py')


def synthetic_cases():
    native=candidate.native
    def event(source,subset=None):
        local,names=native.normalize(source if subset is None else subset)
        return dict(root=native.token(local,Counter()),mapping=[list(x) for x in enumerate(names,1)],fixed=[])
    def template(cl):return dict(clauses=[list(cl)],assumptions=[[abs(l),l<0] for l in sorted(cl,key=abs)],trace=[],conflict=0)
    rows=[]
    for n in (8,32,128):
        source=native.normalize([(i,i+1) for i in range(1,n)])[0]
        for kind,ts in (('none',[]),('single',[template(source[0])]),('novel',[template(cl) for cl in source]),('repeated',[template(source[0]) for _ in source])):
            rows.append(dict(name=f'{kind}-{n}',kind=kind,source=source,templates=ts,event=event(source)))
        source=native.normalize([(1,2),(-2,3),(1,3)]+[(i,i+1) for i in range(3,n)])[0]
        ts=[dict(clauses=[[-2,3],[1,2]],assumptions=[[1,False],[3,False]],trace=[[2,1]],conflict=0)]
        rows.append(dict(name=f'missing-support-{n}',kind='missing-support',source=source,templates=ts,event=event(source,[(1,3)]+[(i,i+1) for i in range(3,n)])))
    return rows


def prepare(out):
    assert not (out/'protocol.json').exists();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    seeds=old.bound(cp['shared_joint_preparation']['remaining'])['rows'];compact(out/'synthetic-cases.json',dict(rows=synthetic_cases()))
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),parent_protocol=old.binding(PARENT/'protocol.json'),
        seeds=cp['shared_joint_preparation']['remaining'],targets=sorted({r['target'] for r in seeds}),pilot=old.binding(out/'pilot.json'),pilot_source=old.binding(out/'pilot-source.py'),
        profile=old.binding(out/'baseline-profile.json'),synthetic_cases=old.binding(out/'synthetic-cases.json'),synthetic_repeats=16,
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},orders=[list(MODES),list(reversed(MODES))],limits=dict(probe_limit=64,work_limit=262144,trace_limit=256),limitations=[
        'Sixteen currently unresolved inputs; replay only, no additional search frontier or structural coverage. All actual binary prefixes are empty. Profiling identifies repeated local-hint canonicalization rather than repeated binary prefix steps.',
        'Both arms retain exact source/event coordinate and conditioned-subset checks, every original template check, transport containment, lifted template checks and every local RUP reason/conflict check. Context preparation is owned and lazy within a single reconstruction call.',
        'The context arm reuses existing LocalContext and transport_state. Its context never crosses events or calls; no caller-supplied prepared object or verified flag is accepted. Source/template/event/prefix edits require new checked reconstruction.',
        'Both arms use the same frozen binary-prefix replay, shared joint discovery, independent shared cold validation and search allowances. Final audit additionally reconstructs every result through the original bind and frozen full search validator.',
        'Two isolated opposite-order census repetitions charge complete reconstruction including ownership copying, discovery, persistence/reload and cold checking. Input loading/startup, historical acquisition, profiling, pilot and final audit are additional.',
        'Synthetic controls cover 8,32,128 variables with no hints, one hint, novel and repeated hints, and valid original support absent from the local subset. Each isolated arm executes sixteen independent cold local_hints calls per fixture. Fixture creation and summary serialization are outside these diagnostic reconstruction timings; full persistence is charged in the main census.',
        'Context construction can be wasted if a candidate passes guard filtering but its clause support does not survive. Retain that regression and zero/single-hint overhead; no claim that sharing always wins.',
        'Existing native certificates, proofs, cumulative/reference tables and the 2070735-byte open export remain unchanged. New benchmark artifacts add lifetime storage. No production default or unrestricted SAT bound changes.']))


def inputs(p,target):return prior.inputs(old.bound(p['parent_protocol']),target)


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter();bind=prior.bind if mode=='frozen' else candidate.bind
    for ref,seed in refs:
        rc=Counter();tick=time.perf_counter();_,_,state=bind(source,ts,ref,events[ref['event']],rc);reconstruction=time.perf_counter()-tick
        hints=[h['template'] for h in state['hints']];assert list(map(list,state['local']))==seed['final_source'] and hints==seed['templates']
        args=(state['local'],hints,*(seed[k] for k in FIELDS[2:]));cl=seed['joint_cursor_feedback_closure'];cc=Counter();tick=time.perf_counter()
        result=search.discover(*args,closure=cl,counts=cc,**p['limits']);elapsed=time.perf_counter()-tick
        tick=time.perf_counter();path=dest/f'result-{ref["event"]}.json';compact(path,result);cold=base.load(path);binding=old.binding(path);persistence=time.perf_counter()-tick
        vc=Counter();tick=time.perf_counter();search.validate(*args,closure=cl,result=cold,counts=vc);verification=time.perf_counter()-tick
        rows.append(dict(target=target,event=ref['event'],root=ref['root'],result=binding,counts=dict(cc),verification_counts=dict(vc),reconstruction_counts=dict(rc),
            reconstruction_seconds=reconstruction,discovery_seconds=elapsed,persistence_seconds=persistence,verification_seconds=verification,record_bytes=path.stat().st_size))
    compact(dest/'events.json',dict(rows=rows));base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        **{k:sum(r[k] for r in rows) for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','record_bytes')},
        complete_seconds=time.perf_counter()-start,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        counts=dict(sum((Counter(r['counts']) for r in rows),Counter())),reconstruction_counts=dict(sum((Counter(r['reconstruction_counts']) for r in rows),Counter())),verification_counts=dict(sum((Counter(r['verification_counts']) for r in rows),Counter()))))


def run_census(out):
    p=base.load(out/'protocol.json');samples=[]
    for target in p['targets']:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'census-{target}-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'census',str(out),str(dest),str(target),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),target=target,mode=mode,repeat=repeat))
        print(base.encode(dict(completed_target=target)),flush=True)
    base.write(out/'censuses.json',dict(samples=samples))


def synthetic(out,dest,mode):
    p=base.load(out/'protocol.json');rows=[];fn=candidate.frozen.local_hints if mode=='frozen' else candidate.local_hints;dest.mkdir()
    for case in old.bound(p['synthetic_cases'])['rows']:
        cc=Counter();tick=time.perf_counter()
        for _ in range(p['synthetic_repeats']):result=fn(case['source'],case['templates'],case['event'],cc)
        rows.append(dict(name=case['name'],kind=case['kind'],result=result,counts=dict(cc),seconds=time.perf_counter()-tick))
    compact(dest/'results.json',dict(rows=rows));base.write(dest/'report.json',dict(mode=mode,results=old.binding(dest/'results.json'),peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def run_synthetic(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'synthetic-{mode}-{repeat}';subprocess.run([sys.executable,__file__,'synthetic',str(out),str(dest),mode],check=True)
            samples.append(dict(**old.binding(dest/'report.json'),mode=mode,repeat=repeat))
    base.write(out/'synthetic.json',dict(samples=samples))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census':census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    elif action=='synthetic':synthetic(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)
