#!/usr/bin/env python3
"""Audit B12 sharing against frozen validation, source ledgers and both orders."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip, re, subprocess, sys, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shared_b12_preparation as study
from experiments.validate_cnf_b12_progress_order import independent
base=study.base; old=study.old; c=study.candidate
METRICS=('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes')
SEARCH=('probe_roots','probe_occurrence_visits','unit_probes','probe_index_literals','probe_index_builds','probe_initialization_clauses','probe_units','probe_queue_insertions','probe_open_closures','cursor_completed_probes','cursor_lifted_steps','cursor_promoted_probes','cursor_base_probes','cursor_interrupted_probes','b12_imported_completed','b12_imported_cursors','b12_hint_slots','b12_unseen_priority_literals','b12_deferred_literals')


def validate(out):
    start=time.perf_counter(); p=base.load(out/'protocol.json'); parent=old.bound(p['parent']); pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']); mp=Path(p['parent_manifest']['path']); old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts'])); artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items(): assert base.sha(f)==h,f; artifacts+=1
    assert (len(manifests),artifacts)==(210,30651)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_shared_b12_preparation.py':base.sha(__file__)}
    for f,h in sources.items(): assert base.sha(f)==h,f
    assert len(sources)==1175
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    assert Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    seeds={(r['target'],r['event']):r for r in study.prior.prior.load_frontier(p['seeds'])}; assert len(seeds)==14
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']}; assert pilot.keys()==seeds.keys()
    frontier={(r['target'],r['event']):r for r in study.prior.load_frontier(p['remaining'])}; assert frontier.keys()==seeds.keys()
    original={(key,order):old.bound(row['b12_'+order+'_result']) for key,row in frontier.items() for order in ('source','unseen')}
    samples=base.load(out/'censuses.json')['samples']; assert len(samples)==len(p['targets'])*12
    events={}; groups={}; totals={m:Counter() for m in study.MODES}; counts={m:Counter() for m in study.MODES}; vcounters={m:Counter() for m in study.MODES}; rss=Counter()
    for sample in samples:
        report=old.bound(sample); mode=sample['mode']; target=sample['target']; ordering,arm=mode.split('_',1)
        assert report['mode']==mode and report['target']==target
        groups.setdefault((target,mode),[]).append(report)
        rows=old.bound(report['events'])['rows']; assert {r['event'] for r in rows}=={e for t,e in seeds if t==target}
        for row in rows:
            key=row['target'],row['event']; result=old.bound(row['result']); seed=seeds[key]
            assert row['root']==seed['root'] and result==original[key,ordering] and row['record_bytes']==Path(row['result']['path']).stat().st_size
            args=study.prior.arguments(seed); kw=study.prior.options(seed); vc=Counter()
            checker=c if arm=='shared_both' else c.prior
            prepared=checker.validate(*args,**kw,ordering=ordering,result=result,counts=vc); assert dict(vc)==row['verification_counts']
            # Check all results through both frozen full validation and its
            # independent lower-bank/provenance reconstruction, outside timing.
            assert prepared==c.prior.validate(*args,**kw,ordering=ordering,result=result,counts=Counter())
            assert prepared==independent(args,kw,result,ordering)[0]
            events.setdefault((key,mode),[]).append((row,result))
    for (target,mode),(a,b) in groups.items():
        for k in ('counts','verification_counts','record_bytes'): assert a[k]==b[k]
        for k in METRICS: totals[mode][k]+=(a[k]+b[k])/2
        counts[mode].update(a['counts']); vcounters[mode].update(a['verification_counts']); rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    for target in p['targets']:
        source,ts,refs,original_events=study.inputs(p,target)
        for ref,seed in refs:
            key=target,ref['event']; rc=Counter(); _,_,state=study.bind(source,ts,ref,original_events[ref['event']],rc)
            assert list(map(list,state['local']))==seed['final_source'] and [h['template'] for h in state['hints']]==seed['templates']
            args=study.prior.arguments(seed); kw=study.prior.options(seed)
            for mode in study.MODES:
                ordering,arm=mode.split('_',1); (a,pa),(b,pb)=events[key,mode]; assert pa==pb
                for field in ('counts','verification_counts','reconstruction_counts'): assert a[field]==b[field]
                assert a['reconstruction_counts']==dict(rc)
                module=c.prior if arm=='separate' else c; cc=Counter(); actual=module.discover(*args,**kw,ordering=ordering,counts=cc,**p['limits'])
                assert actual==pa and dict(cc)==a['counts']
                pilot_arm=pilot[key]['arms'][ordering+('_separate' if arm=='separate' else '_shared')]
                assert actual==pilot_arm['result'] and dict(cc)==pilot_arm['counts']
                var=ordering+('_shared' if arm=='shared_both' else '_separate')
                assert a['verification_counts']==pilot[key]['arms'][var]['validation_counts']
                assert actual==original[key,ordering]
                baseline=ordering+'_separate'
                assert actual==events[key,baseline][0][1]
                for field in SEARCH: assert a['counts'].get(field,0)==events[key,baseline][0][0]['counts'].get(field,0),(key,mode,field)
    for ordering in ('source','unseen'):
        for arm in study.ARMS[1:]:
            mode=ordering+'_'+arm
            assert counts[mode]['shared_b12_prefix_preparations']==14 and counts[mode]['shared_b12_histories_checked']==42
            assert counts[mode]['shared_b10_histories_checked']==42
            assert counts[ordering+'_separate']['context_preparations']==2*counts[mode]['context_preparations']==28
        mode=ordering+'_shared_both'
        assert vcounters[mode]['shared_b12_prefix_preparations']==14 and vcounters[mode]['shared_b12_histories_checked']==42
        assert vcounters[ordering+'_separate']['context_preparations']==2*vcounters[mode]['context_preparations']==28
    comparisons={mode:{metric:dict(improved=sum(sum(row[metric] for row,_ in events[key,mode])/2<sum(row[metric] for row,_ in events[key,mode.split('_',1)[0]+'_separate'])/2 for key in seeds),
        regressed=[list(key) for key in seeds if sum(row[metric] for row,_ in events[key,mode])>sum(row[metric] for row,_ in events[key,mode.split('_',1)[0]+'_separate'])])
        for metric in ('discovery_seconds','verification_seconds','persistence_seconds','record_bytes')} for mode in study.MODES if not mode.endswith('_separate')}
    analysis=dict(events=14,coverage=dict(before=232,after=232,total=246),remaining_events=14,frontier_unchanged=True,totals=totals,counts=counts,verification_counts=vcounters,
        peak_rss_bytes=rss,comparisons=comparisons,search_counters={order:{k:counts[order+'_separate'][k] for k in SEARCH} for order in ('source','unseen')},
        open_export=dict(**p['remaining'],bytes=Path(p['remaining']['path']).stat().st_size,duplicated=False),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent); cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,shared_b12_preparation={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','analysis')})
    cp['shared_b12_preparation']['remaining']=p['remaining']; base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=[],parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,comparisons=comparisons,peak_rss_bytes=rss)))


def seal(out):
    v=base.load(out/'validation.json'); assert v['passed']; cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items(): assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'; before=subprocess.check_output(['git','show','a2f8aea5:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}'; proofs=re.findall(pat,before,re.S); assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text(); focus=(out/'focused-tests.log').read_text(); latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2127 tests in .*\n\nOK',full) and re.search(r'Ran 36 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['shared_b12_preparation']['decision']=old.binding(out/'decision.json'); base.write(out/'checkpoint.json',cp); v['checkpoint']=old.binding(out/'checkpoint.json'); base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2127,focused_tests=36,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1171,final_sources=len(cp['source_fingerprints']),prior_manifests=210,prior_artifacts=30651,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes(); Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0)); f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json'); base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=211,next_artifacts=30651+len(files))))


if __name__=='__main__': globals()[sys.argv[1]](Path(sys.argv[2]))
