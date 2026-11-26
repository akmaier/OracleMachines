#!/usr/bin/env python3
"""Audit full-result checked handoff and preserve all predecessor evidence."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_checked_b6_restore as study
base=study.base;old=study.old;c=study.c
METRICS=('reconstruction_seconds','restoration_seconds','advance_seconds','persistence_seconds','verification_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(198,27922)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_checked_b6_restore.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    assert Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    seeds={(r['target'],r['event']):r for r in old.bound(p['seeds'])['rows']};assert len(seeds)==18
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};assert seeds.keys()==pilot.keys()
    groups={};events={};totals={m:Counter() for m in study.MODES};restoration_counts={m:Counter() for m in study.MODES};advance_counts={m:Counter() for m in study.MODES};rss=Counter()
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==len(p['targets'])*4
    for sample in samples:
        report=old.bound(sample);groups.setdefault((sample['target'],sample['mode']),[]).append(report)
        rows=old.bound(report['events'])['rows'];assert {r['event'] for r in rows}=={e for t,e in seeds if t==sample['target']}
        for row in rows:
            key=(row['target'],row['event']);result=old.bound(row['result']);seed=seeds[key];mode=sample['mode'];expected=pilot[key]['arms'][mode]
            assert row['root']==seed['root'] and result==expected['result']
            for field in ('restoration_counts','advance_counts'):assert row[field]==expected[field]
            assert row['record_bytes']==Path(row['result']['path']).stat().st_size
            vc=Counter();args=tuple(seed[k] for k in study.FIELDS);c.validate(*args,result,vc);assert dict(vc)==row['verification_counts']
            events.setdefault((key,mode),[]).append((row,result))
    for (target,mode),(a,b) in groups.items():
        for field in ('restoration_counts','advance_counts','record_bytes'):assert a[field]==b[field]
        for field in METRICS:totals[mode][field]+=(a[field]+b[field])/2
        restoration_counts[mode].update(a['restoration_counts']);advance_counts[mode].update(a['advance_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
    remaining=[];summary=[];exhausted=[];failed=[];prior_failures=0
    for key,seed in seeds.items():
        args=tuple(seed[k] for k in study.FIELDS);row=dict(target=key[0],event=key[1],arms={});results={}
        for mode in study.MODES:
            (a,ra),(b,rb)=events[key,mode];assert ra==rb
            for field in ('restoration_counts','advance_counts','verification_counts','reconstruction_counts'):assert a[field]==b[field]
            row['arms'][mode]={k:(a[k]+b[k])/2 for k in METRICS if k!='complete_seconds'};results[mode]=ra
            rc=Counter();session=study.recover(args,seed['b6_prepared_cursor'],mode,rc);ac=Counter();replayed=session.advance(ac,probe_limit=8)
            assert replayed==ra and dict(rc)==a['restoration_counts'] and dict(ac)==a['advance_counts']
            reference=c.discover(*args,Counter(),cursor=seed['b6_prepared_cursor']['cursor'],probe_limit=8)
            assert replayed==reference;c.validate(*args,reference,Counter())
        assert results['separate']==results['shared'];assert events[key,'separate'][0][0]['advance_counts']==events[key,'shared'][0][0]['advance_counts']
        result=results['shared'];assert result['program']['status']=='unresolved' and result['program']['reason'] in ('complete','probe_limit')
        oldhistory=seed['b6_prepared_cursor']['cursor'];newhistory=result['cursor']
        assert newhistory['completed'][:len(oldhistory['completed'])]==oldhistory['completed']
        assert newhistory['probes'][:len(oldhistory['probes'])]==oldhistory['probes'];prior_failures+=len(oldhistory['probes'])
        remaining.append(dict(seed,b6_checked_restore_cursor=result));summary.append(row)
        if result['program']['reason']=='complete':exhausted.append(dict(target=key[0],event=key[1],completed=len(newhistory['completed'])))
        if newhistory['probes']:failed.append(dict(target=key[0],event=key[1],failures=len(newhistory['probes'])))
    assert prior_failures==24 and sum(r['failures'] for r in failed)==25 and len(failed)==7 and len(exhausted)==13
    assert advance_counts['separate']==advance_counts['shared']
    study.compact(out/'remaining.json',dict(rows=remaining))
    diagnostic=old.bound(p['diagnostic'])['rows'];assert {(r['target'],r['event']) for r in diagnostic}==set(seeds);extra=0;changed=0
    for row in diagnostic:
        key=(row['target'],row['event']);seed=seeds[key]
        assert {k:v for k,v in row.items() if not k.startswith('b6_composition_')}==seed
        dc=Counter();prepared=c.validate(*(seed[k] for k in study.FIELDS),seed['b6_prepared_cursor'],dc)
        bank=tuple(sorted(set(prepared[13])|{(-r['assumption'],) for r in seed['b6_prepared_cursor']['program']['probes']}))
        fixed,trace,conflict=c.native.propagate(bank,dc);assert conflict is None
        closure=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]));assert closure==row['b6_composition_closure']
        assert c.prior.check_closure(bank,closure,dc)==fixed and dict(dc)==row['b6_composition_counts']
        added=sorted(set(fixed)-dict(seed['b5_cursor_feedback_closure']['assignment']).keys());assert added==row['b6_composition_added_variables'];extra+=len(added);changed+=bool(added)
    assert (extra,changed)==(25,7)
    comparisons={k:dict(improved=sum(r['arms']['shared'][k]<r['arms']['separate'][k] for r in summary),regressed=[(r['target'],r['event']) for r in summary if r['arms']['shared'][k]>r['arms']['separate'][k]]) for k in ('restoration_seconds','advance_seconds','verification_seconds','record_bytes')}
    analysis=dict(events=18,coverage=dict(before=228,after=228,total=246),remaining_events=18,totals=totals,restoration_counts=restoration_counts,advance_counts=advance_counts,peak_rss_bytes=rss,summary=summary,comparisons=comparisons,
        retained_failures=failed,prior_failures=24,new_failures=1,exhausted_orders=exhausted,diagnostic=dict(refutations=0,changed_cases=7,additional_assignments=25),
        result_bytes=dict(previous=Path(p['seeds']['path']).stat().st_size,remaining=(out/'remaining.json').stat().st_size,diagnostic=Path(p['diagnostic']['path']).stat().st_size),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,checked_b6_restore={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','composition-diagnostic','remaining','censuses','analysis')});base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,new_native_archives=0,
        seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,failures=failed,exhausted=exhausted,diagnostic=analysis['diagnostic'])),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','4c188268:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2021 tests in .*\n\nOK',full) and re.search(r'Ran 156 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['checked_b6_restore']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2021,focused_tests=156,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1120,final_sources=len(cp['source_fingerprints']),prior_manifests=198,prior_artifacts=27922,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=199,next_artifacts=27922+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
