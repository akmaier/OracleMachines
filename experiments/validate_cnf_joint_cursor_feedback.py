#!/usr/bin/env python3
"""Audit mixed original-bank proofs, native archives, and retained open closures."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_cursor_feedback as study
from experiments.validate_cnf_layered_feedback import deterministic_result
base=study.base;old=study.old;previous=study.previous;c=study.candidate
METRICS=('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(201,28609)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_joint_cursor_feedback.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    assert Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    seeds={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']};assert len(seeds)==18
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert seeds.keys()==pilot.keys()
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*8
    groups={};events={};ct={m:Counter() for m in study.MODES};cc={m:Counter() for m in study.MODES};rss=Counter()
    for sample in samples:
        report=old.bound(sample);groups.setdefault((sample['target'],sample['mode']),[]).append(report)
        rows=old.bound(report['events'])['rows'];assert {r['event'] for r in rows}=={e for t,e in seeds if t==sample['target']}
        for row in rows:
            key=(row['target'],row['event']);program=old.bound(row['program']);mode=sample['mode'];expected=pilot[key]['arms'][mode]
            assert row['root']==seeds[key]['root'] and program==expected['program'] and row['counts']==expected['counts']
            assert row['record_bytes']==Path(row['program']['path']).stat().st_size
            vc=Counter();args=tuple(seeds[key][k] for k in study.FIELDS);c.validate(*args,program=program,counts=vc);assert dict(vc)==row['verification_counts']
            events.setdefault((key,mode),[]).append((row,program))
    for (target,mode),(a,b) in groups.items():
        for field in ('counts','record_bytes'):assert a[field]==b[field]
        for field in METRICS:ct[mode][field]+=(a[field]+b[field])/2
        cc[mode].update(a['counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    gains={mode:set() for mode in study.MODES};scans=[]
    for key,seed in seeds.items():
        args=tuple(seed[k] for k in study.FIELDS)
        for mode in study.MODES:
            (a,pa),(b,pb)=events[key,mode];assert pa==pb
            for field in ('counts','verification_counts','reconstruction_counts'):assert a[field]==b[field]
            rc=Counter();actual=c.discover(*args,counts=rc,mode=mode,**p['limits']);assert actual==pa and dict(rc)==a['counts']
            assert rc['probe_roots']==0 and rc['unit_probes']==1 and rc['probe_occurrence_visits']<=p['limits']['work_limit']
            prepared=c.validate(*args,program=actual,counts=Counter());dc=Counter();fixed,trace,conflict=c.native.propagate(prepared[17],dc)
            scan=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]),conflict=conflict)
            assert scan==pilot[key]['arms'][mode]['scan'] and dict(dc)==pilot[key]['arms'][mode]['scan_counts']
            if conflict is None:
                c.cursor.prior.check_closure(prepared[17],dict(units=trace,assignment=scan['assignment']),Counter());assert actual['reason']=='open'
            else:
                c.frozen.check_trace(prepared[0],prepared[17],None,dict(units=trace,conflict=conflict),Counter(),max(1,len(trace)))
                assert actual['status']=='refuted';gains[mode].add(key)
            scans.append(dict(target=key[0],event=key[1],mode=mode,assignments=len(fixed),scan_units=len(trace),bounded_units=None if actual['proof'] is None else len(actual['proof']['units'])))
    assert not gains['base'] and not gains['b6_only'] and gains['b7_only']==gains['joint']=={(37,40)}
    remaining=base.load(out/'remaining.json')['rows'];assert {(r['target'],r['event']) for r in remaining}==set(seeds)-gains['joint']
    closures=[];diagnostic_counts=Counter();diagnostic_seconds=0.0
    for row in remaining:
        key=(row['target'],row['event']);assert {k:v for k,v in row.items() if k!='joint_cursor_feedback'}==seeds[key]
        assert row['joint_cursor_feedback']==events[key,'joint'][0][1]
        args=tuple(row[k] for k in study.FIELDS);dc=Counter();tick=time.perf_counter();prepared=c.prepare(*args,counts=dc)
        fixed,trace,conflict=c.native.propagate(prepared[17],dc);assert conflict is None
        closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]));assert c.cursor.prior.check_closure(prepared[17],closure,dc)==fixed
        oldfixed=dict(row['b6_cursor_feedback_closure']['assignment']);assert oldfixed.items()<=fixed.items();extra=sorted(fixed.keys()-oldfixed.keys())
        exclusions={abs(x['assumption']) for k in ('b6_comparison_cursor','b7_probe_cursor') for x in row[k]['program']['probes']}
        closures.append(dict(row,joint_cursor_feedback_closure=closure,joint_cursor_feedback_added_variables=extra,joint_cursor_feedback_beyond_exclusions=sorted(set(extra)-exclusions),joint_cursor_feedback_counts=dict(dc)))
        diagnostic_counts.update(dc);diagnostic_seconds+=time.perf_counter()-tick
    assert len(closures)==17 and sum(bool(r['joint_cursor_feedback_added_variables']) for r in closures)==4
    assert sum(len(r['joint_cursor_feedback_added_variables']) for r in closures)==8
    study.compact(out/'remaining-closures.json',dict(rows=closures,counts=dict(diagnostic_counts),seconds=diagnostic_seconds,
        scope='Separate complete checked fixed-point diagnostic on the joint B8 bank, outside bounded census timing. Earlier banks and both histories remain unchanged; old cursors cannot be relabelled onto changed inputs.'))
    cd=base.load(out/'cases.json');cases=[old.bound(b) for b in cd['cases']];assert len(cases)==1
    assert {(r['target'],r['event']) for r in cd['proposals']}==gains['joint']
    earlier=set()
    for folder in ('cnf-probe-support','cnf-probe-feedback','cnf-closure-probes','cnf-layered-feedback','cnf-changed-closure-probes','cnf-third-feedback','cnf-probe-cursor','cnf-cursor-feedback','cnf-b4-cursor-feedback','cnf-b5-probe-cursor','cnf-b5-cursor-feedback','cnf-b6-probe-cursor'):
        for b in base.load(Path('experiments/results')/folder/'cases.json')['cases']:earlier.add(old.bound(b)['root'])
    assert not earlier.intersection(r['root'] for r in cases)
    for case in cases:
        key=(case['target'],case['event']);seed=seeds[key];assert case['snapshot_answer']=='unsat'
        for field in study.FIELDS[2:]:assert case[field]==seed[field]
        _,tail=c.frozen.bind_prefix(case['source'],case['templates'],case['prefix'],Counter());ts=[h['template'] for h in tail['hints']]
        assert list(map(list,tail['local']))==seed['final_source'] and ts==seed['templates']
        for mode in study.MODES:
            assert case['programs'][mode]==events[key,mode][0][1]
            c.validate(tail['local'],ts,*(case[k] for k in study.FIELDS[2:]),program=case['programs'][mode],counts=Counter())
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==len(cases)*8;tg={};audits={};archives=[]
    for sample in trials:
        r=old.bound(sample);i=sample['index'];mode=sample['mode'];case=cases[i]
        assert r['case']==cd['cases'][i] and r['mode']==mode and r['result']['status']=='unsat' and r['result']['result']['root']==case['root']
        a=r['archive'];assert base.sha(a['path'])==a['sha256'];key=(a['sha256'],case['root'])
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(a,path);stored,readers=previous.audit(path,[dict(source=case['source'])],[r['result']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits[key]=dict(archive=a,root=case['root'],readers=readers);archives.append(a)
        tg.setdefault((i,mode),[]).append(r)
    totals={m:Counter() for m in study.NATIVE_MODES};counts={m:Counter() for m in totals};native_counts={m:Counter() for m in totals};summary=[]
    for i,case in enumerate(cases):
        row=dict(name=case['name'],snapshot_answer=case['snapshot_answer'],arms={})
        for mode in totals:
            a,b=tg[i,mode];assert deterministic_result(a['result'])==deterministic_result(b['result'])
            for k in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[k]==b[k],(i,mode,k)
            if mode in ('b7_direct','joint_direct'):assert sum(a['counts'].get(k,0) for k in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=262144
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metrics['records']=sum(a['authority_tables'].values());totals[mode].update(metrics);counts[mode].update(a['counts']);native_counts[mode].update(a['native_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes']);row['arms'][mode]=metrics
        summary.append(row)
    assert counts['disabled']['joint_expanded_b6_comparison_probe'] and counts['disabled']['joint_expanded_b7_probe']
    comparisons={control:{k:dict(improved=sum(r['arms']['joint_direct'][k]<r['arms'][control][k] for r in summary),regressed=[r['name'] for r in summary if r['arms']['joint_direct'][k]>r['arms'][control][k]]) for k in ('solve_seconds','warm_seconds','cold_seconds','complete_seconds','record_bytes')} for control in ('fresh','disabled','b7_direct')}
    analysis=dict(events=18,new_refuted_events=1,new_roots=1,remaining_events=17,coverage=dict(before=228,after=229,total=246),census_totals=ct,census_counts=cc,
        totals=totals,counts=counts,native_counts=native_counts,summary=summary,comparisons=comparisons,peak_rss_bytes=rss,scan_diagnostics=scans,
        open_closures=dict(events=17,changed_events=4,additional_assignments=8,additional_beyond_exclusions=sum(len(r['joint_cursor_feedback_beyond_exclusions']) for r in closures),diagnostic_seconds=diagnostic_seconds),
        retained_b6_failures=sum(len(r['b6_comparison_cursor']['program']['probes']) for r in remaining),retained_b7_failures=sum(len(r['b7_probe_cursor']['program']['probes']) for r in remaining),
        result_bytes=dict(previous=Path(p['seeds']['path']).stat().st_size,remaining=(out/'remaining.json').stat().st_size,closures=(out/'remaining-closures.json').stat().st_size,cases=sum(Path(b['path']).stat().st_size for b in cd['cases'])),
        unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,joint_cursor_feedback={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','cases','remaining','remaining-closures','censuses','comparisons','analysis')})
    cp['joint_cursor_feedback']['supplemental_archives']=archives;base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,census_totals=ct,closures=analysis['open_closures'],archives=len(audits))),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','29743e61:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2048 tests in .*\n\nOK',full) and re.search(r'Ran 183 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['joint_cursor_feedback']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2048,focused_tests=183,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1133,final_sources=len(cp['source_fingerprints']),prior_manifests=201,prior_artifacts=28609,archive_audits=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=202,next_artifacts=28609+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
