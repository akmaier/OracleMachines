#!/usr/bin/env python3
"""Audit policy-bound ordering, original-bank proofs and cumulative evidence."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,json,re,subprocess,sys,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_b12_progress_order as study,cnf_b10_probe_feedback as frozen_feedback
from experiments import compare_cnf_prepared_prefix_replay as reconstruction
base=study.base;old=study.old;c=study.candidate
METRICS=('reconstruction_seconds','discovery_seconds','verification_seconds','persistence_seconds','complete_seconds','record_bytes')


def compose(bank,probes,counts):
    clauses=tuple(sorted(set(bank)|{(-r['assumption'],) for r in probes}))
    fixed,trace,conflict=c.engine.native.propagate(clauses,counts)
    assert conflict is None,'New contradiction requires source-only native certification before coverage publication'
    cl=dict(units=trace,assignment=sorted([list(x) for x in fixed.items()]))
    assert c.engine.prior.check_closure(clauses,cl,counts)==fixed
    return cl


def independent(args,kw,result,ordering):
    old_kw={k:kw[k] for k in ('closure','feedback_closure','joint_closure')}
    prepared=frozen_feedback.prepare(*args[:22],**old_kw,counts=Counter())
    c.prior.validate(*args[:22],**{k:v for k,v in kw.items() if k!='latest_closure'},result=args[22],counts=Counter())
    lower=c.prior.prior.validate(*args[:21],**old_kw,result=args[23],counts=Counter())
    assert lower==prepared[:23]
    entries=dict(zip(prepared[23],prepared[24]))
    for kind,book in (('b10_comparison_probe',args[23]['program']),('b11_probe',args[22]['program'])):
        for i,row in enumerate(book['probes']):entries.setdefault((-row['assumption'],),dict(kind=kind,index=i))
    clauses=tuple(sorted(entries));prepared=(*prepared,clauses,[entries[cl] for cl in clauses])
    fixed=c.engine.prior.check_closure(clauses,kw['latest_closure'],Counter())
    bank,_=c.engine.prior.residual_bank(clauses,fixed,Counter());active={abs(l) for cl in bank for l in cl}
    source_order=tuple(l for l in c.engine.frozen.roots(prepared[0]) if abs(l) in active)
    limit=result['program']['trace_limit'];same=prepared[23]==clauses and kw['next_closure']==kw['latest_closure'] and args[22]['program']['trace_limit']==limit
    seen=set(args[22]['cursor']['completed'])|set(args[23]['cursor']['completed'])
    order=source_order if ordering=='source' or same else tuple(l for l in source_order if l not in seen)+tuple(l for l in source_order if l in seen)
    assert len(order)==len(source_order) and set(order)==set(source_order)
    binding=json.dumps([c.POLICY,ordering,prepared[0],clauses,kw['latest_closure'],order,limit],sort_keys=True,separators=(',',':'))
    cursor=deepcopy(result['cursor']);assert cursor['format']==c.FORMAT;cursor['format']=c.engine.FORMAT
    state=c.engine.load((*prepared[:15],clauses,prepared[26]),order,binding,cursor,Counter(),limit)
    c.engine.prior.check_program(prepared[0],clauses,result['program'],Counter())
    assert result['program']==c.engine._program(state[4],state[6],limit,result['program']['reason'])
    return prepared,same,seen


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(209,30430)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_b12_progress_order.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1171 and Path(p['pilot_source']['path']).read_bytes()==Path(study.FILES[0]).read_bytes()
    old.bound(p['pilot']);assert base.sha(p['pilot_source']['path'])==p['pilot_source']['sha256']
    seeds={(r['target'],r['event']):r for r in study.prior.load_frontier(p['seeds'])};assert len(seeds)==14
    pilot={(r['target'],r['event']):r for r in old.bound(p['pilot'])['rows']};cmp_pilot={(r['target'],r['event']):r for r in old.bound(p['comparison_pilot'])['rows']}
    assert pilot.keys()==cmp_pilot.keys()==seeds.keys()
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
    deltas=[];diagnostics=[];novelty=[];failures=[];changed=[];exhausted=[];feedback_seconds=0.0
    for target in p['targets']:
        source,ts,pairs,original_events=study.inputs(p,target)
        for ref,seed in pairs:
            key=target,ref['event'];args=study.arguments(seed);kw=study.options(seed);rc=Counter()
            actual=study.bind(source,ts,ref,original_events[ref['event']],rc)
            assert actual==reconstruction.prior.bind(source,ts,ref,original_events[ref['event']],Counter())
            assert list(map(list,actual[2]['local']))==seed['final_source'] and [h['template'] for h in actual[2]['hints']]==seed['templates']
            for mode in study.MODES:
                (a,pa),(b,pb)=events[key,mode];assert pa==pb and pa['program']['status']=='unresolved'
                for field in ('counts','verification_counts','reconstruction_counts'):assert a[field]==b[field]
                assert a['reconstruction_counts']==dict(rc)
                cc=Counter();r=study.search(args,seed,mode,cc,p['limits']);assert r==pa and dict(cc)==a['counts']
                if mode in ('source','unseen'):assert r==pilot[key]['arms'][mode]['result'] and dict(cc)==pilot[key]['arms'][mode]['counts']
                if mode=='b11':assert r==cmp_pilot[key]['result'] and dict(cc)==cmp_pilot[key]['counts']
            ur,unseen=events[key,'unseen'][0];sr,source_result=events[key,'source'][0];br,baseline=events[key,'b11'][0]
            assert unseen==events[key,'matched'][0][1]
            tick=time.perf_counter();prepared,same,seen=independent(args,kw,unseen,'unseen')
            assert prepared==independent(args,kw,source_result,'source')[0]
            for mode,r in (('source',source_result),('unseen',unseen)):
                assert prepared==c.validate(*args,**kw,ordering=mode,result=r,counts=Counter())
            c.prior.validate(*args[:22],**study.prior.options(seed),result=baseline,counts=Counter())
            cl_source=compose(prepared[25],source_result['program']['probes'],Counter())
            cl_unseen=compose(prepared[25],unseen['program']['probes'],Counter())
            joint=compose(prepared[25],source_result['program']['probes']+unseen['program']['probes']+baseline['program']['probes'],Counter())
            elapsed=time.perf_counter()-tick;feedback_seconds+=elapsed;oldfixed=dict(kw['latest_closure']['assignment'])
            for cl in (cl_source,cl_unseen,joint):assert oldfixed.items()<=dict(cl['assignment']).items()
            diagnostics.append(dict(target=target,event=key[1],source_added=sorted(set(dict(cl_source['assignment']))-set(oldfixed)),unseen_added=sorted(set(dict(cl_unseen['assignment']))-set(oldfixed)),joint_added=sorted(set(dict(joint['assignment']))-set(oldfixed)),seconds=elapsed))
            deltas.append(dict(target=target,event=key[1],b12_source_result=sr['result'],b12_unseen_result=ur['result'],b11_continuation_result=br['result'],b12_source_feedback_closure=cl_source,b12_unseen_feedback_closure=cl_unseen,b12_joint_closure=joint))
            if not same:
                changed.append(list(key))
                for mode,r in (('source',source_result),('unseen',unseen)):
                    completed=r['cursor']['completed'];assert len(completed)==events[key,mode][0][0]['counts']['cursor_completed_probes']
                    novelty.append(dict(target=target,event=key[1],mode=mode,completed=len(completed),previously_unseen=sum(x not in seen for x in completed),previously_seen=sum(x in seen for x in completed)))
            if unseen['program']['reason']=='complete':exhausted.append(list(key))
            oldfail={r['assumption'] for r in args[22]['program']['probes']}
            sf=[x['assumption'] for x in source_result['program']['probes']];uf=[x['assumption'] for x in unseen['program']['probes']];bf=sorted({x['assumption'] for x in baseline['program']['probes']}-oldfail)
            if sf or uf or bf:failures.append(dict(target=target,event=key[1],source=sf,unseen=uf,b11_new=bf))
    assert changed==[[37,39],[67,63]] and len(exhausted)==11
    assert failures==[dict(target=67,event=63,source=[-68],unseen=[83],b11_new=[-39])]
    assert sum(len(r['joint_added']) for r in diagnostics)==2
    assert counts['unseen']['b12_imported_cursors']==counts['source']['b12_imported_cursors']==12
    assert counts['matched']['probe_roots']-counts['unseen']['probe_roots']==1946
    tick=time.perf_counter();study.compact(out/'remaining-overlay.json',dict(parent=p['seeds'],rows=deltas));binding=old.binding(out/'remaining-overlay.json');loaded=study.load_frontier(binding)
    for row in loaded:
        key=row['target'],row['event'];assert {k:row[k] for k in seeds[key]}==seeds[key]
        for field,mode in (('b12_source_result','source'),('b12_unseen_result','unseen'),('b11_continuation_result','b11')):assert old.bound(row[field])==events[key,mode][0][1]
    export_seconds=time.perf_counter()-tick;deps=set();current=binding
    fields=('b8_comparison_result','b9_result','b10_result','b9_continuation_result','b11_result','b10_comparison_result','b12_source_result','b12_unseen_result','b11_continuation_result')
    while True:
        payload=old.bound(current)
        if current!=binding:deps.add(current['path'])
        for row in payload['rows']:
            for field in fields:
                if field in row:old.bound(row[field]);deps.add(row[field]['path'])
        if 'parent' not in payload:break
        current=payload['parent']
    comparisons={other:{metric:dict(improved=sum(sum(r[metric] for r,_ in events[key,'unseen'])<sum(r[metric] for r,_ in events[key,other]) for key in seeds),regressed=[list(key) for key in seeds if sum(r[metric] for r,_ in events[key,'unseen'])>sum(r[metric] for r,_ in events[key,other])]) for metric in METRICS if metric!='complete_seconds'} for other in ('source','matched')}
    analysis=dict(events=14,coverage=dict(before=232,after=232,total=246),remaining_events=14,changed_events=changed,new_failures=failures,novelty=novelty,feedback=diagnostics,feedback_seconds=feedback_seconds,exhausted_events=exhausted,unfinished_events=[list(k) for k in seeds if list(k) not in exhausted],census_totals=totals,census_counts=counts,peak_rss_bytes=rss,comparisons=comparisons,overlay_export_reload_seconds=export_seconds,storage=dict(overlay_bytes=Path(binding['path']).stat().st_size,referenced_files=len(deps),referenced_bytes=sum(Path(f).stat().st_size for f in deps)),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,b12_progress_order={k:old.binding(out/(k+'.json')) for k in ('protocol','pilot','censuses','analysis')});cp['b12_progress_order']['remaining']=binding;base.write(out/'checkpoint.json',cp)
    assert all(cp[k]==v for k,v in parent.items() if k not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=[],parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,novelty=novelty,storage=analysis['storage'],feedback_seconds=feedback_seconds,failures=failures)))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items(): assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','6eb8898b:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2118 tests in .*\n\nOK',full) and re.search(r'Ran 43 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['b12_progress_order']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2118,focused_tests=43,proof_blocks_unchanged=64,
        manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1167,final_sources=len(cp['source_fingerprints']),
        prior_manifests=209,prior_artifacts=30430,new_native_archives=0,
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0))
        f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=210,next_artifacts=30430+len(files))))


if __name__=='__main__': globals()[sys.argv[1]](Path(sys.argv[2]))
