#!/usr/bin/env python3
"""Seal complete-pool priority, all regressions and the next discovery target."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_whole_pool_priority as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and (v['query_audits'],v['regression_query_audits'])==(1728,144)
    assert v['previous_partition_records']==342
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(155,13851)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],
        'experiments/profile_cnf_whole_pool_priority.py':base.sha('experiments/profile_cnf_whole_pool_priority.py'),
        'experiments/finalize_cnf_whole_pool_priority.py':base.sha(__file__)}
    assert len(sources)==895
    for f,h in sources.items():assert base.sha(f)==h,f
    head='40052c5f';paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    old=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full,focused=[(out/f).read_text() for f in ('full-tests.log','focused-tests.log')]
    assert re.search(r'Ran 1661 tests in .*\n\nOK',full)
    focus_count=int(re.search(r'Ran (\d+) tests in .*\n\nOK',focused)[1])
    assert focus_count>=50
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    analysis=base.load(out/'analysis.json')['summary'];coverage={};pairs=[];unresolved={}
    for split in study.SPLITS:
        cases=study.bound(p['cases'][split]);coverage[split]={}
        for mode in study.MODES:
            rows=base.load(out/f'{split}-{mode}-0/queries.json')
            roots={c['root'] for c,r in zip(cases,rows) if r['result'] is not None}
            allroots={c['root'] for c in cases};assert len(allroots)==48 and len(roots)==42
            coverage[split][mode]=dict(completed_distinct_roots=len(roots),distinct_roots=len(allroots),
                statuses=dict(Counter(r['status'] for r in rows)))
            if mode=='priority':
                seen=set();unresolved[split]=[]
                for c,r in zip(cases,rows):
                    if c['root'] not in roots and c['root'] not in seen:
                        seen.add(c['root']);unresolved[split].append(dict(case=c,attempt=r))
        for repeat in range(4):
            y=base.load(out/f'{split}-priority-{repeat}/report.json')['summary']
            for control in ('completion','reuse'):
                x=base.load(out/f'{split}-{control}-{repeat}/report.json')['summary']
                pairs.append(dict(split=split,control=control,repeat=repeat,
                    solve_change=y['solve_seconds']/x['solve_seconds']-1,
                    worker_change=y['complete_worker_seconds']/x['complete_worker_seconds']-1))
    assert not any(r['known_in_parent'] for r in p['novelty']['holdout'])
    prior,new=[base.load(out/f'exposed-{m}-0/queries.json') for m in ('reuse','priority')]
    for i,n in ((31,57),(34,58)):
        assert prior[i]['metrics']['expanded_nodes']==n and new[i]['metrics'].get('expanded_nodes',0)==0
        assert new[i]['result']['whole_pool']['route']=='negative-pool'
    transfer={m:base.load(out/f'transfer-{m}-0/queries.json')[70] for m in ('reuse','priority')}
    assert transfer['reuse']['metrics']['expanded_nodes']==223
    assert all(r['status']=='unsat' and r['metrics']['expanded_nodes']<=256 and 'whole_plan' in r['result'] for r in transfer.values())
    profile=base.load(out/'profiling.json');assert len(profile['records'])==2
    for r in profile['records']:
        assert base.sha(r['profile']['path'])==r['profile']['sha256']
        row=base.load(out/f"holdout-{r['mode']}-0/queries.json")[r['case']]
        assert (row['status'],row['metrics'])==(r['result']['status'],r['result']['metrics'])
    from experiments.cnf_residual_dag import normalize
    for split in (*study.SPLITS,'transfer'):
        cases=study.bound(p['cases'][split]);members={c['root']:set(normalize(c['source'])[0]) for c in cases}
        for row in base.load(out/f'{split}-priority-0/queries.json'):
            r=row['result']
            if r is None:continue
            origin=r['whole_pool']['near_origin'] if 'whole_pool' in r else r['whole_plan']['origin'] if 'whole_plan' in r else None
            if origin is not None:
                assert len(members[origin]-members[r['root']])==1 and members[origin]&members[r['root']]
    base.write(out/'eligibility.json',dict(protocol=study.binding(out/'protocol.json'),
        condition='len(origin_clauses - target_clauses) == 1 and bool(origin_clauses & target_clauses)',
        clarification='Exactly one origin clause is absent from the target; the number of added target clauses is unrestricted. This makes the frozen protocol wording precise and does not change the frozen implementation or inputs.',
        checked_successful_priority_routes=True))
    frontier=dict(protocol=study.binding(out/'protocol.json'),analysis=study.binding(out/'analysis.json'),
        eligibility=study.binding(out/'eligibility.json'),
        profiling=study.binding(out/'profiling.json'),coverage=coverage,pairs=pairs,unresolved=unresolved,
        plan_audits=v['plan_audits'],pool_audits=v['pool_audits'],transfer=transfer,
        decision='Keep explicit arbitration and its miss costs. Complete-pool priority avoids known unnecessary expansion while preserving partial fallback; this adds no distinct-root coverage.',
        next_question='Return to the six unresolved fresh random-three roots. Profile the largest unresolved attempt and test whether the prepared cofactor and nonconflicting propagation from whole-clause probes can pass directly to the actual ordinary child. First establish the producer/consumer correspondence and preserve higher-priority recognition. Reuse the existing cnf_cofactor_handoff machinery where applicable, retain its earlier mixed total-cost results, and charge offers that are never consumed. Do not equate nonconflicting propagation with a satisfying model.',
        archive_reader=cp['reference_union_reader'],
        limitations=p['limitations']+profile['limitations']+v['limitations']+[
            'All 64 earlier proof environments are unchanged; the full suite retains pre-existing SQLite ResourceWarnings.',
            'Per-worker payload savings do not retroactively shrink the cumulative union: earlier authoritative payloads remain unchanged, with alternate proofs preserved in raw archives.',
            'Chunking preserves the complete compressed stream and database bytes. It does not reduce cumulative retained storage or the cost of rebuilding the union.'])
    base.write(out/'next-target.json',frontier)
    cp['source_fingerprints']=sources
    cp['whole_pool_priority'].update(next_target=study.binding(out/'next-target.json'),
        profile=study.binding(out/'profiling.json'),eligibility=study.binding(out/'eligibility.json'),decision=frontier['decision'])
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'));base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=887,final_sources=len(sources),
        prior_artifacts=13851,prior_manifests=155,full_tests=1661,focused_tests=focus_count,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,source_fingerprints=sources,
        final_union_tables=v['preserved_tables'],final_checkpoint=study.binding(out/'checkpoint.json'),
        archive_conversion=v['archive_conversion'],limitations=frontier['limitations']))
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=13851+len(files),next_manifests=156,
        sources=len(sources),pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
