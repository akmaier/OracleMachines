#!/usr/bin/env python3
"""Audit B4 frontier persistence, failure proofs and preserved lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b4_probe_cursor as study
base=study.base;old=study.old


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(192,26679)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b4_probe_cursor.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert Path(p['pilot_source']['path']).read_bytes()==Path('experiments/cnf_b4_probe_cursor.py').read_bytes()
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    saved={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']}
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert saved.keys()==pilot.keys() and len(saved)==29
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*4
    groups={};event_groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};rss=Counter()
    for s in samples:
        r=old.bound(s);assert (r['target'],r['mode'])==(s['target'],s['mode']);groups.setdefault((s['target'],s['mode']),[]).append(r)
        rows=old.bound(r['events'])['rows']
        assert {x['event'] for x in rows}=={e for t,e in saved if t==s['target']}
        for x in rows:
            key=(x['target'],x['event']);result=old.bound(x['result']);seed=saved[key]
            assert x['root']==seed['root'] and result==pilot[key]['arms'][s['mode']]['result']
            assert x['counts']==pilot[key]['arms'][s['mode']]['counts']
            vc=Counter();study.candidate.validate(*(seed[k] for k in study.FIELDS),result,vc);assert dict(vc)==x['verification_counts']
            assert x['record_bytes']==Path(x['result']['path']).stat().st_size
            assert x['counts'].get('probe_occurrence_visits',0)<=p['limits']['work_limit']
            assert x['counts'].get('probe_roots',0)<=p['limits']['probe_limit']
            if result['action']=='searched':assert result['program']['status']=='unresolved'
            event_groups.setdefault((key,s['mode']),[]).append((x,result))
    regressions=[]
    for (target,mode),(a,b) in groups.items():
        for k in ('counts','record_bytes'):assert a[k]==b[k]
        for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes'):totals[mode][k]+=(a[k]+b[k])/2
        counts[mode].update(a['counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    remaining=[];selected=[];failures=0;failed_cases=[];skips=[];reasons=Counter();summary=[]
    for key,seed in saved.items():
        row=dict(target=key[0],event=key[1],arms={});results={}
        for mode in study.MODES:
            (a,ra),(b,rb)=event_groups[key,mode];assert ra==rb and a['counts']==b['counts'] and a['reconstruction_counts']==b['reconstruction_counts']
            results[mode]=ra;row['arms'][mode]={k:(a[k]+b[k])/2 for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','record_bytes')}
        probes=results['all']['program']['probes'];failures+=len(probes);reasons[results['all']['program']['reason']]+=1
        if probes:failed_cases.append(dict(target=key[0],event=key[1],failures=len(probes)))
        if results['changed']['action']=='unchanged':assert not probes;skips.append(key)
        else:assert results['changed']==results['all']
        if row['arms']['changed']['discovery_seconds']>row['arms']['all']['discovery_seconds']:regressions.append(key)
        # Preserve the measured control's complete history even for skipped cases.
        # Its acquisition costs belong to all, not to the changed-only policy.
        remaining.append(dict(seed,b4_probe_cursor=results['all']))
        selected.append(dict(target=key[0],event=key[1],result=results['changed']))
        summary.append(row)
    assert failures==69 and len(failed_cases)==13 and len(skips)==10
    assert counts['all']['probe_roots']==1856 and counts['changed']['probe_roots']==1216
    study.compact(out/'remaining.json',dict(rows=remaining));study.compact(out/'selected-cursors.json',dict(rows=selected))
    analysis=dict(events=29,new_refutations=0,recognized_events=217,total_events=246,remaining_events=29,failed_proofs=failures,failed_cases=failed_cases,
        skips=skips,reasons=reasons,totals=totals,counts=counts,peak_rss_bytes=rss,discovery_regressions=regressions,summary=summary,
        inherited_export_bytes=Path(p['seeds']['path']).stat().st_size,remaining_export_bytes=(out/'remaining.json').stat().st_size,
        selected_export_bytes=(out/'selected-cursors.json').stat().st_size,limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        b4_probe_cursor={k:old.binding(out/(k+'.json')) for k in ('protocol','censuses','analysis','remaining','selected-cursors')});base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=[],checked_cursor_results=len(samples)//len(p['targets'])*len(saved),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,failures=failures,failed_cases=len(failed_cases),skips=len(skips),reasons=reasons,rss=rss)),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','767057a7:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1969 tests in .*\n\nOK',full) and re.search(r'Ran 104 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b4_probe_cursor']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1969,focused_tests=104,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1094,final_sources=len(cp['source_fingerprints']),prior_manifests=192,prior_artifacts=26679,new_archive_audits=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=193,next_artifacts=26679+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
