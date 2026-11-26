#!/usr/bin/env python3
"""Audit joint implications, compact supports, cold certificates and lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,math,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cross_pivot_feedback as s
from experiments.validate_cnf_layered_feedback import deterministic_result
from solver.test_cnf_b13_probe_cursor import independent
base=s.base;old=s.old
REPLAY=('load_seconds','preparation_seconds','check_seconds','persistence_seconds','complete_seconds','input_bytes','output_bytes')
NATIVE=('load_seconds','solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json');pa=base.load(s.PARENT/'analysis.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(219,33298)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_cross_pivot_feedback.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1213
    cases={name:old.bound(binding) for name,binding in p['cases'].items()};prepared={};results={};metrics={}
    assert set(cases)=={'61-0','61-50','67-0'}
    for name,case in cases.items():
        lower=independent(case['inputs'],case['options'],case['search']);entries=dict(zip(lower[27],lower[28]))
        for i,probe in enumerate(case['search']['program']['probes']):entries.setdefault((-probe['assumption'],),dict(kind='b13_probe',index=i))
        bank=tuple(sorted(entries));prepared[name]=(*lower,bank,[entries[cl] for cl in bank]);assert prepared[name]==s.prior.seed(case,Counter())
        assert s.compiler.native.token(tuple(map(tuple,case['source'])),Counter())==case['root']
        history=old.bound(p['records'][name]['history']);assert all(t['status']=='unresolved' for t in history['trials']);cc=Counter();prep=s.prior.seed(case,cc)
        full=s.joint.collect(bank,history['trials'],cc,order_source=prep[0]);acq=next(r for r in p['acquisitions'] if r['name']==name);assert dict(cc)==acq['full_counts']
        cc=Counter();small=s.joint.compact(bank,full,cc,order_source=prep[0]);assert dict(cc)==acq['compact_counts']
        for mode,result in (('full',full),('compact',small)):
            assert result==old.bound(p['records'][name][mode])==base.load(out/f'pilot-{name}-{mode}.json')
            s.joint.validate(bank,result,Counter(),order_source=prep[0]);results[name,mode]=result
            assert Path(p['records'][name][mode]['path']).stat().st_size==acq['bytes'][mode]
        d=next(r for r in pa['diagnostics'] if r['name']==name)
        assert sorted(-r['assumption'] for r in full['lemmas'])==sorted(d['derived_units'])
        assert full['proof']==d['combined_proof'] and full['closure']==d['closure']
        assert s.joint.compact(bank,small,Counter(),order_source=prep[0])==small
        metrics[name]=dict(status=full['status'],full_lemmas=len(full['lemmas']),compact_lemmas=len(small['lemmas']),full_trace_steps=None if full['proof'] is None else len(full['proof']['units']),
            compact_trace_steps=None if small['proof'] is None else len(small['proof']['units']),retained_assumptions=[r['assumption'] for r in small['lemmas']])
    assert [(metrics[n]['full_lemmas'],metrics[n]['compact_lemmas']) for n in ('61-0','61-50','67-0')]==[(9,7),(2,2),(10,3)]
    samples=base.load(out/'replays.json')['samples'];assert len(samples)==18
    assert {(r['mode'],r['repeat']) for r in samples}=={(m,i) for m in s.MODES for i in range(6)}
    groups={};events={}
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];assert r['mode']==mode and {e['name'] for e in r['events']}==set(cases);groups.setdefault(mode,[]).append(r)
        for e in r['events']:
            name=e['name'];result=results[name,'full' if mode=='history' else mode]
            expected=dict(status=result['status'],units=[-x['assumption'] for x in result['lemmas']],proof=result['proof'],closure=result['closure'])
            assert old.bound(e['result'])==expected and e['input_bytes']==Path(p['records'][name][mode]['path']).stat().st_size and e['output_bytes']==Path(e['result']['path']).stat().st_size
            events.setdefault((name,mode),[]).append(e)
        for key in REPLAY:
            if key!='complete_seconds':assert abs(r[key]-sum(e[key] for e in r['events']))<1e-8
    for (name,mode),es in events.items():
        for e in es:
            for key in ('counts','input_bytes','output_bytes'):assert e[key]==es[0][key]
        cc=Counter();prep=s.prior.seed(cases[name],cc);record=old.bound(p['records'][name][mode])
        if mode=='history':s.joint.collect(prep[29],record['trials'],cc,order_source=prep[0])
        else:s.joint.validate(prep[29],record,cc,order_source=prep[0])
        assert dict(cc)==es[0]['counts']
    totals={m:{key:sum(r[key] for r in rs)/6 for key in REPLAY} for m,rs in groups.items()};rss={m:max(r['peak_rss_bytes'] for r in rs) for m,rs in groups.items()}
    ns=base.load(out/'comparisons.json')['samples'];assert len(ns)==36
    assert {(r['name'],r['mode'],r['repeat']) for r in ns}=={(name,mode,i) for name in ('61-0','67-0') for mode in s.NATIVE for i in range(6)}
    ngroups={};audits={};archives=[]
    for sample in ns:
        r=old.bound(sample);name=sample['name'];mode=sample['mode'];case=cases[name];assert (r['name'],r['mode'],r['case'])==(name,mode,p['cases'][name])
        if mode!='fresh':assert r['result']['status']=='unsat' and r['result']['result']['root']==case['root']
        archive=r['archive'];assert base.sha(archive['path'])==archive['sha256'];key=archive['sha256'],case['root']
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';s.previous.restore_archive(archive,db);tables,readers=s.previous.audit(db,[dict(source=case['source'])],[r['result']])
            assert {t:len(v) for t,v in tables.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items())==r['record_bytes']
            if mode!='fresh':assert all(not records for table,records in tables.items() if table!='cnf_residual_v1')
            audits[key]=dict(name=name,archive=archive,root=case['root'],status=r['result']['status'],readers=readers);archives.append(archive)
        ngroups.setdefault((name,mode),[]).append(r)
    nt={};nr={};nbytes={};nrss={};statuses={};selected={};alltotals={m:Counter() for m in s.NATIVE}
    for name in ('61-0','67-0'):
        nt[name]={};nr[name]={};nbytes[name]={};nrss[name]={};statuses[name]={}
        for mode in s.NATIVE:
            rs=ngroups[name,mode];assert len(rs)==6
            for r in rs:
                assert deterministic_result(r['result'])==deterministic_result(rs[0]['result'])
                for key in ('counts','warm_counts','native_counts','digest','record_bytes','authority_tables'):assert r[key]==rs[0][key],(name,mode,key)
            nt[name][mode]={key:sum(r[key] for r in rs)/6 for key in NATIVE};alltotals[mode].update(nt[name][mode]);nr[name][mode]=sum(rs[0]['authority_tables'].values());nbytes[name][mode]=Path(rs[0]['archive']['path']).stat().st_size
            nrss[name][mode]=max(r['peak_rss_bytes'] for r in rs);statuses[name][mode]=rs[0]['result']['status']
            if mode!='fresh':
                assert rs[0]['warm_counts']['cross_native_extension_hits']==1 and rs[0]['counts']['cross_native_branch_expansions']>0
                assert sum(rs[0]['counts'].get(x,0) for x in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=262144
        assert ngroups[name,'full'][0]['digest']==ngroups[name,'compact'][0]['digest']
        pilot=next(r for r in base.load(out/'pilot.json')['rows'] if r['name']==name);trial=ngroups[name,'compact'][0]
        assert base.sha(pilot['archive']['path'])==pilot['archive']['sha256']==trial['archive']['sha256']
        best=min((m for m in s.NATIVE if statuses[name][m]=='unsat'),key=lambda m:nt[name][m]['complete_seconds'])
        selected[name]=dict(mode=best,root=cases[name]['root'],archive=ngroups[name,best][0]['archive'])
    acqfull=sum(r['full_seconds'] for r in p['acquisitions']);acqcompact=sum(r['compact_additional_seconds'] for r in p['acquisitions'])
    def breakeven(cost,a,b):
        saving=totals[a]['complete_seconds']-totals[b]['complete_seconds']
        return dict(extra_acquisition_seconds=cost,seconds_saved_per_replay=saving,first_replay_count_to_repay=math.ceil(cost/saving) if saving>0 else None)
    remaining_parent=parent['conditioned_saturation']['remaining'];s.compact(out/'remaining-overlay.json',dict(parent=remaining_parent,excluded=[[61,0],[67,0]],certificates=selected));binding=old.binding(out/'remaining-overlay.json')
    remaining=s.load_frontier(binding);assert remaining==[r for r in s.rows() if (r['target'],r['event'])==(61,50)]
    analysis=dict(coverage=dict(before=243,after=245,total=246),remaining_events=1,remaining_id=[61,50],summary_metrics=metrics,replay_totals=totals,replay_peak_rss_bytes=rss,native_totals=nt,
        native_all_totals=alltotals,native_records=nr,native_archive_bytes=nbytes,native_peak_rss_bytes=nrss,native_statuses=statuses,selected=selected,unique_archive_audits=len(audits),
        acquisition=dict(full_seconds=acqfull,compact_additional_seconds=acqcompact),break_even=dict(full_from_history=breakeven(acqfull,'history','full'),compact_from_history=breakeven(acqfull+acqcompact,'history','compact'),compact_from_full=breakeven(acqcompact,'full','compact')),
        compact_vs_history_percent={key:100*(totals['compact'][key]/totals['history'][key]-1) for key in REPLAY},limitations=p['limitations'])
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        cross_pivot_feedback={key:old.binding(out/(key+'.json')) for key in ('protocol','replays','comparisons','analysis')})
    cp['cross_pivot_feedback'].update(remaining=binding,summaries=p['records'],supplemental_archives=archives);base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),
        parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(coverage=analysis['coverage'],replay_totals=totals,native_totals=nt,break_even=analysis['break_even'])))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','6431db03:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2200 tests in .*\n\nOK',full) and re.search(r'Ran 25 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['cross_pivot_feedback']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2200,focused_tests=25,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1208,final_sources=len(cp['source_fingerprints']),
        prior_manifests=219,prior_artifacts=33298,new_native_archives=len(v['supplemental_archive_audits']),warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=220,next_artifacts=33298+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
