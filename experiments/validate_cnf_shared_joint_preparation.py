#!/usr/bin/env python3
"""Audit common-prefix sharing against frozen full discovery and validation."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shared_joint_preparation as study
base=study.base;old=study.old;c=study.candidate
METRICS=('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes')
SEARCH=('probe_roots','probe_occurrence_visits','unit_probes','probe_index_literals','probe_index_builds','probe_initialization_clauses','probe_units','probe_queue_insertions','probe_open_closures','cursor_completed_probes','cursor_lifted_steps','cursor_promoted_probes','cursor_base_probes','cursor_interrupted_probes','joint_probe_imported_completed','joint_probe_imported_cursors')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(203,29141)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_shared_joint_preparation.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1146
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    assert Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    seeds={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']};assert len(seeds)==16
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert pilot.keys()==seeds.keys()
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*6
    events={};groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};vcounters={m:Counter() for m in study.MODES};rss=Counter()
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];target=sample['target'];groups.setdefault((target,mode),[]).append(report)
        rows=old.bound(report['events'])['rows'];assert {r['event'] for r in rows}=={e for t,e in seeds if t==target}
        for row in rows:
            key=row['target'],row['event'];result=old.bound(row['result']);seed=seeds[key]
            assert row['root']==seed['root'] and result==seed['joint_probe_cursor'] and row['record_bytes']==Path(row['result']['path']).stat().st_size
            args=tuple(seed[k] for k in study.FIELDS);cl=seed['joint_cursor_feedback_closure'];vc=Counter()
            checker=c if mode=='shared_both' else c.prior
            prepared=checker.validate(*args,closure=cl,result=result,counts=vc);assert dict(vc)==row['verification_counts']
            # Frozen full checker is mandatory even when measured checking used
            # shared preparation. Every bank and origin tuple must also agree.
            assert prepared==c.prior.validate(*args,closure=cl,result=result,counts=Counter())
            events.setdefault((key,mode),[]).append((row,result))
    for (target,mode),(a,b) in groups.items():
        for k in ('counts','verification_counts','record_bytes'):assert a[k]==b[k]
        for k in METRICS:totals[mode][k]+=(a[k]+b[k])/2
        counts[mode].update(a['counts']);vcounters[mode].update(a['verification_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    for target in p['targets']:
        source,ts,refs,original_events=study.inputs(p,target)
        for ref,seed in refs:
            key=target,ref['event'];rc=Counter();_,_,state=study.bind(source,ts,ref,original_events[ref['event']],rc)
            assert list(map(list,state['local']))==seed['final_source'] and [h['template'] for h in state['hints']]==seed['templates']
            args=tuple(seed[k] for k in study.FIELDS);cl=seed['joint_cursor_feedback_closure']
            for mode in study.MODES:
                (a,pa),(b,pb)=events[key,mode];assert pa==pb
                for field in ('counts','verification_counts','reconstruction_counts'):assert a[field]==b[field]
                assert a['reconstruction_counts']==dict(rc)
                module=c.prior if mode=='separate' else c;cc=Counter();actual=module.discover(*args,closure=cl,counts=cc,**p['limits'])
                assert actual==pa and dict(cc)==a['counts']
                arm=pilot[key]['arms']['separate' if mode=='separate' else 'shared']
                assert actual==arm['result'] and dict(cc)==arm['counts']
                var='shared' if mode=='shared_both' else 'separate'
                assert a['verification_counts']==pilot[key]['arms'][var]['validation_counts']
                assert actual['program']['status']=='unresolved'
            for mode in study.MODES[1:]:
                assert events[key,mode][0][1]==events[key,'separate'][0][1]
                for field in SEARCH:assert events[key,mode][0][0]['counts'].get(field,0)==events[key,'separate'][0][0]['counts'].get(field,0),(key,mode,field)
    for mode in study.MODES[1:]:
        assert counts[mode]['shared_joint_prefix_preparations']==16 and counts[mode]['shared_joint_histories_checked']==48
        assert counts['separate']['context_preparations']==2*counts[mode]['context_preparations']
    assert vcounters['shared_both']['shared_joint_prefix_preparations']==16 and vcounters['shared_both']['shared_joint_histories_checked']==48
    assert vcounters['separate']['context_preparations']==2*vcounters['shared_both']['context_preparations']
    comparisons={mode:{metric:dict(improved=sum(sum(row[metric] for row,_ in events[key,mode])/2<sum(row[metric] for row,_ in events[key,'separate'])/2 for key in seeds),
        regressed=[list(key) for key in seeds if sum(row[metric] for row,_ in events[key,mode])>sum(row[metric] for row,_ in events[key,'separate'])])
        for metric in ('discovery_seconds','verification_seconds','record_bytes')} for mode in study.MODES[1:]}
    analysis=dict(events=16,coverage=dict(before=230,after=230,total=246),remaining_events=16,frontier_unchanged=True,totals=totals,counts=counts,verification_counts=vcounters,
        peak_rss_bytes=rss,comparisons=comparisons,search_counters={k:counts['separate'][k] for k in SEARCH},
        open_export=dict(**p['seeds'],bytes=Path(p['seeds']['path']).stat().st_size,duplicated=False),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,shared_joint_preparation={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','analysis')})
    cp['shared_joint_preparation']['remaining']=p['seeds'];base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=[],parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,comparisons=comparisons,peak_rss_bytes=rss)))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','cc23c783:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2066 tests in .*\n\nOK',full) and re.search(r'Ran 55 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['shared_joint_preparation']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2066,focused_tests=55,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1142,final_sources=len(cp['source_fingerprints']),prior_manifests=203,prior_artifacts=29141,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=204,next_artifacts=29141+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
