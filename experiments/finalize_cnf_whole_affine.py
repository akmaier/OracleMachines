#!/usr/bin/env python3
"""Seal whole-input affine completion, coverage and total-cost evidence."""
from collections import Counter
from pathlib import Path
import re, subprocess, sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_whole_affine as study
from experiments.cnf_affine_patterns import check_affine
from experiments.cnf_residual_dag import normalize
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json'); v=base.load(out/'validation.json')
    cp=base.load(out/'checkpoint.json'); a=base.load(out/'analysis.json')['summary']
    assert v['passed'] and v['query_audits']==1728 and v['previous_partition_records']==342
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(153,13586)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],
        'experiments/profile_cnf_whole_affine.py':base.sha('experiments/profile_cnf_whole_affine.py'),
        'experiments/inspect_cnf_affine_frontier.py':base.sha('experiments/inspect_cnf_affine_frontier.py'),
        'experiments/finalize_cnf_whole_affine.py':base.sha(__file__)}
    assert len(sources)==879
    for f,h in sources.items():assert base.sha(f)==h,f
    head='366a47c6';paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    old=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full,focused=[(out/f).read_text() for f in ('full-tests.log','focused-tests.log')]
    assert re.search(r'Ran 1638 tests in .*\n\nOK',full)
    assert re.search(r'Ran 47 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    coverage={};pairs=[]
    for split in study.SPLITS:
        cases=study.bound(p['cases'][split]);coverage[split]={}
        for mode in study.MODES:
            rows=base.load(out/f'{split}-{mode}-0/queries.json')
            roots={c['root'] for c,r in zip(cases,rows) if r['result'] is not None}
            allroots={c['root'] for c in cases};assert len(allroots)==48
            coverage[split][mode]=dict(completed_distinct_roots=len(roots),distinct_roots=len(allroots),
                unresolved_distinct_roots=sorted(allroots-roots),statuses=dict(Counter(r['status'] for r in rows)))
        for repeat in range(4):
            x,y=[base.load(out/f'{split}-{mode}-{repeat}/report.json')['summary'] for mode in ('ordered','completion')]
            pairs.append(dict(split=split,repeat=repeat,solve_change=y['solve_seconds']/x['solve_seconds']-1,
                query_change=y['query_seconds']/x['query_seconds']-1,
                worker_change=y['complete_worker_seconds']/x['complete_worker_seconds']-1))
    assert [coverage['exposed'][m]['completed_distinct_roots'] for m in study.MODES]==[38,39,40]
    assert [coverage['holdout'][m]['completed_distinct_roots'] for m in study.MODES]==[38,38,38]
    for repeat in range(4):
        assert v['table_digests'][f'holdout-ordered-{repeat}']==v['table_digests'][f'holdout-completion-{repeat}']
    for field in ('native_payload','affine_payload','extension_payload','checked_python_bytes','database_bytes','compressed_bytes'):
        assert a['holdout']['ordered'][field]==a['holdout']['completion'][field]
    assert not any(row['known_in_parent'] for row in p['novelty']['holdout'])
    fresh_rows=base.load(out/'holdout-completion-0/queries.json')
    assert fresh_rows[69]['status']=='unsat' and fresh_rows[69]['metrics']['expanded_nodes']==246
    assert fresh_rows[70]['status']=='unresolved' and fresh_rows[70]['metrics']['expanded_nodes']==256
    assert fresh_rows[60]['status']=='unresolved' and fresh_rows[62]['status']=='unsat'
    oldrows,newrows=[base.load(out/f'exposed-{mode}-0/queries.json') for mode in ('ordered','completion')]
    assert oldrows[43]['status']=='unresolved' and newrows[43]['status']=='unsat'
    counts=newrows[43]['metrics']
    assert counts['whole_affine_candidates']==16 and counts['whole_affine_negative_publications']==1
    assert counts.get('expanded_nodes',0)==0 and newrows[43]['result']['authority']=='cnf-affine-negative-v1'
    assert len(v['completion_audits'])==4
    assert all(row['split']=='exposed' and row['case']==43 and row['answer'] is False for row in v['completion_audits'])
    inspection=base.load(out/'frontier-inspection.json');cases=study.bound(p['cases']['holdout'])
    inspected=set()
    for r in inspection['records']:
        cnf,names=normalize(cases[r['case']]['source'])
        assert check_affine(cnf,r['affine'],Counter())==r['summary']
        assert len(names)-r['summary']['rank']==r['free']
        inspected.add(r['root'])
    assert inspected==set(coverage['holdout']['completion']['unresolved_distinct_roots'])
    profile=base.load(out/'profiling.json');assert len(profile['records'])==8
    for r in profile['records']:
        assert base.sha(r['profile']['path'])==r['profile']['sha256']
        row=base.load(out/f"{r['split']}-{r['mode']}-0/queries.json")[r['case']]
        assert (row['status'],row['metrics'])==(r['result']['status'],r['result']['metrics'])
    frontier=dict(protocol=study.binding(out/'protocol.json'),analysis=study.binding(out/'analysis.json'),
        profiling=study.binding(out/'profiling.json'),inspection=study.binding(out/'frontier-inspection.json'),coverage=coverage,pairs=pairs,
        exposed_case43=dict(case=study.bound(p['cases']['exposed'])[43],ordered=oldrows[43],completion=newrows[43]),
        chronological_next_cases=[dict(case=cases[i],result=fresh_rows[i]) for i in (60,61,62,69,70,71)],
        completion_audits=v['completion_audits'],
        decision='Retain bounded whole-input affine completion as an optional integrated policy; keep its measured coverage and all total-cost comparisons separate from unrestricted SAT claims.',
        next_question='Test automatic extraction and partial reuse of the checked whole-CNF proof from fresh case 69 on its still-unresolved edit 70. Identify the lost source support and surviving branches without a supplied family label, guard or future answer; price extraction and recomposition with the existing partial-cover machinery. Random-three inputs dominate time and remain no-equation controls; case 61 is an additional unresolved mixed interaction.',
        limitations=p['limitations']+profile['limitations']+inspection['limitations']+[
            'Completion enumerates at most 2^d affine candidates for d<=8; native dispatch counts alone omit this work, independent space checks and publication.',
            'Positive completion is native full-source model authority; negative exhaustion uses the existing separate affine extension. Native certificates never depend on extension answers.',
            'Development-test failure retained: a complete four-variable cube needs only one extraction XOR, so the corrected XOR-stop fixture adds a second cube.',
            'Selected retained Python size excludes native and transient allocations. Cold replay and compression are charged separately; cumulative archive growth includes all alternative raw trials.',
            'The full suite retains pre-existing SQLite ResourceWarnings; focused tests have none. All 64 prior proof environments are unchanged.'])
    base.write(out/'next-target.json',frontier)
    cp['source_fingerprints']=sources
    cp['whole_affine'].update(next_target=study.binding(out/'next-target.json'),
        profile=study.binding(out/'profiling.json'),decision=frontier['decision'])
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=872,final_sources=len(sources),
        prior_artifacts=13586,prior_manifests=153,full_tests=1638,focused_tests=47,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        source_fingerprints=sources,final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out/'checkpoint.json'),limitations=frontier['limitations']+v['limitations']))
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=13586+len(files),next_manifests=154,
        sources=len(sources),pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
