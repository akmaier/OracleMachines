#!/usr/bin/env python3
"""Compare structural negative-search reuse with ordinary budget expansion."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_context as prior
from experiments import cnf_shortening_reach_reuse as checked
from experiments import cnf_shortening_reach_bfs as cached
base=prior.base;old=prior.old;native=prior.native
PARENT=Path('experiments/results/cnf-shortening-context')
MODES=('frozen64','expanded128','checked64','cached64')
COMPILERS=('fresh','full','support')
FILES=('experiments/cnf_shortening_reach_reuse.py','experiments/cnf_shortening_reach_bfs.py','solver/test_cnf_shortening_reach_reuse.py','experiments/probe_cnf_reach_reuse.py','experiments/compare_cnf_reach_reuse.py')


def prepare(out):
    assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    test=Path('solver/test_cnf_shortening_reach_reuse.py').read_text()
    a=test.index('    def test_complete_bfs_admissions_are_closed');b=test.index('    def test_unlabelled_inputs_against_truth',a)
    initial=(test[:a]+test[b:]).replace('from experiments import cnf_shortening_reach_reuse as checked\nfrom experiments import cnf_shortening_reach_bfs as reuse','from experiments import cnf_shortening_reach_reuse as reuse')
    Path(out/'initial-tests.py.txt').write_text(initial)
    assert base.sha(out/'initial-tests.py.txt')==base.load(out/'probe.json')['source_fingerprints']['solver/test_cnf_shortening_reach_reuse.py']
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        previous_census=parent['guard_shortening']['census'],old_protocol=parent['guard_covers']['protocol'],
        limits=prior.previous.LIMITS,targets=[1,4,28,37,40,61,64,67],orders=[list(MODES),list(reversed(MODES))],
        compilation_orders=[list(COMPILERS),list(reversed(COMPILERS))],node_limit=256,
        exploration=dict(checked_probe=old.binding(out/'probe.json'),bfs_probe=old.binding(out/'bfs-probe/probe.json'),
                         bfs_actual_candidate=old.binding('experiments/cnf_shortening_reach_bfs.py'),initial_test_snapshot=old.binding(out/'initial-tests.py.txt')),
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=['Two alternating isolated census repetitions per target; all 615 events retained, including misses and regressions. Initial source binding is separately timed; origin acquisition and input/protocol loading are additional.',
        'frozen64 and expanded128 use the preceding shared-context detector. checked64 charges a full closure scan on every admission. cached64 admits only complete BFS results internally, but checks supplied sets and every relevant added edge.',
        'All reuse modes retain 64 fresh BFS roots, 32 rounds, path length 256, and 16384 combined BFS/admission/invalidation edge checks. Cache hits permit more candidate attempts; this is not an equal total-work budget. Graph construction/deltas, lookup, index maintenance and memory are reported separately.',
        'Negative cache contains at most 16384 literal memberships plus an inverse index and graph edges; this is not a process-RAM cap. It is query-local, in original source coordinates. Refutations still require independent native compilation.',
        'All newly recognized cached64 roots enter local fresh/full/support compilation comparisons. Earlier 97 roots remain covered by their preserved archives. This is an exposed offline study, not a live query rerun or evidence for arbitrary-SAT tractability.']))


def inputs(p,target):
    priorp=old.bound(p['old_protocol']);position=priorp['targets'].index(target)
    source=native.normalize(old.bound(priorp['cases'])[target]['source'])[0]
    templates=old.bound(old.bound(priorp['inputs'][position])['extraction'])['templates']
    refs=[r for r in old.bound(p['previous_census'])['records'] if r['target']==target]
    events=old.bound(refs[0]['events'])['events']
    return source,templates,refs,events


def census(dest,out,target,mode):
    p=base.load(out/'protocol.json');source,templates,refs,events=inputs(p,target)
    limits=dict(p['limits']);module=prior.shared
    if mode=='expanded128':limits['root_limit']=128
    elif mode=='checked64':module=checked
    elif mode=='cached64':module=cached
    dest.mkdir();started=time.perf_counter();rows=[]
    for ref in refs:
        c=Counter();tick=time.perf_counter();local,hints,whole=prior.previous.local_hints(source,templates,events[ref['event']],c)
        binding=time.perf_counter()-tick;c=Counter();tick=time.perf_counter();program=module.discover(local,[h['template'] for h in hints],c,**limits)
        seconds=time.perf_counter()-tick
        if mode=='frozen64':assert program==ref['program']
        if mode in ('cached64','checked64'):assert c['reach_edge_visits']+c['cache_admission_edge_checks']+c['reuse_invalidation_checks']<=limits['edge_limit']
        rows.append(dict(event=ref['event'],root=ref['source_root'],program=program,counts=dict(c),binding_seconds=binding,discovery_seconds=seconds))
    base.write(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(mode=mode,target=target,events=old.binding(dest/'events.json'),
        binding_seconds=sum(r['binding_seconds'] for r in rows),discovery_seconds=sum(r['discovery_seconds'] for r in rows),
        complete_seconds=time.perf_counter()-started,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
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


def prepare_cases(out):
    p=base.load(out/'protocol.json');refs=old.bound(p['previous_census'])['records']
    oldroots={r['source_root'] for r in refs if r['program']['status']=='refuted'};cases=[];proposals=[];seen=set()
    for target in p['targets']:
        source,templates,rs,events=inputs(p,target)
        report=base.load(out/f'census-{target}-cached64-0/report.json');rows=old.bound(report['events'])['rows']
        query=base.load(f'experiments/results/cnf-guard-covers/serial/target-{target}-census-0/report.json')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'query';prior.previous.restore_archive(query['archive'],path);reader=prior.previous.CanonicalVerifySnapshot(path)
            affine=prior.previous.TerminalStore(reader);equiv=prior.previous.MultiEquivalenceStore(reader)
            try:
                for row in rows:
                    if row['program']['status']!='refuted' or row['root'] in oldroots:continue
                    event=events[row['event']];c=Counter();local,hints,whole=prior.previous.local_hints(source,templates,event,c)
                    ts=[h['template'] for h in hints];cached.validate(local,ts,row['program'],Counter())
                    present=reader._read(row['root']) is not None or affine.read(row['root']) is not None or equiv.read(row['root']) is not None
                    proposal=dict(target=target,event=row['event'],root=row['root'],present_after_query=present,duplicate=row['root'] in seen)
                    proposals.append(proposal)
                    if row['root'] in seen:continue
                    seen.add(row['root']);name=f'new-{target}-{row["event"]}'
                    case=dict(name=name,source=local,templates=ts,program=row['program'],root=row['root'],target=target,event=row['event'],present_after_query=present)
                    base.write(out/(name+'.json'),case);cases.append(old.binding(out/(name+'.json')))
            finally:reader.close()
    base.write(out/'cases.json',dict(cases=cases,proposals=proposals))
    print(base.encode(dict(new_roots=len(cases),proposals=len(proposals),not_previously_saved=sum(not old.bound(b)['present_after_query'] for b in cases))),flush=True)


def trial(dest,out,index,mode):
    p=base.load(out/'protocol.json');binding=base.load(out/'cases.json')['cases'][index];case=old.bound(binding);dest.mkdir();started=time.perf_counter();c=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=prior.previous.LazyBinaryClosureSolver(path,node_limit=256) if mode=='fresh' else native.ResidualSolver(path)
        try:
            tick=time.perf_counter()
            if mode=='fresh':result=prior.previous.attempt(s,case['source'])
            else:
                root=cached.compile_program(s,case['source'],case['templates'],case['program'],c,select_support=mode=='support')
                result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            solve=time.perf_counter()-tick;stored=old.tables(s.db);nc=dict(s.counts)
            tick=time.perf_counter()
            if result['status']=='unsat':
                if mode=='fresh':assert prior.previous.attempt(s,case['source'])['status']=='unsat'
                else:assert cached.compile_program(s,case['source'],case['templates'],case['program'],Counter(),select_support=mode=='support')==case['root']
            warm=time.perf_counter()-tick;assert old.tables(s.db)==stored
        finally:s.close()
        tick=time.perf_counter();actual,readers=prior.previous.audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick;assert actual==stored
        tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
    base.write(dest/'report.json',dict(case=binding,mode=mode,result=result,counts=dict(c),native_counts=nc,solve_seconds=solve,warm_seconds=warm,
        cold_seconds=cold,persistence_seconds=persistence,complete_seconds=time.perf_counter()-started,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,authority_tables={t:len(v) for t,v in stored.items()},
        digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()},record_bytes=sum(len(k.encode())+len(v.encode()) for r in stored.values() for k,v in r.items()),archive=archive,cold_readers=readers))


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


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action in ('prepare','run_census','prepare_cases','run_trials'):globals()[action](out)
    else:globals()[action](Path(sys.argv[3]),out,int(sys.argv[4]),sys.argv[5])
