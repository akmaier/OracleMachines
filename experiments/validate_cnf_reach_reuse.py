#!/usr/bin/env python3
"""Audit bounded negative-search reuse, its costs, and native proof archives."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import cProfile,gzip,pstats,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_reach_reuse as study
base=study.base;old=study.old;previous=study.prior.previous


def diagnose(out):
    p=base.load(out/'protocol.json');rows=[]
    # Opposite sides of the matched non-dominance comparison, chosen after census.
    for target,event_id in ((1,25),(37,17)):
        source,templates,refs,events=study.inputs(p,target)
        local,hints,_=previous.local_hints(source,templates,events[event_id],Counter());ts=[h['template'] for h in hints]
        for mode in ('frozen64','expanded128','cached64'):
            module=study.cached if mode=='cached64' else study.prior.shared
            limits=dict(p['limits']);limits['root_limit']=128 if mode=='expanded128' else 64
            c=Counter();prof=cProfile.Profile();program=prof.runcall(module.discover,local,ts,c,**limits)
            report=base.load(out/f'census-{target}-{mode}-0/report.json')
            ref=next(r for r in old.bound(report['events'])['rows'] if r['event']==event_id)
            assert program==ref['program'] and dict(c)==ref['counts']
            prof.dump_stats(str(out/f'profile-{target}-{event_id}-{mode}.pstats'))
            stats=pstats.Stats(prof)
            functions=[dict(file=k[0],line=k[1],function=k[2],calls=v[1],own_seconds=v[2],cumulative_seconds=v[3]) for k,v in stats.stats.items()]
            rows.append(dict(target=target,event=event_id,mode=mode,status=program['status'],reason=program['reason'],counts=dict(c),
                profile_seconds=stats.total_tt,functions=sorted(functions,key=lambda r:r['cumulative_seconds'],reverse=True)[:30]))
    base.write(out/'profiles.json',dict(rows=rows,limitations='Two exposed cases selected after census illustrate opposite coverage outcomes. Instrumentation changes timing; cumulative entries overlap. This is not a held-out performance estimate.'))


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent'])
    pv=base.load(study.PARENT/'validation.json');manifests=deepcopy(pv['parent_manifests'])
    mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']))
    artifacts=0
    for path,e in manifests.items():
        assert base.sha(path)==e['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(175,19708)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_reach_reuse.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    for binding in p['exploration'].values():assert base.sha(binding['path'])==binding['sha256']
    assert base.sha(p['exploration']['initial_test_snapshot']['path'])==old.bound(p['exploration']['checked_probe'])['source_fingerprints']['solver/test_cnf_shortening_reach_reuse.py']
    assert p['exploration']['bfs_actual_candidate']==old.binding(str(Path(study.cached.__file__).relative_to(Path.cwd())))
    refs={(r['target'],r['event']):r for r in old.bound(p['previous_census'])['records']}
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==64
    groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};rss={m:0 for m in study.MODES}
    membership={m:0 for m in study.MODES};rows_by_mode={m:{} for m in study.MODES}
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];target=sample['target'];rows=old.bound(report['events'])['rows']
        assert report['mode']==mode and report['target']==target
        assert {(target,r['event']) for r in rows}=={k for k in refs if k[0]==target}
        for row in rows:
            ref=refs[(target,row['event'])];assert row['root']==ref['source_root'];c=row['counts']
            assert c.get('reach_roots',0)<=(128 if mode=='expanded128' else 64)
            assert c.get('rounds',0)<=33
            if mode=='frozen64':assert row['program']==ref['program']
            if mode in ('checked64','cached64'):
                assert sum(c.get(k,0) for k in ('reach_edge_visits','reuse_invalidation_checks','cache_admission_edge_checks'))<=16384
                assert c.get('cache_peak_vertices',0)<=16384
                if mode=='cached64':assert c.get('cache_admission_edge_checks',0)==0
            if sample['repeat']==0:rows_by_mode[mode][(target,row['event'])]=row
            membership[mode]=max(membership[mode],c.get('cache_peak_vertices',0))
        groups.setdefault((target,mode),[]).append(rows)
        totals[mode].update({k:report[k]/2 for k in ('discovery_seconds','binding_seconds','complete_seconds')})
        counts[mode].update({k:v/2 for k,v in report['counts'].items()})
        rss[mode]=max(rss[mode],report['peak_rss_bytes'])
    for pair in groups.values():
        assert len(pair)==2
        assert [(r['root'],r['program'],r['counts']) for r in pair[0]]==[(r['root'],r['program'],r['counts']) for r in pair[1]]
    coverage={};old_success={k for k,r in rows_by_mode['frozen64'].items() if r['program']['status']=='refuted'}
    for mode,rows in rows_by_mode.items():
        success={k for k,r in rows.items() if r['program']['status']=='refuted'}
        coverage[mode]=dict(outcomes=dict(Counter('refuted' if r['program']['status']=='refuted' else r['program']['reason'] for r in rows.values())),
            unique_roots=len({rows[k]['root'] for k in success}),gained_events=sorted(success-old_success),lost_events=sorted(old_success-success))
    # Check every positive comparison program against its actual local source,
    # including larger-budget positives outside the new-root compilation cohort.
    positive_checks=Counter()
    for target in p['targets']:
        source,templates,rs,events=study.inputs(p,target)
        for ref in rs:
            key=(target,ref['event']);positive=[m for m in study.MODES if rows_by_mode[m][key]['program']['status']=='refuted']
            if not positive:continue
            local,hints,_=previous.local_hints(source,templates,events[ref['event']],Counter())
            for mode in positive:
                study.cached.validate(local,[h['template'] for h in hints],rows_by_mode[mode][key]['program'],Counter())
                positive_checks[mode]+=1
    cache_success={k for k,r in rows_by_mode['cached64'].items() if r['program']['status']=='refuted'}
    expanded_success={k for k,r in rows_by_mode['expanded128'].items() if r['program']['status']=='refuted'}
    coverage_comparison=dict(cached_only=sorted(cache_success-expanded_success),expanded_only=sorted(expanded_success-cache_success),
        union_events=len(cache_success|expanded_success),union_roots=len({rows_by_mode['cached64'][k]['root'] for k in cache_success|expanded_success}))
    # The reusable variant and its completed-BFS exploration must agree exactly.
    explored=old.bound(p['exploration']['bfs_probe'])
    assert len(explored['rows'])==615
    for row in explored['rows']:
        measured=rows_by_mode['cached64'][(row['target'],row['event'])]
        assert row['new']==measured['program'] and row['counts']==measured['counts']
    case_data=base.load(out/'cases.json');cases=[old.bound(b) for b in case_data['cases']]
    old_roots={r['source_root'] for r in refs.values() if r['program']['status']=='refuted'}
    new_roots={r['root'] for r in rows_by_mode['cached64'].values() if r['program']['status']=='refuted'}-old_roots
    assert len(cases)==len(new_roots) and {c['root'] for c in cases}==new_roots
    proposals=case_data['proposals']
    assert {(r['target'],r['event']) for r in proposals}=={k for k,r in rows_by_mode['cached64'].items() if r['root'] in new_roots and r['program']['status']=='refuted'}
    for case in cases:study.cached.validate(case['source'],case['templates'],case['program'],Counter())
    comparison=base.load(out/'comparisons.json');assert len(comparison['samples'])==len(cases)*6
    trial_groups={};audits={};archives=[]
    for sample in comparison['samples']:
        r=old.bound(sample);i=sample['index'];mode=sample['mode'];assert r['case']==case_data['cases'][i] and r['mode']==mode
        assert r['result']['status'] in ('unsat','unresolved')
        if mode!='fresh':assert r['result']['status']=='unsat'
        if r['result']['status']=='unsat':assert r['result']['result']['root']==cases[i]['root']
        archive=r['archive'];assert base.sha(archive['path'])==archive['sha256']
        key=(archive['sha256'],cases[i]['root'])
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(archive,path);assert base.sha(path)==archive['database_sha256']
                stored,readers=previous.audit(path,[dict(source=cases[i]['source'])],[r['result']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits[key]=dict(archive=archive,root=cases[i]['root'],readers=readers);archives.append(archive)
        trial_groups.setdefault((i,mode),[]).append(r)
    trial_totals={m:Counter() for m in study.COMPILERS};trial_rss={m:0 for m in study.COMPILERS};summary=[]
    for i,case in enumerate(cases):
        row=dict(name=case['name'],root=case['root'],present_after_query=case['present_after_query'],arms={})
        for mode in study.COMPILERS:
            a,b=trial_groups[(i,mode)];assert a['result']['status']==b['result']['status']
            for key in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[key]==b[key],(i,mode,key)
            metric={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metric['records']=sum(a['authority_tables'].values());trial_totals[mode].update(metric)
            trial_rss[mode]=max(trial_rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
            row['arms'][mode]=dict(status=a['result']['status'],**metric)
        summary.append(row)
    analysis=dict(census_totals=totals,census_counts=counts,census_max_rss_bytes=rss,census_max_cached_memberships=membership,
        coverage=coverage,coverage_comparison=coverage_comparison,positive_program_checks=positive_checks,
        trial_totals=trial_totals,trial_max_rss_bytes=trial_rss,summary=summary,
        new_roots=len(cases),new_event_proposals=len(proposals),not_previously_saved=sum(not c['present_after_query'] for c in cases),
        trial_statuses={m:dict(Counter(s['arms'][m]['status'] for s in summary)) for m in study.COMPILERS},
        sources=len(sources),unique_archive_audits=len(audits),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        reach_reuse={**{k:old.binding(out/(k+'.json')) for k in ('protocol','censuses','cases','comparisons','analysis','profiles')},'supplemental_archives':archives})
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],
        preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),
        seconds=time.perf_counter()-began,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(passed=True,census_totals=totals,coverage=coverage,trial_totals=trial_totals,archives=len(audits))),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','4dca6868:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text()
    assert re.search(r'Ran 1839 tests in .*\n\nOK',full) and re.search(r'Ran 32 tests in .*\n\nOK',focus)
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['reach_reuse']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1839,focused_tests=32,proof_blocks_unchanged=64,
        manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1015,final_sources=len(cp['source_fingerprints']),
        prior_manifests=175,prior_artifacts=19708,archive_audits=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),
        checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0))
        f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=176,next_artifacts=19708+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
