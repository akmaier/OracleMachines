#!/usr/bin/env python3
"""Audit generic failed-literal saturation, native recomposition and old lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_saturation as s
from experiments.validate_cnf_layered_feedback import deterministic_result
from solver.test_cnf_b13_probe_cursor import independent
base=s.base;old=s.old;k=s.kernel
CENSUS=('preparation_seconds','discovery_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes')
NATIVE=('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(216,32729)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_probe_saturation.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1199
    for name in ('cnf_checked_probe_saturation.py','cnf_saturated_probe_native.py'):
        assert (out/('pilot-'+name)).read_bytes()==Path('experiments',name).read_bytes()
    assert (out/'initial-kernel.py').read_bytes()!=(out/'pilot-cnf_checked_probe_saturation.py').read_bytes()
    case=old.bound(p['case']);reconstructed=s.build_case()
    assert base.encode({key:v for key,v in reconstructed.items() if key!='reconstruction_seconds'})==base.encode({key:v for key,v in case.items() if key!='reconstruction_seconds'})
    prepared=independent(case['inputs'],case['options'],case['search'])
    entries=dict(zip(prepared[27],prepared[28]))
    for i,probe in enumerate(case['search']['program']['probes']):entries.setdefault((-probe['assumption'],),dict(kind='b13_probe',index=i))
    seed=tuple(sorted(entries));assert s.seed(case,Counter())==(*prepared,seed,[entries[cl] for cl in seed])
    assert (len(prepared[27]),len(seed))==(602,604)
    rows=s.parent.load_frontier(p['seeds']);assert len(rows)==13
    row=next(r for r in rows if (r['target'],r['event'])==(37,39))
    frames,tail=s.compiler.frozen.bind_prefix(case['source'],case['templates'],case['prefix'],Counter())
    assert list(map(list,tail['local']))==row['final_source'] and [h['template'] for h in tail['hints']]==row['templates']
    assert s.compiler.native.token(tuple(map(tuple,case['source'])),Counter())==row['root']==case['root']
    skipped=[]
    for row in rows:
        if (row['target'],row['event'])==(37,39):continue
        args=s.parent.prior.arguments(row,'strengthen');options=s.parent.prior.options(row,'strengthen');search=old.bound(row['b13_strength_result'])
        before=independent(args,options,search);after=s.parent.feedback.prepare(*args,search,**options,counts=Counter())
        assert row['b13_strength_state']=='unchanged_exhausted' and search['program']['reason']=='complete' and not search['program']['probes']
        assert before==after[:29] and before[27:29]==after[29:31]
        k.closure_check.check_closure(after[29],row['b13_strength_context_closure'],Counter())
        skipped.append([row['target'],row['event']])
    assert len(skipped)==12
    census_samples=base.load(out/'censuses.json')['samples'];assert len(census_samples)==18
    assert {(x['mode'],x['repeat']) for x in census_samples}=={(mode,i) for mode in s.MODES for i in range(6)}
    census_groups={};results={};ctotals={};ccounts={};crss={}
    for sample in census_samples:
        report=old.bound(sample);mode=sample['mode'];assert report['mode']==mode and report['case']==p['case']
        result=old.bound(report['result']);vc=Counter();cold=s.seed(case,vc);k.validate(cold[29],result,vc,order_source=cold[0])
        assert dict(vc)==report['verification_counts'] and report['record_bytes']==Path(report['result']['path']).stat().st_size
        if mode in results:assert result==results[mode]
        results[mode]=result;census_groups.setdefault(mode,[]).append(report)
    for mode,reports in census_groups.items():
        assert len(reports)==6
        for report in reports:
            for key in ('counts','verification_counts','record_bytes'):assert report[key]==reports[0][key],(mode,key)
        ctotals[mode]={key:sum(r[key] for r in reports)/6 for key in CENSUS};ccounts[mode]=reports[0]['counts'];crss[mode]=max(r['peak_rss_bytes'] for r in reports)
        cc=Counter();prepared=s.seed(case,cc);limits={**p['limits'],'round_limit':1 if mode=='once' else p['limits']['round_limit']}
        result=k.discover(prepared[29],cc,order_source=prepared[0],previous=old.bound(p['once']) if mode=='resume' else None,**limits)
        assert result==results[mode] and dict(cc)==reports[0]['counts']
    assert results['once']==old.bound(p['once']) and results['once']['reason']=='round_limit'
    full=results['saturate'];assert full==results['resume'] and (full['status'],full['reason'])==('refuted','units')
    assert full==base.load(out/'pilot-case.json')['saturation']
    failures=[[probe['assumption'] for probe in row['search']['program']['probes']] for row in full['rounds']]
    assert failures==[[44,142,-80,-60,50],[-62,5,-43,107,-74,84,132,88,108]]
    assert ccounts['saturate']['probe_roots']==530 and ccounts['resume']['probe_roots']==260
    assert ccounts['once']['probe_roots']==270
    native_samples=base.load(out/'comparisons.json')['samples'];assert len(native_samples)==4
    assert {(x['mode'],x['repeat']) for x in native_samples}=={(mode,i) for mode in s.NATIVE_MODES for i in range(2)}
    ngroups={};audits={};archives=[]
    # Pilot archives are also independently replayed, but excluded from timings.
    reports=[old.bound(sample) for sample in native_samples]+[base.load(out/f'pilot-native-{mode}/report.json') for mode in s.NATIVE_MODES]
    for i,report in enumerate(reports):
        mode=report['mode'];assert report['result']['status']=='unsat' and report['result']['result']['root']==case['root']
        if i<4:assert report['case']==p['case'];ngroups.setdefault(mode,[]).append(report)
        archive=report['archive'];assert base.sha(archive['path'])==archive['sha256'];key=archive['sha256'],case['root']
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';s.previous.restore_archive(archive,db)
                tables,readers=s.previous.audit(db,[dict(source=case['source'])],[report['result']])
            assert {t:len(v) for t,v in tables.items()}==report['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}==report['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items())==report['record_bytes']
            assert all(not records for table,records in tables.items() if table!='cnf_residual_v1')
            audits[key]=dict(archive=archive,root=case['root'],status='unsat',readers=readers);archives.append(archive)
    ntotals={};ncounts={};nrss={};records={};archive_bytes={}
    for mode,reports in ngroups.items():
        assert len(reports)==2
        for report in reports:
            assert deterministic_result(report['result'])==deterministic_result(reports[0]['result'])
            for key in ('counts','warm_counts','native_counts','digest','record_bytes','authority_tables'):assert report[key]==reports[0][key],(mode,key)
        ntotals[mode]={key:sum(r[key] for r in reports)/2 for key in NATIVE};ncounts[mode]=reports[0]['counts'];nrss[mode]=max(r['peak_rss_bytes'] for r in reports)
        records[mode]=sum(reports[0]['authority_tables'].values());archive_bytes[mode]=Path(reports[0]['archive']['path']).stat().st_size
        if mode=='direct':assert reports[0]['warm_counts']['saturation_native_extension_hits']==1
    for stage in (0,1):assert ncounts['direct'][f'saturation_native_expanded_saturation_probe_{stage}']>0
    assert sum(ncounts['direct'].get(key,0) for key in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=262144
    selected=ngroups['fresh'][0]['archive']
    s.compact(out/'remaining-overlay.json',dict(parent=p['seeds'],excluded=[[37,39]],certified_root=case['root'],native_archive=selected))
    binding=old.binding(out/'remaining-overlay.json');remaining=s.load_frontier(binding)
    assert remaining==[row for row in rows if (row['target'],row['event'])!=(37,39)] and len(remaining)==12
    analysis=dict(coverage=dict(before=233,after=234,total=246),gained_events=[[37,39]],remaining_events=12,skipped_identical_exhausted=skipped,
        seed_clauses=len(seed),productive_rounds=len(full['rounds']),failed_assumptions=failures,prefix_steps=len(frames),final_proof_steps=len(full['proof']['units']),
        census_totals=ctotals,census_counts=ccounts,census_peak_rss_bytes=crss,
        resume_percent_change={key:100*(ctotals['resume'][key]/ctotals['saturate'][key]-1) for key in CENSUS},
        acquire_then_resume_totals={key:ctotals['once'][key]+ctotals['resume'][key] for key in CENSUS},
        native_totals=ntotals,native_counts=ncounts,native_peak_rss_bytes=nrss,native_records=records,compressed_archive_bytes=archive_bytes,
        direct_over_fresh={key:ntotals['direct'][key]/ntotals['fresh'][key] for key in NATIVE},unique_archive_audits=len(audits),
        reconstruction_seconds=case['reconstruction_seconds'],reconstruction_counts=case['reconstruction_counts'],
        storage=dict(case_bytes=Path(p['case']['path']).stat().st_size,once_bytes=Path(p['once']['path']).stat().st_size,
        overlay_bytes=Path(binding['path']).stat().st_size,selected_archive_bytes=Path(selected['path']).stat().st_size),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        probe_saturation={key:old.binding(out/(key+'.json')) for key in ('protocol','case','once','censuses','comparisons','analysis')})
    cp['probe_saturation'].update(remaining=binding,supplemental_archives=archives);base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(coverage=analysis['coverage'],census=ctotals,native=ntotals,records=records,archive_audits=len(audits))))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','5f49a1ee:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2175 tests in .*\n\nOK',full) and re.search(r'Ran 21 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['probe_saturation']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2175,focused_tests=21,proof_blocks_unchanged=64,
        manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1194,final_sources=len(cp['source_fingerprints']),
        prior_manifests=216,prior_artifacts=32729,new_native_archives=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=217,next_artifacts=32729+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
