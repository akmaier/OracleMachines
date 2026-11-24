#!/usr/bin/env python3
"""Seal binary-probe coverage, full costs, regressions and preserved authority."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_probe_binary_closure as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and (v['query_audits'],v['diagnostic_query_audits'],v['census_events'])==(1152,68,353)
    assert v['census_verdicts']['binary-unsat']==19 and v['previous_partition_records']==342
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(158,14286)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],
        'experiments/profile_cnf_probe_binary_closure.py':base.sha('experiments/profile_cnf_probe_binary_closure.py'),
        'experiments/finalize_cnf_probe_binary_closure.py':base.sha(__file__)}
    assert len(sources)==918
    for f,h in sources.items():assert base.sha(f)==h,f
    head='9e5e897e';paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    old=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}';proofs=re.findall(pattern,old,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full,focused=[(out/f).read_text() for f in ('full-tests.log','focused-tests.log')]
    assert re.search(r'Ran 1689 tests in .*\n\nOK',full)
    focus_count=int(re.search(r'Ran (\d+) tests in .*\n\nOK',focused)[1]);assert focus_count==78
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text();assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    analysis=base.load(out/'analysis.json')['summary'];coverage={};pairs=[];frontiers={};comparisons={};queries={}
    for split in study.SPLITS:
        cases=study.bound(p['cases'][split]);coverage[split]={};queries[split]={};sets={}
        allroots={c['root'] for c in cases};assert len(allroots)==48
        for mode in study.MODES:
            allrows=[base.load(out/f'{split}-{mode}-{i}/queries.json') for i in range(4)];rows=allrows[0]
            roots={c['root'] for c,r in zip(cases,rows) if r['result'] is not None};sets[mode]=roots
            coverage[split][mode]=dict(completed_distinct_roots=len(roots),distinct_roots=48,statuses=dict(Counter(r['status'] for r in rows)))
            queries[split][mode]=[dict(case=c['case'],family=c['family'],root=c['root'],status=r['status'],
                mean_solve_seconds=sum(rr[i]['solve_seconds'] for rr in allrows)/4,metrics=r['metrics']) for i,(c,r) in enumerate(zip(cases,rows))]
        frontiers[split]=dict(gained_roots=sorted(sets['closure']-sets['current']),lost_roots=sorted(sets['current']-sets['closure']),
            unresolved_roots=sorted(allroots-sets['closure']))
        x,y=analysis[split]['current'],analysis[split]['closure']
        comparisons[split]={k:y[k]/x[k]-1 for k in ('mean_solve_seconds','mean_complete_worker_seconds','mean_peak_rss_bytes','native_payload','native_nodes','checked_python_bytes','database_bytes','compressed_bytes')}
        comparisons[split]['expanded_nodes']=y['counters']['expanded_nodes']/x['counters']['expanded_nodes']-1
        for repeat in range(4):
            a=base.load(out/f'{split}-current-{repeat}/report.json')['summary'];b=base.load(out/f'{split}-closure-{repeat}/report.json')['summary']
            pairs.append(dict(split=split,repeat=repeat,solve_change=b['solve_seconds']/a['solve_seconds']-1,
                worker_change=b['complete_worker_seconds']/a['complete_worker_seconds']-1))
    assert not any(r['known_in_parent'] for r in p['novelty']['holdout'])
    profile=base.load(out/'profiling.json');assert len(profile['records'])==2
    for r in profile['records']:
        assert base.sha(r['profile']['path'])==r['profile']['sha256']
        row=base.load(out/f"holdout-{r['mode']}-0/queries.json")[r['case']]
        assert (row['status'],row['metrics'])==(r['result']['status'],r['result']['metrics'])
    decision=base.load(out/'decision.json')
    frontier=dict(protocol=study.binding(out/'protocol.json'),analysis=study.binding(out/'analysis.json'),
        profiling=study.binding(out/'profiling.json'),coverage=coverage,frontiers=frontiers,
        comparisons=comparisons,pairs=pairs,queries=queries,decision=decision,
        archive_reader=cp['reference_union_reader'],limitations=p['limitations']+v['limitations']+profile['limitations']+[
            'More certified cofactors need not improve whole-input coverage, total time or retained space. Full costs and regressions remain visible.',
            'All 64 preceding proof environments are unchanged; the full suite retains pre-existing SQLite ResourceWarnings.',
            'The initial guard-test failure and its fixture correction remain preserved. No population performance or unrestricted tractability guarantee is inferred.'])
    base.write(out/'next-target.json',frontier)
    cp['source_fingerprints']=sources;cp['probe_binary_closure'].update(next_target=study.binding(out/'next-target.json'),
        profile=study.binding(out/'profiling.json'),decision=decision);base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=909,final_sources=len(sources),
        prior_artifacts=14286,prior_manifests=158,full_tests=1689,focused_tests=focus_count,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        source_fingerprints=sources,final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),limitations=frontier['limitations']))
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=14286+len(files),next_manifests=159,
        sources=len(sources),pages=pages,warnings=warnings,tables=v['preserved_tables'],coverage=coverage,comparisons=comparisons)),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
