#!/usr/bin/env python3
"""Audit B10 joint search, source-only native certificates and retained frontiers."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b10_probe_cursor as study, cnf_joint_probe_feedback as frozen_feedback
base=study.base;old=study.old;c=study.candidate;feedback=study.feedback
from experiments.validate_cnf_layered_feedback import deterministic_result
METRICS=('reconstruction_seconds','discovery_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes')


def compose(bank,probes,counts):
    clauses=tuple(sorted(set(bank)|{(-r['assumption'],) for r in probes}))
    fixed,trace,conflict=c.engine.native.propagate(clauses,counts)
    assert conflict is None, 'New contradiction requires explicit native certification before coverage publication'
    closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
    assert c.engine.prior.check_closure(clauses,closure,counts)==fixed
    return closure


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items(): assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(206,29728)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b10_probe_cursor.py':base.sha(__file__)}
    for f,h in sources.items(): assert base.sha(f)==h,f
    assert len(sources)==1159
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    assert Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    assert Path(p['feedback_pilot_source']['path']).read_bytes()==Path(study.FILES[1]).read_bytes()
    for f,h in p['native_runner_correction'].items(): assert base.sha(f)==h,f
    initial=base.load(out/'initial-protocol.json')
    assert all(initial['source_fingerprints'][f]==h for f,h in p['source_fingerprints'].items() if f!=study.FILES[2])
    before=(out/'initial-compare.py').read_text();after=Path(study.FILES[2]).read_text()
    assert before[:before.index('def trial(')]==after[:after.index('def trial(')]
    seeds={(r['target'],r['event']):r for r in study.prior.load_frontier(p['seeds'])};assert len(seeds)==16
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert pilot.keys()==seeds.keys()
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*8
    events={};groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};rss=Counter()
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];target=sample['target'];assert report['mode']==mode and report['target']==target
        groups.setdefault((target,mode),[]).append(report);rows=old.bound(report['events'])['rows']
        assert {r['event'] for r in rows}=={e for t,e in seeds if t==target}
        for row in rows:
            key=row['target'],row['event'];seed=seeds[key];result=old.bound(row['result']);vc=Counter()
            assert row['root']==seed['root'] and row['record_bytes']==Path(row['result']['path']).stat().st_size
            study.check(study.arguments(seed),seed,mode,result,vc);assert dict(vc)==row['verification_counts']
            events.setdefault((key,mode),[]).append((row,result))
    for (target,mode),(a,b) in groups.items():
        for k in ('counts','reconstruction_counts','verification_counts','record_bytes'): assert a[k]==b[k]
        for k in METRICS: totals[mode][k]+=(a[k]+b[k])/2
        counts[mode].update(a['counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    failures=[];exhausted=[];changed=[];deltas=[];closure_rows=[];b9_diagnostics=[];gains=set();b9_gains=set();closure_seconds=0.0
    diagnostics={(r['target'],r['event']):r for r in base.load(out/'feedback-diagnostics.json')['rows']}
    b9pilot={(r['target'],r['event']):r for r in old.bound(p['b9_pilot'])['rows']}
    for target in p['targets']:
        source,ts,pairs,original_events=study.inputs(p,target)
        for ref,seed in pairs:
            key=target,ref['event'];args=study.arguments(seed);kw=study.options(seed);rc=Counter()
            actual=study.prior.prior.candidate.bind(source,ts,ref,original_events[ref['event']],rc)
            assert actual==study.prior.prior.prior.bind(source,ts,ref,original_events[ref['event']],Counter())
            assert list(map(list,actual[2]['local']))==seed['final_source'] and [h['template'] for h in actual[2]['hints']]==seed['templates']
            for mode in study.MODES:
                (a,pa),(b,pb)=events[key,mode];assert pa==pb
                for field in ('counts','verification_counts','reconstruction_counts'): assert a[field]==b[field]
                assert a['reconstruction_counts']==dict(rc)
                cc=Counter();result=study.search(args,seed,mode,cc,p['limits'])
                assert result==pa and dict(cc)==a['counts']
                if mode=='reuse': assert result==pilot[key]['result'] and dict(cc)==pilot[key]['counts']
                if mode=='b9': assert result==b9pilot[key]['result']
            a,result=events[key,'reuse'][0];b,comparison=events[key,'b9'][0]
            assert result==events[key,'matched'][0][1]
            if result['program']['reason']=='complete': exhausted.append(list(key))
            if not a['counts'].get('b10_imported_cursors'): changed.append(list(key))
            if result['program']['probes']: failures.append(dict(target=target,event=key[1],assumptions=[x['assumption'] for x in result['program']['probes']]))
            # Reconstruct every prior bank through the frozen B8 feedback path.
            frozen=frozen_feedback.prepare(*args[:19],closure=kw['closure'],counts=Counter())
            c.prior.prior.validate(*args[:18],closure=kw['closure'],result=args[20],counts=Counter())
            c.prior.validate(*args[:19],closure=kw['closure'],feedback_closure=kw['feedback_closure'],result=args[19],counts=Counter())
            entries=dict(zip(frozen[19],frozen[20]))
            for kind,book in (('b8_comparison_probe',args[20]['program']),('b9_probe',args[19]['program'])):
                for i,probe in enumerate(book['probes']): entries.setdefault((-probe['assumption'],),dict(kind=kind,index=i))
            clauses=tuple(sorted(entries));expected=(*frozen,clauses,[entries[cl] for cl in clauses])
            prepared=c.validate(*args,**kw,result=result,counts=Counter());assert prepared==expected
            c.engine.prior.check_program(prepared[0],prepared[21],result['program'],Counter())
            cc=Counter();program=feedback.discover(*args,result,**kw,counts=cc)
            assert program==diagnostics[key]['program'] and dict(cc)==diagnostics[key]['counts']
            full=feedback.validate(*args,result,**kw,program=program,counts=Counter())
            assert set(full[23])==set(prepared[21])|{(-x['assumption'],) for x in result['program']['probes']}
            if program['status']=='refuted': gains.add(key)
            # Continuing B9 is a separate coverage comparison on its own original bank.
            tick=time.perf_counter();bc=Counter()
            c.prior.validate(*args[:19],closure=kw['closure'],feedback_closure=kw['feedback_closure'],result=comparison,counts=bc)
            cmpbank=tuple(sorted(set(frozen[19])|{(-x['assumption'],) for x in comparison['program']['probes']}))
            fixed,trace,conflict=c.engine.native.propagate(cmpbank,bc)
            if conflict is not None:
                c.engine.frozen.check_trace(frozen[0],cmpbank,None,dict(units=trace,conflict=conflict),bc,256);b9_gains.add(key)
            b9_diagnostics.append(dict(target=target,event=key[1],units=trace,conflict=conflict,assignment=sorted([list(x) for x in fixed.items()]),counts=dict(bc),seconds=time.perf_counter()-tick))
            assert conflict==b9pilot[key]['conflict'] and trace==b9pilot[key]['units']
            if key in gains: continue
            tick=time.perf_counter();cc=Counter();closure=compose(prepared[21],result['program']['probes'],cc)
            oldfixed=dict(kw['joint_closure']['assignment']);assert oldfixed.items()<=dict(closure['assignment']).items()
            added=sorted(set(dict(closure['assignment']))-set(oldfixed));elapsed=time.perf_counter()-tick;closure_seconds+=elapsed
            deltas.append(dict(target=target,event=key[1],b10_result=a['result'],b9_continuation_result=b['result'],b10_feedback_closure=closure))
            closure_rows.append(dict(target=target,event=key[1],added_variables=added,seconds=elapsed,counts=dict(cc)))
    assert gains=={(28,18),(40,0)} and b9_gains=={(40,0)}
    assert counts['reuse']['b10_imported_cursors']==12 and len(changed)==4
    assert sum(len(r['assumptions']) for r in failures)==17 and len(exhausted)==11 and len(deltas)==14
    tick=time.perf_counter();study.compact(out/'remaining-overlay.json',dict(parent=p['seeds'],excluded=sorted(map(list,gains)),rows=deltas));binding=old.binding(out/'remaining-overlay.json')
    loaded=study.load_frontier(binding)
    for row in loaded:
        key=row['target'],row['event'];assert {k:row[k] for k in seeds[key]}==seeds[key]
        assert old.bound(row['b10_result'])==events[key,'reuse'][0][1] and old.bound(row['b9_continuation_result'])==events[key,'b9'][0][1]
    export_seconds=time.perf_counter()-tick
    # Enumerate transitive data dependencies; the old overlay retains all sixteen cases.
    parent_overlay=old.bound(p['seeds']);deps={p['seeds']['path'],parent_overlay['parent']['path']}
    deps.update(r[k]['path'] for r in parent_overlay['rows'] for k in ('b9_result','b8_comparison_result'))
    deps.update(r[k]['path'] for r in deltas for k in ('b10_result','b9_continuation_result'))
    expanded=[]
    for row in loaded:
        row=deepcopy(row)
        for key in ('b9_result','b8_comparison_result','b10_result','b9_continuation_result'): row[key]=old.bound(row[key])
        expanded.append(row)
    cd=base.load(out/'cases.json');cases=[old.bound(b) for b in cd['cases']]
    assert {(r['target'],r['event']) for r in cases}==gains and len({r['root'] for r in cases})==2
    known={(r['target'],r['event']):r for r in base.load('experiments/results/cnf-shortening-budget-frontier/residual-diagnosis.json')['rows']}
    for case in cases:
        key=case['target'],case['event'];seed=seeds[key];assert case['root']==seed['root'] and known[key]['snapshot_answer']=='unsat'
        assert base.encode(case['inputs'])==base.encode(study.arguments(seed)) and case['options']==study.options(seed)
        assert case['search']==events[key,'reuse'][0][1] and case['program']==diagnostics[key]['program']
        _,tail=feedback.frozen.bind_prefix(case['source'],case['templates'],case['prefix'],Counter())
        assert list(map(list,tail['local']))==seed['final_source'] and [h['template'] for h in tail['hints']]==seed['templates']
    groups={};audits={};archives=[]
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==12
    for sample in samples:
        report=old.bound(sample);i=sample['index'];mode=sample['mode'];case=cases[i]
        assert report['case']==cd['cases'][i] and report['mode']==mode
        assert report['result']['status']==('unresolved' if (case['target'],case['event'])==(40,0) and mode=='fresh' else 'unsat')
        a=report['archive'];assert base.sha(a['path'])==a['sha256'];key=a['sha256'],case['root']
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';study.previous.restore_archive(a,path)
                stored,readers=study.previous.audit(path,[dict(source=case['source'])],[report['result']])
            assert {t:len(v) for t,v in stored.items()}==report['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==report['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==report['record_bytes']
            audits[key]=dict(archive=a,root=case['root'],status=report['result']['status'],readers=readers);archives.append(a)
        groups.setdefault((i,mode),[]).append(report)
    nt={m:Counter() for m in study.NATIVE_MODES};nc={m:Counter() for m in nt};summary=[];native_rss=Counter()
    for i,case in enumerate(cases):
        row=dict(target=case['target'],event=case['event'],arms={})
        for mode in study.NATIVE_MODES:
            a,b=groups[i,mode];assert deterministic_result(a['result'])==deterministic_result(b['result'])
            for k in ('counts','native_counts','digest','record_bytes','authority_tables'): assert a[k]==b[k],(i,mode,k)
            if mode=='direct': assert sum(a['counts'].get(k,0) for k in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=262144
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metrics['records']=sum(a['authority_tables'].values());nt[mode].update(metrics);nc[mode].update(a['counts'])
            row['arms'][mode]=dict(metrics,status=a['result']['status']);native_rss[mode]=max(native_rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
        summary.append(row)
    assert nc['disabled']['b10_probe_feedback_expanded_b10_probe']>0
    comparisons={metric:dict(improved=sum(sum(r[metric] for r,_ in events[key,'reuse'])<sum(r[metric] for r,_ in events[key,'matched']) for key in seeds),
        regressed=[list(key) for key in seeds if sum(r[metric] for r,_ in events[key,'reuse'])>sum(r[metric] for r,_ in events[key,'matched'])]) for metric in METRICS if metric!='complete_seconds'}
    analysis=dict(events=16,coverage=dict(before=230,after=232,total=246),gained_events=sorted(map(list,gains)),b9_only_gained_events=sorted(map(list,b9_gains)),
        remaining_events=14,new_failures=failures,changed_events=changed,exhausted_events=exhausted,
        unfinished_events=[list(k) for k in seeds if k not in gains and list(k) not in exhausted],remaining_closures=closure_rows,
        census_totals=totals,census_counts=counts,peak_rss_bytes=rss,comparisons=comparisons,native_totals=nt,native_counts=nc,native_summary=summary,native_peak_rss_bytes=native_rss,
        probe_reduction=counts['matched']['probe_roots']-counts['reuse']['probe_roots'],unique_archive_audits=len(audits),
        feedback_seconds=sum(r['seconds'] for r in diagnostics.values()),b9_comparison_feedback=b9_diagnostics,remaining_closure_seconds=closure_seconds,
        overlay_export_reload_seconds=export_seconds,storage=dict(parent_overlay_bytes=Path(p['seeds']['path']).stat().st_size,overlay_bytes=Path(binding['path']).stat().st_size,
        referenced_files=len(deps),referenced_bytes=sum(Path(f).stat().st_size for f in deps),expanded_compact_bytes=len(base.encode(dict(rows=expanded)).encode())),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,b10_probe_cursor={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','cases','comparisons','feedback-diagnostics','analysis')})
    cp['b10_probe_cursor'].update(remaining=binding,supplemental_archives=archives);base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(coverage=analysis['coverage'],totals=totals,native=summary,storage=analysis['storage'],unfinished=analysis['unfinished_events'])))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items(): assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','50a7e030:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2091 tests in .*\n\nOK',full) and re.search(r'Ran 43 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b10_probe_cursor']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2091,focused_tests=43,proof_blocks_unchanged=64,
        manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1154,final_sources=len(cp['source_fingerprints']),
        prior_manifests=206,prior_artifacts=29728,new_native_archives=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        if str(f) in base.load(out/'protocol.json')['native_runner_correction']: continue
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0))
        f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=207,next_artifacts=29728+len(files))))


if __name__=='__main__': globals()[sys.argv[1]](Path(sys.argv[2]))
