#!/usr/bin/env python3
"""Audit generic feedback levels, resumed discovery and final finite coverage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_strengthened_cross_pivot as s
from experiments.validate_cnf_layered_feedback import deterministic_result
from solver.test_cnf_b13_probe_cursor import independent
base=s.base;old=s.old
CENSUS=('load_seconds','preparation_seconds','discovery_seconds','verification_seconds','persistence_seconds','complete_seconds','chain_bytes','search_bytes')
NATIVE=('load_seconds','solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(220,33491)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_strengthened_cross_pivot.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1218
    case=old.bound(p['case']);assert case==base.load(out/'pilot-case.json');assert (case['target'],case['event'])==(61,50)
    lower=independent(case['inputs'],case['options'],case['search']);entries=dict(zip(lower[27],lower[28]))
    for i,probe in enumerate(case['search']['program']['probes']):entries.setdefault((-probe['assumption'],),dict(kind='b13_probe',index=i))
    bank=tuple(sorted(entries));prepared=(*lower,bank,[entries[cl] for cl in bank]);assert prepared==s.seed(case,Counter())
    assert s.compiler.native.token(tuple(map(tuple,case['source'])),Counter())==case['root']
    first=old.bound(p['first']);summary=base.load(out/'pilot-summary.json');cc=Counter();assert s.first_chain(case,summary,cc)==first
    assert dict(cc)==p['first_wrapping']['counts'] and Path(p['first']['path']).stat().st_size==p['first_wrapping']['bytes']
    _,_,strengthened=s.kernel.validate(bank,first,Counter(),order_source=prepared[0])
    for name,clauses in (('old',bank),('strengthened',strengthened)):
        result=base.load(out/f'pilot-{name}.json');s.kernel.k.validate(clauses,result,Counter(),order_source=prepared[0]);counts=Counter()
        assert s.kernel.k.discover(clauses,counts,order_source=prepared[0])==result
        assert result['reason']=='fixed_point' and not result['rounds'][0]['search']['program']['probes']
        assert dict(counts)==next(r['counts'] for r in base.load(out/'pilot.json')['rows'] if r['mode']==name)
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==18
    assert {(x['mode'],x['repeat']) for x in samples}=={(m,i) for m in s.MODES for i in range(6)}
    groups={};results={};searches={}
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];assert r['mode']==mode and r['case']==p['case'];chain=old.bound(r['chain']);search=old.bound(r['searches'])
        vc=Counter();cold=s.seed(case,vc);s.kernel.validate(cold[29],chain,vc,order_source=cold[0]);assert dict(vc)==r['verification_counts']
        assert r['chain_bytes']==Path(r['chain']['path']).stat().st_size and r['search_bytes']==Path(r['searches']['path']).stat().st_size
        groups.setdefault(mode,[]).append(r)
        if mode in results:assert chain==results[mode] and search==searches[mode]
        else:results[mode]=chain;searches[mode]=search
    for mode,rs in groups.items():
        cc=Counter();prep=s.seed(case,cc);chain,search=s.kernel.discover(prep[29],cc,order_source=prep[0],previous=first if mode=='resume' else None,round_limit=2 if mode=='restart' else 1,**p['limits'])
        assert chain==results[mode] and search==searches[mode]
        for r in rs:
            assert r['counts']==dict(cc)
            for key in ('verification_counts','chain_bytes','search_bytes'):assert r[key]==rs[0][key]
    assert results['once']==first and results['restart']==results['resume']==base.load(out/'pilot-chain-full.json')
    assert searches['restart']==searches['once']+searches['resume']==base.load(out/'pilot-searches.json')
    assert searches['resume']==[base.load(out/'pilot-partitions.json')]
    assert searches['once']==[base.load('experiments/results/cnf-conditioned-saturation/census-conditioned-0/61-50.json')['trials']]
    assert [len(x['lemmas']) for x in results['restart']['levels']]==[2,9]
    cc=Counter();prep=s.seed(case,cc);small=s.kernel.compact(prep[29],results['restart'],cc,order_source=prep[0]);compaction=base.load(out/'compaction.json')
    assert dict(cc)==compaction['counts'] and small==old.bound(compaction['result'])==base.load(out/'pilot-chain-compact.json')
    assert small['levels'][0]==first['levels'][0] and small['levels'][1]==base.load(out/'pilot-joint-compact.json')
    assert [len(x['lemmas']) for x in small['levels']]==[2,7] and small['status']=='refuted'
    totals={m:{key:sum(r[key] for r in rs)/6 for key in CENSUS} for m,rs in groups.items()};rss={m:max(r['peak_rss_bytes'] for r in rs) for m,rs in groups.items()}
    counts={m:rs[0]['counts'] for m,rs in groups.items()}
    ns=base.load(out/'comparisons.json')['samples'];assert len(ns)==16
    assert {(x['mode'],x['repeat']) for x in ns}=={(m,i) for m in s.NATIVE for i in range(4)}
    ngroups={};audits={};archives=[]
    for sample in ns:
        r=old.bound(sample);mode=sample['mode'];assert r['mode']==mode and r['case']==p['case']
        if mode!='fresh':assert r['result']['status']=='unsat' and r['result']['result']['root']==case['root']
        archive=r['archive'];assert base.sha(archive['path'])==archive['sha256'];key=archive['sha256'],case['root']
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';s.previous.restore_archive(archive,db);tables,readers=s.previous.audit(db,[dict(source=case['source'])],[r['result']])
            assert {t:len(v) for t,v in tables.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items())==r['record_bytes']
            if mode!='fresh':assert all(not records for table,records in tables.items() if table!='cnf_residual_v1')
            audits[key]=dict(archive=archive,root=case['root'],status=r['result']['status'],readers=readers);archives.append(archive)
        ngroups.setdefault(mode,[]).append(r)
    nt={};nr={};nbytes={};nrss={};statuses={};nc={}
    for mode,rs in ngroups.items():
        assert len(rs)==4
        for r in rs:
            assert deterministic_result(r['result'])==deterministic_result(rs[0]['result'])
            for key in ('counts','warm_counts','native_counts','digest','record_bytes','authority_tables'):assert r[key]==rs[0][key],(mode,key)
        nt[mode]={key:sum(r[key] for r in rs)/4 for key in NATIVE};nr[mode]=sum(rs[0]['authority_tables'].values());nbytes[mode]=Path(rs[0]['archive']['path']).stat().st_size
        nrss[mode]=max(r['peak_rss_bytes'] for r in rs);statuses[mode]=rs[0]['result']['status'];nc[mode]=rs[0]['counts']
        if mode!='fresh':
            assert rs[0]['warm_counts']['cross_native_extension_hits']==1 and nc[mode]['cross_native_branch_expansions']>0
            assert sum(nc[mode].get(x,0) for x in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))<=p['large_unit_work_limit' if mode=='compact_large' else 'unit_work_limit']
    assert ngroups['full'][0]['digest']==ngroups['compact'][0]['digest']
    pilot=base.load(out/'native-pilot.json');assert base.sha(pilot['archive']['path'])==pilot['archive']['sha256']==ngroups['compact'][0]['archive']['sha256']
    assert pilot['counts']==nc['compact'] and pilot['records']==nr['compact'] and pilot['record_bytes']==nt['compact']['record_bytes']
    assert nc['compact']['direct_budget_skips']>0
    best=min((m for m in s.NATIVE if statuses[m]=='unsat'),key=lambda m:nt[m]['complete_seconds']);selected=dict(mode=best,root=case['root'],archive=ngroups[best][0]['archive'])
    s.compact(out/'remaining-overlay.json',dict(parent=parent['cross_pivot_feedback']['remaining'],excluded=[[61,50]],certificate=selected));binding=old.binding(out/'remaining-overlay.json');assert s.load_frontier(binding)==[]
    analysis=dict(coverage=dict(before=245,after=246,total=246),remaining_events=0,closure_scope='All 246 retained frontier snapshots, not unrestricted SAT or all generating target formulas.',
        census_totals=totals,census_counts=counts,census_peak_rss_bytes=rss,resume_vs_restart_percent={key:100*(totals['resume'][key]/totals['restart'][key]-1) for key in CENSUS},
        saved_probes=counts['restart']['probe_roots']-counts['resume']['probe_roots'],compaction=compaction,first_wrapping=p['first_wrapping'],earlier_acquisition=p['earlier_acquisition'],
        from_scratch_once_plus_resume_seconds=totals['once']['complete_seconds']+totals['resume']['complete_seconds'],native_totals=nt,native_records=nr,native_archive_bytes=nbytes,native_peak_rss_bytes=nrss,
        native_statuses=statuses,native_counts=nc,selected=selected,unique_archive_audits=len(audits),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis);cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        strengthened_cross_pivot={key:old.binding(out/(key+'.json')) for key in ('protocol','censuses','comparisons','analysis')})
    cp['strengthened_cross_pivot'].update(remaining=binding,chain=compaction['result'],supplemental_archives=archives);base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,supplemental_archive_audits=list(audits.values()),
        parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(coverage=analysis['coverage'],census_totals=totals,native_totals=nt,native_records=nr,selected=selected)))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','94b0d459:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S);assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2210 tests in .*\n\nOK',full) and re.search(r'Ran 27 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['strengthened_cross_pivot']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2210,focused_tests=27,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1213,final_sources=len(cp['source_fingerprints']),
        prior_manifests=220,prior_artifacts=33491,new_native_archives=len(v['supplemental_archive_audits']),warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=221,next_artifacts=33491+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
