#!/usr/bin/env python3
"""Audit local-context reconstruction, matched search and synthetic regressions."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_prepared_prefix_replay as study
base=study.base;old=study.old;c=study.candidate
METRICS=('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(204,29327)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_prepared_prefix_replay.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1150
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    assert Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    for f,h in p['test_fixture_correction'].items():assert base.sha(f)==h,f
    before=(out/'initial-tests.py').read_text();after=Path(study.FILES[2]).read_text()
    assert before.replace('source=c.native.normalize([[1,2],[1,-2],[3,4,5]])[0]','source=c.native.normalize([[1,2],[1,-2],[-1,3,4]])[0]')==after
    initial=base.load(out/'initial-protocol.json')
    assert all(initial['source_fingerprints'][f]==h for f,h in p['source_fingerprints'].items() if f!=study.FILES[2])
    seeds={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']};assert len(seeds)==16
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert pilot.keys()==seeds.keys()
    profile=old.bound(p['profile']);assert len(profile['rows'])==16 and all(r['prefix_steps']==0 for r in profile['rows'])
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*4
    events={};groups={};totals={m:Counter() for m in study.MODES};rcs={m:Counter() for m in study.MODES};ccs={m:Counter() for m in study.MODES};vcs={m:Counter() for m in study.MODES};rss=Counter()
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];target=sample['target'];groups.setdefault((target,mode),[]).append(report)
        rows=old.bound(report['events'])['rows'];assert {r['event'] for r in rows}=={e for t,e in seeds if t==target}
        for row in rows:
            key=row['target'],row['event'];result=old.bound(row['result']);seed=seeds[key]
            assert row['root']==seed['root'] and result==seed['joint_probe_cursor'] and row['record_bytes']==Path(row['result']['path']).stat().st_size
            args=tuple(seed[k] for k in study.FIELDS);cl=seed['joint_cursor_feedback_closure'];vc=Counter()
            prepared=study.search.validate(*args,closure=cl,result=result,counts=vc);assert dict(vc)==row['verification_counts']
            assert prepared==study.search.prior.validate(*args,closure=cl,result=result,counts=Counter())
            events.setdefault((key,mode),[]).append((row,result))
    for (target,mode),(a,b) in groups.items():
        for k in ('counts','reconstruction_counts','verification_counts','record_bytes'):assert a[k]==b[k]
        for k in METRICS:totals[mode][k]+=(a[k]+b[k])/2
        rcs[mode].update(a['reconstruction_counts']);ccs[mode].update(a['counts']);vcs[mode].update(a['verification_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    for target in p['targets']:
        source,ts,refs,original_events=study.inputs(p,target)
        for ref,seed in refs:
            key=target,ref['event'];args=tuple(seed[k] for k in study.FIELDS);cl=seed['joint_cursor_feedback_closure'];assert not ref['program']['steps']
            rc=Counter();expected=study.prior.bind(source,ts,ref,original_events[ref['event']],rc)
            assert base.encode(expected)==base.encode(pilot[key]['arms']['frozen']['bound']) and dict(rc)==pilot[key]['arms']['frozen']['counts']
            for mode in study.MODES:
                (a,pa),(b,pb)=events[key,mode];assert pa==pb
                for field in ('counts','verification_counts','reconstruction_counts'):assert a[field]==b[field]
                fn=study.prior.bind if mode=='frozen' else c.bind;cc=Counter();bound=fn(source,ts,ref,original_events[ref['event']],cc)
                assert bound==expected and dict(cc)==a['reconstruction_counts']==pilot[key]['arms'][mode]['counts']
                assert list(map(list,bound[2]['local']))==seed['final_source'] and [h['template'] for h in bound[2]['hints']]==seed['templates']
                search_counts=Counter();actual=study.search.discover(*args,closure=cl,counts=search_counts,**p['limits'])
                assert actual==pa and dict(search_counts)==a['counts']
            assert events[key,'context'][0][1]==events[key,'frozen'][0][1]
    assert ccs['context']==ccs['frozen'] and vcs['context']==vcs['frozen']
    for key in ('verified_core_hints','hint_check_literals','template_candidates','local_containment_clauses','trace_transport_steps'):assert rcs['context'][key]==rcs['frozen'][key],key
    assert rcs['context']['replay_local_contexts']==16 and rcs['context']['normalization_literal_visits']<rcs['frozen']['normalization_literal_visits']
    fixtures=old.bound(p['synthetic_cases'])['rows'];assert base.encode(fixtures)==base.encode(study.synthetic_cases())
    samples=base.load(out/'synthetic.json')['samples'];assert len(samples)==4;sgroups={};synthetic_rss=Counter()
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];rows=old.bound(report['results'])['rows'];assert {r['name'] for r in rows}=={r['name'] for r in fixtures}
        synthetic_rss[mode]=max(synthetic_rss[mode],report['peak_rss_bytes'])
        for row in rows:sgroups.setdefault((row['name'],mode),[]).append(row)
    synthetic=[]
    for fixture in fixtures:
        summary=dict(name=fixture['name'],kind=fixture['kind'],arms={})
        expected=c.frozen.local_hints(fixture['source'],fixture['templates'],fixture['event'],Counter())
        for mode in study.MODES:
            a,b=sgroups[fixture['name'],mode];assert a['result']==b['result'] and a['counts']==b['counts']
            fn=c.frozen.local_hints if mode=='frozen' else c.local_hints;cc=Counter()
            for _ in range(p['synthetic_repeats']):actual=fn(fixture['source'],fixture['templates'],fixture['event'],cc)
            assert actual==expected and base.encode(actual)==base.encode(a['result']) and dict(cc)==a['counts']
            for hint in actual[1]:c.frozen.check_rup(actual[0],hint['clause'],hint['proof'],Counter())
            summary['arms'][mode]=dict(seconds=(a['seconds']+b['seconds'])/2,counts=a['counts'],accepted_hints=len(actual[1]))
        summary['context_faster']=summary['arms']['context']['seconds']<summary['arms']['frozen']['seconds'];synthetic.append(summary)
    comparisons={metric:dict(improved=sum(sum(row[metric] for row,_ in events[key,'context'])<sum(row[metric] for row,_ in events[key,'frozen']) for key in seeds),
        regressed=[list(key) for key in seeds if sum(row[metric] for row,_ in events[key,'context'])>sum(row[metric] for row,_ in events[key,'frozen'])]) for metric in ('reconstruction_seconds','discovery_seconds','verification_seconds','record_bytes')}
    analysis=dict(events=16,coverage=dict(before=230,after=230,total=246),frontier_unchanged=True,remaining_events=16,totals=totals,reconstruction_counts=rcs,counts=ccs,verification_counts=vcs,
        peak_rss_bytes=rss,comparisons=comparisons,profile=p['profile'],synthetic=synthetic,synthetic_peak_rss_bytes=synthetic_rss,
        open_export=dict(**p['seeds'],bytes=Path(p['seeds']['path']).stat().st_size,duplicated=False),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,prepared_prefix_replay={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','synthetic','analysis')})
    cp['prepared_prefix_replay']['remaining']=p['seeds'];base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=[],parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,comparisons=comparisons,peak_rss_bytes=rss,synthetic_regressions=[r['name'] for r in synthetic if not r['context_faster']])))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','3cd85b38:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2075 tests in .*\n\nOK',full) and re.search(r'Ran 64 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['prepared_prefix_replay']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2075,focused_tests=64,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1146,final_sources=len(cp['source_fingerprints']),prior_manifests=204,prior_artifacts=29327,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=205,next_artifacts=29327+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
