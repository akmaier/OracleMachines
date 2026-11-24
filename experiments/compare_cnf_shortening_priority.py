#!/usr/bin/env python3
"""Fixed ternary-yield ordering versus numeric roots, with and without reuse."""
from collections import Counter
from pathlib import Path
import random,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_reach_reuse as prior
from experiments import cnf_shortening_priority as candidate
from experiments.cnf_conditional_unit_support import transport
base=prior.base;old=prior.old;native=prior.native;previous=prior.prior.previous
PARENT=Path('experiments/results/cnf-reach-reuse')
MODES=('cached64','priority64','priority_plain64','expanded128')
FILES=('experiments/cnf_shortening_priority.py','solver/test_cnf_shortening_priority.py','experiments/compare_cnf_shortening_priority.py')


def prepare(out):
    assert not out.exists();out.mkdir();parent=base.load(PARENT/'checkpoint.json')
    for f,h in parent['source_fingerprints'].items():assert base.sha(f)==h,f
    p=old.bound(parent['reach_reuse']['protocol'])
    base.write(out/'protocol.json',dict(parent=old.binding(PARENT/'checkpoint.json'),parent_manifest=old.binding(PARENT/'manifest.json'),
        previous_protocol=parent['reach_reuse']['protocol'],old_protocol=p['old_protocol'],previous_census=p['previous_census'],
        limits=p['limits'],targets=p['targets'],orders=[list(MODES),list(reversed(MODES))],compilation_orders=[['fresh','support'],['support','fresh']],
        source_fingerprints={**parent['source_fingerprints'],**{f:base.sha(f) for f in FILES}},
        rule='Descending exact current ternary-source occurrence count for eligible model-false literals; signed numeric tie break. Fixed before new census, with no parameter tuning.',
        limitations=['Two alternating isolated repetitions per target; all 615 exposed saved events, including losses and misses. Initial guard binding is separately timed.',
        'All 64-root modes retain 32 rounds, witness length 256, and 16384 BFS/invalidation edge checks; priority scanning and sorting, source preparation, graph differences and cache index work are additional, not an equal total-work budget.',
        'priority_plain64 disables negative certificate storage and lookup but retains the same graph-coordinate preparation; it is an ablation, not a claim to the fastest uncached implementation.',
        'Only newly recognized roots beyond the union of previous cached64 and expanded128 controls enter the fresh/support local comparison. No whole-query policy changes.',
        'New support-preserving clause additions and signed permutations test edits after the policy was fixed. They share exposed source families and are not an independent-domain holdout.',
        'Input loading, process startup, original template acquisition, final reports and preservation audits remain additional. No new arbitrary-SAT tractability claim.']))


def run_program(mode,source,ts,c,limits):
    limits=dict(limits)
    if mode=='expanded128':limits['root_limit']=128;return prior.prior.shared.discover(source,ts,c,**limits)
    if mode=='cached64':return prior.cached.discover(source,ts,c,**limits)
    return candidate.discover(source,ts,c,reuse=mode=='priority64',**limits)


def census(dest,out,target,mode):
    p=base.load(out/'protocol.json');source,templates,refs,events=prior.inputs(p,target);dest.mkdir();rows=[];start=time.perf_counter()
    control={}
    if mode in ('cached64','expanded128'):
        r=base.load(PARENT/f'census-{target}-{mode}-0/report.json');control={r['event']:r for r in old.bound(r['events'])['rows']}
    for ref in refs:
        c=Counter();tick=time.perf_counter();local,hints,_=previous.local_hints(source,templates,events[ref['event']],c)
        binding=time.perf_counter()-tick;c=Counter();tick=time.perf_counter();program=run_program(mode,local,[h['template'] for h in hints],c,p['limits']);elapsed=time.perf_counter()-tick
        if control:assert program==control[ref['event']]['program'] and dict(c)==control[ref['event']]['counts']
        rows.append(dict(event=ref['event'],root=ref['source_root'],program=program,counts=dict(c),binding_seconds=binding,discovery_seconds=elapsed))
    base.write(dest/'events.json',dict(rows=rows))
    base.write(dest/'report.json',dict(target=target,mode=mode,events=old.binding(dest/'events.json'),
        binding_seconds=sum(r['binding_seconds'] for r in rows),discovery_seconds=sum(r['discovery_seconds'] for r in rows),
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


def prepare_cases(out):
    p=base.load(out/'protocol.json');oldroots=set();cases=[];proposals=[];seen=set()
    for target in p['targets']:
        for mode in ('cached64','expanded128'):
            r=base.load(out/f'census-{target}-{mode}-0/report.json');oldroots.update(r['root'] for r in old.bound(r['events'])['rows'] if r['program']['status']=='refuted')
    for target in p['targets']:
        source,templates,refs,events=prior.inputs(p,target)
        query=base.load(f'experiments/results/cnf-guard-covers/serial/target-{target}-census-0/report.json')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'query';previous.restore_archive(query['archive'],path);reader=previous.CanonicalVerifySnapshot(path)
            affine=previous.TerminalStore(reader);equiv=previous.MultiEquivalenceStore(reader)
            try:
                for mode in ('priority64','priority_plain64'):
                    r=base.load(out/f'census-{target}-{mode}-0/report.json')
                    for row in old.bound(r['events'])['rows']:
                        if row['program']['status']!='refuted' or row['root'] in oldroots:continue
                        local,hints,_=previous.local_hints(source,templates,events[row['event']],Counter());ts=[h['template'] for h in hints]
                        candidate.validate(local,ts,row['program'],Counter())
                        present=reader._read(row['root']) is not None or affine.read(row['root']) is not None or equiv.read(row['root']) is not None
                        proposals.append(dict(target=target,event=row['event'],mode=mode,root=row['root'],present_after_query=present,duplicate=row['root'] in seen))
                        if row['root'] in seen:continue
                        seen.add(row['root']);name=f'new-{target}-{row["event"]}'
                        base.write(out/(name+'.json'),dict(name=name,source=local,templates=ts,program=row['program'],root=row['root'],target=target,event=row['event'],present_after_query=present))
                        cases.append(old.binding(out/(name+'.json')))
            finally:reader.close()
    base.write(out/'cases.json',dict(cases=cases,proposals=proposals,old_union_roots=len(oldroots)))
    print(base.encode(dict(new_roots=len(cases),proposals=len(proposals))),flush=True)


def trial(dest,out,index,mode):
    # Existing native compiler and both independent readers remain unchanged.
    prior.trial(dest,out,index,mode)


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
    p=base.load(out/'protocol.json');rng=random.Random(242124);cases=[];rows=[]
    # Three fixed chronological positions per target, two deterministic edits each.
    for target in p['targets']:
        source,templates,refs,events=prior.inputs(p,target)
        for ref in (refs[0],refs[len(refs)//2],refs[-1]):
            local,hints,_=previous.local_hints(source,templates,events[ref['event']],Counter());ts=[h['template'] for h in hints]
            names=sorted({abs(l) for cl in local for l in cl});permuted=names[:];rng.shuffle(permuted)
            mapping={v:w*rng.choice((-1,1)) for v,w in zip(names,permuted)}
            def lit(l):return mapping[abs(l)]*(1 if l>0 else -1)
            for kind in ('renamed','added_clause'):
                clauses=[[lit(l) for l in cl] for cl in local];translated=[transport(t,mapping) for t in ts]
                if kind=='added_clause' and len(names)>=3:
                    clauses.append([v*rng.choice((-1,1)) for v in rng.sample(names,3)])
                changed=native.normalize(clauses)[0];case=dict(target=target,event=ref['event'],kind=kind,source=changed,templates=translated,mapping=sorted(mapping.items()))
                cases.append(case);index=len(cases)-1
                for repeat,order in enumerate(p['orders']):
                    for mode in order:
                        c=Counter();tick=time.perf_counter();program=run_program(mode,changed,translated,c,p['limits']);elapsed=time.perf_counter()-tick
                        tick=time.perf_counter()
                        if program['status']=='refuted':candidate.validate(changed,translated,program,Counter())
                        rows.append(dict(index=index,repeat=repeat,mode=mode,program=program,counts=dict(c),discovery_seconds=elapsed,verification_seconds=time.perf_counter()-tick))
    base.write(out/'edits.json',dict(cases=cases,rows=rows,limitations='48 deterministic edits of exposed cases, serial within one process; source transport is included in generator time, outside per-discovery samples. No independent-domain generalization claim.'))


if __name__=='__main__':
    action=sys.argv[1];out=Path(sys.argv[2])
    if action in ('prepare','run_census','prepare_cases','run_trials','edits'):globals()[action](out)
    else:globals()[action](Path(sys.argv[3]),out,int(sys.argv[4]),sys.argv[5])
