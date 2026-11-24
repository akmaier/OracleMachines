#!/usr/bin/env python3
"""Audit immutable source preparation, exact programs/proofs and saved lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_prepared_source as study
base=study.base;old=study.old;previous=study.previous


def equivalent(a,b,source,ts):
    assert a['program']==b['program']
    actual=Counter(b['counts']);rounds=actual['rounds']
    assert actual['source_preparations']==1 and actual['prepared_templates']==len(ts)
    for k in study.EXTRA:actual.pop(k,None)
    static=study.static_counts(source,ts)
    actual.update({k:v*rounds for k,v in static.items()})
    assert actual==Counter(a['counts']),(actual,Counter(a['counts']))


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(178,21373)
    correction=p['archive_helper_correction'];initial=old.bound(correction['initial_protocol'])
    binding=correction['initial_driver'];assert base.sha(binding['path'])==binding['sha256']
    before=Path(binding['path']).read_text()
    assert before.replace("base.archive(path,dest/'proofs.sqlite.gz')","base.archive(path,dest)")==Path(study.__file__).read_text()
    expected=deepcopy(initial);expected['source_fingerprints']['experiments/compare_cnf_shortening_prepared_source.py']=base.sha(study.__file__)
    expected['archive_helper_correction']=correction;assert expected==p
    sources={**p['source_fingerprints'],'experiments/validate_cnf_shortening_prepared_source.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==32
    groups={};rows={};totals={m:Counter() for m in study.MODULES};counts={m:Counter() for m in study.MODULES};rss=Counter()
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];target=sample['target'];assert r['mode']==mode and r['target']==target
        es=old.bound(r['events'])['rows'];groups.setdefault((target,mode),[]).append(es)
        for e in es:
            c=e['counts'];assert c['rounds']<=33 and c.get('reach_roots',0)<=64
            assert sum(c.get(k,0) for k in ('reach_edge_visits','reuse_invalidation_checks','cache_admission_edge_checks'))<=16384
            if sample['repeat']==0:rows[(target,e['event'],mode)]=e
        totals[mode].update({k:r[k]/2 for k in ('discovery_seconds','binding_seconds','complete_seconds')})
        counts[mode].update({k:v/2 for k,v in r['counts'].items()});rss[mode]=max(rss[mode],r['peak_rss_bytes'])
    for pair in groups.values():
        assert len(pair)==2
        assert [(e['root'],e['program'],e['counts']) for e in pair[0]]==[(e['root'],e['program'],e['counts']) for e in pair[1]]
    assert len(rows)==1230
    checks=0;classes={};unique=set();expected_cases=[]
    for target in p['targets']:
        source,ts,refs,events=study.reuse.inputs(p,target)
        oldrows=old.bound(base.load(study.PARENT/f'census-{target}-priority_endpoint-0/report.json')['events'])['rows']
        frozen={r['event']:r for r in oldrows}
        for ref in refs:
            a=rows[(target,ref['event'],'control')];b=rows[(target,ref['event'],'prepared')]
            assert a['root']==b['root']==ref['source_root'] and a['program']==frozen[ref['event']]['program']
            expected=Counter(frozen[ref['event']]['counts']);expected.pop('filter_incoming_edges',None);expected.pop('filter_adjacency_vertices',None)
            assert expected==Counter(a['counts'])
            local,hints,_=previous.local_hints(source,ts,events[ref['event']],Counter());templates=[h['template'] for h in hints]
            equivalent(a,b,local,templates)
            if b['program']['status']=='refuted':
                study.candidate.validate(local,templates,b['program'],Counter());checks+=1
                if b['root'] not in unique:
                    unique.add(b['root']);expected_cases.append(dict(source=[list(cl) for cl in local],templates=templates,root=b['root'],program=b['program'],target=target,event=ref['event']))
            label='one_state' if b['counts']['rounds']==1 else 'multiple_states'
            cl=classes.setdefault(label,dict(events=0,control_seconds=0,prepared_seconds=0));cl['events']+=1
            for mode in study.MODULES:
                es=groups[(target,mode)];cl[mode+'_seconds']+=sum(next(e['discovery_seconds'] for e in group if e['event']==ref['event']) for group in es)/2
    cases=base.load(out/'cases.json')['cases'];assert cases==expected_cases and checks==266 and len(cases)==173
    reports=[old.bound(b) for b in base.load(out/'streams.json')['samples']];a,b=reports
    assert [r['mode'] for r in reports]==['control','prepared']
    for key in ('digest','authority_tables','record_bytes','warm_counts'):assert a[key]==b[key],key
    assert a['archive']['database_sha256']==b['archive']['database_sha256']
    for case,ar,br in zip(cases,a['rows'],b['rows']):
        assert ar['root']==br['root']==case['root'] and ar['result']==br['result'] and ar['compile_counts']==br['compile_counts']
    assert len(a['rows'])==len(b['rows'])==173
    audits=[];seen=set();stream_totals={}
    for r in reports:
        archive=r['archive'];assert base.sha(archive['path'])==archive['sha256'];key=archive['database_sha256']
        if key not in seen:
            seen.add(key)
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(archive,path);stored,readers=previous.audit(path,cases,[r['result'] for r in r['rows']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits.append(dict(archive=archive,readers=readers))
        stream_totals[r['mode']]=dict(discovery_seconds=sum(e['discovery_seconds'] for e in r['rows']),compile_seconds=sum(e['compile_seconds'] for e in r['rows']),
            **{k:r[k] for k in ('warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes','authority_tables','peak_rss_bytes')})
    edits=base.load(out/'edits.json');oldedits=old.bound(edits['cases_binding']);assert len(edits['rows'])==192
    erows={(r['index'],r['mode']):r for r in edits['rows']};eref={r['index']:r for r in oldedits['rows'] if r['mode']=='priority_endpoint' and r['repeat']==0}
    for i,case in enumerate(oldedits['cases']):
        equivalent(erows[(i,'control')],erows[(i,'prepared')],case['source'],case['templates'])
        assert erows[(i,'control')]['program']==eref[i]['program']
    scaling=base.load(out/'scaling.json')['rows'];assert len(scaling)==36;sg={}
    for r in scaling:sg.setdefault((r['depth'],r['padding'],r['repeat']),{})[r['mode']]=r
    for (depth,padding,repeat),rs in sg.items():equivalent(rs['control'],rs['prepared'],*previous.chain(depth,padding))
    profiles=base.load(out/'profiles.json');assert profiles['modes']['control']['program']==profiles['modes']['prepared']['program']
    expansion=base.load(out/'expansion.json')['rows']
    for i,r in enumerate(expansion):
        assert base.sha(r['archive']['path'])==r['archive']['sha256']
        if i:assert r['added_records']==1 and r['compile_counts']['support_hits']==1
    analysis=dict(events=615,recognized_events=checks,recognized_roots=len(cases),coverage_changes=0,census_totals=totals,census_counts=counts,census_peak_rss_bytes=rss,
        conditioning_groups=classes,
        peak_prepared_slots=max(r['counts'].get('prepared_input_slots',0) for r in rows.values()),native_streams=stream_totals,unique_archive_audits=len(audits),
        edit_cases=96,expansion_steps=len(expansion),sources=len(sources),limitations=p['limitations'])
    # Record the exact four kinds of removed static validation work explicitly.
    analysis['removed_counts']={k:counts['control'][k]-counts['prepared'][k] for k in ('normalization_literal_visits','guard_input_literals','template_checked_reason_literals','templates_checked')}
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        shortening_prepared_source={k:old.binding(out/(k+'.json')) for k in ('protocol','censuses','cases','streams','edits','profiles','scaling','expansion','analysis')})
    cp['shortening_prepared_source']['supplemental_archives']=[r['archive'] for r in reports]
    base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=audits,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(analysis),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','b99a4ebb:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1861 tests in .*\n\nOK',full) and re.search(r'Ran 19 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['shortening_prepared_source']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1861,focused_tests=19,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1032,final_sources=len(cp['source_fingerprints']),prior_manifests=178,prior_artifacts=21373,archive_audits=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=179,next_artifacts=21373+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
