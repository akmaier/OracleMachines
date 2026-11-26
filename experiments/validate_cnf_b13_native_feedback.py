#!/usr/bin/env python3
"""Independently audit source-only B13 certificates and preserved lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip, re, subprocess, sys, tempfile, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b13_native_feedback as s
from experiments.validate_cnf_layered_feedback import deterministic_result
from solver.test_cnf_b13_probe_cursor import independent
base=s.base;old=s.old
METRICS=('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(215,32649)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b13_native_feedback.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1194
    for f in ('cnf_b13_probe_feedback.py','compare_cnf_b13_native_feedback.py'):
        assert (out/'pilot'/f).read_bytes()==Path('experiments',f).read_bytes()
    initial=(out/'initial-test-source.py').read_text();current=Path(s.FILES[2]).read_text()
    assert initial.replace("elif kind=='source':bad['source'][0].append(9999)","elif kind=='source':bad['source']=[list(cl) for cl in bad['source']];bad['source'][0].append(9999)").replace("elif kind=='prefix':bad['prefix']['steps'].pop()","elif kind=='prefix':bad['prefix']['status']='refuted'")==current
    assert "AttributeError: 'tuple' object has no attribute 'append'" in (out/'initial-test-fixture-failure.log').read_text()
    initial_protocol=base.load(out/'initial-protocol.json');test=s.FILES[2]
    assert initial_protocol['source_fingerprints'][test]==base.sha(out/'second-test-source.py')
    assert {k:v for k,v in initial_protocol.items() if k!='source_fingerprints'}=={k:v for k,v in p.items() if k!='source_fingerprints'}
    assert {k:v for k,v in initial_protocol['source_fingerprints'].items() if k!=test}=={k:v for k,v in p['source_fingerprints'].items() if k!=test}
    assert 'IndexError: pop from empty list' in (out/'second-test-fixture-failure.log').read_text()
    case=old.bound(p['case']);reconstructed=s.build_case()
    assert base.encode({k:v for k,v in reconstructed.items() if k!='reconstruction_seconds'})==base.encode({k:v for k,v in case.items() if k!='reconstruction_seconds'})
    seeds=s.prior.load_frontier(p['seeds']);assert len(seeds)==14
    seed=next(r for r in seeds if (r['target'],r['event'])==(67,63))
    assert seed['b13_strength_state']=='candidate_refutation_pending_native'
    prepared=independent(case['inputs'],case['options'],case['search'])
    entries=dict(zip(prepared[27],prepared[28]))
    for i,r in enumerate(case['search']['program']['probes']):entries.setdefault((-r['assumption'],),dict(kind='b13_probe',index=i))
    clauses=tuple(sorted(entries));expected=(*prepared,clauses,[entries[cl] for cl in clauses]);cc=Counter()
    actual=s.feedback.validate(*case['inputs'],case['search'],**case['options'],program=case['program'],counts=cc)
    assert actual==expected and case['program']['status']=='refuted'
    s.feedback.frozen.check_trace(prepared[0],clauses,None,case['program']['proof'],Counter(),256)
    assert s.feedback.discover(*case['inputs'],case['search'],**case['options'],counts=Counter())==case['program']
    frames,tail=s.feedback.frozen.bind_prefix(case['source'],case['templates'],case['prefix'],Counter())
    assert list(map(list,tail['local']))==seed['final_source'] and [h['template'] for h in tail['hints']]==seed['templates']
    assert s.native.token(tuple(map(tuple,case['source'])),Counter())==case['root']==seed['root']
    groups={};audits={};archives=[];samples=base.load(out/'comparisons.json')['samples']
    assert len(samples)==18 and {(x['mode'],x['repeat']) for x in samples}=={(m,r) for m in s.MODES for r in range(6)}
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];assert report['mode']==mode and report['case']==p['case']
        assert report['result']['status']=='unsat' and report['result']['result']['root']==case['root']
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
        groups.setdefault(mode,[]).append(report)
    totals={};counts={};rss={};records={};archive_bytes={}
    for mode,reports in groups.items():
        assert len(reports)==6
        for report in reports:
            assert deterministic_result(report['result'])==deterministic_result(reports[0]['result'])
            for key in ('counts','warm_counts','native_counts','digest','record_bytes','authority_tables'):
                assert report[key]==reports[0][key],(mode,key)
        totals[mode]={key:sum(r[key] for r in reports)/6 for key in METRICS}
        counts[mode]=reports[0]['counts'];rss[mode]=max(r['peak_rss_bytes'] for r in reports)
        records[mode]=sum(reports[0]['authority_tables'].values());archive_bytes[mode]=Path(reports[0]['archive']['path']).stat().st_size
        if mode!='fresh':assert reports[0]['warm_counts']['b13_probe_feedback_extension_hits']==1
    for mode in ('disabled','direct'):
        for kind in ('b13_probe','b12_source_probe','b11_continuation_probe','b10_comparison_probe'):
            assert counts[mode]['b13_probe_feedback_expanded_'+kind]>0
    assert sum(counts['direct'].get(k,0) for k in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=p['unit_work_limit']
    comparison={mode:{key:100*(totals[mode][key]/totals['fresh'][key]-1) for key in METRICS} for mode in ('disabled','direct')}
    compact_archive=groups['direct'][0]['archive']
    s.compact(out/'remaining-overlay.json',dict(parent=p['seeds'],excluded=[[67,63]],certified_root=case['root'],native_archive=compact_archive))
    binding=old.binding(out/'remaining-overlay.json');remaining=s.load_frontier(binding)
    assert remaining==[r for r in seeds if (r['target'],r['event'])!=(67,63)] and len(remaining)==13
    analysis=dict(coverage=dict(before=232,after=233,total=246),gained_events=[[67,63]],remaining_events=13,
        native_totals=totals,native_counts=counts,peak_rss_bytes=rss,native_records=records,compressed_archive_bytes=archive_bytes,
        percent_increase_vs_fresh=comparison,source_clauses=len(case['source']),source_literals=sum(map(len,case['source'])),
        prefix_steps=len(frames),final_feedback_steps=len(case['program']['proof']['units']),unique_archive_audits=len(audits),
        reconstruction_seconds=case['reconstruction_seconds'],reconstruction_counts=case['reconstruction_counts'],
        candidate_check_counts=dict(cc),storage=dict(case_bytes=Path(p['case']['path']).stat().st_size,
        overlay_bytes=Path(binding['path']).stat().st_size,selected_archive_bytes=Path(compact_archive['path']).stat().st_size),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        b13_native_feedback={k:old.binding(out/(k+'.json')) for k in ('protocol','case','comparisons','analysis')})
    cp['b13_native_feedback'].update(remaining=binding,supplemental_archives=archives);base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(coverage=analysis['coverage'],totals=totals,records=records,percent_increase_vs_fresh=comparison,archive_audits=len(audits))))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','b1700a1a:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2167 tests in .*\n\nOK',full) and re.search(r'Ran 31 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b13_native_feedback']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2167,focused_tests=31,proof_blocks_unchanged=64,
        manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1190,final_sources=len(cp['source_fingerprints']),
        prior_manifests=215,prior_artifacts=32649,new_native_archives=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=216,next_artifacts=32649+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
