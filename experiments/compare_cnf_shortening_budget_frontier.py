#!/usr/bin/env python3
"""Spend immutable-preparation savings on a fixed discovery-budget sweep."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_prepared_source as prior
base=prior.base;old=prior.old;previous=prior.previous;native=prior.native
PARENT=Path('experiments/results/cnf-shortening-prepared-source')
MODES=('control64','prepared64','prepared96','prepared128','prepared256')
FILES=('experiments/compare_cnf_shortening_budget_frontier.py','solver/test_cnf_shortening_budget_frontier.py')


def prepare(out):
    assert not out.exists();out.mkdir();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    p=old.bound(cp['shortening_prepared_source']['protocol'])
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        old_protocol=p['old_protocol'],previous_census=p['previous_census'],targets=p['targets'],limits=p['limits'],policy=p['policy'],
        orders=[list(MODES),list(reversed(MODES))],compilation_orders=[['fresh','support'],['support','fresh']],
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=['Fixed sweep at 64,96,128,256 fresh BFS roots, decided before this run. All other bounds and inference rules unchanged. Candidate uses the frozen prepared source; control64 uses preceding repeated preparation.',
        'All 615 exposed events, two alternating isolated workers per target/arm. Copying, recognition and search included; initial binding separately timed. No equal total-work or wall-time guarantee follows from root limits.',
        'All 96 preceding edits retained. They are exposed-family transformations, not independent-domain validation.',
        'Every new local root beyond prepared64 enters two alternating fresh/support native trials. All six tables and both readers checked; whole-query saved-root presence is reported.',
        'Origin acquisition, process startup, loading and preservation audits are additional. More recognition at a measured cost is not a new tractable SAT family, a live default change or a whole-query speedup.']))


def root_limit(mode):return 64 if mode=='control64' else int(mode.removeprefix('prepared'))


def run(mode,source,ts,c,p):
    assert mode in MODES;limits=dict(p['limits'],root_limit=root_limit(mode))
    module=prior.control if mode=='control64' else prior.candidate
    return module.discover(source,ts,c,**limits,**p['policy'])


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=prior.reuse.inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        tick=time.perf_counter();local,hints,_=previous.local_hints(source,ts,events[ref['event']],Counter());templates=[h['template'] for h in hints]
        binding=time.perf_counter()-tick;c=Counter();tick=time.perf_counter();program=run(mode,local,templates,c,p);elapsed=time.perf_counter()-tick
        rows.append(dict(event=ref['event'],root=ref['source_root'],program=program,counts=dict(c),binding_seconds=binding,discovery_seconds=elapsed))
    base.write(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        discovery_seconds=sum(r['discovery_seconds'] for r in rows),binding_seconds=sum(r['binding_seconds'] for r in rows),
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
        print(base.encode(dict(target=target)),flush=True)
    base.write(out/'censuses.json',dict(samples=samples))


def cases(out):
    p=base.load(out/'protocol.json');roots64=set();prior_union=set()
    for target in p['targets']:
        r=base.load(out/f'census-{target}-prepared64-0/report.json')
        roots64.update(e['root'] for e in old.bound(r['events'])['rows'] if e['program']['status']=='refuted')
        for mode in prior.prior.MODES:
            r=base.load(prior.PARENT/f'census-{target}-{mode}-0/report.json')
            prior_union.update(e['root'] for e in old.bound(r['events'])['rows'] if e['program']['status']=='refuted')
    refs=[];proposals=[];seen=set()
    for target in p['targets']:
        source,ts,_,events=prior.reuse.inputs(p,target)
        query=base.load(f'experiments/results/cnf-guard-covers/serial/target-{target}-census-0/report.json')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';previous.restore_archive(query['archive'],path);reader=previous.CanonicalVerifySnapshot(path)
            affine=previous.TerminalStore(reader);equiv=previous.MultiEquivalenceStore(reader)
            try:
                for mode in MODES[2:]:
                    r=base.load(out/f'census-{target}-{mode}-0/report.json')
                    for e in old.bound(r['events'])['rows']:
                        if e['program']['status']!='refuted' or e['root'] in roots64:continue
                        present=reader._read(e['root']) is not None or affine.read(e['root']) is not None or equiv.read(e['root']) is not None
                        proposals.append(dict(target=target,event=e['event'],mode=mode,root=e['root'],present_after_query=present,in_prior_filter_union=e['root'] in prior_union,duplicate=e['root'] in seen))
                        if e['root'] in seen:continue
                        seen.add(e['root']);local,hints,_=previous.local_hints(source,ts,events[e['event']],Counter());templates=[h['template'] for h in hints]
                        prior.candidate.validate(local,templates,e['program'],Counter())
                        name=f'new-{target}-{e["event"]}';path=out/(name+'.json')
                        base.write(path,dict(name=name,source=local,templates=templates,program=e['program'],root=e['root'],target=target,event=e['event'],mode=mode,present_after_query=present,in_prior_filter_union=e['root'] in prior_union))
                        refs.append(old.binding(path))
            finally:reader.close()
    base.write(out/'cases.json',dict(cases=refs,proposals=proposals,baseline_roots=len(roots64),prior_filter_union_roots=len(prior_union)))
    print(base.encode(dict(new_roots=len(refs),proposals=len(proposals))),flush=True)


def trial(out,dest,index,mode):
    # The frozen native compiler and ordinary-search control remain independent.
    prior.reuse.trial(dest,out,index,mode)


def run_trials(out):
    p=base.load(out/'protocol.json');cases=base.load(out/'cases.json')['cases'];samples=[]
    for index in range(len(cases)):
        for repeat,order in enumerate(p['compilation_orders']):
            for mode in order:
                dest=out/f'case-{index}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'trial',str(out),str(dest),str(index),mode],check=True)
                samples.append(dict(**old.binding(dest/'report.json'),index=index,mode=mode,repeat=repeat))
        print(base.encode(dict(case=index,total=len(cases))),flush=True)
    base.write(out/'comparisons.json',dict(samples=samples))


def edits(out):
    p=base.load(out/'protocol.json');original=base.load(prior.PARENT/'edits.json');rows=[]
    for index,case in enumerate(original['cases']):
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                c=Counter();tick=time.perf_counter();program=run(mode,case['source'],case['templates'],c,p);elapsed=time.perf_counter()-tick
                tick=time.perf_counter()
                if program['status']=='refuted':prior.candidate.validate(case['source'],case['templates'],program,Counter())
                rows.append(dict(index=index,repeat=repeat,mode=mode,program=program,counts=dict(c),discovery_seconds=elapsed,verification_seconds=time.perf_counter()-tick))
    base.write(out/'edits.json',dict(cases_binding=old.binding(prior.PARENT/'edits.json'),rows=rows))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census':census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    else:globals()[action](out)
