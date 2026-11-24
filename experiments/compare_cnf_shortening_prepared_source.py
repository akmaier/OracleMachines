#!/usr/bin/env python3
"""Matched source preparation study; frozen policy, programs and native proofs."""
from collections import Counter
from pathlib import Path
import cProfile,pstats,resource,subprocess,sys,tempfile,time,tracemalloc
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_filters as prior
from experiments import compare_cnf_reach_reuse as reuse
from experiments import cnf_shortening_prepared_source as candidate
from experiments import cnf_shortening_clause_filters as control
from experiments.cnf_conditional_unit_support import check_template
base=prior.base;old=prior.old;previous=prior.previous;native=prior.native
PARENT=Path('experiments/results/cnf-shortening-filters')
FILES=('experiments/cnf_shortening_prepared_source.py','solver/test_cnf_shortening_prepared_source.py','experiments/compare_cnf_shortening_prepared_source.py')
MODULES={'control':control,'prepared':candidate}
EXTRA=('source_preparations','prepared_templates','prepared_input_slots')


def prepare(out):
    assert not out.exists();out.mkdir();cp=base.load(PARENT/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    parent=old.bound(cp['shortening_filters']['protocol'])
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        old_protocol=parent['old_protocol'],previous_census=parent['previous_census'],targets=parent['targets'],limits=parent['limits'],
        orders=[['control','prepared'],['prepared','control']],policy=dict(order='priority',filters='endpoint'),
        source_fingerprints={**cp['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=['Two alternating isolated workers per target/engine, all 615 exposed events; preparation and copying included in discovery. Initial event binding separately timed.',
        'No search budget, ordering, filtering, program, or native authority change. Static preparation cannot be reused after a source/template edit. Mutable caller inputs are detached.',
        'Reduced template validation, current source normalization, local positions and RUP checks still run. No prepared objects accepted as certificates.',
        'All 96 previous edits retained. Native compilation streams use the first occurrence of every recognized local root. Cold readers and all six tables must agree; previous artifacts are retained.',
        'RSS includes interpreter/input state; logical prepared slots are not byte counts. Tracemalloc/profile instrumentation is separate from timing comparisons.',
        'Origin acquisition, loading, process startup and preservation audits are additional. Same coverage, no whole-query runtime claim, no unrestricted-SAT tractability claim.']))


def run(module,source,ts,c,p):return module.discover(source,ts,c,**p['limits'],**p['policy'])


def static_counts(source,ts):
    c=Counter();native.normalize(source,c)
    for t in ts:check_template(t,c)
    return c


def census(out,dest,target,mode):
    p=base.load(out/'protocol.json');source,ts,refs,events=reuse.inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    for ref in refs:
        tick=time.perf_counter();local,hints,_=previous.local_hints(source,ts,events[ref['event']],Counter());templates=[h['template'] for h in hints]
        binding=time.perf_counter()-tick;c=Counter();tick=time.perf_counter();program=run(MODULES[mode],local,templates,c,p);elapsed=time.perf_counter()-tick
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
    p=base.load(out/'protocol.json');rows=[];seen=set()
    for target in p['targets']:
        source,ts,refs,events=reuse.inputs(p,target)
        report=base.load(out/f'census-{target}-prepared-0/report.json')
        for r in old.bound(report['events'])['rows']:
            if r['program']['status']!='refuted' or r['root'] in seen:continue
            seen.add(r['root']);local,hints,_=previous.local_hints(source,ts,events[r['event']],Counter())
            rows.append(dict(source=local,templates=[h['template'] for h in hints],root=r['root'],program=r['program'],target=target,event=r['event']))
    base.write(out/'cases.json',dict(cases=rows))
    print(base.encode(dict(native_cases=len(rows))),flush=True)


def native_stream(out,dest,mode):
    p=base.load(out/'protocol.json');cases=base.load(out/'cases.json')['cases'];dest.mkdir();rows=[];allstart=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=native.ResidualSolver(path)
        try:
            for case in cases:
                c=Counter();tick=time.perf_counter();program=run(MODULES[mode],case['source'],case['templates'],c,p);discovery=time.perf_counter()-tick
                assert program==case['program'];cc=Counter();tick=time.perf_counter();root=MODULES[mode].compile_program(s,case['source'],case['templates'],program,cc)
                elapsed=time.perf_counter()-tick;assert root==case['root']
                rows.append(dict(root=root,discovery_seconds=discovery,compile_seconds=elapsed,discovery_counts=dict(c),compile_counts=dict(cc),
                    result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))))
            tables=old.tables(s.db);tick=time.perf_counter();warm=Counter()
            for case in cases:assert MODULES[mode].compile_program(s,case['source'],case['templates'],case['program'],warm)==case['root']
            warm_seconds=time.perf_counter()-tick;assert tables==old.tables(s.db)
        finally:s.close()
        tick=time.perf_counter();stored,readers=previous.audit(path,cases,[r['result'] for r in rows]);cold=time.perf_counter()-tick;assert tables==stored
        tick=time.perf_counter();archive=base.archive(path,dest);persist=time.perf_counter()-tick
    base.write(dest/'report.json',dict(mode=mode,rows=rows,warm_counts=dict(warm),warm_seconds=warm_seconds,cold_seconds=cold,persistence_seconds=persist,
        archive=archive,readers=readers,authority_tables={t:len(v) for t,v in tables.items()},
        digest={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()},
        record_bytes=sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items()),
        complete_seconds=time.perf_counter()-allstart,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss))


def streams(out):
    samples=[]
    for mode in MODULES:
        dest=out/('native-'+mode)
        subprocess.run([sys.executable,__file__,'native_stream',str(out),str(dest),mode],check=True)
        samples.append(old.binding(dest/'report.json'))
    base.write(out/'streams.json',dict(samples=samples,limitations='One stream per engine, shared expanding database within each stream; timing is descriptive. Programs and native table content must match exactly. No whole-query rerun.'))


def auxiliary(out):
    p=base.load(out/'protocol.json');edits=base.load(PARENT/'edits.json')['cases'];rows=[]
    for i,case in enumerate(edits):
        for mode,module in MODULES.items():
            c=Counter();tick=time.perf_counter();program=run(module,case['source'],case['templates'],c,p)
            rows.append(dict(index=i,mode=mode,program=program,counts=dict(c),seconds=time.perf_counter()-tick))
    base.write(out/'edits.json',dict(cases_binding=old.binding(PARENT/'edits.json'),rows=rows))
    source,ts,refs,events=reuse.inputs(p,37);local,hints,_=previous.local_hints(source,ts,events[17],Counter());templates=[h['template'] for h in hints];profiles={}
    for mode,module in MODULES.items():
        prof=cProfile.Profile();counts=Counter();program=prof.runcall(run,module,local,templates,counts,p)
        prof.dump_stats(str(out/(mode+'-profile.pstats')))
        with (out/(mode+'-profile.log')).open('w') as f:pstats.Stats(prof,stream=f).sort_stats('cumulative').print_stats(35)
        functions=[dict(file=k[0],line=k[1],function=k[2],calls=v[1],own_seconds=v[2],cumulative_seconds=v[3]) for k,v in pstats.Stats(prof).stats.items()]
        tracemalloc.start();again=run(module,local,templates,Counter(),p);current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();assert program==again
        profiles[mode]=dict(program=program,counts=dict(counts),functions=sorted(functions,key=lambda r:r['cumulative_seconds'],reverse=True)[:35],traced_peak_bytes=peak,traced_current_bytes=current)
    base.write(out/'profiles.json',dict(target=37,event=17,modes=profiles,limitations='One exposed instrumented case, independent calls for profiling and tracemalloc; cumulative times overlap. Not a runtime or memory bound.'))
    # Scaling and a cold reopen expansion stream with previously archived proofs.
    scaling=[]
    for depth in (1,4,16):
        for padding in (0,64,256):
            source,ts=previous.chain(depth,padding)
            for repeat,order in enumerate(p['orders']):
                for mode in order:
                    c=Counter();tick=time.perf_counter();program=run(MODULES[mode],source,ts,c,p)
                    scaling.append(dict(depth=depth,padding=padding,repeat=repeat,mode=mode,program=program,counts=dict(c),seconds=time.perf_counter()-tick))
    base.write(out/'scaling.json',dict(rows=scaling,limitations='Synthetic conditional chains, two alternating serial repetitions per size, template construction excluded. Does not establish arbitrary-CNF scaling.'))
    references=base.load('experiments/results/cnf-shortening-context/streams.json')['modes']['shared']['rows'];stream=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db'
        for ref in references:
            source,ts=previous.chain(4,ref['padding']);c=Counter();tick=time.perf_counter();program=run(candidate,source,ts,c,p);discovery=time.perf_counter()-tick
            s=native.ResidualSolver(path)
            try:
                before=old.tables(s.db);cc=Counter();tick=time.perf_counter();root=candidate.compile_program(s,source,ts,program,cc);elapsed=time.perf_counter()-tick;after=old.tables(s.db)
                added=sum(len(after[t])-len(before[t]) for t in before)
                assert all(after[t].get(k)==v for t in before for k,v in before[t].items())
                if stream:assert added==1 and cc['support_hits']==1
            finally:s.close()
            tick=time.perf_counter();actual,readers=previous.audit(path,[dict(source=source)],[ref['result']]);cold=time.perf_counter()-tick
            assert actual==after and root==ref['result']['result']['root'] and base.sha(path)==ref['archive']['database_sha256']
            stream.append(dict(padding=ref['padding'],archive=ref['archive'],result=ref['result'],added_records=added,discovery_counts=dict(c),compile_counts=dict(cc),
                discovery_seconds=discovery,compile_seconds=elapsed,cold_seconds=cold,readers=readers))
    base.write(out/'expansion.json',dict(rows=stream,limitations='One candidate cold reopen stream; references byte-identical prior archives, no duplicated authority.'))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='census':census(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
    elif action=='native_stream':native_stream(out,Path(sys.argv[3]),sys.argv[4])
    else:globals()[action](out)
