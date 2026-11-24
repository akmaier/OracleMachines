#!/usr/bin/env python3
"""Audit shared-state preparation, exact proof identity, reuse and preservation."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import cProfile,gzip,pstats,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_context as study
base=study.base;old=study.old;previous=study.previous


def auxiliary(out):
    parent=base.load(study.PARENT/'checkpoint.json');p=old.bound(parent['guard_covers']['protocol'])
    target=37;event_id=17;pos=p['targets'].index(target)
    source=study.native.normalize(old.bound(p['cases'])[target]['source'])[0]
    ts=old.bound(old.bound(p['inputs'][pos])['extraction'])['templates']
    refs=base.load(study.PARENT/'census.json')['records'];ref=next(r for r in refs if r['target']==target and r['event']==event_id)
    event=old.bound(ref['events'])['events'][event_id]
    local,hints,_=previous.local_hints(source,ts,event,Counter());templates=[h['template'] for h in hints];profiles={}
    for mode,module in (('frozen',study.frozen),('shared',study.shared)):
        c=Counter();prof=cProfile.Profile();program=prof.runcall(module.discover,local,templates,c,**previous.LIMITS);assert program==ref['program']
        prof.dump_stats(str(out/(mode+'-profile.pstats')))
        with (out/(mode+'-profile.log')).open('w') as f:pstats.Stats(prof,stream=f).sort_stats('cumulative').print_stats(30)
        functions=[dict(file=k[0],line=k[1],function=k[2],calls=v[1],own_seconds=v[2],cumulative_seconds=v[3]) for k,v in pstats.Stats(prof).stats.items()]
        profiles[mode]=dict(counts=dict(c),functions=sorted(functions,key=lambda r:r['cumulative_seconds'],reverse=True)[:30])
    base.write(out/'profiles.json',dict(target=target,event=event_id,modes=profiles,limitations='One instrumented miss; cumulative times overlap. No causal or population-wide speed ratio follows from this profile.'))
    # Matched cold reopen stream uses identical prior archives; no copied banks.
    references=base.load(study.PARENT/'stream.json')['rows'];streams={}
    for mode,module in (('frozen',study.frozen),('shared',study.shared)):
        rows=[];began=time.perf_counter()
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db'
            for reference in references:
                source,templates=previous.chain(4,reference['padding']);c=Counter();tick=time.perf_counter()
                program=module.discover(source,templates,c,**previous.LIMITS);discovery=time.perf_counter()-tick
                s=study.native.ResidualSolver(path)
                try:
                    before=old.tables(s.db);tick=time.perf_counter();root=module.compile_program(s,source,templates,program,c)
                    elapsed=time.perf_counter()-tick;after=old.tables(s.db)
                    assert all(after[t].get(k)==v for t in before for k,v in before[t].items())
                    if rows:assert c['support_hits']==1 and sum(len(after[t])-len(before[t]) for t in before)==1
                finally:s.close()
                tick=time.perf_counter();actual,readers=previous.audit(path,[dict(source=source)],[reference['result']]);cold=time.perf_counter()-tick;assert actual==after
                assert base.sha(path)==reference['archive']['database_sha256']
                rows.append(dict(padding=reference['padding'],source=source,result=reference['result'],archive=reference['archive'],
                    discovery_seconds=discovery,compile_seconds=elapsed,cold_seconds=cold,counts=dict(c),
                    added_records=sum(len(after[t])-len(before[t]) for t in before),cold_readers=readers))
        streams[mode]=dict(rows=rows,complete_seconds=time.perf_counter()-began)
    base.write(out/'streams.json',dict(modes=streams,limitations='One frozen/shared sequential stream each; identity and reopen reuse test, not a stable timing estimate.'))
    # Preserve the newly accepted empty-cofactor proof separately from the census.
    dest=out/'empty-cofactor';dest.mkdir();source,templates=previous.chain(1,4)
    program=study.frozen.discover(source,templates,Counter());source=study.native.normalize(list(source)+[(1,)])[0]
    program=dict(program,steps=[program['steps'][0]],terminal=dict(kind='empty'))
    try:study.frozen.validate(source,templates,program,Counter())
    except ValueError as error:rejection=str(error)
    else:raise AssertionError('Expected preserved whole-cofactor rejection')
    assert rejection=='Expected whole cofactor'
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=study.native.ResidualSolver(path)
        try:root=study.shared.compile_program(s,source,templates,program,Counter())
        finally:s.close()
        result=dict(status='unsat',result=dict(root=root,answer=False,model=None,authority='native'))
        stored,readers=previous.audit(path,[dict(source=source)],[result]);archive=base.archive(path,dest)
    base.write(out/'empty-cofactor.json',dict(source=source,templates=templates,program=program,result=result,archive=archive,
        old_rejection=rejection,cold_readers=readers,records=sum(map(len,stored.values())),
        limitations='A sound contradiction-normalization edge case outside the matched 615-event census. It is not a new whole-query result.'))


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=study.PARENT/'manifest.json'
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,e in manifests.items():
        assert base.sha(path)==e['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(174,18750)
    failed=old.bound(p['failed_manifest'])
    for f,h in failed['artifacts'].items():assert base.sha(f)==h,f
    sources={**p['source_fingerprints'],'experiments/validate_cnf_shortening_context.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    # Check structural identity of every algorithm function except preparation.
    import ast
    def functions(module):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(Path(module.__file__).read_text()).body if isinstance(n,ast.FunctionDef) and n.name!='_state'}
    assert functions(study.frozen)==functions(study.shared)
    refs={(r['target'],r['event']):r for r in old.bound(p['previous_census'])['records']}
    census_samples=base.load(out/'censuses.json')['samples'];assert len(census_samples)==32
    census_groups={};census_totals={m:Counter() for m in ('frozen','shared')};census_counts={m:Counter() for m in census_totals}
    for sample in census_samples:
        r=old.bound(sample);rows=old.bound(r['events'])['rows'];target=r['target'];mode=r['mode']
        assert len(rows)==sum(t==target for t,e in refs)
        for row in rows:
            ref=refs[(target,row['event'])];assert row['program_sha256']==base.key_sha(base.encode(ref['program']))
            assert row['status']==ref['program']['status'] and row['reason']==ref['program']['reason']
            for key in ('templates_checked','template_checked_reason_literals','hint_check_literals','verified_core_hints','reach_roots','reach_edge_visits','forced_steps','rounds'):
                assert row['counts'].get(key,0)==ref['counts'].get(key,0),(target,row['event'],key)
        census_groups.setdefault((target,mode),[]).append(rows)
        census_totals[mode].update({k:r[k]/2 for k in ('discovery_seconds','binding_seconds','complete_seconds','peak_rss_bytes')})
        census_counts[mode].update({k:v/2 for k,v in r['counts'].items()})
    for key,pair in census_groups.items():
        assert len(pair)==2
        for a,b in zip(*pair):assert a['counts']==b['counts'] and a['binding_counts']==b['binding_counts']
    comparison=base.load(out/'comparisons.json');assert comparison['protocol']==old.binding(out/'protocol.json')
    assert len(comparison['samples'])==630
    cases=[old.bound(b) for b in p['cases']];groups={};audits={};reused=[]
    def inspect(archive,source,result):
        assert base.sha(archive['path'])==archive['sha256']
        if archive['sha256'] in audits:return
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';previous.restore_archive(archive,path);assert base.sha(path)==archive['database_sha256']
            stored,readers=previous.audit(path,[dict(source=source)],[result])
        audits[archive['sha256']]=dict(archive=archive,readers=readers);reused.append(archive)
    for sample in comparison['samples']:
        r=old.bound(sample);i=sample['index'];mode=sample['mode'];reference=old.bound(p['controls'][str(i)]['fresh' if mode=='fresh' else 'support'])
        assert r['case']==p['cases'][i] and r['result']['status']=='unsat'
        for key in ('digest','record_bytes','authority_tables','native_counts'):assert r[key]==reference[key],(i,mode,key)
        assert r['archive']==reference['archive'] and r['temporary_compression']['database_sha256']==r['archive']['database_sha256']
        inspect(r['archive'],cases[i]['source'],r['result']);groups.setdefault((i,mode),[]).append(r)
    assert len(groups)==315
    totals={};summary=[]
    for i,case in enumerate(cases):
        row=dict(name=case['name'],category=case['category'],arms={})
        for mode in study.MODES:
            a,b=groups[(i,mode)];assert a['counts']==b['counts']
            metric={k:(a[k]+b[k])/2 for k in ('solve_seconds','complete_seconds','warm_seconds','cold_seconds','record_bytes','peak_rss_bytes')}
            metric['records']=sum(a['authority_tables'].values());row['arms'][mode]=metric
            totals.setdefault(case['category'],{}).setdefault(mode,Counter()).update(metric)
        summary.append(row)
    streams=base.load(out/'streams.json')
    for mode,s in streams['modes'].items():
        assert [r['added_records'] for r in s['rows']]==[12,1,1,1]
        for row in s['rows']:inspect(row['archive'],row['source'],row['result'])
    special=base.load(out/'empty-cofactor.json');inspect(special['archive'],special['source'],special['result'])
    base.write(out/'analysis.json',dict(census_totals=census_totals,census_counts=census_counts,totals=totals,summary=summary,
        unchanged=dict(events=615,refuted_events=142,root_limit=388,no_useful_forced_literal=85,local_roots=97),
        sources=len(sources),unique_archive_audits=len(audits),limitations=p['limitations']))
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        shortening_context={**{k:old.binding(out/(k+'.json')) for k in ('protocol','censuses','comparisons','analysis','profiles','streams','empty-cofactor')},
                            'archive_references':reused,'supplemental_archives':[special['archive']]})
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,failed_artifacts=len(failed['artifacts']),
        source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],
        preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),
        new_supplemental_archives=1,seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(passed=True,census_totals=census_totals,totals=totals,archives=len(audits))),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','cced9ad1:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1832 tests in .*\n\nOK',full) and re.search(r'Ran 41 tests in .*\n\nOK',focus)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['shortening_context']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1832,focused_tests=41,proof_blocks_unchanged=64,
        manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1010,final_sources=len(cp['source_fingerprints']),
        prior_manifests=174,prior_artifacts=18750,archive_audits=len(v['supplemental_archive_audits']),new_supplemental_archives=1,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),
        checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0))
        f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    # Include the untouched failed attempt in this published preservation boundary.
    failed_path=Path(base.load(out/'protocol.json')['failed_manifest']['path']).parent
    files+=sorted(f for f in failed_path.rglob('*') if f.is_file())
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=175,next_artifacts=18750+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
