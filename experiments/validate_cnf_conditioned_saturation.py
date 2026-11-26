#!/usr/bin/env python3
"""Audit exact conditioned branches, original-source certificates and lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditioned_saturation as s
from experiments.validate_cnf_layered_feedback import deterministic_result
from solver.test_cnf_b13_probe_cursor import independent
base=s.base;old=s.old
CENSUS=('preparation_seconds','discovery_seconds','verification_seconds','persistence_seconds','complete_seconds','record_bytes')
NATIVE=('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(218,32919)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_conditioned_saturation.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1208
    for f in s.FILES[:2]:assert (out/('pilot-'+Path(f).name)).read_bytes()==Path(f).read_bytes()
    assert 'StopIteration' in (out/'initial-native-pilot-failure.log').read_text()
    assert 'AssertionError' in (out/'initial-validation-failure.log').read_text()
    cases={n:old.bound(b) for n,b in p['cases'].items()};rebuilt=s.build_cases();prepared={}
    for name,case in cases.items():
        assert base.encode({key:v for key,v in case.items() if key!='reconstruction_seconds'})==base.encode({key:v for key,v in rebuilt[name].items() if key!='reconstruction_seconds'})
        lower=independent(case['inputs'],case['options'],case['search']);entries=dict(zip(lower[27],lower[28]))
        for i,probe in enumerate(case['search']['program']['probes']):entries.setdefault((-probe['assumption'],),dict(kind='b13_probe',index=i))
        clauses=tuple(sorted(entries));expected=(*lower,clauses,[entries[cl] for cl in clauses]);prepared[name]=s.seed(case,Counter());assert prepared[name]==expected
        assert s.compiler.native.token(tuple(map(tuple,case['source'])),Counter())==case['root']
        first=old.bound(p['firsts'][name]);s.condition.validate(clauses,first,Counter(),order_source=prepared[name][0])
        cc=Counter();fresh=s.seed(case,cc);again=s.condition.discover(fresh[29],s.order(fresh,cc)[0],cc,order_source=fresh[0],round_limit=1,probe_limit=32,work_limit=2097152,trace_limit=256)
        acquisition=next(r for r in p['first_acquisition'] if r['name']==name)
        assert again==first and dict(cc)==acquisition['counts'] and acquisition['bytes']==Path(p['firsts'][name]['path']).stat().st_size
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==18
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(6)}
    groups={};events={};ctotals={};ccounts={};crss={}
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];assert report['mode']==mode and {e['name'] for e in report['events']}==set(cases)
        groups.setdefault(mode,[]).append(report)
        for event in report['events']:
            name=event['name'];result=old.bound(event['result']);vc=Counter();s.check(s.seed(cases[name],vc),result,vc)
            assert dict(vc)==event['verification_counts'] and event['record_bytes']==Path(event['result']['path']).stat().st_size
            events.setdefault((name,mode),[]).append((event,result))
        for key in CENSUS:
            if key!='complete_seconds':assert abs(report[key]-sum(e[key] for e in report['events']))<1e-8
    for mode,reports in groups.items():
        assert len(reports)==6;ctotals[mode]={key:sum(r[key] for r in reports)/6 for key in CENSUS};crss[mode]=max(r['peak_rss_bytes'] for r in reports)
        ccounts[mode]=dict(sum((Counter(e['counts']) for e in reports[0]['events']),Counter()))
    candidates=[];diagnostics=[]
    for name,case in cases.items():
        for mode in s.MODES:
            rows=events[name,mode];event,result=rows[0]
            for other,another in rows:
                assert another==result
                for key in ('counts','verification_counts','record_bytes'):assert other[key]==event[key]
            cc=Counter();prep=s.seed(case,cc);actual=s.search(prep,mode,cc,old.bound(p['firsts'][name]) if mode=='resume' else None)
            assert actual==result and dict(cc)==event['counts']
        flat=events[name,'flat'][0][1]['result'];assert flat['status']=='unresolved' and flat['reason']=='fixed_point' and not any(r['search']['program']['probes'] for r in flat['rounds'])
        result=events[name,'conditioned'][0][1];assert result==events[name,'resume'][0][1]
        pilot=next(row for row in base.load(out/'pilot.json')['rows'] if (row['target'],row['event'])==(case['target'],case['event']))
        assert len(result['trials'])==len(pilot['trials'])
        for actual,initial in zip(result['trials'],pilot['trials']):
            assert actual['pivot']==initial['pivot'] and [actual['low'],actual['high']]==[arm['result'] for arm in initial['arms']]
        if result['status']=='refuted':candidates.append(name)
        learned=[]
        for trial in result['trials']:
            for field,lit in (('low',-trial['pivot']),('high',trial['pivot'])):
                if trial[field]['status']=='refuted':learned.append(-lit)
        bank=prepared[name][29];before,_,conflict=s.k.native.propagate(bank,Counter());assert conflict is None
        expanded=tuple(sorted(set(bank)|{(lit,) for lit in learned}));after,trace,conflict=s.k.native.propagate(expanded,Counter())
        before_residual,_=s.k.closure_check.residual_bank(bank,before,Counter())
        if conflict is not None:s.k.frozen.check_trace(prepared[name][0],expanded,None,dict(units=trace,conflict=conflict),Counter(),256)
        after_residual=None if conflict is not None else s.k.closure_check.residual_bank(expanded,after,Counter())[0]
        diagnostics.append(dict(name=name,pivots=len(result['trials']),failed_branches=len(learned),derived_units=learned,pair_refuted=result['status']=='refuted',
            combined_unit_conflict=conflict is not None,combined_proof=dict(units=trace,conflict=conflict) if conflict is not None else None,
            closure=None if conflict is not None else dict(units=trace,assignment=sorted([list(x) for x in after.items()])),
            before_clauses=len(before_residual),after_clauses=None if after_residual is None else len(after_residual),
            added_assignments=[] if conflict is not None else sorted([v,b] for v,b in after.items() if v not in before)))
    assert set(candidates)=={'1-0','1-15','28-17','61-21','61-51','61-52','61-60','61-61','61-74'}
    ns=base.load(out/'comparisons.json')['samples'];assert len(ns)==36
    assert {(x['name'],x['mode'],x['repeat']) for x in ns}=={(name,mode,i) for name in candidates for mode in s.NATIVE for i in range(2)}
    ngroups={};audits={};archives=[]
    for sample in ns:
        report=old.bound(sample);name=sample['name'];mode=sample['mode'];case=cases[name]
        assert (report['name'],report['mode'],report['case'])==(name,mode,p['cases'][name])
        if mode=='conditioned':assert report['result']['status']=='unsat' and report['result']['result']['root']==case['root']
        archive=report['archive'];assert base.sha(archive['path'])==archive['sha256'];key=archive['sha256'],case['root']
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';s.previous.restore_archive(archive,db);tables,readers=s.previous.audit(db,[dict(source=case['source'])],[report['result']])
            assert {t:len(v) for t,v in tables.items()}==report['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}==report['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items())==report['record_bytes']
            # The existing fresh solver may also publish checked binary authority.
            # Only the conditioned compiler promises exclusively residual records.
            extra={table:len(records) for table,records in tables.items() if records and table!='cnf_residual_v1'}
            assert extra==({'cnf_binary_equivalence_v2':1} if (name,mode)==('61-21','fresh') else {})
            audits[key]=dict(name=name,archive=archive,root=case['root'],status=report['result']['status'],readers=readers);archives.append(archive)
        ngroups.setdefault((name,mode),[]).append(report)
    pilot=base.load(out/'native-pilot.json');trial=ngroups['28-17','conditioned'][0]
    assert base.sha(pilot['archive']['path'])==pilot['archive']['sha256']==trial['archive']['sha256']
    assert pilot['record_bytes']==trial['record_bytes'] and pilot['records']==sum(trial['authority_tables'].values())
    totals={};rss={};records={};statuses={};selected={};alltotals={mode:Counter() for mode in s.NATIVE}
    for name in candidates:
        totals[name]={};rss[name]={};records[name]={};statuses[name]={}
        for mode in s.NATIVE:
            reports=ngroups[name,mode];assert len(reports)==2
            for report in reports:
                assert deterministic_result(report['result'])==deterministic_result(reports[0]['result'])
                for key in ('counts','warm_counts','native_counts','digest','record_bytes','authority_tables'):assert report[key]==reports[0][key],(name,mode,key)
            totals[name][mode]={key:sum(r[key] for r in reports)/2 for key in NATIVE};alltotals[mode].update(totals[name][mode]);rss[name][mode]=max(r['peak_rss_bytes'] for r in reports)
            records[name][mode]=sum(reports[0]['authority_tables'].values());statuses[name][mode]=reports[0]['result']['status']
            if mode=='conditioned':
                assert reports[0]['warm_counts']['conditioned_native_extension_hits']==1
                assert sum(reports[0]['counts'].get(key,0) for key in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=524288
        best=min((m for m in s.NATIVE if statuses[name][m]=='unsat'),key=lambda m:totals[name][m]['complete_seconds'])
        selected[name]=dict(mode=best,root=cases[name]['root'],archive=ngroups[name,best][0]['archive'])
    excluded=sorted([[cases[n]['target'],cases[n]['event']] for n in candidates]);remaining_parent=parent['sliced_saturation']['remaining']
    compact=s.compact;compact(out/'remaining-overlay.json',dict(parent=remaining_parent,excluded=excluded,certificates=selected));binding=old.binding(out/'remaining-overlay.json')
    remaining=s.load_frontier(binding);assert remaining==[r for r in s.rows() if [r['target'],r['event']] not in excluded] and len(remaining)==3
    analysis=dict(coverage=dict(before=234,after=243,total=246),gained_events=excluded,remaining_events=3,census_totals=ctotals,census_counts=ccounts,census_peak_rss_bytes=crss,
        resume_percent_change={key:100*(ctotals['resume'][key]/ctotals['conditioned'][key]-1) for key in CENSUS},
        first_acquisition=dict(seconds=sum(r['seconds'] for r in p['first_acquisition']),bytes=sum(r['bytes'] for r in p['first_acquisition'])),
        diagnostics=diagnostics,native_totals=totals,native_all_totals=alltotals,native_peak_rss_bytes=rss,native_records=records,native_statuses=statuses,selected=selected,
        source_reconstruction_seconds=sum(case['reconstruction_seconds'] for case in cases.values()),unique_archive_audits=len(audits),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,conditioned_saturation={key:old.binding(out/(key+'.json')) for key in ('protocol','censuses','comparisons','analysis')})
    cp['conditioned_saturation'].update(remaining=binding,supplemental_archives=archives);base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(coverage=analysis['coverage'],census_totals=ctotals,native_totals=alltotals,remaining=[d for d in diagnostics if not d['pair_refuted']])) )


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','5bbcc2de:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2191 tests in .*\n\nOK',full) and re.search(r'Ran 24 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['conditioned_saturation']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2191,focused_tests=24,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1203,final_sources=len(cp['source_fingerprints']),prior_manifests=218,prior_artifacts=32919,new_native_archives=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=219,next_artifacts=32919+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
