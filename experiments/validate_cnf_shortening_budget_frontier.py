#!/usr/bin/env python3
"""Audit budget-prefix invariance, certified gains, native costs and lineage."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip,re,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_shortening_budget_frontier as study
base=study.base;old=study.old;previous=study.previous


def extends(a,b):
    assert a['steps']==b['steps'][:len(a['steps'])]
    if a['reason']!='root_limit':assert a==b


def validate(out):
    start=time.perf_counter();p=base.load(out/'protocol.json');parent=old.bound(p['parent']);pv=base.load(study.PARENT/'validation.json')
    manifests=deepcopy(pv['parent_manifests']);mp=Path(p['parent_manifest']['path']);old.bound(p['parent_manifest'])
    manifests[str(mp)]=dict(sha256=base.sha(mp),artifacts_checked=len(base.load(mp)['artifacts']));artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f;artifacts+=1
    assert (len(manifests),artifacts)==(179,21482)
    diagnosis=base.load(out/'residual-diagnosis.json')
    assert diagnosis['program_source']==old.binding(out/'censuses.json')
    sources={**p['source_fingerprints'],**diagnosis['source_fingerprints'],'experiments/validate_cnf_shortening_budget_frontier.py':base.sha(__file__)}
    for f,h in sources.items():assert base.sha(f)==h,f
    samples=base.load(out/'censuses.json')['samples'];assert len(samples)==80
    rows={m:{} for m in study.MODES};groups={};totals={m:Counter() for m in study.MODES};counts={m:Counter() for m in study.MODES};rss=Counter();peaks={m:Counter() for m in study.MODES}
    for sample in samples:
        r=old.bound(sample);mode=sample['mode'];target=sample['target'];assert r['mode']==mode and r['target']==target
        es=old.bound(r['events'])['rows'];groups.setdefault((target,mode),[]).append(es)
        for e in es:
            c=e['counts'];assert c['rounds']<=33 and c.get('reach_roots',0)<=study.root_limit(mode)
            assert sum(c.get(k,0) for k in ('reach_edge_visits','reuse_invalidation_checks','cache_admission_edge_checks'))<=16384
            assert c.get('cache_peak_vertices',0)<=16384
            if sample['repeat']==0:rows[mode][(target,e['event'])]=e
            for key in ('cache_peak_vertices','cache_peak_roots','peak_reach_vertices','context_peak_literal_slots','prepared_input_slots'):
                peaks[mode][key]=max(peaks[mode][key],c.get(key,0))
        totals[mode].update({k:r[k]/2 for k in ('discovery_seconds','binding_seconds','complete_seconds')})
        counts[mode].update({k:v/2 for k,v in r['counts'].items()});rss[mode]=max(rss[mode],r['peak_rss_bytes'])
    for pair in groups.values():
        assert len(pair)==2
        assert [(e['root'],e['program'],e['counts']) for e in pair[0]]==[(e['root'],e['program'],e['counts']) for e in pair[1]]
    assert all(len(rs)==615 and rs.keys()==rows['prepared64'].keys() for rs in rows.values())
    checks=Counter()
    for target in p['targets']:
        source,ts,refs,events=study.prior.reuse.inputs(p,target)
        for mode,oldmode in (('control64','control'),('prepared64','prepared')):
            report=base.load(study.PARENT/f'census-{target}-{oldmode}-0/report.json')
            for e in old.bound(report['events'])['rows']:
                current=rows[mode][(target,e['event'])];assert current['program']==e['program'] and current['counts']==e['counts']
        for ref in refs:
            key=(target,ref['event']);oldp=rows['prepared64'][key]['program']
            for mode in study.MODES[2:]:
                newp=rows[mode][key]['program'];extends(oldp,newp);oldp=newp
            positive=[m for m in study.MODES[1:] if rows[m][key]['program']['status']=='refuted']
            if positive:
                local,hints,_=previous.local_hints(source,ts,events[ref['event']],Counter());templates=[h['template'] for h in hints]
                for mode in positive:study.prior.candidate.validate(local,templates,rows[mode][key]['program'],Counter());checks[mode]+=1
    success={m:{k for k,r in rs.items() if r['program']['status']=='refuted'} for m,rs in rows.items()}
    roots={m:{rows[m][k]['root'] for k in ss} for m,ss in success.items()}
    outcomes={m:dict(Counter('refuted' if r['program']['status']=='refuted' else r['program']['reason'] for r in rs.values())) for m,rs in rows.items()}
    transitions={m:dict(Counter(rows['prepared64'][k]['program']['reason']+' -> '+('refuted' if r['program']['status']=='refuted' else r['program']['reason']) for k,r in rs.items())) for m,rs in rows.items()}
    assert len(success['prepared64'])==266 and len(roots['prepared64'])==173
    coverage={m:dict(events=len(success[m]),roots=len(roots[m]),gained_events=sorted(success[m]-success['prepared64']),lost_events=sorted(success['prepared64']-success[m]),
        gained_roots=sorted(roots[m]-roots['prepared64']),outcomes=outcomes[m],transitions_from64=transitions[m]) for m in study.MODES}
    observed_frontier=[m for m in study.MODES if not any(totals[n]['complete_seconds']<=totals[m]['complete_seconds'] and len(success[n])>=len(success[m]) and
        (totals[n]['complete_seconds']<totals[m]['complete_seconds'] or len(success[n])>len(success[m])) for n in study.MODES if n!=m)]
    within_old=[m for m in study.MODES[1:] if totals[m]['discovery_seconds']<=totals['control64']['discovery_seconds'] and totals[m]['complete_seconds']<=totals['control64']['complete_seconds']]
    case_data=base.load(out/'cases.json');cases=[old.bound(b) for b in case_data['cases']]
    assert {c['root'] for c in cases}==roots['prepared256']-roots['prepared64']
    for case in cases:
        r=rows[case['mode']][(case['target'],case['event'])];assert case['root']==r['root'] and case['program']==r['program']
        study.prior.candidate.validate(case['source'],case['templates'],case['program'],Counter())
    # Recheck presence in the ordinary whole-query snapshots used by the study.
    residuals={(r['target'],r['event']):r for r in diagnosis['rows']}
    assert residuals.keys()==rows['prepared256'].keys()-success['prepared256']
    for key,r in residuals.items():
        assert r['reason']==rows['prepared256'][key]['program']['reason'] and r['root']==rows['prepared256'][key]['root']
        assert r['forced_steps']==len(rows['prepared256'][key]['program']['steps'])
    presence={}
    for target in p['targets']:
        query=base.load(f'experiments/results/cnf-guard-covers/serial/target-{target}-census-0/report.json')
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/'db';previous.restore_archive(query['archive'],path);reader=previous.CanonicalVerifySnapshot(path)
            affine=previous.TerminalStore(reader);equiv=previous.MultiEquivalenceStore(reader)
            try:
                for case in cases:
                    if case['target']!=target:continue
                    found=reader._read(case['root']) is not None or affine.read(case['root']) is not None or equiv.read(case['root']) is not None
                    assert found==case['present_after_query'];presence[case['root']]=found
                for (target_id,event),r in residuals.items():
                    if target_id!=target:continue
                    node=reader._read(r['root'])
                    if node is None:node=affine.read(r['root'])
                    if node is None:node=equiv.read(r['root'])
                    answer='unknown' if node is None else ('sat' if node['answer'] else 'unsat')
                    assert answer==r['snapshot_answer']
                    if r['binary_model_completion_is_sat']:assert answer!='unsat'
            finally:reader.close()
    trials=base.load(out/'comparisons.json')['samples'];assert len(trials)==len(cases)*4;tg={};audits={};archives=[]
    for sample in trials:
        r=old.bound(sample);index=sample['index'];mode=sample['mode'];assert r['case']==case_data['cases'][index] and r['mode']==mode
        if mode=='support':assert r['result']['status']=='unsat'
        if r['result']['status']=='unsat':assert r['result']['result']['root']==cases[index]['root']
        a=r['archive'];assert base.sha(a['path'])==a['sha256'];key=(a['sha256'],cases[index]['root'])
        if key not in audits:
            with tempfile.TemporaryDirectory() as td:
                path=Path(td)/'db';previous.restore_archive(a,path);stored,readers=previous.audit(path,[dict(source=cases[index]['source'])],[r['result']])
            assert {t:len(v) for t,v in stored.items()}==r['authority_tables']
            assert {t:base.key_sha(base.encode(sorted(v.items()))) for t,v in stored.items()}==r['digest']
            assert sum(len(k.encode())+len(v.encode()) for table in stored.values() for k,v in table.items())==r['record_bytes']
            audits[key]=dict(archive=a,root=cases[index]['root'],readers=readers);archives.append(a)
        tg.setdefault((index,mode),[]).append(r)
    trial_totals={m:Counter() for m in ('fresh','support')};trial_rss=Counter();summary=[]
    for index,case in enumerate(cases):
        row=dict(name=case['name'],root=case['root'],present_after_query=case['present_after_query'],arms={})
        for mode in trial_totals:
            a,b=tg[(index,mode)]
            for key in ('counts','native_counts','digest','record_bytes','authority_tables'):assert a[key]==b[key],(index,mode,key)
            assert a['result']['status']==b['result']['status']
            metrics={k:(a[k]+b[k])/2 for k in ('solve_seconds','warm_seconds','cold_seconds','persistence_seconds','complete_seconds','record_bytes')}
            metrics['records']=sum(a['authority_tables'].values());trial_totals[mode].update(metrics)
            trial_rss[mode]=max(trial_rss[mode],a['peak_rss_bytes'],b['peak_rss_bytes']);row['arms'][mode]=dict(status=a['result']['status'],**metrics)
        summary.append(row)
    incremental={}
    for mode in study.MODES[1:]:
        selected=[r for r in summary if r['root'] in roots[mode]-roots['prepared64']]
        incremental[mode]={arm:dict(sum((Counter({k:r['arms'][arm][k] for k in ('solve_seconds','cold_seconds','complete_seconds','record_bytes','records')}) for r in selected),Counter())) for arm in trial_totals}
    edits=base.load(out/'edits.json');oldedits=old.bound(edits['cases_binding']);assert len(edits['rows'])==960
    eg={};es={m:set() for m in study.MODES};et={m:Counter() for m in study.MODES}
    for r in edits['rows']:
        eg.setdefault((r['index'],r['mode']),[]).append(r)
        if r['program']['status']=='refuted':
            case=oldedits['cases'][r['index']];study.prior.candidate.validate(case['source'],case['templates'],r['program'],Counter());es[r['mode']].add(r['index'])
        et[r['mode']].update({k:r[k]/2 for k in ('discovery_seconds','verification_seconds')})
    for pair in eg.values():
        assert len(pair)==2;assert pair[0]['program']==pair[1]['program'] and pair[0]['counts']==pair[1]['counts']
    earlier=base.load(study.PARENT/'edits.json');er={(r['index'],r['mode']):r for r in earlier['rows']}
    for i in range(96):
        for mode,oldmode in (('control64','control'),('prepared64','prepared')):
            assert eg[(i,mode)][0]['program']==er[(i,oldmode)]['program'] and eg[(i,mode)][0]['counts']==er[(i,oldmode)]['counts']
        for a,b in zip(study.MODES[1:],study.MODES[2:]):extends(eg[(i,a)][0]['program'],eg[(i,b)][0]['program'])
    analysis=dict(coverage=coverage,census_totals=totals,census_counts=counts,census_peaks=peaks,census_peak_rss_bytes=rss,positive_program_checks=checks,
        observed_complete_phase_frontier=observed_frontier,observed_within_old64_cost=within_old,
        new_roots=len(cases),not_previously_saved=sum(not v for v in presence.values()),new_beyond_prior_filter_union=sum(not c['in_prior_filter_union'] for c in cases),
        trial_totals=trial_totals,trial_max_rss_bytes=trial_rss,trial_summary=summary,incremental_local_trials=incremental,
        trial_statuses={m:dict(Counter(r['arms'][m]['status'] for r in summary)) for m in trial_totals},
        edit_coverage={m:dict(events=len(v),gained=sorted(v-es['prepared64']),lost=sorted(es['prepared64']-v)) for m,v in es.items()},edit_totals=et,
        residual_diagnosis=diagnosis['summary'],unique_archive_audits=len(audits),sources=len(sources),limitations=p['limitations']+['Incremental local trial sums use isolated databases for each newly recognized root; their bytes can duplicate shared subproofs. They are not cumulative-bank growth or an end-to-end pipeline timing. The observed cost frontier is descriptive, not a statistical or instance-wise guarantee.'])
    base.write(out/'analysis.json',analysis)
    cp=deepcopy(parent);cp.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        shortening_budget_frontier={k:old.binding(out/(k+'.json')) for k in ('protocol','censuses','cases','comparisons','edits','residual-diagnosis','analysis')})
    cp['shortening_budget_frontier']['supplemental_archives']=archives;base.write(out/'checkpoint.json',cp)
    base.write(out/'validation.json',dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        reference_union_unchanged=cp['reference_union']==parent['reference_union'],preserved_tables=pv['preserved_tables'],new_cumulative_records=0,
        supplemental_archive_audits=list(audits.values()),seconds=time.perf_counter()-start,checkpoint=old.binding(out/'checkpoint.json')))
    print(base.encode(dict(coverage={m:dict(events=len(success[m]),roots=len(roots[m]),outcomes=outcomes[m]) for m in study.MODES},totals=totals,within_old=within_old,trial_totals=trial_totals,new_roots=len(cases),edits=analysis['edit_coverage'])),flush=True)


def seal(out):
    v=base.load(out/'validation.json');assert v['passed'];cp=base.load(out/'checkpoint.json')
    for f,h in cp['source_fingerprints'].items():assert base.sha(f)==h,f
    paper='paper/bounded_domain_sat_and_amortized_reasoning.tex';before=subprocess.check_output(['git','show','d869f249:'+paper],text=True)
    pat=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pat,before,re.S);assert len(proofs)==64 and proofs==re.findall(pat,Path(paper).read_text(),re.S)
    full=(out/'full-tests.log').read_text();focus=(out/'focused-tests.log').read_text();latex=(out/'latex-final.log').read_text()
    assert re.search(r'Ran 1865 tests in .*\n\nOK',full) and re.search(r'Ran 12 tests in .*\n\nOK',focus)
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    cp['shortening_budget_frontier']['decision']=old.binding(out/'decision.json');base.write(out/'checkpoint.json',cp)
    v['checkpoint']=old.binding(out/'checkpoint.json');base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,full_tests=1865,focused_tests=12,proof_blocks_unchanged=64,manuscript_pages=int(re.search(r'\((\d+) pages,',latex)[1]),
        prior_sources=1036,final_sources=len(cp['source_fingerprints']),prior_manifests=179,prior_artifacts=21482,archive_audits=len(v['supplemental_archive_audits']),
        warnings=dict(full=full.count('ResourceWarning: unclosed database'),focused=focus.count('ResourceWarning: unclosed database')),checkpoint=old.binding(out/'checkpoint.json')))
    for f in out.rglob('*.log'):
        raw=f.read_bytes();Path(str(f)+'.raw.gz').write_bytes(gzip.compress(raw,mtime=0));f.write_text('\n'.join(line.rstrip() for line in raw.decode().splitlines()).rstrip()+'\n')
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(sealed=True,artifacts=len(files),next_manifests=180,next_artifacts=21482+len(files))))


if __name__=='__main__':globals()[sys.argv[1]](Path(sys.argv[2]))
