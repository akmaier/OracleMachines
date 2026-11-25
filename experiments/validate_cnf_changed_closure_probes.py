#!/usr/bin/env python3
"""Audit changed-closure proofs, search policy, native readers and lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_changed_closure_probes as study
from experiments.validate_cnf_layered_feedback import deterministic_result
base=study.base;old=study.old;previous=study.previous


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(187,25456)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_changed_closure_probes.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    seeds={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']};assert len(seeds)==53
    groups={};census_totals={m:Counter() for m in study.MODES};census_counts={m:Counter() for m in study.MODES};rss=Counter()
    for sample in base.load(out/'censuses.json')['samples']:
        r=old.bound(sample);mode=sample['mode'];groups.setdefault((sample['target'],mode),[]).append(r)
    events={m:{} for m in study.MODES}
    for (target,mode),reports in groups.items():
        assert len(reports)==2;a,b=reports;aa=old.bound(a['events'])['rows'];bb=old.bound(b['events'])['rows'];assert len(aa)==len(bb)
        for x,y in zip(aa,bb):
            for k in ('target','event','root','result','counts','reconstruction_counts'):assert x[k]==y[k],(target,mode,k)
            key=(target,x['event']);assert key not in events[mode];events[mode][key]=x
            seed=seeds[key];assert x['root']==seed['root']
            study.search.validate(seed['final_source'],seed['templates'],seed['seed'],seed['closure'],seed['new'],seed['next_closure'],x['result'],Counter())
            assert x['counts'].get('probe_roots',0)<=p['limits']['probe_limit']
            assert x['counts'].get('probe_occurrence_visits',0)<=p['limits']['work_limit']
        assert a['counts']==b['counts'];census_counts[mode].update(a['counts'])
        for k in ('discovery_seconds','reconstruction_seconds','complete_seconds'):census_totals[mode][k]+=(a[k]+b[k])/2
        rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    assert all(set(rows)==set(seeds) for rows in events.values())
    skipped=0;gains=[]
    for key,seed in seeds.items():
        all_result=events['all'][key]['result'];changed=events['changed'][key]['result']
        if changed['action']=='unchanged':
            skipped+=1;assert all_result['program']['status']=='unresolved' and not all_result['program']['probes']
            assert not seed['new']['probes'];assert not seed['additional_variables']
            assert events['changed'][key]['counts'].get('probe_roots',0)==0
        else:
            assert all_result==changed
            if changed['program']['status']=='refuted':gains.append(key)
    assert skipped==32 and len(gains)==8
    pilot=base.load(out/'pilot.json')['rows'];assert len(pilot)==53
    for r in pilot:assert r['result']==events['all'][r['target'],r['event']]['result']
    remaining=base.load(out/'remaining.json')['rows'];assert len(remaining)==45
    for row in remaining:
        key=(row['target'],row['event']);assert key not in gains
        assert {k:v for k,v in row.items() if k!='third'}==seeds[key]
        assert row['third']==events['changed'][key]['result']
    assert {(r['target'],r['event']) for r in remaining}==set(seeds)-set(gains)
    cd=base.load(out/'cases.json');cases=[old.bound(b) for b in cd['cases']]
    assert {(r['target'],r['event']) for r in cd['proposals']}==set(gains)
    assert len({r['root'] for r in cases})==len(cases)==len({r['root'] for r in cd['proposals']})
    previous_roots=set()
    for folder in ('cnf-probe-support','cnf-probe-feedback','cnf-closure-probes','cnf-layered-feedback'):
        for binding in base.load(Path('experiments/results')/folder/'cases.json')['cases']:previous_roots.add(old.bound(binding)['root'])
    assert not previous_roots.intersection(r['root'] for r in cases)
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==len(cases)*4;trial_groups={};audits={};archives=[]
    for sample in trials:
        r=old.bound(sample);i=sample['index'];mode=sample['mode'];case=cases[i]
        assert r['case']==cd['cases'][i] and r['mode']==mode and r['result']['status']=='unsat'
        assert r['result']['result']['root']==case['root']
        a=r['archive'];assert base.sha(a['path'])==a['sha256'];key=(a['sha256'],case['root'])
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(a,path);stored,readers=previous.audit(path,[dict(source=case['source'])],[r['result']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits[key]=dict(archive=a,root=case['root'],readers=readers);archives.append(a)
        trial_groups.setdefault((i,mode),[]).append(r)
    totals={m:Counter() for m in ('fresh','layered')};counts={m:Counter() for m in totals};native_counts={m:Counter() for m in totals};summary=[]
    for i,case in enumerate(cases):
        row=dict(name=case['name'],snapshot_answer=case['snapshot_answer'],arms={})
        for mode in totals:
            a,b=trial_groups[i,mode];assert deterministic_result(a['result'])==deterministic_result(b['result'])
            for k in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[k]==b[k],(i,mode,k)
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metrics['records']=sum(a['authority_tables'].values());totals[mode].update(metrics);counts[mode].update(a['counts']);native_counts[mode].update(a['native_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes']);row['arms'][mode]=metrics
        summary.append(row)
    comparisons={k:dict(improved=sum(r['arms']['layered'][k]<r['arms']['fresh'][k] for r in summary),regressed=[r['name'] for r in summary if r['arms']['layered'][k]>r['arms']['fresh'][k]]) for k in ('solve_seconds','complete_seconds','record_bytes')}
    analysis=dict(events=53,changed=21,skipped=skipped,new_refuted_events=len(gains),new_roots=len(cases),remaining_events=len(remaining),coverage=dict(before=193,after=201,total=246),
        census_totals=census_totals,census_counts=census_counts,totals=totals,counts=counts,native_counts=native_counts,summary=summary,comparisons=comparisons,peak_rss_bytes=rss,
        remaining_new_failures=sum(len(r['third']['program']['probes']) for r in remaining if r['third']['action']=='searched'),
        remaining_with_new_failures=sum(bool(r['third']['program']['probes']) for r in remaining if r['third']['action']=='searched'),
        result_bytes=dict(remaining=(out/'remaining.json').stat().st_size,cases=sum(Path(b['path']).stat().st_size for b in cd['cases'])),
        unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,changed_closure_probes={k:old.binding(out/(k+'.json')) for k in ('protocol','cases','remaining','censuses','comparisons','analysis')})
    cp['changed_closure_probes']['supplemental_archives']=archives;base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(analysis),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','0c670980:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1927 tests in .*\n\nOK',full) and re.search(r'Ran 62 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['changed_closure_probes']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1927,focused_tests=62,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1072,final_sources=len(cp['source_fingerprints']),prior_manifests=187,prior_artifacts=25456,archive_audits=len(v['supplemental_archive_audits']),warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=188,next_artifacts=25456+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
