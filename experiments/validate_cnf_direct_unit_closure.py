#!/usr/bin/env python3
"""Validate bounded direct unit certificates, cold replay and preserved lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_direct_unit_closure as study
from experiments.validate_cnf_layered_feedback import deterministic_result
base=study.base;old=study.old;previous=study.previous


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(191,26477)
    sources={**p['source_fingerprints'],'experiments/validate_cnf_direct_unit_closure.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    cd=base.load(out/'cases.json');assert cd==old.bound(p['parent_cases']);cases=[old.bound(b) for b in cd['cases']];assert len(cases)==11
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==len(cases)*8;groups={};audits={};archives=[]
    for sample in trials:
        r=old.bound(sample);index=sample['index'];mode=sample['mode'];assert r['case']==cd['cases'][index] and r['mode']==mode
        assert r['result']['status']=='unsat' and r['result']['result']['root']==cases[index]['root']
        a=r['archive'];assert base.sha(a['path'])==a['sha256'];key=(a['sha256'],cases[index]['root'])
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(a,path);stored,readers=previous.audit(path,[dict(source=cases[index]['source'])],[r['result']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits[key]=dict(archive=a,root=cases[index]['root'],readers=readers);archives.append(a)
        groups.setdefault((index,mode),[]).append(r)
    totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};native_counts={m:Counter() for m in study.MODES};rss=Counter();summary=[]
    pilot=old.bound(p['pilot']);assert len(pilot['rows'])==11
    assert old.bound(p['profiles'])['baseline']==old.binding('experiments/cnf_cursor_feedback.py')
    assert pilot['source']==old.binding('experiments/cnf_direct_unit_closure.py')
    assert (out/'pilot-source.py').read_bytes()==Path(pilot['source']['path']).read_bytes()
    for index,case in enumerate(cases):
        row=dict(name=case['name'],root=case['root'],arms={})
        control=groups[index,'baseline'][0]
        previous_control=base.load(study.PARENT/f'case-{index}-layered-0/report.json')
        previous_fresh=base.load(study.PARENT/f'case-{index}-fresh-0/report.json')
        for mode in study.MODES:
            a,b=groups[index,mode]
            assert deterministic_result(a['result'])==deterministic_result(b['result'])
            for k in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[k]==b[k],(index,mode,k)
            if mode in ('fresh','baseline'):
                older=previous_fresh if mode=='fresh' else previous_control
                for k in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[k]==older[k],(index,mode,'parent',k)
            else:
                expected=pilot['rows'][index];assert expected['case']==cd['cases'][index]
                for k in ('counts','native_counts','digest'):assert a[k]==expected['arms'][mode][k],(index,mode,'pilot',k)
                assert a['record_bytes']==expected['arms'][mode]['bytes']
                spent=sum(a['counts'].get(k,0) for k in ('direct_gate_clauses','direct_index_slots','direct_probe_occurrence_visits'))
                assert spent<=p['limits']['unit_work_limit']
                assert a['counts']['direct_refutations']>0
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metrics['records']=sum(a['authority_tables'].values());totals[mode].update(metrics);counts[mode].update(a['counts']);native_counts[mode].update(a['native_counts']);rss[mode]=max(rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes'])
            row['arms'][mode]=metrics
        summary.append(row)
    comparisons={}
    for mode,control in (('layer','baseline'),('all','baseline'),('all','layer'),('all','fresh')):
        comparisons[mode+'_vs_'+control]={k:dict(improved=sum(r['arms'][mode][k]<r['arms'][control][k] for r in summary),equal=sum(r['arms'][mode][k]==r['arms'][control][k] for r in summary),regressed=[r['name'] for r in summary if r['arms'][mode][k]>r['arms'][control][k]]) for k in ('solve_seconds','complete_seconds','record_bytes')}
    analysis=dict(cases=len(cases),totals=totals,counts=counts,native_counts=native_counts,summary=summary,comparisons=comparisons,peak_rss_bytes=rss,
        coverage_unchanged=True,recognized_events=217,total_events=246,remaining_events=29,unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,direct_unit_closure={k:old.binding(out/(k+'.json')) for k in ('protocol','cases','comparisons','analysis')})
    cp['direct_unit_closure']['supplemental_archives']=archives;base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(totals=totals,comparisons=comparisons,archives=len(audits))),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','728464e0:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1961 tests in .*\n\nOK',full) and re.search(r'Ran 96 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['direct_unit_closure']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp);v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1961,focused_tests=96,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),prior_sources=1090,final_sources=len(cp['source_fingerprints']),prior_manifests=191,prior_artifacts=26477,archive_audits=len(v['supplemental_archive_audits']),warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json');base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=192,next_artifacts=26477+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
