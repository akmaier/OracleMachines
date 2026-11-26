#!/usr/bin/env python3
"""Audit B7 composition, matched fresh/reused frontiers, and complete lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b7_probe_cursor as study
base=study.base;old=study.old;c=study.c
METRICS=('reconstruction_seconds','composition_seconds','discovery_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(199,28081)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b7_probe_cursor.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    assert Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[1]).read_bytes()
    seeds={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']};assert len(seeds)==18
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert seeds.keys()==pilot.keys()
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*8
    groups={};events={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};composition_counts={m:Counter() for m in study.MODES};rss=Counter()
    for sample in samples:
        report=old.bound(sample);groups.setdefault((sample['target'],sample['mode']),[]).append(report)
        rows=old.bound(report['events'])['rows'];assert {r['event'] for r in rows}=={e for t,e in seeds if t==sample['target']}
        for row in rows:
            key=(row['target'],row['event']);payload=old.bound(row['result']);mode=sample['mode'];expected=pilot[key]['arms'][mode]
            assert row['root']==seeds[key]['root'] and payload['result']==expected['result'] and row['counts']==expected['counts']
            assert payload['closure']==(None if mode=='base' else pilot[key]['closure'])
            assert row['composition_counts']==({} if mode=='base' else pilot[key]['composition_counts'])
            assert row['record_bytes']==Path(row['result']['path']).stat().st_size
            vc=Counter();args=tuple(seeds[key][k] for k in study.FIELDS);study.check(args,payload['closure'],payload['result'],mode,vc)
            assert dict(vc)==row['verification_counts'];events.setdefault((key,mode),[]).append((row,payload))
    for (target,mode),(a,b) in groups.items():
        for field in ('counts','composition_counts','record_bytes'):assert a[field]==b[field]
        for field in METRICS:totals[mode][field]+=(a[field]+b[field])/2
        counts[mode].update(a['counts']);composition_counts[mode].update(a['composition_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    remaining=[];summary=[];changed=[];imported=[];failed=[];base_failed=[];exhausted=[];base_exhausted=[];prior_failures=0
    for key,seed in seeds.items():
        args=tuple(seed[k] for k in study.FIELDS);dc=Counter();closure=study.compose(args,dc)
        assert closure==pilot[key]['closure'] and dict(dc)==pilot[key]['composition_counts']
        oldfixed=dict(args[-2]['assignment']);fixed=dict(closure['assignment']);assert oldfixed.items()<=fixed.items()
        added=sorted(fixed.keys()-oldfixed.keys());assert added==pilot[key]['additional_variables']
        if added:changed.append(dict(target=key[0],event=key[1],additional_variables=added))
        row=dict(target=key[0],event=key[1],arms={});results={}
        for mode in study.MODES:
            (a,pa),(b,pb)=events[key,mode];assert pa==pb
            for field in ('counts','composition_counts','verification_counts','reconstruction_counts'):assert a[field]==b[field]
            rc=Counter();result=study.search(args,closure,mode,rc);assert result==pa['result'] and dict(rc)==a['counts']
            assert result['program']['status']=='unresolved' and result['program']['reason'] in ('complete','probe_limit')
            row['arms'][mode]={k:(a[k]+b[k])/2 for k in METRICS if k!='complete_seconds'};results[mode]=result
        assert results['matched']==results['reuse']
        if events[key,'reuse'][0][0]['counts'].get('b7_imported_cursors',0):
            assert not added and not args[-1]['program']['probes']
            assert results['reuse']['cursor']['completed'][:len(args[-1]['cursor']['completed'])]==args[-1]['cursor']['completed']
            imported.append(dict(target=key[0],event=key[1],completed=len(args[-1]['cursor']['completed'])))
        else:assert results['reuse']==results['restart']
        assert results['base']['cursor']['completed'][:len(args[-1]['cursor']['completed'])]==args[-1]['cursor']['completed']
        prior_failures+=len(args[-1]['program']['probes'])
        for mode,dest,ends in (('reuse',failed,exhausted),('base',base_failed,base_exhausted)):
            result=results[mode]
            if result['program']['probes']:dest.append(dict(target=key[0],event=key[1],failures=len(result['program']['probes'])))
            if result['program']['reason']=='complete':ends.append(dict(target=key[0],event=key[1],completed=len(result['cursor']['completed'])))
        remaining.append(dict(seed,b6_cursor_feedback_closure=closure,b6_cursor_feedback_added_variables=added,b6_comparison_cursor=results['base'],b7_probe_cursor=results['reuse']));summary.append(row)
    assert prior_failures==25 and len(changed)==7 and sum(len(x['additional_variables']) for x in changed)==26
    assert len(imported)==11 and sum(r['failures'] for r in failed)==15 and len(failed)==5
    assert sum(r['failures'] for r in base_failed)==30 and len(base_failed)==8
    assert len(exhausted)==10 and len(base_exhausted)==16
    assert counts['reuse']['probe_roots']+counts['reuse']['b7_imported_completed']==counts['matched']['probe_roots']
    study.compact(out/'remaining.json',dict(rows=remaining))
    comparisons={control:{k:dict(improved=sum(r['arms']['reuse'][k]<r['arms'][control][k] for r in summary),regressed=[(r['target'],r['event']) for r in summary if r['arms']['reuse'][k]>r['arms'][control][k]]) for k in ('composition_seconds','discovery_seconds','verification_seconds','record_bytes')} for control in ('base','restart','matched')}
    analysis=dict(events=18,coverage=dict(before=228,after=228,total=246),remaining_events=18,totals=totals,counts=counts,composition_counts=composition_counts,peak_rss_bytes=rss,summary=summary,comparisons=comparisons,
        prior_failures=prior_failures,changed_closures=changed,imported_histories=imported,retained_b7_failures=failed,base_b6_failures=base_failed,b7_exhausted_orders=exhausted,base_b6_exhausted_orders=base_exhausted,
        result_bytes=dict(previous=Path(p['seeds']['path']).stat().st_size,remaining=(out/'remaining.json').stat().st_size),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,b7_probe_cursor={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','remaining','censuses','analysis')});base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,new_native_archives=0,
        seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,imported=imported,b7_failures=failed,b6_failures=base_failed)),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','12348a36:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2030 tests in .*\n\nOK',full) and re.search(r'Ran 165 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b7_probe_cursor']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2030,focused_tests=165,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1124,final_sources=len(cp['source_fingerprints']),prior_manifests=199,prior_artifacts=28081,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=200,next_artifacts=28081+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
