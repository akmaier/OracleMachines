#!/usr/bin/env python3
"""Audit exact batch snapshots, bounded rounds, cold checking and frontier gain."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b12_continuation_batch as study
from experiments.validate_cnf_b12_progress_order import independent
from solver.test_cnf_b13_probe_cursor import independent as b13_independent
base=study.base;old=study.old;c=study.candidate
METRICS=('reconstruction_seconds','discovery_seconds','verification_seconds','persistence_seconds','complete_seconds','record_bytes')
SEARCH=('probe_roots','probe_occurrence_visits','unit_probes','probe_index_literals','probe_index_builds','probe_initialization_clauses','probe_units','probe_queue_insertions','probe_open_closures','cursor_completed_probes','cursor_lifted_steps','cursor_promoted_probes','cursor_base_probes','cursor_interrupted_probes','b12_continued_cursors')


def compose(bank,probes,counts):
    clauses=tuple(sorted(set(bank)|{(-p['assumption'],) for p in probes}))
    fixed,trace,conflict=c.prior.engine.native.propagate(clauses,counts)
    assert conflict is None,'A contradiction requires native source-only certification before coverage publication'
    cl=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
    assert c.prior.engine.prior.check_closure(clauses,cl,counts)==fixed
    return cl,clauses


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(212,31573)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b12_continuation_batch.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1183 and Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    seeds={(r['target'],r['event']):r for r in study.prior.load_frontier(p['seeds'])};assert len(seeds)==14
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert pilot.keys()==seeds.keys()
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*16
    events={};groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};vcounters={m:Counter() for m in study.MODES};rss=Counter()
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];target=sample['target'];assert report['mode']==mode and report['target']==target
        groups.setdefault((target,mode),[]).append(report);rows=old.bound(report['events'])['rows'];assert {r['event'] for r in rows}=={e for t,e in seeds if t==target}
        for row in rows:
            key=target,row['event'];results=[old.bound(b) for b in row['results']];seed=seeds[key];vc=Counter()
            assert row['root']==seed['root'] and row['record_bytes']==sum(Path(b['path']).stat().st_size for b in row['results'])
            study.check(study.arguments(seed),seed,mode,results,vc);assert dict(vc)==row['verification_counts']
            events.setdefault((key,mode),[]).append((row,results))
    for (target,mode),reports in groups.items():
        assert len(reports)==4
        for r in reports:
            for k in ('counts','reconstruction_counts','verification_counts','record_bytes'):assert r[k]==reports[0][k]
            for k in METRICS:totals[mode][k]+=r[k]/4
            rss[mode]=max(rss[mode],r['peak_rss_bytes'])
        counts[mode].update(reports[0]['counts']);vcounters[mode].update(reports[0]['verification_counts'])
    deltas=[];diagnostics=[];failures=[];feedback_seconds=0.0
    for target in p['targets']:
        source,ts,refs,original_events=study.inputs(p,target)
        for ref,seed in refs:
            key=target,ref['event'];args=study.arguments(seed);kw=study.options(seed);rc=Counter()
            _,_,state=study.bind(source,ts,ref,original_events[ref['event']],rc)
            assert list(map(list,state['local']))==seed['final_source'] and [h['template'] for h in state['hints']]==seed['templates']
            for mode in study.MODES:
                ordering,arm=mode.split('_',1);samples=events[key,mode];row,results=samples[0]
                for other,books in samples:
                    assert books==results
                    for field in ('counts','verification_counts','reconstruction_counts'):assert other[field]==row[field]
                assert row['reconstruction_counts']==dict(rc)
                cc=Counter();actual=study.search(args,seed,mode,cc,p['limits']);assert actual==results and dict(cc)==row['counts']
                arm_pilot=pilot[key]['arms'][ordering];assert results==arm_pilot['results']
                assert dict(cc)==arm_pilot['counts' if arm=='batch' else 'baseline_counts']
                assert results[-1]['program']['reason']=='complete' and all(r['program']['status']=='unresolved' for r in results)
                assert len(results)==(3 if key in ((37,39),(67,63)) else 1)
                for r in results:
                    prepared=independent(args,kw,r,ordering)[0]
                    assert prepared==c.prior.prior.validate(*args,**kw,ordering=ordering,result=r,counts=Counter())
                baseline=events[key,ordering+'_separate'][0]
                assert results==baseline[1] and row['verification_counts']==baseline[0]['verification_counts']
                for name in SEARCH:assert row['counts'].get(name,0)==baseline[0]['counts'].get(name,0),(key,mode,name)
            tick=time.perf_counter();prepared=b13_independent(study.prior.arguments(seed),study.prior.options(seed),old.bound(seed['b13_result']))
            sr,source_books=events[key,'source_batch'][0];ur,unseen_books=events[key,'unseen_batch'][0]
            assert prepared[:27]==independent(args,kw,source_books[-1],'source')[0]
            probes=source_books[-1]['program']['probes']+unseen_books[-1]['program']['probes']+old.bound(seed['b13_result'])['program']['probes']
            joint,clauses=compose(prepared[27],probes,Counter());oldfixed=dict(seed['b13_joint_closure']['assignment'])
            assert oldfixed.items()<=dict(joint['assignment']).items()
            additions=sorted([v,b] for v,b in dict(joint['assignment']).items() if v not in oldfixed)
            prior_probes=[p for field in ('b12_source_continuation_result','b12_unseen_continuation_result','b13_result') for p in old.bound(seed[field])['program']['probes']]
            old_clauses=tuple(sorted(set(prepared[27])|{(-r['assumption'],) for r in prior_probes}))
            assert c.prior.engine.prior.check_closure(old_clauses,seed['b13_joint_closure'],Counter())==oldfixed
            before,_=c.prior.engine.prior.residual_bank(old_clauses,oldfixed,Counter());after,_=c.prior.engine.prior.residual_bank(clauses,dict(joint['assignment']),Counter())
            oldfail={p['assumption'] for p in prior_probes}
            novel=sorted({p['assumption'] for p in probes}-oldfail)
            if novel:failures.append(dict(target=target,event=key[1],globally_new_failures=novel))
            source_new=sorted({r['assumption'] for r in source_books[-1]['program']['probes']}-{r['assumption'] for r in study.saved_cursor(seed,'source')['probes']})
            unseen_new=sorted({r['assumption'] for r in unseen_books[-1]['program']['probes']}-{r['assumption'] for r in study.saved_cursor(seed,'unseen')['probes']})
            elapsed=time.perf_counter()-tick;feedback_seconds+=elapsed
            diagnostics.append(dict(target=target,event=key[1],joint_added=additions,source_new=source_new,unseen_new=unseen_new,seconds=elapsed,
                residual_before=dict(clauses=len(before),literals=sum(map(len,before)),variables=len({abs(l) for cl in before for l in cl})),
                residual_after=dict(clauses=len(after),literals=sum(map(len,after)),variables=len({abs(l) for cl in after for l in cl}))))
            deltas.append(dict(target=target,event=key[1],b12_batch_source_rounds=sr['results'],b12_batch_unseen_rounds=ur['results'],b12_batch_source_result=sr['results'][-1],b12_batch_unseen_result=ur['results'][-1],b12_batch_joint_closure=joint))
    assert failures==[dict(target=37,event=39,globally_new_failures=[32]),dict(target=67,event=63,globally_new_failures=[131])]
    for ordering in ('source','unseen'):
        batch=ordering+'_batch';sep=ordering+'_separate'
        assert counts[batch]['context_preparations']==14 and counts[sep]['context_preparations']==18 and counts[batch]['batch_rounds']==18
        assert counts[batch]['batch_prefix_preparations']==14 and vcounters[batch]==vcounters[sep]
    comparisons={order:{metric:dict(improved=sum(sum(r[metric] for r,_ in events[key,order+'_batch'])<sum(r[metric] for r,_ in events[key,order+'_separate']) for key in seeds),regressed=[list(key) for key in seeds if sum(r[metric] for r,_ in events[key,order+'_batch'])>sum(r[metric] for r,_ in events[key,order+'_separate'])]) for metric in METRICS if metric!='complete_seconds'} for order in ('source','unseen')}
    productive={mode:{metric:sum(sum(r[metric] for r,_ in events[key,mode])/4 for key in ((37,39),(67,63))) for metric in METRICS if metric!='complete_seconds'} for mode in study.MODES}
    tick=time.perf_counter();study.compact(out/'remaining-overlay.json',dict(parent=p['seeds'],rows=deltas));binding=old.binding(out/'remaining-overlay.json');loaded=study.load_frontier(binding)
    for row in loaded:
        key=row['target'],row['event'];assert {k:row[k] for k in seeds[key]}==seeds[key]
        for order in ('source','unseen'):
            assert [old.bound(b) for b in row['b12_batch_'+order+'_rounds']]==events[key,order+'_batch'][0][1]
    export_seconds=time.perf_counter()-tick;deps=set();current=binding
    while True:
        payload=old.bound(current)
        if current!=binding:deps.add(current['path'])
        for row in payload['rows']:
            for value in row.values():
                values=value if isinstance(value,list) else [value]
                for item in values:
                    if isinstance(item,dict) and 'path' in item and 'sha256' in item:old.bound(item);deps.add(item['path'])
        if 'parent' not in payload:break
        current=payload['parent']
    analysis=dict(events=14,coverage=dict(before=232,after=232,total=246),remaining_events=14,new_failures=failures,feedback=diagnostics,feedback_seconds=feedback_seconds,
        exhausted_b12_events=[list(k) for k in seeds],unfinished_b12_events=[],other_banks_not_exhausted=True,census_totals=totals,census_counts=counts,verification_counts=vcounters,
        peak_rss_bytes=rss,comparisons=comparisons,productive_case_stage_totals=productive,overlay_export_reload_seconds=export_seconds,
        storage=dict(overlay_bytes=Path(binding['path']).stat().st_size,referenced_files=len(deps),referenced_bytes=sum(Path(f).stat().st_size for f in deps)),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,b12_continuation_batch={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','analysis')});cp['b12_continuation_batch']['remaining']=binding;base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=[],parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,failures=failures,feedback=diagnostics,storage=analysis['storage'])))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','fd6176db:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2145 tests in .*\n\nOK',full) and re.search(r'Ran 36 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b12_continuation_batch']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2145,focused_tests=36,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1179,final_sources=len(cp['source_fingerprints']),prior_manifests=212,prior_artifacts=31573,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=213,next_artifacts=31573+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
