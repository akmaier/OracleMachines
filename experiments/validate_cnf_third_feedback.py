#!/usr/bin/env python3
"""Validate B3 composition, retained closures, native archives and lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_third_feedback as study
from experiments.validate_cnf_layered_feedback import deterministic_result
base=study.base;old=study.old;previous=study.previous


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(188,25615)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_third_feedback.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    seeds={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']};assert len(seeds)==45
    groups={};ct={m:Counter() for m in study.MODES};cc={m:Counter() for m in study.MODES};rss=Counter();events={m:{} for m in study.MODES}
    for sample in base.load(out/'censuses.json')['samples']:
        report=old.bound(sample);groups.setdefault((sample['target'],sample['mode']),[]).append(report)
    for (target,mode),reports in groups.items():
        assert len(reports)==2;a,b=reports;aa=old.bound(a['events'])['rows'];bb=old.bound(b['events'])['rows'];assert len(aa)==len(bb)
        for x,y in zip(aa,bb):
            for k in ('target','event','root','program','counts','reconstruction_counts'):assert x[k]==y[k],(target,mode,k)
            key=(target,x['event']);assert key not in events[mode];events[mode][key]=x
            seed=seeds[key];assert x['root']==seed['root'];args=[seed[k] for k in ('final_source','templates','seed','closure','new','next_closure','third')]
            c=Counter();actual=study.candidate.discover(*args,c,mode=mode,**p['limits'])
            assert actual==x['program'] and dict(c)==x['counts'];study.candidate.validate(*args,actual,Counter())
            assert c['probe_roots']==0 and c['unit_probes']==1 and c['probe_occurrence_visits']<=p['limits']['work_limit']
        assert a['counts']==b['counts'];cc[mode].update(a['counts'])
        for k in ('discovery_seconds','reconstruction_seconds','complete_seconds'):ct[mode][k]+=(a[k]+b[k])/2
        rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    assert all(set(rows)==set(seeds) for rows in events.values())
    assert all(r['program']['reason']=='open' for r in events['base'].values())
    gains={key for key,r in events['feedback'].items() if r['program']['status']=='refuted'};assert gains=={(1,57),(37,62)}
    pilot=base.load(out/'pilot.json')['rows'];assert len(pilot)==45
    for r in pilot:
        for mode in study.MODES:
            actual=events[mode][r['target'],r['event']]
            assert actual['program']==r['arms'][mode]['program'] and actual['counts']==r['arms'][mode]['counts']
    remaining=base.load(out/'remaining.json')['rows'];assert len(remaining)==43
    closures=[];diagnostic_counts=Counter();diagnostic_seconds=0.0
    for row in remaining:
        key=(row['target'],row['event']);assert key not in gains
        assert {k:v for k,v in row.items() if k!='feedback'}==seeds[key]
        assert row['feedback']==events['feedback'][key]['program'];assert row['feedback']['reason']=='open'
        dc=Counter();tick=time.perf_counter();args=[row[k] for k in ('final_source','templates','seed','closure','new','next_closure','third')]
        prepared=study.candidate.prepare(*args,dc);fixed,trace,conflict=study.native.propagate(prepared[7],dc);assert conflict is None
        closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
        assert study.candidate.changed.prior.check_closure(prepared[7],closure,dc)==fixed
        oldfixed=dict(row['next_closure']['assignment']);assert oldfixed.items()<=fixed.items()
        assert len(fixed)==events['feedback'][key]['counts'].get('probe_units',0)
        extra=set(fixed)-set(oldfixed)
        newvars=set() if row['third']['action']=='unchanged' else {abs(x['assumption']) for x in row['third']['program']['probes']}
        closures.append(dict(row,feedback_closure=closure,feedback_additional_variables=sorted(extra),feedback_additional_beyond_exclusions=sorted(extra-newvars),feedback_counts=dict(dc)))
        diagnostic_counts.update(dc);diagnostic_seconds+=time.perf_counter()-tick
    assert {(r['target'],r['event']) for r in remaining}==set(seeds)-gains
    study.compact(out/'remaining-closures.json',dict(rows=closures,counts=dict(diagnostic_counts),seconds=diagnostic_seconds,
        scope='Separate scan-based diagnostic outside bounded census timing. feedback_closure is a complete checked unit fixed point on B3, not a SAT verdict. All previous fields and proof layers are retained.'))
    cd=base.load(out/'cases.json');cases=[old.bound(b) for b in cd['cases']]
    assert {(r['target'],r['event']) for r in cd['proposals']}==gains
    assert len(cases)==len({r['root'] for r in cases})==2
    earlier=set()
    for folder in ('cnf-probe-support','cnf-probe-feedback','cnf-closure-probes','cnf-layered-feedback','cnf-changed-closure-probes'):
        for binding in base.load(Path('experiments/results')/folder/'cases.json')['cases']:earlier.add(old.bound(binding)['root'])
    assert not earlier.intersection(r['root'] for r in cases)
    plans=[]
    for case in cases:
        key=(case['target'],case['event']);seed=seeds[key]
        for field in ('seed','closure','new','next_closure','third'):assert case[field]==seed[field]
        assert case['program']==events['feedback'][key]['program']
        _,tail=study.candidate.frozen.bind_prefix(case['source'],case['templates'],case['prefix'],Counter());ts=[h['template'] for h in tail['hints']]
        assert list(map(list,tail['local']))==seed['final_source'] and ts==seed['templates']
        c=Counter();prepared=study.candidate.validate(tail['local'],ts,case['seed'],case['closure'],case['new'],case['next_closure'],case['third'],case['program'],c)
        plan=study.candidate._plan(tail['local'],ts,case['seed'],case['new'],case['third'],case['program'],prepared,c)
        plans.append(dict(name=case['name'],plan=None if plan is None else {k:v for k,v in plan.items() if k!='prepared'},counts=dict(c)))
    study.compact(out/'support-plans.json',dict(rows=plans))
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==8;tg={};audits={};archives=[]
    for sample in trials:
        r=old.bound(sample);i=sample['index'];mode=sample['mode'];case=cases[i]
        assert r['case']==cd['cases'][i] and r['mode']==mode and r['result']['status']=='unsat'
        assert r['result']['result']['root']==case['root']
        a=r['archive'];assert base.sha(a['path'])==a['sha256'];key=(a['sha256'],case['root'])
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(a,path);stored,readers=previous.audit(path,[dict(source=case['source'])],[r['result']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits[key]=dict(archive=a,root=case['root'],readers=readers);archives.append(a)
        tg.setdefault((i,mode),[]).append(r)
    totals={m:Counter() for m in ('fresh','layered')};counts={m:Counter() for m in totals};native_counts={m:Counter() for m in totals};summary=[]
    for i,case in enumerate(cases):
        row=dict(name=case['name'],snapshot_answer=case['snapshot_answer'],arms={})
        for mode in totals:
            a,b=tg[i,mode];assert deterministic_result(a['result'])==deterministic_result(b['result'])
            for k in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[k]==b[k],(i,mode,k)
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metrics['records']=sum(a['authority_tables'].values());totals[mode].update(metrics);counts[mode].update(a['counts']);native_counts[mode].update(a['native_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes']);row['arms'][mode]=metrics
        summary.append(row)
    comparisons={k:dict(improved=sum(r['arms']['layered'][k]<r['arms']['fresh'][k] for r in summary),regressed=[r['name'] for r in summary if r['arms']['layered'][k]>r['arms']['fresh'][k]]) for k in ('solve_seconds','complete_seconds','record_bytes')}
    analysis=dict(events=45,new_refuted_events=2,new_roots=2,remaining_events=43,coverage=dict(before=201,after=203,total=246),
        census_totals=ct,census_counts=cc,totals=totals,counts=counts,native_counts=native_counts,summary=summary,comparisons=comparisons,peak_rss_bytes=rss,
        open_closures=dict(events=len(closures),assignments=sum(len(r['feedback_closure']['assignment']) for r in closures),changed_events=sum(bool(r['feedback_additional_variables']) for r in closures),additional_assignments=sum(len(r['feedback_additional_variables']) for r in closures),additional_beyond_exclusions=sum(len(r['feedback_additional_beyond_exclusions']) for r in closures),diagnostic_seconds=diagnostic_seconds),
        retained_third_failures=sum(len(r['third']['program']['probes']) for r in remaining if r['third']['action']=='searched'),
        result_bytes=dict(remaining=(out/'remaining.json').stat().st_size,closures=(out/'remaining-closures.json').stat().st_size,cases=sum(Path(b['path']).stat().st_size for b in cd['cases'])),
        unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,third_feedback={k:old.binding(out/(k+'.json')) for k in ('protocol','cases','remaining','remaining-closures','support-plans','censuses','comparisons','analysis')})
    cp['third_feedback']['supplemental_archives']=archives;base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,census_totals=ct,closures=analysis['open_closures'],archives=len(audits))),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','482668a7:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1935 tests in .*\n\nOK',full) and re.search(r'Ran 70 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['third_feedback']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1935,focused_tests=70,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1077,final_sources=len(cp['source_fingerprints']),prior_manifests=188,prior_artifacts=25615,archive_audits=len(v['supplemental_archive_audits']),warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=189,next_artifacts=25615+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
