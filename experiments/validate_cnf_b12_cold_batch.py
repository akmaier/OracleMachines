#!/usr/bin/env python3
"""Audit independently cold-checked batches against every preserved B12 snapshot."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b12_cold_batch as study
from experiments.validate_cnf_b12_progress_order import independent
base=study.base;old=study.old;c=study.candidate
METRICS=('reconstruction_seconds','discovery_seconds','verification_seconds','persistence_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(213,32048)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b12_cold_batch.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1187 and Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    seeds={(r['target'],r['event']):r for r in study.prior.load_frontier(p['seeds'])};assert len(seeds)==14
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert pilot.keys()==seeds.keys()
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*16
    events={};groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};vcounters={m:Counter() for m in study.MODES};rss=Counter()
    assert {(s['target'],s['mode'],s['repeat']) for s in samples}=={(t,m,r) for t in p['targets'] for m in study.MODES for r in range(4)}
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];target=sample['target'];assert report['mode']==mode and report['target']==target
        groups.setdefault((target,mode),[]).append(report);rows=old.bound(report['events'])['rows'];assert {r['event'] for r in rows}=={e for t,e in seeds if t==target}
        for row in rows:
            key=target,row['event'];results=[old.bound(b) for b in row['results']];seed=seeds[key];vc=Counter()
            assert row['root']==seed['root'] and row['record_bytes']==sum(Path(b['path']).stat().st_size for b in row['results'])
            study.check(study.arguments(seed),seed,mode,results,vc);assert dict(vc)==row['verification_counts']
            events.setdefault((key,mode),[]).append((row,results))
        for field in ('counts','reconstruction_counts','verification_counts'):
            assert report[field]==dict(sum((Counter(row[field]) for row in rows),Counter()))
        for metric in METRICS:
            if metric!='complete_seconds':assert abs(report[metric]-sum(r[metric] for r in rows))<1e-9
    for (target,mode),reports in groups.items():
        assert len(reports)==4
        for r in reports:
            for k in ('counts','reconstruction_counts','verification_counts','record_bytes'):assert r[k]==reports[0][k]
            for k in METRICS:totals[mode][k]+=r[k]/4
            rss[mode]=max(rss[mode],r['peak_rss_bytes'])
        counts[mode].update(reports[0]['counts']);vcounters[mode].update(reports[0]['verification_counts'])
    snapshots_checked=0
    for target in p['targets']:
        source,ts,refs,original_events=study.inputs(p,target)
        for ref,seed in refs:
            key=target,ref['event'];args=study.arguments(seed);kw=study.options(seed);rc=Counter()
            _,_,state=study.bind(source,ts,ref,original_events[ref['event']],rc)
            assert list(map(list,state['local']))==seed['final_source'] and [h['template'] for h in state['hints']]==seed['templates']
            for mode in study.MODES:
                ordering,arm=mode.split('_',1);case_samples=events[key,mode];row,results=case_samples[0]
                for other,books in case_samples:
                    assert books==results
                    for field in ('counts','verification_counts','reconstruction_counts'):assert other[field]==row[field]
                assert row['reconstruction_counts']==dict(rc)
                cc=Counter();actual=study.search(args,seed,mode,cc,p['limits']);assert actual==results and dict(cc)==row['counts']
                assert row['verification_counts']==pilot[key]['arms'][mode]['counts']
                preserved=[old.bound(b) for b in seed['b12_batch_'+ordering+'_rounds']]
                assert results==preserved and results[-1]['program']['reason']=='complete'
                assert all(r['program']['status']=='unresolved' for r in results)
                assert len(results)==(3 if key in ((37,39),(67,63)) else 1)
                batch_prepared=study.check(args,seed,mode,results,Counter())
                for r in results:
                    prepared=independent(args,kw,r,ordering)[0]
                    assert prepared==batch_prepared==c.prior.prior.validate(*args,**kw,ordering=ordering,result=r,counts=Counter())
                    snapshots_checked+=1
                baseline=events[key,ordering+'_separate'][0]
                assert results==baseline[1] and row['counts']==baseline[0]['counts']
                assert row['verification_counts']['context_preparations']==(1 if arm=='batch' else len(results))
                if arm=='batch':assert row['verification_counts']['cold_batch_snapshots_checked']==len(results)
    assert snapshots_checked==72
    for ordering in ('source','unseen'):
        batch=ordering+'_batch';sep=ordering+'_separate'
        assert counts[batch]==counts[sep] and counts[batch]['context_preparations']==14 and counts[batch]['batch_rounds']==18
        assert vcounters[batch]['context_preparations']==14 and vcounters[sep]['context_preparations']==18
        assert vcounters[batch]['cold_batch_prefix_preparations']==14 and vcounters[batch]['cold_batch_snapshots_checked']==18
    comparisons={order:{metric:dict(improved=sum(sum(r[metric] for r,_ in events[key,order+'_batch'])<sum(r[metric] for r,_ in events[key,order+'_separate']) for key in seeds),regressed=[list(key) for key in seeds if sum(r[metric] for r,_ in events[key,order+'_batch'])>sum(r[metric] for r,_ in events[key,order+'_separate'])]) for metric in METRICS if metric!='complete_seconds'} for order in ('source','unseen')}
    productive={mode:{metric:sum(sum(r[metric] for r,_ in events[key,mode])/4 for key in ((37,39),(67,63))) for metric in METRICS if metric!='complete_seconds'} for mode in study.MODES}
    binding=p['seeds'];deps=set();current=binding
    while True:
        payload=old.bound(current)
        if current!=binding:deps.add(current['path'])
        for row in payload['rows']:
            for value in row.values():
                values=value if isinstance(value,list) else [value]
                for item in values:
                    if isinstance(item,dict) and 'path' in item and 'sha256' in item:old.bound(item);deps.add(item['path'])
        if 'parent' not in payload:break
        current=payload['parent']
    analysis=dict(events=14,coverage=dict(before=232,after=232,total=246),remaining_events=14,new_failures=[],new_assignments=[],new_native_records=0,
        independently_rechecked_snapshots=snapshots_checked,census_totals=totals,census_counts=counts,verification_counts=vcounters,
        peak_rss_bytes=rss,comparisons=comparisons,productive_case_stage_totals=productive,remaining_unchanged=True,
        storage=dict(overlay_bytes=Path(binding['path']).stat().st_size,referenced_files=len(deps),referenced_bytes=sum(Path(f).stat().st_size for f in deps)),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,b12_cold_batch={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','analysis')});cp['b12_cold_batch']['remaining']=binding;base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=[],parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,storage=analysis['storage'],snapshots_checked=snapshots_checked)))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','f28420e5:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2154 tests in .*\n\nOK',full) and re.search(r'Ran 36 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b12_cold_batch']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2154,focused_tests=36,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1183,final_sources=len(cp['source_fingerprints']),prior_manifests=213,prior_artifacts=32048,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=214,next_artifacts=32048+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
