#!/usr/bin/env python3
"""Audit cursor replay, cold persistence, new native proofs and preserved history."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_cursor as study
from experiments.validate_cnf_layered_feedback import deterministic_result
base=study.base;old=study.old;previous=study.previous


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(189,25722)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_probe_cursor.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    seeds={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']};assert len(seeds)==43
    groups={};ct={m:Counter() for m in study.MODES};cc={m:Counter() for m in study.MODES};rss=Counter();events={m:{} for m in study.MODES}
    for sample in base.load(out/'censuses.json')['samples']:
        report=old.bound(sample);groups.setdefault((sample['target'],sample['mode']),[]).append(report)
    for (target,mode),reports in groups.items():
        assert len(reports)==2;a,b=reports;aa=old.bound(a['events'])['rows'];bb=old.bound(b['events'])['rows'];assert len(aa)==len(bb)
        for x,y in zip(aa,bb):
            for k in ('target','event','root','counts','verification_counts','reconstruction_counts'):assert x[k]==y[k],(target,mode,k)
            assert old.bound(x['result'])==old.bound(y['result'])
            if x['initial'] is not None:assert old.bound(x['initial'])==old.bound(y['initial'])
            assert [v['counts'] for v in x['phases']]==[v['counts'] for v in y['phases']]
            key=(target,x['event']);assert key not in events[mode];events[mode][key]=x;assert x['root']==seeds[key]['root']
            for phase in x['phases']:
                assert phase['counts'].get('probe_occurrence_visits',0)<=524288
                assert not phase['counts'].get('cursor_interrupted_probes',0)
        assert a['counts']==b['counts'];cc[mode].update(a['counts'])
        for k in ('discovery_seconds','reconstruction_seconds','persistence_seconds','verification_seconds','complete_seconds'):ct[mode][k]+=(a[k]+b[k])/2
        rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    assert all(set(rows)==set(seeds) for rows in events.values())
    pilot={(r['target'],r['event']):r for r in base.load(out/'pilot.json')['rows']};gains=set();extra_failures=0;extra_events=0;first_failures=0;first_refuted=0;cursor_bytes=0;initial_completed=0;completed_total=0
    for key,seed in seeds.items():
        args=[seed[k] for k in ('final_source','templates','seed','closure','new','next_closure','third','feedback_closure')]
        single=old.bound(events['single'][key]['result']);restart=old.bound(events['restart'][key]['result']);resume=old.bound(events['resume'][key]['result'])
        assert single==restart==resume==pilot[key]['second']==pilot[key]['single']
        first=old.bound(events['resume'][key]['initial']);assert first==old.bound(events['restart'][key]['initial'])==pilot[key]['first']
        c1=Counter();again=study.search.discover(*args,c1);assert again==first and dict(c1)==events['resume'][key]['phases'][0]['counts']
        if first['program']['status']!='refuted':
            cr=Counter();again=study.search.discover(*args,cr,cursor=first['cursor']);assert again==resume and dict(cr)==events['resume'][key]['phases'][1]['counts']
            initial_completed+=len(first['cursor']['completed'])
        else:first_refuted+=1
        study.search.validate(*args,resume,Counter())
        if resume['program']['status']=='refuted':gains.add(key)
        delta=len(resume['program']['probes'])-len(first['program']['probes']);extra_failures+=delta;extra_events+=delta>0
        first_failures+=len(first['program']['probes']);completed_total+=len(resume['cursor']['completed'])
        cursor_bytes+=len(base.encode(resume['cursor']).encode())
    assert gains=={(40,46),(67,48)} and first_refuted==2 and extra_failures==142 and extra_events==31
    assert cc['resume']['probe_roots']==cc['single']['probe_roots']==5271
    assert cc['restart']['probe_roots']-cc['resume']['probe_roots']==initial_completed==2624
    remaining=base.load(out/'remaining.json')['rows'];assert len(remaining)==41
    for row in remaining:
        key=(row['target'],row['event']);assert key not in gains
        assert {k:v for k,v in row.items() if k!='probe_cursor'}==seeds[key]
        assert row['probe_cursor']==old.bound(events['resume'][key]['result'])
    assert {(r['target'],r['event']) for r in remaining}==set(seeds)-gains
    cd=base.load(out/'cases.json');cases=[old.bound(b) for b in cd['cases']];assert len(cases)==len({r['root'] for r in cases})==2
    assert {(r['target'],r['event']) for r in cd['proposals']}==gains
    earlier=set()
    for folder in ('cnf-probe-support','cnf-probe-feedback','cnf-closure-probes','cnf-layered-feedback','cnf-changed-closure-probes','cnf-third-feedback'):
        for binding in base.load(Path('experiments/results')/folder/'cases.json')['cases']:earlier.add(old.bound(binding)['root'])
    assert not earlier.intersection(r['root'] for r in cases)
    for case in cases:
        key=(case['target'],case['event']);seed=seeds[key]
        for field in ('seed','closure','new','next_closure','third','feedback_closure'):assert case[field]==seed[field]
        assert case['result']==old.bound(events['resume'][key]['result'])
        _,tail=study.search.frozen.bind_prefix(case['source'],case['templates'],case['prefix'],Counter())
        assert list(map(list,tail['local']))==seed['final_source'] and [h['template'] for h in tail['hints']]==seed['templates']
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==8;tg={};audits={};archives=[]
    for sample in trials:
        r=old.bound(sample);i=sample['index'];mode=sample['mode'];case=cases[i]
        assert r['case']==cd['cases'][i] and r['mode']==mode and r['result']['status']=='unsat' and r['result']['result']['root']==case['root']
        a=r['archive'];assert base.sha(a['path'])==a['sha256'];key=(a['sha256'],case['root'])
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(a,path);stored,readers=previous.audit(path,[dict(source=case['source'])],[r['result']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits[key]=dict(archive=a,root=case['root'],readers=readers);archives.append(a)
        tg.setdefault((i,mode),[]).append(r)
    totals={m:Counter() for m in ('fresh','layered')};counts={m:Counter() for m in totals};native_counts={m:Counter() for m in totals};summary=[]
    for i,case in enumerate(cases):
        row=dict(name=case['name'],snapshot_answer=case['snapshot_answer'],arms={})
        for mode in totals:
            a,b=tg[i,mode];assert deterministic_result(a['result'])==deterministic_result(b['result'])
            for k in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[k]==b[k],(i,mode,k)
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metrics['records']=sum(a['authority_tables'].values());totals[mode].update(metrics);counts[mode].update(a['counts']);native_counts[mode].update(a['native_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes']);row['arms'][mode]=metrics
        summary.append(row)
    comparisons={k:dict(improved=sum(r['arms']['layered'][k]<r['arms']['fresh'][k] for r in summary),regressed=[r['name'] for r in summary if r['arms']['layered'][k]>r['arms']['fresh'][k]]) for k in ('solve_seconds','complete_seconds','record_bytes')}
    analysis=dict(events=43,new_refuted_events=2,new_roots=2,remaining_events=41,coverage=dict(before=203,after=205,total=246),
        census_totals=ct,census_counts=cc,totals=totals,counts=counts,native_counts=native_counts,summary=summary,comparisons=comparisons,peak_rss_bytes=rss,
        first_refutations=first_refuted,resume_additional_refutations=len(gains)-first_refuted,first_failures=first_failures,additional_failures=extra_failures,events_with_additional_failures=extra_events,
        total_completed=completed_total,avoided_repeated_probes=initial_completed,remaining_failures=sum(len(r['probe_cursor']['program']['probes']) for r in remaining),remaining_with_failures=sum(bool(r['probe_cursor']['program']['probes']) for r in remaining),
        result_bytes=dict(remaining=(out/'remaining.json').stat().st_size,final_cursors=cursor_bytes,cases=sum(Path(b['path']).stat().st_size for b in cd['cases'])),
        unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,probe_cursor={k:old.binding(out/(k+'.json')) for k in ('protocol','cases','remaining','censuses','comparisons','analysis')})
    cp['probe_cursor']['supplemental_archives']=archives;base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(census=ct,totals=totals,additional_failures=extra_failures,avoided=initial_completed)),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','ff89b0b1:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1945 tests in .*\n\nOK',full) and re.search(r'Ran 80 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['probe_cursor']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1945,focused_tests=80,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1081,final_sources=len(cp['source_fingerprints']),prior_manifests=189,prior_artifacts=25722,archive_audits=len(v['supplemental_archive_audits']),warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=190,next_artifacts=25722+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
