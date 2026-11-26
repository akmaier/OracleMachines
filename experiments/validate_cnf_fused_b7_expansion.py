#!/usr/bin/env python3
"""Audit single-preparation expansion and unchanged portable B7 results."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_fused_b7_expansion as study
base=study.base;old=study.old;c=study.c
METRICS=('reconstruction_seconds','expansion_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(200,28380)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_fused_b7_expansion.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    assert Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    # Preserve a test-fixture correction without changing measured code/inputs.
    if 'test_fixture_correction' in p:
        correction=p['test_fixture_correction']
        for path,h in correction['artifacts'].items():assert base.sha(path)==h,path
        initial=base.load(out/'initial-protocol.json');test=study.FILES[2]
        assert initial['source_fingerprints'][test]==base.sha(out/'initial-test-fixture.py')
        initial['source_fingerprints'][test]=p['source_fingerprints'][test]
        assert initial=={k:v for k,v in p.items() if k!='test_fixture_correction'}
        assert 'Not an open unit fixed point' in (out/'fixture-failure.log').read_text()
    seeds={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']};assert len(seeds)==18
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert seeds.keys()==pilot.keys()
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*6
    groups={};events={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};rss=Counter()
    for sample in samples:
        report=old.bound(sample);groups.setdefault((sample['target'],sample['mode']),[]).append(report)
        rows=old.bound(report['events'])['rows'];assert {r['event'] for r in rows}=={e for t,e in seeds if t==sample['target']}
        for row in rows:
            key=(row['target'],row['event']);payload=old.bound(row['result']);mode=sample['mode'];expected=pilot[key]['arms'][mode]
            assert row['root']==seeds[key]['root'] and payload==expected['payload'] and row['counts']==expected['counts']
            assert payload==dict(closure=seeds[key]['b6_cursor_feedback_closure'],result=seeds[key]['b7_probe_cursor'])
            assert row['record_bytes']==Path(row['result']['path']).stat().st_size
            vc=Counter();args=tuple(seeds[key][k] for k in study.FIELDS);study.check(args,payload,vc);assert dict(vc)==row['verification_counts']
            events.setdefault((key,mode),[]).append((row,payload))
    for (target,mode),(a,b) in groups.items():
        for field in ('counts','record_bytes'):assert a[field]==b[field]
        for field in METRICS:totals[mode][field]+=(a[field]+b[field])/2
        counts[mode].update(a['counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    summary=[];noops=[]
    for key,seed in seeds.items():
        args=tuple(seed[k] for k in study.FIELDS);row=dict(target=key[0],event=key[1],arms={});results={}
        for mode in study.MODES:
            (a,pa),(b,pb)=events[key,mode];assert pa==pb
            for field in ('counts','verification_counts','reconstruction_counts'):assert a[field]==b[field]
            rc=Counter();actual=study.run(args,mode,rc);assert actual==pa and dict(rc)==a['counts']
            row['arms'][mode]={k:(a[k]+b[k])/2 for k in METRICS if k!='complete_seconds'};results[mode]=actual
        assert all(r==results['split'] for r in results.values());summary.append(row)
        cc=events[key,'fused'][0][0]['counts']
        if cc.get('expansion_empty_layers_reused',0):
            assert not seed['b6_checked_restore_cursor']['program']['probes']
            assert results['fused']['closure']==seed['b5_cursor_feedback_closure']
            noops.append(dict(target=key[0],event=key[1]))
        assert results['fused']['result']['program']['status']=='unresolved'
    assert len(noops)==11 and counts['fused']['expansion_rebuilt_layers']==7
    for mode in study.MODES:
        assert counts[mode]['probe_roots']==546 and counts[mode]['probe_initialization_clauses']==217940 and counts[mode]['probe_occurrence_visits']==23500
    assert counts['fused']['expansion_checked_schedule_handoffs']==counts['fused_rebuild']['expansion_checked_schedule_handoffs']==11
    comparisons={control:{k:dict(improved=sum(r['arms']['fused'][k]<r['arms'][control][k] for r in summary),regressed=[(r['target'],r['event']) for r in summary if r['arms']['fused'][k]>r['arms'][control][k]]) for k in ('expansion_seconds','verification_seconds','record_bytes')} for control in ('split','fused_rebuild')}
    analysis=dict(events=18,coverage=dict(before=228,after=228,total=246),remaining_events=18,totals=totals,counts=counts,peak_rss_bytes=rss,summary=summary,comparisons=comparisons,
        empty_layers_reused=noops,remaining=p['seeds'],remaining_bytes=Path(p['seeds']['path']).stat().st_size,retained_b6_failures=30,retained_b7_failures=15,
        sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,fused_b7_expansion={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','analysis')})
    cp['fused_b7_expansion']['remaining']=p['seeds'];base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,new_native_archives=0,
        remaining_unchanged=p['seeds'],seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,noops=noops,remaining_bytes=analysis['remaining_bytes'])),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','55cc1b10:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2039 tests in .*\n\nOK',full) and re.search(r'Ran 174 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['fused_b7_expansion']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2039,focused_tests=174,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1129,final_sources=len(cp['source_fingerprints']),prior_manifests=200,prior_artifacts=28380,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=201,next_artifacts=28380+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
