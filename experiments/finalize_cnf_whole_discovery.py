#!/usr/bin/env python3
"""Seal the whole-input coverage/cost tradeoff and an explicit next frontier."""
from collections import Counter
from pathlib import Path
import re, subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_whole_discovery as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json'); v=base.load(out/'validation.json')
    cp=base.load(out/'checkpoint.json'); a=base.load(out/'analysis.json')['summary']
    assert v['passed'] and v['query_audits']==1224 and v['previous_partition_records']==342
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(151,13361)
    for path, entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],
        'experiments/profile_cnf_whole_discovery.py':base.sha('experiments/profile_cnf_whole_discovery.py'),
        'experiments/finalize_cnf_whole_discovery.py':base.sha(__file__)}
    assert len(sources)==865
    for f,h in sources.items():assert base.sha(f)==h,f
    head='e14ca1da';paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    old=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full,focused=[(out/f).read_text() for f in ('full-tests.log','focused-tests.log')]
    assert re.search(r'Ran 1620 tests in .*\n\nOK',full)
    assert re.search(r'Ran 29 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    pairs=[];coverage={}
    for split in study.SPLITS:
        cases=study.bound(p['cases'][split]); coverage[split]={}
        for mode in study.MODES:
            rows=base.load(out/f'{split}-{mode}-0/queries.json')
            roots={c['root'] for c,r in zip(cases,rows) if r['result'] is not None}
            allroots={c['root'] for c in cases}
            coverage[split][mode]=dict(completed_distinct_roots=len(roots),distinct_roots=len(allroots),
                unresolved_distinct_roots=sorted(allroots-roots),statuses=dict(Counter(r['status'] for r in rows)))
            assert len(roots)==(48 if split=='exposed' else 47)
        assert coverage[split]['current']['unresolved_distinct_roots']==coverage[split]['lookahead']['unresolved_distinct_roots']
        for repeat in range(4):
            x,y=[base.load(out/f'{split}-{mode}-{repeat}/report.json')['summary'] for mode in study.MODES]
            pairs.append(dict(split=split,repeat=repeat,query_change=y['query_seconds']/x['query_seconds']-1,
                worker_change=y['complete_worker_seconds']/x['complete_worker_seconds']-1))
    assert all(x['query_change']>0 for x in pairs)
    assert a['exposed']['current']['counters']['expanded_nodes']==1330
    assert a['exposed']['lookahead']['counters']['expanded_nodes']==1169
    assert a['holdout']['current']['counters']['expanded_nodes']==2567
    assert a['holdout']['lookahead']['counters']['expanded_nodes']==2142
    assert a['exposed']['lookahead']['counters']['whole_probe_misses']==310
    assert a['holdout']['lookahead']['counters']['whole_probe_misses']==499
    cases=study.bound(p['cases']['holdout'])
    oldrows,newrows=[base.load(out/f'holdout-{mode}-0/queries.json') for mode in study.MODES]
    assert oldrows[36]['status']=='unresolved' and newrows[36]['status']=='sat'
    assert newrows[36]['metrics']['expanded_nodes']==251
    assert oldrows[1]['status']==newrows[1]['status']=='unresolved'
    profile=base.load(out/'profiling.json');assert len(profile['records'])==6
    for r in profile['records']:
        assert base.sha(r['profile']['path'])==r['profile']['sha256']
        row=base.load(out/f"{r['split']}-{r['mode']}-0/queries.json")[r['case']]
        assert (row['status'],row['metrics'])==(r['result']['status'],r['result']['metrics'])
    frontier=dict(protocol=study.binding(out/'protocol.json'),analysis=study.binding(out/'analysis.json'),
        profiling=study.binding(out/'profiling.json'),coverage=coverage,pairs=pairs,
        cases=[dict(case=cases[i],current=oldrows[i],lookahead=newrows[i]) for i in (0,1,2,36,37,38)],
        decision='Keep optional: earlier completion and smaller retained proofs, but no distinct-root coverage gain and higher solve/query time.',
        next_question='Recognize useful whole-clause probes cheaply and reuse prepared cofactors; price failed probes and preserve exact cached negative authority on random and shared mixtures. Freeze a new holdout before tuning.',
        limitations=p['limitations']+profile['limitations']+[
            'Both policies eventually complete 47/48 distinct held-out roots. Counts of unresolved attempts include a base root completed on repeat.',
            'Holdout case 36 gains first-pass completion within an expansion cap, not a matched wall-time speedup. Case 1 remains unresolved.',
            'Full-suite SQLite ResourceWarnings are pre-existing; focused tests have none. All 64 prior proof environments are unchanged.',
            'The exposed isolated profile has 224 dispatches; chronological replay has a different retained prefix and 220. Do not conflate these profiles.',
            'Development failures are preserved: archive destination absent; root-counter test included recursive calls; audit table order and absent unused legacy tables needed adapter corrections.'])
    base.write(out/'next-target.json',frontier)
    cp['source_fingerprints']=sources
    cp['whole_discovery'].update(next_target=study.binding(out/'next-target.json'),
        profile=study.binding(out/'profiling.json'),decision=frontier['decision'])
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=857,final_sources=len(sources),
        prior_artifacts=13361,prior_manifests=151,full_tests=1620,focused_tests=29,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        source_fingerprints=sources,final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out/'checkpoint.json'),limitations=frontier['limitations']+v['limitations']))
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=13361+len(files),next_manifests=152,
        sources=len(sources),pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
