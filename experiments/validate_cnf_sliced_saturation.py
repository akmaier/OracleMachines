#!/usr/bin/env python3
"""Audit causal slicing, matched native graphs and immutable research lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_sliced_saturation as s
from experiments.validate_cnf_layered_feedback import deterministic_result
base=s.base;old=s.old
METRICS=('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(s.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(217,32817)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_sliced_saturation.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    assert len(sources)==1203
    assert (out/'pilot-source.py').read_bytes()==Path(s.FILES[0]).read_bytes()
    initial=(out/'initial-comparison.py').read_text()
    assert initial.replace('from experiments import compare_cnf_probe_saturation as parent,cnf_sliced_saturation_native as sliced','# Load the old base first to bound import nesting through the frozen history.\nfrom experiments import compare_cnf_bootstrap\nfrom experiments import compare_cnf_probe_saturation as parent,cnf_sliced_saturation_native as sliced')==Path(s.FILES[1]).read_text()
    assert 'RecursionError: maximum recursion depth exceeded' in (out/'initial-import-failure.log').read_text()
    cases={name:old.bound(binding) for name,binding in p['cases'].items()};assert cases==s.build_cases()
    sliced_audits={}
    for name,case in cases.items():
        prepared,program=s.parent.compiler.prepare(*case['inputs'],case['search'],saturation=case['saturation'],counts=Counter(),**case['options'])
        banks=prepared[1::2];books=[(14+len(case['saturation']['rounds']),None,program['proof'])]
        # Check every new round trace independently, including ones not visited by conversion.
        for i,row in enumerate(case['saturation']['rounds']):
            books.extend((14+i,probe['assumption'],probe['proof']) for probe in row['search']['program']['probes'])
        cc=Counter()
        for stage,assumption,proof in books:
            compact,_=s.sliced.slice_trace(banks[stage],proof,assumption,cc)
            s.sliced.frozen.check_trace(prepared[0],banks[stage],assumption,compact,Counter(),256)
            assert len(compact['units'])<=len(proof['units'])
        sliced_audits[name]=dict(checked_traces=len(books),counts=dict(cc))
    samples=base.load(out/'comparisons.json')['samples'];assert len(samples)==32
    assert {(x['name'],x['mode'],x['repeat']) for x in samples}=={(name,mode,i) for name in cases for mode in s.MODES for i in range(4)}
    groups={};audits={};archives=[]
    for sample in samples:
        report=old.bound(sample);name=sample['name'];mode=sample['mode'];case=cases[name]
        assert (report['name'],report['mode'],report['case'])==(name,mode,p['cases'][name])
        assert report['result']['status']=='unsat' and report['result']['result']['root']==case['root']
        archive=report['archive'];assert base.sha(archive['path'])==archive['sha256'];key=archive['sha256'],case['root']
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                db=Path(td)/'db';s.previous.restore_archive(archive,db)
                tables,readers=s.previous.audit(db,[dict(source=case['source'])],[report['result']])
            assert {t:len(v) for t,v in tables.items()}==report['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in tables.items()}==report['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in tables.values() for k,v in table.items())==report['record_bytes']
            assert all(not records for table,records in tables.items() if table!='cnf_residual_v1')
            audits[key]=dict(name=name,archive=archive,root=case['root'],status='unsat',readers=readers);archives.append(archive)
        groups.setdefault((name,mode),[]).append(report)
    pilot=base.load(out/'pilot.json');budget=base.load(out/'budget-pilot.json');picked=groups['cascade','sliced'][0]
    assert base.sha(pilot['archive']['path'])==pilot['archive']['sha256']==picked['archive']['sha256']
    assert deterministic_result(pilot['result'])==deterministic_result(picked['result'])
    for record,mode in ((pilot,'sliced'),(budget,'full_large')):
        first=groups['cascade',mode][0]
        assert record['record_bytes']==first['record_bytes'] and record['records']==sum(first['authority_tables'].values())
        assert record['counts']==first['counts']
    for mode,old_mode in (('full','direct'),('fresh','fresh')):
        original=base.load(s.PARENT/f'native-{old_mode}-0/report.json');first=groups['cascade',mode][0]
        for key in ('digest','authority_tables','record_bytes'):assert first[key]==original[key]
    totals={};counts={};rss={};records={};archive_bytes={};ratios={};selected={}
    for name in cases:
        totals[name]={};counts[name]={};rss[name]={};records[name]={};archive_bytes[name]={}
        for mode in s.MODES:
            reports=groups[name,mode];assert len(reports)==4
            for report in reports:
                assert deterministic_result(report['result'])==deterministic_result(reports[0]['result'])
                for key in ('counts','warm_counts','native_counts','digest','record_bytes','authority_tables'):assert report[key]==reports[0][key],(name,mode,key)
            totals[name][mode]={key:sum(r[key] for r in reports)/4 for key in METRICS};counts[name][mode]=reports[0]['counts'];rss[name][mode]=max(r['peak_rss_bytes'] for r in reports)
            records[name][mode]=sum(reports[0]['authority_tables'].values());archive_bytes[name][mode]=Path(reports[0]['archive']['path']).stat().st_size
            if mode!='fresh':
                assert reports[0]['warm_counts']['saturation_native_extension_hits']==1
                spent=sum(reports[0]['counts'].get(key,0) for key in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))
                assert spent<=p['limits']['large_unit_work_limit' if mode=='full_large' else 'unit_work_limit']
            if mode=='sliced':
                assert counts[name][mode]['support_trace_kept']<counts[name][mode]['support_trace_steps']
                assert reports[0]['warm_counts'].get('slice_unique_traces',0)==0
        ratios[name]={baseline:{key:totals[name]['sliced'][key]/totals[name][baseline][key] for key in METRICS} for baseline in ('full','full_large','fresh')}
        # A recommendation only; all four arms and their native certificates remain intact.
        best=min(s.MODES,key=lambda mode:totals[name][mode]['complete_seconds']);selected[name]=dict(mode=best,archive=groups[name,best][0]['archive'])
    assert counts['cascade']['full']['direct_budget_skips']>0
    assert counts['cascade']['sliced'].get('direct_budget_skips',0)==counts['cascade']['full_large'].get('direct_budget_skips',0)==0
    remaining=parent['probe_saturation']['remaining'];assert len(s.parent.load_frontier(remaining))==12
    analysis=dict(coverage=dict(before=234,after=234,total=246),remaining_events=12,gained_events=[],
        totals=totals,counts=counts,peak_rss_bytes=rss,native_records=records,compressed_archive_bytes=archive_bytes,sliced_over_baseline=ratios,
        selected=selected,independent_sliced_trace_audits=sliced_audits,unique_archive_audits=len(audits),remaining=remaining,limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        sliced_saturation={key:old.binding(out/(key+'.json')) for key in ('protocol','comparisons','analysis')})
    cp['sliced_saturation'].update(remaining=remaining,supplemental_archives=archives);base.write(out/'checkpoint.json',cp)
    assert all(cp[key]==value for key,value in parent.items() if key not in ('parent_checkpoint','source_fingerprints'))
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),parent_native_archives_unchanged=True,seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,records=records,ratios=ratios,archive_audits=len(audits))))


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','f642a462:'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,before,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 2183 tests in .*\n\nOK',full) and re.search(r'Ran 22 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['sliced_saturation']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=2183,focused_tests=22,proof_blocks_unchanged=64,
        manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1199,final_sources=len(cp['source_fingerprints']),
        prior_manifests=217,prior_artifacts=32817,new_native_archives=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=218,next_artifacts=32817+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
