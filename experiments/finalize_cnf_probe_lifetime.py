#!/usr/bin/env python3
"""Seal handoff costs, unchanged authority, regressions and the next target."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_lifetime as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and (v['query_audits'],v['diagnostic_query_audits'])==(2304,76)
    assert v['previous_partition_records']==342
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(157,14120)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],'experiments/profile_cnf_probe_lifetime.py':base.sha('experiments/profile_cnf_probe_lifetime.py'),
        'experiments/finalize_cnf_probe_lifetime.py':base.sha(__file__)}
    assert len(sources)==909
    for f,h in sources.items():assert base.sha(f)==h,f
    head='c08e5b64';paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    old=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,old,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full,focused=[(out/f).read_text() for f in ('full-tests.log','focused-tests.log')]
    assert re.search(r'Ran 1677 tests in .*\n\nOK',full)
    focus_count=int(re.search(r'Ran (\d+) tests in .*\n\nOK',focused)[1]);assert focus_count>=40
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    analysis=base.load(out/'analysis.json')['summary'];coverage={};pairs=[];unresolved={};comparisons={};queries={}
    for split in study.SPLITS:
        cases=study.bound(p['cases'][split]);coverage[split]={};comparisons[split]={};queries[split]={}
        control=analysis[split]['retain']
        for mode in study.MODES:
            allrows=[base.load(out/f'{split}-{mode}-{repeat}/queries.json') for repeat in range(4)];rows=allrows[0]
            roots={c['root'] for c,r in zip(cases,rows) if r['result'] is not None};allroots={c['root'] for c in cases};assert len(allroots)==48
            coverage[split][mode]=dict(completed_distinct_roots=len(roots),distinct_roots=48,statuses=dict(Counter(r['status'] for r in rows)))
            queries[split][mode]=[dict(case=c['case'],family=c['family'],status=r['status'],
                mean_solve_seconds=sum(rr[i]['solve_seconds'] for rr in allrows)/4,metrics=r['metrics']) for i,(c,r) in enumerate(zip(cases,rows))]
            if mode=='transfer':
                seen=set();unresolved[split]=[]
                for c,r in zip(cases,rows):
                    if c['root'] not in roots and c['root'] not in seen:
                        seen.add(c['root']);unresolved[split].append(dict(case=c,attempt=r))
            if mode=='retain':continue
            candidate=analysis[split][mode]
            comparisons[split][mode]={k:candidate[k]/control[k]-1 for k in ('mean_solve_seconds','mean_complete_worker_seconds','mean_peak_rss_bytes','native_payload','checked_python_bytes')}
            comparisons[split][mode]['peak_offer_bytes']=max(r['metrics']['whole_handoff_peak_bytes'] for r in rows)
            if mode in ('clear','transfer'):
                comparisons[split][mode]['full_visit_envelope_peak_bytes']=max(r['metrics']['whole_lifetime_full_visit_envelope_peak_bytes'] for r in rows)
                comparisons[split][mode]['transferred_peak_bytes']=max(r['metrics']['whole_lifetime_transferred_peak_bytes'] for r in rows)
            comparisons[split][mode]['solve_change_vs_room']=candidate['mean_solve_seconds']/analysis[split]['room']['mean_solve_seconds']-1
            comparisons[split][mode]['worker_change_vs_room']=candidate['mean_complete_worker_seconds']/analysis[split]['room']['mean_complete_worker_seconds']-1
            for repeat in range(4):
                x=base.load(out/f'{split}-retain-{repeat}/report.json')['summary'];y=base.load(out/f'{split}-{mode}-{repeat}/report.json')['summary']
                z=base.load(out/f'{split}-room-{repeat}/report.json')['summary']
                pairs.append(dict(split=split,mode=mode,repeat=repeat,solve_change=y['solve_seconds']/x['solve_seconds']-1,
                    worker_change=y['complete_worker_seconds']/x['complete_worker_seconds']-1,
                    solve_change_vs_room=y['solve_seconds']/z['solve_seconds']-1,
                    worker_change_vs_room=y['complete_worker_seconds']/z['complete_worker_seconds']-1))
        assert all(coverage[split][m]==coverage[split]['retain'] for m in study.MODES)
    assert not any(r['known_in_parent'] for r in p['novelty']['holdout'])
    profile=base.load(out/'profiling.json');assert len(profile['records'])==4
    for r in profile['records']:
        assert base.sha(r['profile']['path'])==r['profile']['sha256']
        row=base.load(out/f"holdout-{r['mode']}-0/queries.json")[r['case']]
        assert (row['status'],row['metrics'])==(r['result']['status'],r['result']['metrics'])
        assert (row['status'],row['metrics'])==(r['allocation']['status'],r['allocation']['metrics'])
        assert r['allocation']['prefix_payloads_equal']
        assert r['allocation']['peak_bytes']>=r['allocation']['current_bytes']>=0
    frontier=dict(protocol=study.binding(out/'protocol.json'),analysis=study.binding(out/'analysis.json'),
        profiling=study.binding(out/'profiling.json'),coverage=coverage,pairs=pairs,comparisons=comparisons,
        queries=queries,unresolved=unresolved,
        decision='Keep all four policies experimental. Early release saves acquisition time versus 2 MiB retention but has mixed signs against original 4 MiB retention. Cleanup alone does not improve solve mean. The pending cap changes scope; neither the full-visit envelope nor the target allocation trace demonstrates a substantial memory saving. Proof storage and structural coverage are unchanged.',
        next_question='Census exact nonconflicting whole-probe residuals on fresh case 37 and unresolved mixture edits 61/67 for existing source-bound binary refutations, including required post-UP restriction and source lifting. Case 37 has 145 binary SCC checks, ten refutations, 135 satisfiable-subset misses and 49 whole-probe misses; no additional probe refutation has yet been demonstrated. Price both polarities and failed recognition before implementing a gate. Case 61 retains 20/25 prior proof leaves but its remaining acquisition still exhausts 256 dispatches. Broader certified interaction is the primary gap; consult previous proof-normalization memo regressions before addressing the 372 negative-child checks as supporting runtime work.',
        archive_reader=cp['reference_union_reader'],limitations=p['limitations']+v['limitations']+profile['limitations']+[
            'All 64 earlier proof environments are unchanged. The full suite retains pre-existing SQLite ResourceWarnings.',
            'Timing signs and regressions remain visible across all four pairs. No population speedup or process-memory bound is inferred from selected payload accounting.',
            'Old authoritative payloads and failed development checks remain preserved; the cumulative union can grow even when each policy produces identical current-stream proofs.'])
    base.write(out/'next-target.json',frontier)
    cp['source_fingerprints']=sources;cp['probe_lifetime'].update(next_target=study.binding(out/'next-target.json'),
        profile=study.binding(out/'profiling.json'),decision=frontier['decision']);base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=902,final_sources=len(sources),
        prior_artifacts=14120,prior_manifests=157,full_tests=1677,focused_tests=focus_count,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),limitations=frontier['limitations']))
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=14120+len(files),next_manifests=158,
        sources=len(sources),pages=pages,warnings=warnings,tables=v['preserved_tables'],comparisons=comparisons)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
