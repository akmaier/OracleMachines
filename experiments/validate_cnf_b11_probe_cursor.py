#!/usr/bin/env python3
"""Check B11 schedules, original-bank exclusions, costs and referenced frontiers."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b11_probe_cursor as study, cnf_b10_probe_feedback as frozen_feedback
from experiments import compare_cnf_prepared_prefix_replay as reconstruction
base=study.base;old=study.old;c=study.candidate
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
    assert (len(manifests),artifacts)==(208,30211)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b11_probe_cursor.py':base.sha(__file__)}
    for f,h in sources.items(): assert base.sha(f)==h,f
    assert len(sources)==1167
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    assert Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    seeds={(r['target'],r['event']):r for r in study.prior.prior.load_frontier(p['seeds'])};assert len(seeds)==14
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert pilot.keys()==seeds.keys()
    cmp_pilot={(r['target'],r['event']):r for r in old.bound(p['comparison_pilot'])['rows']}
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
    failures=[];exhausted=[];changed=[];deltas=[];diagnostics=[];feedback_seconds=0.0
    for target in p['targets']:
        source,ts,pairs,original_events=study.inputs(p,target)
        for ref,seed in pairs:
            key=target,ref['event'];args=study.arguments(seed);kw=study.options(seed);rc=Counter()
            actual=study.bind(source,ts,ref,original_events[ref['event']],rc)
            assert actual==reconstruction.prior.bind(source,ts,ref,original_events[ref['event']],Counter())
            assert list(map(list,actual[2]['local']))==seed['final_source'] and [h['template'] for h in actual[2]['hints']]==seed['templates']
            for mode in study.MODES:
                (a,pa),(b,pb)=events[key,mode];assert pa==pb
                for field in ('counts','verification_counts','reconstruction_counts'): assert a[field]==b[field]
                assert a['reconstruction_counts']==dict(rc)
                cc=Counter();result=study.search(args,seed,mode,cc,p['limits'])
                assert result==pa and dict(cc)==a['counts'] and result['program']['status']=='unresolved'
                if mode=='reuse': assert result==pilot[key]['result'] and dict(cc)==pilot[key]['counts']
                if mode=='b10': assert result==cmp_pilot[key]['result'] and dict(cc)==cmp_pilot[key]['counts']
            a,result=events[key,'reuse'][0];b,comparison=events[key,'b10'][0]
            assert result==events[key,'matched'][0][1]
            if result['program']['reason']=='complete': exhausted.append(list(key))
            if not a['counts'].get('b11_imported_cursors'): changed.append(list(key))
            # Independent frozen B10 feedback and proof checking do not use B11.prepare.
            tick=time.perf_counter();fc=Counter();prepared=frozen_feedback.prepare(*args,**study.prior.prior.options(seed),counts=fc)
            assert prepared==c.validate(*args,**kw,result=result,counts=Counter())
            c.engine.prior.check_program(prepared[0],prepared[23],result['program'],fc)
            c.prior.validate(*args[:-1],**study.prior.prior.options(seed),result=comparison,counts=fc)
            closure=compose(prepared[23],result['program']['probes'],fc)
            joint=compose(prepared[23],result['program']['probes']+comparison['program']['probes'],fc)
            elapsed=time.perf_counter()-tick;feedback_seconds+=elapsed
            oldfixed=dict(kw['next_closure']['assignment']);assert oldfixed.items()<=dict(closure['assignment']).items()<=dict(joint['assignment']).items()
            added=sorted(set(dict(closure['assignment']))-set(oldfixed));extra=sorted(set(dict(joint['assignment']))-set(oldfixed))
            delta=dict(target=target,event=key[1],b11_result=a['result'],b10_comparison_result=b['result'],b11_feedback_closure=closure,b11_joint_closure=joint)
            deltas.append(delta);diagnostics.append(dict(target=target,event=key[1],added_variables=added,joint_added_variables=extra,seconds=elapsed,counts=dict(fc)))
            oldprobes={x['assumption'] for x in args[-1]['program']['probes']}
            new={x['assumption'] for x in result['program']['probes']};cmp={x['assumption'] for x in comparison['program']['probes']}-oldprobes
            if new or cmp: failures.append(dict(target=target,event=key[1],b11=sorted(new),b10_new=sorted(cmp),b11_only=sorted(new-cmp),b10_only=sorted(cmp-new)))
    assert counts['reuse']['b11_imported_cursors']==12 and changed==[[37,39],[67,63]]
    assert sum(len(r['b11']) for r in failures)==1 and sum(len(r['b10_new']) for r in failures)==2
    assert counts['matched']['probe_roots']-counts['reuse']['probe_roots']==1882
    assert sum(len(r['added_variables']) for r in diagnostics)==1 and sum(len(r['joint_added_variables']) for r in diagnostics)==4
    assert len(exhausted)==11
    tick=time.perf_counter();study.compact(out/'remaining-overlay.json',dict(parent=p['seeds'],rows=deltas));binding=old.binding(out/'remaining-overlay.json')
    loaded=study.load_frontier(binding)
    for row in loaded:
        key=row['target'],row['event'];assert {k:row[k] for k in seeds[key]}==seeds[key]
        assert old.bound(row['b11_result'])==events[key,'reuse'][0][1] and old.bound(row['b10_comparison_result'])==events[key,'b10'][0][1]
    export_seconds=time.perf_counter()-tick
    # Charge all transitive frontier data, including parents retaining solved rows.
    dependency_paths=set();current=binding
    fields=('b8_comparison_result','b9_result','b10_result','b9_continuation_result','b11_result','b10_comparison_result')
    while True:
        payload=old.bound(current)
        if current != binding: dependency_paths.add(current['path'])
        for row in payload['rows']:
            for name in fields:
                if name in row:
                    old.bound(row[name]);dependency_paths.add(row[name]['path'])
        if 'parent' not in payload: break
        current=payload['parent']
    expanded=[dict(seeds[r['target'],r['event']],b11_probe_cursor=old.bound(r['b11_result']),b10_comparison_cursor=old.bound(r['b10_comparison_result']),
        b11_feedback_closure=r['b11_feedback_closure'],b11_joint_closure=r['b11_joint_closure']) for r in deltas]
    comparisons={metric:dict(improved=sum(sum(r[metric] for r,_ in events[key,'reuse'])<sum(r[metric] for r,_ in events[key,'matched']) for key in seeds),
        regressed=[list(key) for key in seeds if sum(r[metric] for r,_ in events[key,'reuse'])>sum(r[metric] for r,_ in events[key,'matched'])]) for metric in METRICS if metric!='complete_seconds'}
    analysis=dict(events=14,coverage=dict(before=232,after=232,total=246),remaining_events=14,new_failures=failures,changed_events=changed,
        exhausted_events=exhausted,unfinished_events=[list(k) for k in seeds if list(k) not in exhausted],feedback=diagnostics,
        census_totals=totals,census_counts=counts,peak_rss_bytes=rss,comparisons=comparisons,feedback_seconds=feedback_seconds,
        overlay_export_reload_seconds=export_seconds,storage=dict(parent_bytes=Path(p['seeds']['path']).stat().st_size,overlay_bytes=Path(binding['path']).stat().st_size,
        referenced_files=len(dependency_paths),referenced_bytes=sum(Path(f).stat().st_size for f in dependency_paths),
        expanded_compact_bytes=len(base.encode(dict(rows=expanded)).encode())),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,b11_probe_cursor={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','analysis')})
    cp['b11_probe_cursor']['remaining']=binding;base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=[],parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,storage=analysis['storage'],feedback_seconds=feedback_seconds,failures=failures,unfinished=analysis['unfinished_events'])))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items(): assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','b1e0e6b3:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2109 tests in .*\n\nOK',full) and re.search(r'Ran 43 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b11_probe_cursor']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2109,focused_tests=43,proof_blocks_unchanged=64,
        manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1163,final_sources=len(cp['source_fingerprints']),
        prior_manifests=208,prior_artifacts=30211,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0))
        f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=209,next_artifacts=30211+len(files))))


if __name__=='__main__': globals()[sys.argv[1]](Path(sys.argv[2]))
