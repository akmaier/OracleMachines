#!/usr/bin/env python3
"""Audit proof-support transport, frozen controls, native archives and lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_layered_feedback as study
base=study.base;old=study.old;previous=study.previous


def deterministic_result(result):
    # The fresh solver embeds two wall-clock fields inside its verdict envelope.
    result=deepcopy(result);result.pop('solve_seconds',None)
    if isinstance(result.get('result'),dict):result['result'].pop('seconds',None)
    return result


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(185,24953)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_layered_feedback.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==32
    rows={m:{} for m in study.MODES};groups={};ct={m:Counter() for m in study.MODES};cc={m:Counter() for m in study.MODES};crss=Counter()
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];target=sample['target'];es=old.bound(r['events'])['rows']
        groups.setdefault((target,mode),[]).append(es)
        for e in es:
            assert e['counts'].get('unit_probes',0)==1 and e['counts'].get('probe_roots',0)==0
            assert e['counts'].get('probe_occurrence_visits',0)<=p['limits']['work_limit']
            if sample['repeat']==0:rows[mode][(target,e['event'])]=e
        ct[mode].update({k:r[k]/2 for k in ('discovery_seconds','reconstruction_seconds','complete_seconds')});cc[mode].update({k:v/2 for k,v in r['counts'].items()});crss[mode]=max(crss[mode],r['peak_rss_bytes'])
    for pair in groups.values():
        assert len(pair)==2
        assert [(e['root'],e['program'],e['counts'],e['reconstruction_counts']) for e in pair[0]]==[(e['root'],e['program'],e['counts'],e['reconstruction_counts']) for e in pair[1]]
    assert all(len(rs)==69 and rs.keys()==rows['base'].keys() for rs in rows.values())
    assert all(r['program']['reason']=='open' for r in rows['base'].values())
    states={};remaining=[];closures=[];closure_counts=Counter();closure_seconds=0.0
    pilot={(r['target'],r['event']):r for r in base.load(out/'pilot.json')['rows']};peaks={m:Counter() for m in study.MODES}
    for target in p['targets']:
        source,ts,refs,events=study.inputs(p,target)
        for ref in refs:
            key=(target,ref['event']);local,templates,state=study.bind(source,ts,ref,events[ref['event']],Counter());states[key]=(local,templates,ref,state)
            hints=[h['template'] for h in state['hints']]
            assert list(map(list,state['local']))==ref['saved_source'] and hints==ref['saved_templates']
            for mode in study.MODES:
                r=rows[mode][key];c=Counter();actual=study.candidate.discover(state['local'],hints,ref['seed'],ref['closure'],ref['new'],c,mode=mode,**p['limits'])
                assert actual==r['program']==pilot[key]['arms'][mode]['program'] and dict(c)==r['counts']==pilot[key]['arms'][mode]['counts']
                study.candidate.validate(state['local'],hints,ref['seed'],ref['closure'],ref['new'],actual,Counter())
                for k in ('probe_occurrence_visits','probe_index_peak_literals','probe_units'):peaks[mode][k]=max(peaks[mode][k],c.get(k,0))
                if mode=='feedback' and actual['status']!='refuted':
                    remaining.append(dict(target=target,event=ref['event'],root=ref['root'],reason=actual['reason'],old_exclusions=len(ref['seed']['probes']),new_exclusions=len(ref['new']['probes']),counts=r['counts']))
                    if actual['reason']=='open':
                        tick=time.perf_counter();dc=Counter();prepared=study.candidate.prepare(state['local'],hints,ref['seed'],ref['closure'],ref['new'],dc)
                        fixed,trace,conflict=study.native.propagate(prepared[5],dc);assert conflict is None
                        closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
                        assert study.candidate.prior.check_closure(prepared[5],closure,dc)==fixed
                        oldfixed=dict(ref['closure']['assignment']);assert oldfixed.items()<=fixed.items()
                        assert len(fixed)==r['counts'].get('probe_units',0)
                        extra=set(fixed)-set(oldfixed);new_variables={abs(row['assumption']) for row in ref['new']['probes']}
                        closures.append(dict(target=target,event=ref['event'],root=ref['root'],final_source=state['local'],templates=hints,seed=ref['seed'],closure=ref['closure'],new=ref['new'],
                            next_closure=closure,additional_variables=sorted(extra),additional_beyond_new_exclusions=sorted(extra-new_variables),counts=dict(dc)))
                        closure_counts.update(dc);closure_seconds+=time.perf_counter()-tick
    study.compact(out/'remaining.json',dict(rows=remaining))
    study.compact(out/'remaining-closures.json',dict(rows=closures,counts=dict(closure_counts),seconds=closure_seconds,scope='Extra scan-based diagnostic outside timed discovery. next_closure reasons are bound to the second feedback bank; closure remains the old first-bank trace. Neither is a SAT verdict. Preserve all proof layers.'))
    cd=base.load(out/'cases.json');cases=[old.bound(b) for b in cd['cases']]
    success=set().union(*({r['root'] for r in rs.values() if r['program']['status']=='refuted'} for rs in rows.values()))
    assert {c['root'] for c in cases}==success and len(cases)==len(success)
    earlier={old.bound(b)['root'] for directory in (study.PARENT,Path('experiments/results/cnf-probe-feedback'),Path('experiments/results/cnf-probe-support')) for b in base.load(directory/'cases.json')['cases']};assert not success&earlier
    plans=[]
    for case in cases:
        local,templates,ref,state=states[(case['target'],case['event'])]
        assert case['source']==list(map(list,local)) and case['templates']==templates and case['prefix']==ref['program'] and case['seed']==ref['seed'] and case['closure']==ref['closure'] and case['new']==ref['new']
        assert case['program']==rows[case['mode']][(case['target'],case['event'])]['program']
        c=Counter();hints=[h['template'] for h in state['hints']]
        prepared=study.candidate.validate(state['local'],hints,case['seed'],case['closure'],case['new'],case['program'],c)
        plan=study.candidate._plan(state['local'],hints,case['seed'],case['new'],case['program'],prepared,c)
        if plan is not None:plan={k:v for k,v in plan.items() if k!='prepared'}
        plans.append(dict(name=case['name'],root=case['root'],plan=plan,counts=dict(c)))
    study.compact(out/'support-plans.json',dict(rows=plans))
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==len(cases)*4;tg={};audits={};archives=[]
    for sample in trials:
        r=old.bound(sample);index=sample['index'];mode=sample['mode'];assert r['case']==cd['cases'][index] and r['mode']==mode
        if mode=='layered':assert r['result']['status']=='unsat'
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
    totals={m:Counter() for m in ('fresh','layered')};counts={m:Counter() for m in totals};rss=Counter();summary=[]
    for i,case in enumerate(cases):
        row=dict(name=case['name'],root=case['root'],snapshot_answer=case['snapshot_answer'],arms={})
        for mode in totals:
            a,b=tg[(i,mode)]
            assert deterministic_result(a['result'])==deterministic_result(b['result']),(i,mode,'verdict')
            for key in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[key]==b[key],(i,mode,key)
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metrics['records']=sum(a['authority_tables'].values());totals[mode].update(metrics);counts[mode].update(a['counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
            row['arms'][mode]=dict(status=a['result']['status'],**metrics)
        continuation=sum(next(e['discovery_seconds']+e['reconstruction_seconds'] for e in es if e['event']==case['event']) for es in groups[(case['target'],case['mode'])])/2
        row['continuation_seconds']=continuation
        row['layered_with_continuation_seconds']=continuation+row['arms']['layered']['complete_seconds']
        summary.append(row)
    comparisons={}
    for control in ('fresh',):
        comparisons[control]={k:dict(improved=sum(r['arms']['layered'][k]<r['arms'][control][k] for r in summary),
            equal=sum(r['arms']['layered'][k]==r['arms'][control][k] for r in summary),
            regressed=[r['name'] for r in summary if r['arms']['layered'][k]>r['arms'][control][k]]) for k in ('solve_seconds','complete_seconds','record_bytes')}
    analysis=dict(cases=len(cases),totals=totals,counts=counts,peak_rss_bytes=rss,summary=summary,comparisons=comparisons,
        partial_cost_accounting=dict(representative_continuation_seconds=sum(r['continuation_seconds'] for r in summary),layered_with_continuation_seconds=sum(r['layered_with_continuation_seconds'] for r in summary),fresh_complete_seconds=totals['fresh']['complete_seconds'],scope='Representative positive cases only. Excludes seed acquisition, unresolved-case fallback, startup/loading, closure diagnostics and final audits. Not a complete workload comparison.'),
        census_totals=ct,census_counts=cc,census_rss=crss,coverage={m:dict(Counter(r['program']['reason'] for r in rows[m].values())) for m in study.MODES},
        remaining=dict(events=len(remaining),with_new_exclusions=sum(r['new_exclusions']>0 for r in remaining),new_exclusions=sum(r['new_exclusions'] for r in remaining),old_exclusions=sum(r['old_exclusions'] for r in remaining)),
        census_peaks=peaks,open_closures=dict(events=len(closures),assignments=sum(len(r['next_closure']['units']) for r in closures),additional_assignments=sum(len(r['additional_variables']) for r in closures),additional_beyond_new_exclusions=sum(len(r['additional_beyond_new_exclusions']) for r in closures),diagnostic_seconds=closure_seconds),
        previously_unknown=sum(c['snapshot_answer']=='unknown' for c in cases),
        support_plans=dict(fallbacks=sum(r['plan'] is None for r in plans)),
        unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        layered_feedback={k:old.binding(out/(k+'.json')) for k in ('protocol','censuses','cases','comparisons','remaining','remaining-closures','support-plans','analysis')})
    cp['layered_feedback']['supplemental_archives']=archives;base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,comparisons=comparisons,plans=analysis['support_plans'],archives=len(audits))),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','6b700720:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1911 tests in .*\n\nOK',full) and re.search(r'Ran 46 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['layered_feedback']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1911,focused_tests=46,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1064,final_sources=len(cp['source_fingerprints']),prior_manifests=185,prior_artifacts=24953,archive_audits=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=186,next_artifacts=24953+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
