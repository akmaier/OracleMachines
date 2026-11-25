#!/usr/bin/env python3
"""Audit B5 frontier migration, failure proofs and preserved lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b5_probe_cursor as study
base=study.base;old=study.old;previous=study.previous
from experiments.validate_cnf_layered_feedback import deterministic_result


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(194,27026)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b5_probe_cursor.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert Path(p['pilot_source']['path']).read_bytes()==Path('experiments/cnf_b5_probe_cursor.py').read_bytes()
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    saved={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']}
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert saved.keys()==pilot.keys() and len(saved)==25
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*6
    groups={};event_groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};rss=Counter()
    for s in samples:
        r=old.bound(s);assert (r['target'],r['mode'])==(s['target'],s['mode']);groups.setdefault((s['target'],s['mode']),[]).append(r)
        rows=old.bound(r['events'])['rows']
        assert {x['event'] for x in rows}=={e for t,e in saved if t==s['target']}
        for x in rows:
            key=(x['target'],x['event']);result=old.bound(x['result']);seed=saved[key]
            assert x['root']==seed['root']
            expected='reuse' if s['mode']=='matched' else s['mode']
            assert result==pilot[key]['arms'][expected]['result']
            if s['mode']!='matched':assert x['counts']==pilot[key]['arms'][s['mode']]['counts']
            vc=Counter();study.candidate.validate(*(seed[k] for k in study.FIELDS),result,vc);assert dict(vc)==x['verification_counts']
            assert x['record_bytes']==Path(x['result']['path']).stat().st_size
            extra=s['mode']=='matched' and list(key) in p['matching_frontier_cases']
            assert x['counts'].get('probe_occurrence_visits',0)<=p['limits']['work_limit']*(2 if extra else 1)
            assert x['counts'].get('probe_roots',0)<=p['limits']['probe_limit']+(64 if extra else 0)
            event_groups.setdefault((key,s['mode']),[]).append((x,result))
    regressions=[]
    for (target,mode),(a,b) in groups.items():
        for k in ('counts','record_bytes'):assert a[k]==b[k]
        for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes'):totals[mode][k]+=(a[k]+b[k])/2
        counts[mode].update(a['counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    remaining=base.load(out/'remaining.json')['rows'];assert len(remaining)==20
    remaining_by_key={(r['target'],r['event']):r for r in remaining}
    gains=set();failed_cases=[];reasons=Counter();summary=[];matches=[]
    for key,seed in saved.items():
        row=dict(target=key[0],event=key[1],arms={});results={}
        for mode in study.MODES:
            (a,ra),(b,rb)=event_groups[key,mode];assert ra==rb and a['counts']==b['counts'] and a['reconstruction_counts']==b['reconstruction_counts']
            results[mode]=ra;row['arms'][mode]={k:(a[k]+b[k])/2 for k in ('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','record_bytes')}
        args=[seed[k] for k in study.FIELDS];prepared,*_=study.candidate.prepare(*args,Counter())
        same=study.candidate.equivalent(prepared,seed['cursor_feedback_closure'],seed['b4_cursor_feedback_closure'],seed['b4_probe_cursor'],256,Counter())
        assert same==(list(key) in p['matching_frontier_cases'])
        if same:matches.append(key)
        else:assert results['restart']==results['reuse']
        assert results['matched']==results['reuse']
        result=results['reuse'];reasons[result['program']['reason']]+=1
        if result['program']['status']=='refuted':gains.add(key)
        else:
            r=remaining_by_key[key];assert {k:v for k,v in r.items() if k!='b5_probe_cursor'}==seed
            assert r['b5_probe_cursor']==result
            failures=len(result['program']['probes'])
            if failures:failed_cases.append(dict(target=key[0],event=key[1],failures=failures))
        summary.append(row)
    assert gains=={(1,16),(1,17),(37,1),(61,1),(64,24)} and set(remaining_by_key)==set(saved)-gains
    assert len(matches)==16 and counts['reuse']['b5_imported_completed']==1024
    assert counts['matched']['probe_roots']-counts['reuse']['probe_roots']==1024
    assert sum(r['failures'] for r in failed_cases)==26 and len(failed_cases)==8
    census=dict(totals=totals,counts=counts,peak_rss_bytes=rss,summary=summary,
        matching_cases=matches,reasons=reasons,retained_failures=failed_cases,
        comparisons={control:{k:dict(improved=sum(r['arms']['reuse'][k]<r['arms'][control][k] for r in summary),regressed=[(r['target'],r['event']) for r in summary if r['arms']['reuse'][k]>r['arms'][control][k]]) for k in ('discovery_seconds','record_bytes')} for control in ('restart','matched')})
    cd=base.load(out/'cases.json');cases=[old.bound(b) for b in cd['cases']]
    assert {(r['target'],r['event']) for r in cd['proposals']}==gains
    assert len(cases)==len({r['root'] for r in cases})==5
    earlier=set()
    for folder in ('cnf-probe-support','cnf-probe-feedback','cnf-closure-probes','cnf-layered-feedback','cnf-changed-closure-probes','cnf-third-feedback','cnf-probe-cursor','cnf-cursor-feedback','cnf-b4-cursor-feedback'):
        for binding in base.load(Path('experiments/results')/folder/'cases.json')['cases']:earlier.add(old.bound(binding)['root'])
    assert not earlier.intersection(r['root'] for r in cases)
    plans=[]
    for case in cases:
        key=(case['target'],case['event']);seed=saved[key]
        for field in study.FIELDS[2:]:assert case[field]==seed[field]
        assert case['result']==event_groups[key,'reuse'][0][1]
        _,tail=study.candidate.frozen.bind_prefix(case['source'],case['templates'],case['prefix'],Counter());ts=[h['template'] for h in tail['hints']]
        assert list(map(list,tail['local']))==seed['final_source'] and ts==seed['templates']
        c=Counter();prepared=study.candidate.validate(tail['local'],ts,*(case[k] for k in study.FIELDS[2:]),case['result'],c)
        plan=study.compiler._plan(tail['local'],ts,case['seed'],case['new'],case['third'],case['probe_cursor']['program'],case['b4_probe_cursor']['program'],case['result']['program'],prepared,c)
        plans.append(dict(name=case['name'],plan=None if plan is None else {k:v for k,v in plan.items() if k!='prepared'},counts=dict(c)))
    study.compact(out/'support-plans.json',dict(rows=plans))
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==len(cases)*4;tg={};audits={};archives=[]
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
    totals={m:Counter() for m in ('fresh','direct')};counts={m:Counter() for m in totals};native_counts={m:Counter() for m in totals};summary=[]
    for i,case in enumerate(cases):
        row=dict(name=case['name'],snapshot_answer=case['snapshot_answer'],arms={})
        for mode in totals:
            a,b=tg[i,mode];assert deterministic_result(a['result'])==deterministic_result(b['result'])
            for k in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[k]==b[k],(i,mode,k)
            if mode=='direct':assert sum(a['counts'].get(k,0) for k in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=262144
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metrics['records']=sum(a['authority_tables'].values());totals[mode].update(metrics);counts[mode].update(a['counts']);native_counts[mode].update(a['native_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes']);row['arms'][mode]=metrics
        summary.append(row)
    comparisons={k:dict(improved=sum(r['arms']['direct'][k]<r['arms']['fresh'][k] for r in summary),regressed=[r['name'] for r in summary if r['arms']['direct'][k]>r['arms']['fresh'][k]]) for k in ('solve_seconds','complete_seconds','record_bytes')}
    analysis=dict(events=25,new_refuted_events=5,new_roots=len(cases),remaining_events=20,coverage=dict(before=221,after=226,total=246),census=census,
        totals=totals,counts=counts,native_counts=native_counts,summary=summary,comparisons=comparisons,peak_rss_bytes=rss,
        result_bytes=dict(remaining=(out/'remaining.json').stat().st_size,previous=Path(p['seeds']['path']).stat().st_size,cases=sum(Path(b['path']).stat().st_size for b in cd['cases'])),
        unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,b5_probe_cursor={k:old.binding(out/(k+'.json')) for k in ('protocol','cases','remaining','support-plans','censuses','comparisons','analysis')})
    cp['b5_probe_cursor']['supplemental_archives']=archives;base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,census=census['totals'],failed_cases=failed_cases,archives=len(audits))),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','397d757e:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1987 tests in .*\n\nOK',full) and re.search(r'Ran 122 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b5_probe_cursor']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1987,focused_tests=122,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1102,final_sources=len(cp['source_fingerprints']),prior_manifests=194,prior_artifacts=27026,new_archive_audits=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=195,next_artifacts=27026+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
