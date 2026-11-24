#!/usr/bin/env python3
"""Matched support-only cover composition, extra proposals and persistent reuse."""
from collections import Counter
from pathlib import Path
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_covers as previous
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_clause_cover import discover,compile_cover
from experiments.cnf_guard_cover_support import compile_support_cover
from experiments.cnf_guard_cover_cases import family
from experiments.cnf_guard_interactions import local_hints
from experiments.cnf_guard_probe_census import decode_key
from experiments.cnf_probe_binary_lazy_solver import LazyBinaryClosureSolver
from experiments.cnf_fresh_mixtures import attempt
from experiments.cnf_archive_parts import restore_archive
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.validate_cnf_whole_proof_reuse import audit
base=previous.base;old=previous.old
PARENT=Path('experiments/results/cnf-guard-covers')
MODES=('fresh','full','support')
FILES=('experiments/cnf_guard_cover_support.py','solver/test_cnf_guard_cover_support.py',
       'experiments/compare_cnf_cover_support.py')


def prepare(out):
    assert not (out/'protocol.json').exists();out.mkdir(parents=True,exist_ok=True)
    started=time.perf_counter();parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    p=old.bound(parent['guard_covers']['protocol']);prior=old.bound(parent['guard_covers']['closures'])
    inputs=old.bound(p['cases']);choices=[]
    for r in prior['records']:choices.append(dict(target=r['target'],event=r['event'],cover=r['cover'],category='bounded',bounds=p['discovery']))
    for r in prior['expanded_discovery']:
        if r['cover'] is not None:choices.append(dict(target=r['target'],event=r['event'],cover=r['cover'],category='relaxed',bounds=r['bounds']))
    assert len(choices)==22
    cases=[];proposals=[];seen={};presence_seconds=0.0
    for target in p['targets']:
        selected=[r for r in choices if r['target']==target]
        if not selected:continue
        report=base.load(PARENT/f'serial/target-{target}-census-0/report.json');events=old.bound(report['events'])['events']
        origin=old.bound(p['inputs'][p['targets'].index(target)]);templates=old.bound(origin['extraction'])['templates']
        source=native.normalize(inputs[target]['source'])[0];tick=time.perf_counter()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'query';restore_archive(report['archive'],path);reader=CanonicalVerifySnapshot(path)
            present={}
            try:
                affine=TerminalStore(reader);equiv=MultiEquivalenceStore(reader)
                for item in selected:
                    root=events[item['event']]['root']
                    if root in present:continue
                    present[root]=reader._read(root) is not None or affine.read(root) is not None or equiv.read(root) is not None
            finally:reader.close()
        presence_seconds+=time.perf_counter()-tick
        for item in selected:
            event=events[item['event']];tick=time.perf_counter();c=Counter();local=decode_key(event['root'])
            cover=discover(local,event['graph'],dict(event['model']),c,**item['bounds']);assert cover==item['cover']
            discovery_seconds=time.perf_counter()-tick;dc=dict(c);c=Counter();tick=time.perf_counter()
            actual,hints,whole=local_hints(source,templates,event,c);assert actual==local
            original={cl for cl in local if len(cl)<=2};bank={tuple(h['clause']):h for h in hints}
            used={tuple(event['graph'][cid]) for path in cover['paths'] for _,cid in path}
            missing=sorted(used-original-bank.keys())
            row=dict(**item,root=event['root'],site_closed=event['site_closed'],whole_residual=whole,
                present_after_query=present[event['root']],missing_support=missing,
                discovery_seconds=discovery_seconds,discovery_counts=dc,support_seconds=time.perf_counter()-tick,
                support_counts=dict(c),events=report['events'])
            if missing:row['status']='unsupported';proposals.append(row);continue
            if event['root'] in seen:
                row.update(status='duplicate',case=seen[event['root']]);proposals.append(row);continue
            name=f'local-{target}-{item["event"]}';needed=[bank[cl] for cl in sorted(used-original)]
            case=dict(name=name,category=item['category'],source=[list(cl) for cl in local],hints=needed,
                graph=event['graph'],cover=cover,root=event['root'],target=target,event=item['event'],
                discovery_seconds=discovery_seconds,support_seconds=row['support_seconds'],
                present_after_query=row['present_after_query'],site_closed=row['site_closed'])
            base.write(out/(name+'.json'),case);cases.append(old.binding(out/(name+'.json')))
            seen[event['root']]=name;row.update(status='selected',case=name);proposals.append(row)
    for width in (3,6):
        for padding in (0,16,64,256):
            tick=time.perf_counter();source,_,hints,graph,model=family(width)
            source=native.normalize(list(source)+[[1,4*width+i+1] for i in range(padding)])[0]
            c=Counter();cover=discover(source,graph,model,c,**p['discovery']);assert cover is not None
            name=f'padded-{width}-{padding}'
            base.write(out/(name+'.json'),dict(name=name,category='controlled',source=source,hints=hints,graph=graph,
                cover=cover,root=native.token(source,Counter()),width=width,padding=padding,
                supplied_preparation_seconds=time.perf_counter()-tick))
            cases.append(old.binding(out/(name+'.json')))
    base.write(out/'proposals.json',dict(parent_closures=parent['guard_covers']['closures'],records=proposals,
        query_presence_seconds=presence_seconds,preparation_seconds=time.perf_counter()-started))
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        cases=cases,proposals=old.binding(out/'proposals.json'),node_limit=256,discovery=p['discovery'],
        orders=[list(MODES),list(reversed(MODES))],source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        limitations=[
            'All 22 earlier proposals, including all seven relaxed-budget candidates, are re-discovered and independently source-bound. Unsupported cases remain explicit; exact root duplicates share one cold comparison. No outcome-based case selection.',
            'Fresh uses the frozen ordinary solver; full uses the frozen cover compiler; support compiles the checked union of selected path supports and the actual wide clause, then lifts a native negative subset. No new proof rule, independence premise or minimum-support claim.',
            'Two alternating serial repetitions in isolated workers. Solve time includes support selection, coordinate transport, lookup, native verification and publication for the new arm. Complete worker time includes input loading, setup, solve, warm checking, both cold readers, accounting and compression; process import/startup and common proposal preparation are additional.',
            'Independent origin/local-support preparation and discovery are reported separately and must be added to compiler cost. Earlier origin acquisition remains additional. Cold workers receive no cumulative or future-query bank.',
            'The eight controlled cases supply known covers of widths 3/6 with 0/16/64/256 extra overlapping clauses. They test context scaling, not automatic pattern discovery or population-level performance.',
            'A separate append-only stream closes and reopens the store between changing contexts. It measures exact canonical support reuse, not complete signed-isomorphism recognition. Supplemental proof archives remain separate from the cumulative/causal history.',
            'No live query policy, whole-query speedup, new Lean refinement or unrestricted-SAT polynomial bound is claimed.']))
    print(base.encode(dict(cases=len(cases),proposal_statuses=Counter(r['status'] for r in proposals),seconds=time.perf_counter()-started)),flush=True)


def verdict(s,case,mode,counts,limits):
    if mode=='fresh':return attempt(s,case['source'])
    fn=compile_cover if mode=='full' else compile_support_cover
    root=fn(s,case['source'],case['hints'],case['graph'],case['cover'],counts,**limits)
    assert root==case['root'] and s._read(root)['answer'] is False
    return dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'),metrics=dict(s.counts))


def trial(dest,out,index,mode):
    p=base.load(out/'protocol.json')
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    began=time.perf_counter();case=old.bound(p['cases'][index]);dest.mkdir();limits={k:p['discovery'][k] for k in ('width_limit','path_limit')}
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';tick=time.perf_counter()
        s=LazyBinaryClosureSolver(path,node_limit=p['node_limit']) if mode=='fresh' else native.ResidualSolver(path)
        setup=time.perf_counter()-tick;c=Counter()
        try:
            tick=time.perf_counter();result=verdict(s,case,mode,c,limits);solve=time.perf_counter()-tick
            assert result['status']=='unsat';stored=old.tables(s.db);native_counts=dict(s.counts);checked_bytes=sum(len(str(v).encode()) for v in s.checked.values())
            tick=time.perf_counter();warm_counts=Counter();warm=verdict(s,case,mode,warm_counts,limits)
            warm_seconds=time.perf_counter()-tick;assert warm['result']['root']==case['root'] and old.tables(s.db)==stored
        finally:s.close()
        tick=time.perf_counter();audited,readers=audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick
        assert audited==stored;tick=time.perf_counter();archive=base.archive(path,dest);persistence=time.perf_counter()-tick
    r=dict(protocol=old.binding(out/'protocol.json'),case=p['cases'][index],index=index,mode=mode,category=case['category'],
        result=result,counts=dict(c),native_counts=native_counts,warm_counts=dict(warm_counts),setup_seconds=setup,
        solve_seconds=solve,warm_seconds=warm_seconds,cold_seconds=cold,persistence_seconds=persistence,
        complete_seconds=time.perf_counter()-began,peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        checked_logical_bytes=checked_bytes,record_bytes=sum(len(k.encode())+len(v.encode()) for rows in stored.values() for k,v in rows.items()),
        authority_tables={t:len(rows) for t,rows in stored.items()},digest={t:base.key_sha(base.encode(sorted(rows.items()))) for t,rows in stored.items()},
        cold_readers=readers,archive=archive)
    base.write(dest/'report.json',r)


def run(out):
    p=base.load(out/'protocol.json');samples=[];began=time.perf_counter()
    for index,binding in enumerate(p['cases']):
        case=old.bound(binding)
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'{case["name"]}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'trial',str(dest),str(out),str(index),mode],check=True)
                samples.append(dict(index=index,mode=mode,repeat=repeat,**old.binding(dest/'report.json')))
        print('compared',case['name'],flush=True)
    base.write(out/'comparisons.json',dict(protocol=old.binding(out/'protocol.json'),samples=samples,complete_seconds=time.perf_counter()-began))


def stream(out):
    p=base.load(out/'protocol.json');cases=[old.bound(b) for b in p['cases'] if old.bound(b)['category']=='controlled']
    limits={k:p['discovery'][k] for k in ('width_limit','path_limit')};rows=[]
    for mode in ('full','support'):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';previous_rows=None
            for case in cases:
                dest=out/f'stream-{mode}-{case["name"]}';dest.mkdir();began=time.perf_counter();s=native.ResidualSolver(path)
                initial=old.tables(s.db);c=Counter()
                if previous_rows is not None:assert initial==previous_rows
                try:
                    tick=time.perf_counter();result=verdict(s,case,mode,c,limits);solve=time.perf_counter()-tick
                    final=old.tables(s.db)
                    for t,stored in initial.items():assert stored.items()<=final[t].items()
                finally:s.close()
                tick=time.perf_counter();stored,readers=audit(path,[dict(source=case['source'])],[result]);cold=time.perf_counter()-tick
                assert stored==final;archive=base.archive(path,dest)
                row=dict(mode=mode,case=case['name'],source=case['source'],result=result,counts=dict(c),
                    solve_seconds=solve,cold_seconds=cold,complete_seconds=time.perf_counter()-began,
                    added={t:len(final[t])-len(initial[t]) for t in final},authority_tables={t:len(x) for t,x in final.items()},
                    record_bytes=sum(len(k.encode())+len(v.encode()) for x in final.values() for k,v in x.items()),
                    digest={t:base.key_sha(base.encode(sorted(x.items()))) for t,x in final.items()},archive=archive,readers=readers)
                base.write(dest/'report.json',row);rows.append(old.binding(dest/'report.json'));previous_rows=final
    base.write(out/'stream.json',dict(protocol=old.binding(out/'protocol.json'),rows=rows))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action=='prepare':prepare(out)
    elif action=='run':run(out)
    elif action=='stream':stream(out)
    elif action=='trial':trial(out,Path(sys.argv[3]),int(sys.argv[4]),sys.argv[5])
