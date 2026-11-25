#!/usr/bin/env python3
"""Audit source-bound probe traces, native reconstruction, costs and lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_wide_guard_probes as study
base=study.base;old=study.old;previous=study.previous


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(180,22276)
    sources={**p['source_fingerprints'],'solver/test_cnf_wide_guard_probe_scope.py':base.sha('solver/test_cnf_wide_guard_probe_scope.py'),'experiments/validate_cnf_wide_guard_probes.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==48
    rows={m:{} for m in study.MODES};groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};rss=Counter();peaks={m:Counter() for m in study.MODES}
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];target=sample['target'];assert r['mode']==mode and r['target']==target
        es=old.bound(r['events'])['rows'];groups.setdefault((target,mode),[]).append(es)
        for e in es:
            c=e['counts'];assert c['probe_index_builds']==1 and c.get('probe_roots',0)<=64 and c.get('probe_occurrence_visits',0)<=262144
            assert c['unit_probes']<=65
            if sample['repeat']==0:rows[mode][(target,e['event'])]=e
            for k in ('probe_index_peak_literals','prepared_input_slots','probe_occurrence_visits'):peaks[mode][k]=max(peaks[mode][k],c.get(k,0))
        totals[mode].update({k:r[k]/2 for k in ('discovery_seconds','reconstruction_seconds','complete_seconds')})
        counts[mode].update({k:v/2 for k,v in r['counts'].items()});rss[mode]=max(rss[mode],r['peak_rss_bytes'])
    for pair in groups.values():
        assert len(pair)==2
        assert [(e['root'],e['program'],e['counts'],e['reconstruction_counts']) for e in pair[0]]==[(e['root'],e['program'],e['counts'],e['reconstruction_counts']) for e in pair[1]]
    assert all(len(rs)==246 and rs.keys()==rows['source'].keys() for rs in rows.values())
    trace_checks=Counter();residuals=[];states={}
    for target in p['targets']:
        source,ts,refs,events=study.inputs(p,target)
        for ref in refs:
            key=(target,ref['event']);local,templates,state=study.bind(source,ts,ref,events[ref['event']],Counter());states[key]=(local,templates,ref,state)
            for mode in study.MODES:
                r=rows[mode][key];assert r['root']==ref['root'];c=Counter()
                study.candidate.validate(state['local'],[h['template'] for h in state['hints']],r['program'],c);trace_checks[mode]+=c['checked_probe_proofs']
                if r['program']['status']=='refuted':continue
                tested=set(study.candidate.roots(state['local'])[:r['counts']['probe_roots']]);failed={q['assumption'] for q in r['program']['probes']}
                untested=sorted(l for l in failed if -l not in tested)
                residuals.append(dict(target=target,event=ref['event'],mode=mode,root=ref['root'],reason=r['program']['reason'],
                    exclusions=len(failed),exclusions_with_untested_complement=untested,exclusions_with_tested_complement=sorted(failed-set(untested))))
    compact=study.compact;compact(out/'remaining-probes.json',dict(rows=residuals,limitations='Literal coordinates are local to the checked final cofactor. The failed branch is certified, but an untested opposite branch has no verdict. Successful traces are retained in event programs; not every conditional trace has a separate native archive.'))
    success={m:{k for k,r in rs.items() if r['program']['status']=='refuted'} for m,rs in rows.items()}
    roots={m:{rows[m][k]['root'] for k in ss} for m,ss in success.items()};union=set().union(*roots.values())
    coverage={m:dict(events=len(success[m]),roots=len(roots[m]),outcomes=dict(Counter(r['program']['reason'] for r in rows[m].values())),
        gained_over_source=sorted(success[m]-success['source']),lost_from_source=sorted(success['source']-success[m]),
        gained_over_binary=sorted(success[m]-success['binary']),lost_from_binary=sorted(success['binary']-success[m])) for m in study.MODES}
    cd=base.load(out/'cases.json');cases=[old.bound(b) for b in cd['cases']];assert {c['root'] for c in cases}==union
    diagnosis={(r['target'],r['event']):r for r in base.load(study.PARENT/'residual-diagnosis.json')['rows']}
    for case in cases:
        key=(case['target'],case['event']);local,templates,ref,state=states[key]
        assert case['source']==list(map(list,local)) and case['templates']==templates and case['prefix']==ref['program']
        assert case['program']==rows[case['mode']][key]['program'] and case['snapshot_answer']==diagnosis[key]['snapshot_answer']
        assert case['snapshot_answer']!='sat'
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==len(cases)*4;tg={};audits={};archives=[]
    for sample in trials:
        r=old.bound(sample);index=sample['index'];mode=sample['mode'];assert r['case']==cd['cases'][index] and r['mode']==mode
        if mode=='extension':assert r['result']['status']=='unsat'
        if r['result']['status']=='unsat':assert r['result']['result']['root']==cases[index]['root']
        a=r['archive'];assert base.sha(a['path'])==a['sha256'];key=(a['sha256'],cases[index]['root'])
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(a,path);stored,readers=previous.audit(path,[dict(source=cases[index]['source'])],[r['result']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits[key]=dict(archive=a,root=cases[index]['root'],readers=readers);archives.append(a)
        tg.setdefault((index,mode),[]).append(r)
    tt={m:Counter() for m in ('fresh','extension')};trss=Counter();summary=[]
    for i,case in enumerate(cases):
        row=dict(name=case['name'],root=case['root'],snapshot_answer=case['snapshot_answer'],arms={})
        for mode in tt:
            a,b=tg[(i,mode)]
            for k in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[k]==b[k],(i,mode,k)
            assert a['result']['status']==b['result']['status']
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metrics['records']=sum(a['authority_tables'].values());tt[mode].update(metrics);trss[mode]=max(trss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
            row['arms'][mode]=dict(status=a['result']['status'],**metrics)
        summary.append(row)
    rem={}
    for mode in study.MODES:
        rs=[r for r in residuals if r['mode']==mode]
        rem[mode]=dict(events=len(rs),with_exclusions=sum(r['exclusions']>0 for r in rs),with_untested_complements=sum(bool(r['exclusions_with_untested_complement']) for r in rs),
            exclusions=sum(r['exclusions'] for r in rs),untested_complements=sum(len(r['exclusions_with_untested_complement']) for r in rs))
    analysis=dict(coverage=coverage,census_totals=totals,census_counts=counts,census_peaks=peaks,census_peak_rss_bytes=rss,checked_probe_proofs=trace_checks,
        remaining=rem,new_roots=len(cases),not_previously_certified=sum(c['snapshot_answer']=='unknown' for c in cases),
        trial_totals=tt,trial_max_rss_bytes=trss,trial_summary=summary,trial_statuses={m:dict(Counter(r['arms'][m]['status'] for r in summary)) for m in tt},
        unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations']+['Trial-byte totals use independent databases and may duplicate shared records. The native compiler expands guarded unit reasoning to source-only splits; it does not retain extended clauses as axioms.'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        wide_guard_probes={k:old.binding(out/(k+'.json')) for k in ('protocol','censuses','cases','comparisons','remaining-probes','analysis')})
    cp['wide_guard_probes']['supplemental_archives']=archives;base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(coverage=coverage,totals=totals,remaining=rem,trials=tt,archives=len(audits))),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','70c12a87:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1875 tests in .*\n\nOK',full) and re.search(r'Ran 18 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['wide_guard_probes']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1875,focused_tests=18,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1040,final_sources=len(cp['source_fingerprints']),prior_manifests=180,prior_artifacts=22276,archive_audits=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=181,next_artifacts=22276+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
