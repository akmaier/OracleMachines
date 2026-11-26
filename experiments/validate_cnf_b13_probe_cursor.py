#!/usr/bin/env python3
"""Check joint-bank construction, three original proof histories and total cost."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip, re, subprocess, sys, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b13_probe_cursor as study
from experiments.validate_cnf_b12_progress_order import independent as lower_independent
from solver.test_cnf_b13_probe_cursor import independent
base=study.base;old=study.old;c=study.candidate
METRICS=('reconstruction_seconds','discovery_seconds','verification_seconds','persistence_seconds','complete_seconds','record_bytes')


def compose(bank,probes,counts):
    clauses=tuple(sorted(set(bank)|{(-r['assumption'],) for r in probes}))
    fixed,trace,conflict=c.engine.native.propagate(clauses,counts)
    assert conflict is None,'New contradiction needs source-only native certification before publication'
    cl=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
    assert c.engine.prior.check_closure(clauses,cl,counts)==fixed
    return cl



def followup(out, protocol, seeds, initial_events):
    plan=base.load(out/'followup-plan.json'); old.bound(plan['initial_censuses']); assert base.sha(plan['runner_source']['path'])==plan['runner_source']['sha256']
    q=base.load(out/'followup/protocol.json'); assert old.bound(q['followup_plan'])==plan
    assert q==dict(protocol,orders=plan['orders'],followup_plan=q['followup_plan'])
    assert plan['orders']==[list(study.MODES[i:]+study.MODES[:i]) for i in range(4)]
    samples=base.load(out/'followup/censuses.json')['samples']; assert len(samples)==len(protocol['targets'])*16
    totals={m:Counter() for m in study.MODES}; rss=Counter(); groups={}; events={}
    for sample in samples:
        report=old.bound(sample); mode=sample['mode']; target=sample['target']
        assert report['mode']==mode and report['target']==target
        groups.setdefault((target,mode),[]).append(report)
        rows=old.bound(report['events'])['rows']; assert {r['event'] for r in rows}=={e for t,e in seeds if t==target}
        for row in rows:
            key=target,row['event']; prior,result=initial_events[key,mode][0]
            assert old.bound(row['result'])==result and row['root']==seeds[key]['root']
            assert row['record_bytes']==Path(row['result']['path']).stat().st_size==prior['record_bytes']
            for field in ('counts','verification_counts','reconstruction_counts'):assert row[field]==prior[field]
            vc=Counter(); study.check(study.arguments(seeds[key]),seeds[key],mode,result,vc)
            assert dict(vc)==row['verification_counts']
            events.setdefault((key,mode),[]).append(row)
    for (target,mode),reports in groups.items():
        assert len(reports)==4
        for report in reports:
            for k in ('counts','verification_counts','reconstruction_counts','record_bytes'):assert report[k]==reports[0][k]
            for k in METRICS:totals[mode][k]+=report[k]/4
            rss[mode]=max(rss[mode],report['peak_rss_bytes'])
    comparisons={other:{metric:dict(improved=sum(sum(r[metric] for r in events[key,'reuse'])<sum(r[metric] for r in events[key,other]) for key in seeds),regressed=[list(key) for key in seeds if sum(r[metric] for r in events[key,'reuse'])>sum(r[metric] for r in events[key,other])]) for metric in METRICS if metric!='complete_seconds'} for other in ('source','unseen','matched')}
    return dict(plan=old.binding(out/'followup-plan.json'),censuses=old.binding(out/'followup/censuses.json'),repetitions=4,totals=totals,peak_rss_bytes=rss,comparisons=comparisons,
        limitations='Follow-up motivated by initial timing variation, declared before this measurement. All initial data retained. Tests finished before this census; validation is additional.')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(211,30962)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b13_probe_cursor.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1179 and Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    seeds={(r['target'],r['event']):r for r in study.prior.load_frontier(p['seeds'])};assert len(seeds)==14
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert pilot.keys()==seeds.keys()
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*8
    events={};groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};rss=Counter()
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];target=sample['target'];assert report['mode']==mode and report['target']==target
        groups.setdefault((target,mode),[]).append(report);rows=old.bound(report['events'])['rows'];assert {r['event'] for r in rows}=={e for t,e in seeds if t==target}
        for row in rows:
            key=row['target'],row['event'];seed=seeds[key];result=old.bound(row['result']);vc=Counter()
            assert row['root']==seed['root'] and row['record_bytes']==Path(row['result']['path']).stat().st_size
            study.check(study.arguments(seed),seed,mode,result,vc);assert dict(vc)==row['verification_counts']
            events.setdefault((key,mode),[]).append((row,result))
    for (target,mode),(a,b) in groups.items():
        for k in ('counts','reconstruction_counts','verification_counts','record_bytes'):assert a[k]==b[k]
        for k in METRICS:totals[mode][k]+=(a[k]+b[k])/2
        counts[mode].update(a['counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    deltas=[];diagnostics=[];failures=[];changed=[];exhausted=[];feedback_seconds=0.0
    for target in p['targets']:
        source,ts,refs,original_events=study.inputs(p,target)
        for ref,seed in refs:
            key=target,ref['event'];args=study.arguments(seed);kw=study.options(seed);rc=Counter()
            _,_,state=study.bind(source,ts,ref,original_events[ref['event']],rc)
            assert list(map(list,state['local']))==seed['final_source'] and [h['template'] for h in state['hints']]==seed['templates']
            for mode in study.MODES:
                (a,pa),(b,pb)=events[key,mode];assert pa==pb and pa['program']['status']=='unresolved'
                for field in ('counts','verification_counts','reconstruction_counts'):assert a[field]==b[field]
                assert a['reconstruction_counts']==dict(rc)
                cc=Counter();r=study.search(args,seed,mode,cc,p['limits']);assert r==pa and dict(cc)==a['counts']
                assert r==pilot[key]['arms'][mode]['result'] and dict(cc)==pilot[key]['arms'][mode]['counts']
            ur,result=events[key,'reuse'][0];sr,source_result=events[key,'source'][0];nr,unseen_result=events[key,'unseen'][0]
            assert result==events[key,'matched'][0][1]
            tick=time.perf_counter();prepared=independent(args,kw,result)
            assert prepared==c.validate(*args,**kw,result=result,counts=Counter())
            for mode,r in (('source',source_result),('unseen',unseen_result)):
                lower=lower_independent(args[:24],study.prior.options(seed),r,mode)[0]
                assert lower==prepared[:27]
                assert lower==c.shared.prior.validate(*args[:24],**study.prior.options(seed),ordering=mode,result=r,counts=Counter())
            own=compose(prepared[27],result['program']['probes'],Counter())
            joint=compose(prepared[27],result['program']['probes']+source_result['program']['probes']+unseen_result['program']['probes'],Counter())
            elapsed=time.perf_counter()-tick;feedback_seconds+=elapsed;oldfixed=dict(kw['combined_closure']['assignment'])
            assert oldfixed.items()<=dict(own['assignment']).items()<=dict(joint['assignment']).items()
            additions=sorted([v,b] for v,b in dict(joint['assignment']).items() if v not in oldfixed)
            source_new=sorted({r['assumption'] for r in source_result['program']['probes']}-{r['assumption'] for r in args[24]['program']['probes']})
            unseen_new=sorted({r['assumption'] for r in unseen_result['program']['probes']}-{r['assumption'] for r in args[25]['program']['probes']})
            b13_new=[r['assumption'] for r in result['program']['probes']]
            if source_new or unseen_new or b13_new:failures.append(dict(target=target,event=key[1],b13=b13_new,source_continuation_new=source_new,unseen_continuation_new=unseen_new))
            before_bank,_=c.engine.prior.residual_bank(prepared[27],oldfixed,Counter())
            after_clauses=tuple(sorted(set(prepared[27])|{(-r['assumption'],) for r in result['program']['probes']+source_result['program']['probes']+unseen_result['program']['probes']}))
            after_bank,_=c.engine.prior.residual_bank(after_clauses,dict(joint['assignment']),Counter())
            locations={mode:{str(lit):(book['cursor']['completed'].index(lit) if lit in book['cursor']['completed'] else None) for lit in source_new} for mode,book in (('source',source_result),('unseen',unseen_result),('b13',result))}
            if key==(67,63):assert locations==dict(source={'-119':103,'-116':105},unseen={'-119':None,'-116':None},b13={'-119':None,'-116':None})
            diagnostics.append(dict(target=target,event=key[1],joint_added=additions,b13_added=sorted(set(dict(own['assignment']))-set(oldfixed)),source_new_failure_positions_zero_based=locations,seconds=elapsed,
                residual_before=dict(clauses=len(before_bank),literals=sum(map(len,before_bank)),variables=len({abs(l) for cl in before_bank for l in cl})),
                residual_after=dict(clauses=len(after_bank),literals=sum(map(len,after_bank)),variables=len({abs(l) for cl in after_bank for l in cl}))))
            deltas.append(dict(target=target,event=key[1],b13_result=ur['result'],b12_source_continuation_result=sr['result'],b12_unseen_continuation_result=nr['result'],b13_feedback_closure=own,b13_joint_closure=joint))
            if not ur['counts'].get('b13_imported_cursors'):changed.append(list(key))
            if result['program']['reason']=='complete':exhausted.append(list(key))
    assert changed==[[67,63]] and len(exhausted)==12
    assert failures==[dict(target=67,event=63,b13=[],source_continuation_new=[-119,-116],unseen_continuation_new=[-68])]
    assert counts['reuse']['b13_imported_cursors']==13 and counts['reuse']['context_preparations']==14
    assert counts['reuse']['b13_histories_checked']==42
    tick=time.perf_counter();study.compact(out/'remaining-overlay.json',dict(parent=p['seeds'],rows=deltas));binding=old.binding(out/'remaining-overlay.json');loaded=study.load_frontier(binding)
    for row in loaded:
        key=row['target'],row['event'];assert {k:row[k] for k in seeds[key]}==seeds[key]
        for field,mode in (('b13_result','reuse'),('b12_source_continuation_result','source'),('b12_unseen_continuation_result','unseen')):assert old.bound(row[field])==events[key,mode][0][1]
    export_seconds=time.perf_counter()-tick;deps=set();current=binding
    fields=('b8_comparison_result','b9_result','b10_result','b9_continuation_result','b11_result','b10_comparison_result','b12_source_result','b12_unseen_result','b11_continuation_result','b13_result','b12_source_continuation_result','b12_unseen_continuation_result')
    while True:
        payload=old.bound(current)
        if current!=binding:deps.add(current['path'])
        for row in payload['rows']:
            for field in fields:
                if field in row:old.bound(row[field]);deps.add(row[field]['path'])
        if 'parent' not in payload:break
        current=payload['parent']
    comparisons={other:{metric:dict(improved=sum(sum(r[metric] for r,_ in events[key,'reuse'])<sum(r[metric] for r,_ in events[key,other]) for key in seeds),regressed=[list(key) for key in seeds if sum(r[metric] for r,_ in events[key,'reuse'])>sum(r[metric] for r,_ in events[key,other])]) for metric in METRICS if metric!='complete_seconds'} for other in ('source','unseen','matched')}
    followup_analysis=followup(out,p,seeds,events)
    base.write(out/'followup-analysis.json',followup_analysis)
    analysis=dict(followup=old.binding(out/'followup-analysis.json'),events=14,coverage=dict(before=232,after=232,total=246),remaining_events=14,changed_events=changed,new_failures=failures,feedback=diagnostics,feedback_seconds=feedback_seconds,
        exhausted_events=exhausted,unfinished_events=[list(k) for k in seeds if list(k) not in exhausted],census_totals=totals,census_counts=counts,peak_rss_bytes=rss,comparisons=comparisons,
        overlay_export_reload_seconds=export_seconds,storage=dict(overlay_bytes=Path(binding['path']).stat().st_size,referenced_files=len(deps),referenced_bytes=sum(Path(f).stat().st_size for f in deps)),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,b13_probe_cursor={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','analysis')});cp['b13_probe_cursor']['remaining']=binding;base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=[],parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,failures=failures,feedback=diagnostics,storage=analysis['storage'])))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','ef2336f6:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2136 tests in .*\n\nOK',full) and re.search(r'Ran 36 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b13_probe_cursor']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2136,focused_tests=36,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1175,final_sources=len(cp['source_fingerprints']),prior_manifests=211,prior_artifacts=30962,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=212,next_artifacts=30962+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
