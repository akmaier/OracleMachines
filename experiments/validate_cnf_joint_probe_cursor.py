#!/usr/bin/env python3
"""Replay discovery, certify new feedback/native proofs, and preserve provenance."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_joint_probe_cursor as study
from experiments.validate_cnf_layered_feedback import deterministic_result
base=study.base;old=study.old;c=study.candidate;feedback=study.feedback;previous=study.previous
METRICS=('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(202,28925)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_joint_probe_cursor.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1142
    assert Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    for f,h in p['case_export_correction'].items():assert base.sha(f)==h
    before=(out/'initial-compare-source.py').read_text();after=Path(study.FILES[2]).read_text()
    assert before[:before.index('def cases(')]==after[:after.index('def cases(')]
    seeds={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']};assert len(seeds)==17
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert pilot.keys()==seeds.keys()
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*6
    events={};groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};rss=Counter()
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];groups.setdefault((sample['target'],mode),[]).append(report)
        for row in old.bound(report['events'])['rows']:
            key=row['target'],row['event'];result=old.bound(row['result']);seed=seeds[key]
            assert row['root']==seed['root'] and row['record_bytes']==Path(row['result']['path']).stat().st_size
            vc=Counter();c.validate(*(seed[k] for k in study.FIELDS),closure=seed['joint_cursor_feedback_closure'],result=result,counts=vc)
            assert dict(vc)==row['verification_counts'];events.setdefault((key,mode),[]).append((row,result))
    for (target,mode),(a,b) in groups.items():
        for k in ('counts','record_bytes'):assert a[k]==b[k]
        for k in METRICS:totals[mode][k]+=(a[k]+b[k])/2
        counts[mode].update(a['counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    failures=[];exhausted=[];changed=[]
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
                cc=Counter();actual=c.discover(*args,closure=cl,counts=cc,policy=mode,**p['limits']);assert actual==pa and dict(cc)==a['counts']
                if mode=='reuse':assert actual==pilot[key]['result'] and dict(cc)==pilot[key]['counts']
                assert actual['program']['status']=='unresolved'
            assert events[key,'reuse'][0][1]==events[key,'matched'][0][1]
            row,result=events[key,'reuse'][0];probes=result['program']['probes']
            if result['program']['reason']=='complete':exhausted.append(list(key))
            if not row['counts'].get('joint_probe_imported_cursors'):changed.append(list(key))
            if probes:failures.append(dict(target=target,event=key[1],assumptions=[x['assumption'] for x in probes]))
    assert counts['reuse']['joint_probe_imported_cursors']==13 and len(changed)==4
    assert sum(len(r['assumptions']) for r in failures)==21
    diagnostic={};gains=set()
    for r in base.load(out/'feedback-diagnostics.json')['rows']:
        key=r['target'],r['event'];seed=seeds[key];result=events[key,'reuse'][0][1];args=tuple(seed[k] for k in study.FIELDS);cc=Counter()
        actual=feedback.discover(*args,result,closure=seed['joint_cursor_feedback_closure'],counts=cc)
        assert actual==r['program'] and dict(cc)==r['counts'];feedback.validate(*args,result,closure=seed['joint_cursor_feedback_closure'],program=actual,counts=Counter())
        if actual['status']=='refuted':gains.add(key)
        diagnostic[key]=actual
    assert gains=={(28,19)}
    remaining=base.load(out/'remaining.json')['rows'];assert {(r['target'],r['event']) for r in remaining}==seeds.keys()-gains
    closures=[];closure_seconds=0.0;closure_counts=Counter()
    for row in remaining:
        key=row['target'],row['event'];assert {k:v for k,v in row.items() if k not in ('joint_probe_cursor','joint_probe_feedback')}==seeds[key]
        assert row['joint_probe_cursor']==events[key,'reuse'][0][1] and row['joint_probe_feedback']==diagnostic[key]
        cc=Counter();tick=time.perf_counter();prepared=feedback.prepare(*(row[k] for k in study.FIELDS),row['joint_probe_cursor'],closure=row['joint_cursor_feedback_closure'],counts=cc)
        fixed,trace,conflict=feedback.native.propagate(prepared[19],cc);assert conflict is None
        cl=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]));assert c.c.prior.check_closure(prepared[19],cl,cc)==fixed
        oldfixed=dict(row['joint_cursor_feedback_closure']['assignment']);assert oldfixed.items()<=fixed.items()
        extra=sorted(fixed.keys()-oldfixed.keys());closures.append(dict(row,joint_probe_feedback_closure=cl,joint_probe_feedback_added_variables=extra))
        closure_counts.update(cc);closure_seconds+=time.perf_counter()-tick
    assert sum(len(r['joint_probe_feedback_added_variables']) for r in closures)==1
    study.compact(out/'remaining-closures.json',dict(rows=closures,counts=dict(closure_counts),seconds=closure_seconds,scope='Checked complete bank-9 closures, measured separately from search census.'))
    cd=base.load(out/'cases.json');cases=[old.bound(b) for b in cd['cases']];assert len(cases)==1
    assert {(r['target'],r['event']) for r in cd['proposals']}==gains
    for case in cases:
        key=case['target'],case['event'];seed=seeds[key];assert case['snapshot_answer']=='unsat'
        for field in study.FIELDS[2:]:assert case[field]==seed[field]
        assert case['search']==events[key,'reuse'][0][1] and case['program']==diagnostic[key]
        _,tail=feedback.frozen.bind_prefix(case['source'],case['templates'],case['prefix'],Counter())
        assert list(map(list,tail['local']))==seed['final_source'] and [h['template'] for h in tail['hints']]==seed['templates']
        feedback.validate(tail['local'],seed['templates'],*(case[k] for k in study.FIELDS[2:]),case['search'],closure=case['joint_closure'],program=case['program'],counts=Counter())
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==6;groups={};audits={};archives=[]
    for sample in trials:
        r=old.bound(sample);i=sample['index'];mode=sample['mode'];case=cases[i]
        assert r['case']==cd['cases'][i] and r['mode']==mode and r['result']['status']=='unsat' and r['result']['result']['root']==case['root']
        a=r['archive'];assert base.sha(a['path'])==a['sha256'];key=a['sha256'],case['root']
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(a,path);stored,readers=previous.audit(path,[dict(source=case['source'])],[r['result']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits[key]=dict(archive=a,root=case['root'],readers=readers);archives.append(a)
        groups.setdefault((i,mode),[]).append(r)
    nt={m:Counter() for m in study.NATIVE_MODES};nc={m:Counter() for m in nt};native_counts={m:Counter() for m in nt};summary=[]
    for i,case in enumerate(cases):
        row=dict(name=case['name'],arms={})
        for mode in nt:
            a,b=groups[i,mode];assert deterministic_result(a['result'])==deterministic_result(b['result'])
            for k in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[k]==b[k],(mode,k)
            if mode=='direct':assert sum(a['counts'].get(k,0) for k in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=262144
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')};metrics['records']=sum(a['authority_tables'].values())
            nt[mode].update(metrics);nc[mode].update(a['counts']);native_counts[mode].update(a['native_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes']);row['arms'][mode]=metrics
        summary.append(row)
    assert nc['disabled']['joint_probe_feedback_expanded_joint_probe']>0
    analysis=dict(events=17,coverage=dict(before=229,after=230,total=246),new_roots=1,remaining_events=16,new_failures=failures,changed_events=changed,exhausted_events=exhausted,
        census_totals=totals,census_counts=counts,native_totals=nt,native_counts=nc,native_solver_counts=native_counts,peak_rss_bytes=rss,native_summary=summary,
        feedback_seconds=sum(r['seconds'] for r in base.load(out/'feedback-diagnostics.json')['rows']),remaining_closure_seconds=closure_seconds,
        probe_reduction=counts['matched']['probe_roots']-counts['reuse']['probe_roots'],remaining_new_failures=sum(len(r['joint_probe_cursor']['program']['probes']) for r in remaining),
        result_bytes=dict(previous=Path(p['seeds']['path']).stat().st_size,remaining=(out/'remaining.json').stat().st_size,closures=(out/'remaining-closures.json').stat().st_size),
        unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,joint_probe_cursor={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','cases','remaining','remaining-closures','censuses','comparisons','analysis','feedback-diagnostics')})
    cp['joint_probe_cursor']['supplemental_archives']=archives;base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(coverage=analysis['coverage'],census_totals=totals,native_totals=nt,probe_reduction=analysis['probe_reduction'],archives=len(audits))))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','89dcb867:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2057 tests in .*\n\nOK',full) and re.search(r'Ran \d+ tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['joint_probe_cursor']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2057,focused_tests=int(re.search(r'Ran (\d+) tests',focus)[1]),proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1137,final_sources=len(cp['source_fingerprints']),prior_manifests=202,prior_artifacts=28925,archive_audits=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=203,next_artifacts=28925+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
