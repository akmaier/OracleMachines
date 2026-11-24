#!/usr/bin/env python3
"""Preserve and independently replay shortening evidence and prior history."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_shortening as study
from experiments.cnf_guard_shortening import discover,compile_program,validate as replay
from experiments.cnf_archive_parts import restore_archive
from experiments.validate_cnf_whole_proof_reuse import audit
base=study.base;old=study.old


def stream(out):
    dest=out/'stream';dest.mkdir();rows=[];seen={};began=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db'
        for padding in (4,16,64,256):
            source,templates=study.chain(4,padding);c=Counter();tick=time.perf_counter()
            program=discover(source,templates,c,**study.LIMITS);discovery=time.perf_counter()-tick
            s=study.native.ResidualSolver(path)
            try:
                before=old.tables(s.db);tick=time.perf_counter();root=compile_program(s,source,templates,program,c)
                elapsed=time.perf_counter()-tick;after=old.tables(s.db)
                assert all(after[t].get(k)==v for t in before for k,v in before[t].items())
                node=s._read(root);support=node['proof']['child']
                if rows: assert support==rows[0]['support'] and c['support_hits']==1 and len(after['cnf_residual_v1'])==len(before['cnf_residual_v1'])+1
            finally:s.close()
            result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
            tick=time.perf_counter();actual,readers=audit(path,[dict(source=source)],[result]);cold=time.perf_counter()-tick;assert actual==after
            rowdir=dest/str(padding);rowdir.mkdir();archive=base.archive(path,rowdir)
            rows.append(dict(padding=padding,source=source,result=result,support=support,counts=dict(c),discovery_seconds=discovery,
                compile_seconds=elapsed,cold_seconds=cold,archive=archive,records=sum(map(len,after.values())),
                added_records=sum(len(after[t])-len(before[t]) for t in before),
                record_bytes=sum(len(k.encode())+len(v.encode()) for r in after.values() for k,v in r.items()),cold_readers=readers))
    base.write(out/'stream.json',dict(rows=rows,complete_seconds=time.perf_counter()-began,limitations='One append-only support arm, not a matched stream runtime comparison; previous row payloads stay unchanged after every reopen.'))


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,e in manifests.items():
        assert base.sha(path)==e['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(173,17347)
    sources={**p['source_fingerprints'],__file__.split('/OracleMachines/')[-1]:base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    census=old.bound(p['census']);records=census['records'];assert len(records)==615
    closed=[r for r in records if r['program']['status']=='refuted']
    new=[r for r in closed if not r['old_cover'] and not r['old_scc_conflict']]
    assert len(closed)==142 and len(new)==104 and len({r['source_root'] for r in new})==67
    assert all(r['program']['steps'] and r['present_after_query'] for r in new)
    missing=[r for r in closed if not r['present_after_query']]
    assert len(missing)==1 and missing[0]['old_scc_conflict'] and not missing[0]['program']['steps']
    comparison=base.load(out/'comparisons.json');assert comparison['protocol']==old.binding(out/'protocol.json')
    cases=[old.bound(b) for b in p['cases']];assert len(cases)==105
    groups={};audits={};archives=[]
    def inspect(r,case):
        a=r['archive'];assert base.sha(a['path'])==a['sha256']
        if a['sha256'] not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';restore_archive(a,path);assert base.sha(path)==a['database_sha256']
                stored,readers=audit(path,[dict(source=case['source'])],[r['result']])
                assert r['digest']=={t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}
                assert r['record_bytes']==sum(len(k.encode())+len(v.encode()) for rows in stored.values() for k,v in rows.items())
            audits[a['sha256']]=dict(archive=a,readers=readers);archives.append(a)
    for sample in comparison['samples']:
        r=old.bound(sample);i=sample['index'];mode=sample['mode'];assert r['case']==p['cases'][i] and r['mode']==mode
        assert r['result']['status'] in ('unsat','unresolved')
        if mode!='fresh':assert r['result']['status']=='unsat'
        inspect(r,cases[i]);groups.setdefault((i,mode),[]).append(r)
    assert len(comparison['samples'])==630 and len(groups)==315
    summary=[];totals={}
    for i,case in enumerate(cases):
        frames,tail,ids=replay(case['source'],case['templates'],case['program'],Counter())
        row=dict(name=case['name'],category=case['category'],steps=len(frames),source_literals=sum(map(len,case['source'])),
            support_literals=sum(len(case['source'][j]) for j in ids),arms={})
        for mode in study.MODES:
            a,b=groups[(i,mode)];assert a['digest']==b['digest'] and a['counts']==b['counts']
            metric={k:sum(r[k] for r in (a,b))/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','peak_rss_bytes','record_bytes')}
            metric.update(records=sum(a['authority_tables'].values()),status=a['result']['status'],sqlite_bytes=a['archive']['database_bytes'])
            row['arms'][mode]=metric
            t=totals.setdefault(case['category'],{}).setdefault(mode,Counter())
            t.update({k:v for k,v in metric.items() if k!='status'});t['unsat']+=metric['status']=='unsat';t['unresolved']+=metric['status']=='unresolved'
        summary.append(row)
    st=base.load(out/'stream.json')
    for r in st['rows']:
        a=r['archive'];assert base.sha(a['path'])==a['sha256']
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';restore_archive(a,path);stored,readers=audit(path,[dict(source=r['source'])],[r['result']])
            assert sum(map(len,stored.values()))==r['records']
        archives.append(a);audits[a['sha256']]=dict(archive=a,readers=readers)
    limits=p['limitations']+['104 same-graph extensions correspond to 67 distinct local roots, all already retained after ordinary search. The one previously absent root is a zero-shortening SCC case enabled by more supported guards; do not credit it to partial shortening.',
        'All 615 event binding and discovery costs, including 473 unresolved attempts, remain charged. No live routing, acquisition, query coverage or production speedup follows from these local measurements.']
    analysis=dict(summary=summary,totals=totals,census=dict(events=615,refuted_events=142,new_events=104,new_roots=67,
        unique_refuted_roots=97,missing_after_query=[dict(target=r['target'],event=r['event'],case=r['case']) for r in missing],
        reasons=census['counts'],binding_seconds=sum(r['binding_seconds'] for r in records),
        discovery_seconds=sum(r['discovery_seconds'] for r in records),
        positive_discovery_seconds=sum(r['discovery_seconds'] for r in records if r['program']['status']=='refuted')),
        selected_case_binding_seconds=sum(c['binding_seconds'] for c in cases if c['category']=='local'),
        selected_case_discovery_seconds=sum(c['discovery_seconds'] for c in cases if c['category']=='local'),
        stream=st,limitations=limits)
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        guard_shortening={**{k:old.binding(out/(k+'.json')) for k in ('protocol','census','comparisons','analysis','stream','profile')},'supplemental_archives':archives})
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],
        preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),
        seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(passed=True,archives=len(audits),totals=totals,census=analysis['census'])),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','0af87518:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1823 tests in .*\n\nOK',full) and re.search(r'Ran 32 tests in .*\n\nOK',focus)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['guard_shortening']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1823,focused_tests=32,proof_blocks_unchanged=64,
        manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1006,final_sources=len(cp['source_fingerprints']),
        prior_manifests=173,prior_artifacts=17347,archives=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),
        checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0))
        f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=174,next_artifacts=17347+len(files))))


def profile(out):
    import cProfile,pstats
    census=base.load(out/'census.json')
    row=max(census['records'],key=lambda r:r['discovery_seconds'])
    parent=old.bound(base.load(out/'protocol.json')['parent'])
    p=old.bound(parent['guard_covers']['protocol']);position=p['targets'].index(row['target'])
    original=old.bound(p['cases'])[row['target']]
    source=study.native.normalize(original['source'])[0]
    templates=old.bound(old.bound(p['inputs'][position])['extraction'])['templates']
    event=old.bound(row['events'])['events'][row['event']]
    local,hints,whole=study.local_hints(source,templates,event,Counter())
    ts=[h['template'] for h in hints];prof=cProfile.Profile();counts=Counter()
    result=prof.runcall(discover,local,ts,counts,**study.LIMITS)
    assert result==row['program'] and dict(counts)==row['counts']
    prof.dump_stats(str(out/'discovery-profile.pstats'))
    with (out/'discovery-profile.log').open('w') as f:
        stats=pstats.Stats(prof,stream=f);stats.sort_stats('cumulative').print_stats(35)
    stats=pstats.Stats(prof)
    rows=[dict(file=k[0],line=k[1],function=k[2],primitive_calls=v[0],calls=v[1],own_seconds=v[2],cumulative_seconds=v[3]) for k,v in stats.stats.items()]
    base.write(out/'profile.json',dict(target=row['target'],event=row['event'],program=result,counts=dict(counts),
        original_discovery_seconds=row['discovery_seconds'],functions=sorted(rows,key=lambda r:r['cumulative_seconds'],reverse=True)[:35],
        limitations='One instrumented, previously most expensive miss. Cumulative times overlap. Selection and setup are outside the profile; this is diagnosis, not a matched speed comparison.'))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
