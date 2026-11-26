#!/usr/bin/env python3
"""Check history-extension gains without promoting an augmented proof to native authority."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b13_strengthened_histories as s
from solver.test_cnf_b13_probe_cursor import independent
base=s.base;old=s.old;c=s.c
METRICS=('reconstruction_seconds','discovery_seconds','verification_seconds','persistence_seconds','complete_seconds','record_bytes')


def feedback(prepared,result,counts):
    clauses=tuple(sorted(set(prepared[27])|{(-r['assumption'],) for r in result['program']['probes']}))
    index=c.engine.frozen.UnitIndex(clauses,counts);start=counts['probe_occurrence_visits']
    proof=index.probe(None,counts,lambda:262144-(counts['probe_occurrence_visits']-start),256)
    program=dict(status='refuted' if proof else 'unresolved',reason='units' if proof else 'open',trace_limit=256,proof=proof)
    if proof:
        c.engine.frozen.check_trace(prepared[0],clauses,None,proof,counts,256)
        return program,clauses,None
    fixed,trace,conflict=c.engine.native.propagate(clauses,counts);assert conflict is None
    closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
    assert c.engine.prior.check_closure(clauses,closure,counts)==fixed
    return program,clauses,closure


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(214,32515)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b13_strengthened_histories.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1190
    original=base.load(out/'initial-protocol.json');test='solver/test_cnf_b13_strengthened_histories.py'
    assert original['source_fingerprints'][test]==base.sha(out/'initial-test-source.py')
    assert {k:v for k,v in original.items() if k!='source_fingerprints'}=={k:v for k,v in p.items() if k!='source_fingerprints'}
    assert {k:v for k,v in original['source_fingerprints'].items() if k!=test}=={k:v for k,v in p['source_fingerprints'].items() if k!=test}
    seeds={(r['target'],r['event']):r for r in s.prior.prior.load_frontier(p['seeds'])};assert len(seeds)==14
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert set(pilot)==set(s.CASES)
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==36
    assert {(x['target'],x['mode'],x['repeat']) for x in samples}=={(t,m,r) for t in p['targets'] for m in s.MODES for r in range(6)}
    events={};groups={};totals={m:Counter() for m in s.MODES};counts={m:Counter() for m in s.MODES};vcounters={m:Counter() for m in s.MODES};rss=Counter()
    for sample in samples:
        report=old.bound(sample);mode=sample['mode'];target=sample['target'];assert report['mode']==mode and report['target']==target
        rows=old.bound(report['events'])['rows'];assert len(rows)==1;groups.setdefault((target,mode),[]).append(report)
        for row in rows:
            key=target,row['event'];assert key in s.CASES;result=old.bound(row['result']);seed=seeds[key];vc=Counter()
            assert row['root']==seed['root'] and row['record_bytes']==Path(row['result']['path']).stat().st_size
            s.check(s.arguments(seed,mode),seed,mode,result,vc);assert dict(vc)==row['verification_counts']
            events.setdefault((key,mode),[]).append((row,result))
        for field in ('counts','reconstruction_counts','verification_counts'):
            assert report[field]==dict(sum((Counter(r[field]) for r in rows),Counter()))
        for metric in METRICS:
            if metric!='complete_seconds':assert abs(report[metric]-sum(r[metric] for r in rows))<1e-9
    for (target,mode),reports in groups.items():
        assert len(reports)==6
        for r in reports:
            for k in ('counts','reconstruction_counts','verification_counts','record_bytes'):assert r[k]==reports[0][k]
            for k in METRICS:totals[mode][k]+=r[k]/6
            rss[mode]=max(rss[mode],r['peak_rss_bytes'])
        counts[mode].update(reports[0]['counts']);vcounters[mode].update(reports[0]['verification_counts'])
    for target in p['targets']:
        source,ts,refs,original_events=s.inputs(p,target)
        for ref,seed in refs:
            key=target,ref['event'];rc=Counter();_,_,state=s.bind(source,ts,ref,original_events[ref['event']],rc)
            assert list(map(list,state['local']))==seed['final_source'] and [h['template'] for h in state['hints']]==seed['templates']
            for mode in s.MODES:
                row,result=events[key,mode][0];args=s.arguments(seed,mode)
                for other,book in events[key,mode]:
                    assert book==result
                    for field in ('counts','verification_counts','reconstruction_counts'):assert other[field]==row[field]
                assert row['reconstruction_counts']==dict(rc)
                cc=Counter();assert s.search(args,seed,mode,cc,p['limits'])==result and dict(cc)==row['counts']
                assert result==pilot[key]['arms']['320_'+mode]['result'] and dict(cc)==pilot[key]['arms']['320_'+mode]['counts']
                assert independent(args,s.options(seed,mode),result)==s.check(args,seed,mode,result,Counter())
                assert (result['program']['status'],result['program']['reason'])==('unresolved','complete')
            assert events[key,'continue'][0][1]==events[key,'fresh'][0][1]
    changed=[];diagnostics=[];deltas=[];candidate_conflicts=[]
    for key,seed in seeds.items():
        oldprep=independent(s.arguments(seed,'continue'),s.options(seed,'continue'),old.bound(seed['b13_result']))
        delta=dict(target=key[0],event=key[1])
        if key not in s.CASES:
            newprep=independent(s.arguments(seed,'strengthen'),s.options(seed,'strengthen'),old.bound(seed['b13_result']))
            assert oldprep==newprep
            delta.update(b13_strength_result=seed['b13_result'],b13_strength_context_closure=seed['b12_batch_joint_closure'],b13_strength_state='unchanged_exhausted')
        else:
            row,result=events[key,'strengthen'][0];newprep=independent(s.arguments(seed,'strengthen'),s.options(seed,'strengthen'),result)
            assert oldprep[:27]==newprep[:27] and set(oldprep[27])<set(newprep[27]);changed.append(list(key))
            tick=time.perf_counter();fc=Counter();program,clauses,closure=feedback(newprep,result,fc);elapsed=time.perf_counter()-tick
            beforefixed=dict(seed['b12_batch_joint_closure']['assignment']);assert c.engine.prior.check_closure(newprep[27],seed['b12_batch_joint_closure'],Counter())==beforefixed
            before,_=c.engine.prior.residual_bank(newprep[27],beforefixed,Counter())
            added=[];after_info=None
            if closure is not None:
                assert beforefixed.items()<=dict(closure['assignment']).items()
                added=sorted([v,b] for v,b in dict(closure['assignment']).items() if v not in beforefixed)
                after,_=c.engine.prior.residual_bank(clauses,dict(closure['assignment']),Counter())
                after_info=dict(clauses=len(after),literals=sum(map(len,after)),variables=len({abs(l) for cl in after for l in cl}))
                delta['b13_strength_joint_closure']=closure
            else:candidate_conflicts.append(list(key))
            previous_failures={p['assumption'] for slot in (24,25,26) for p in s.arguments(seed,'strengthen')[slot]['program']['probes']}
            previous_failures.update(p['assumption'] for p in old.bound(seed['b13_result'])['program']['probes'])
            novel=sorted({p['assumption'] for p in result['program']['probes']}-previous_failures)
            assert all(abs(l) not in beforefixed for l in novel)
            diagnostic=dict(target=key[0],event=key[1],program=program,counts=dict(fc),feedback_seconds=elapsed,new_failures=novel,added_assignments=added,
                residual_before=dict(clauses=len(before),literals=sum(map(len,before)),variables=len({abs(l) for cl in before for l in cl})),residual_after=after_info,
                original_bank_clauses=len(oldprep[27]),strengthened_bank_clauses=len(newprep[27]),native_certified=False)
            diagnostics.append(diagnostic)
            delta.update(b13_strength_result=row['result'],b13_strength_continuation_result=events[key,'continue'][0][0]['result'],
                b13_strength_context_closure=seed['b12_batch_joint_closure'],b13_strength_feedback_program=program,
                b13_strength_state='candidate_refutation_pending_native' if closure is None else 'strengthened_open')
        deltas.append(delta)
    assert changed==[list(k) for k in s.CASES] and candidate_conflicts==[[67,63]]
    assert diagnostics[0]['new_failures']==[-61,37] and diagnostics[0]['added_assignments']==[[37,False],[61,True]]
    assert diagnostics[1]['new_failures']==[-130,-123,-112,-88,-9,45,50,79,100,107,110,133]
    s.compact(out/'remaining-overlay.json',dict(parent=p['seeds'],rows=deltas));binding=old.binding(out/'remaining-overlay.json')
    loaded=s.load_frontier(binding)
    for row in loaded:
        seed=seeds[row['target'],row['event']];assert {k:row[k] for k in seed}==seed
    deps=set();current=binding
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
    analysis=dict(evaluated_cases=2,preserved_open_cases=14,coverage=dict(before=232,after=232,total=246),changed=changed,candidate_refutations_pending_native=candidate_conflicts,
        feedback=diagnostics,new_native_records=0,census_totals=totals,census_counts=counts,verification_counts=vcounters,peak_rss_bytes=rss,
        storage=dict(overlay_bytes=Path(binding['path']).stat().st_size,referenced_files=len(deps),referenced_bytes=sum(Path(f).stat().st_size for f in deps)),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,b13_strengthened_histories={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','analysis')});cp['b13_strengthened_histories']['remaining']=binding;base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=[],parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,feedback=diagnostics,storage=analysis['storage'])))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','918fc95a:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2161 tests in .*\n\nOK',full) and re.search(r'Ran 25 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b13_strengthened_histories']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2161,focused_tests=25,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1187,final_sources=len(cp['source_fingerprints']),prior_manifests=214,prior_artifacts=32515,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=215,next_artifacts=32515+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
