#!/usr/bin/env python3
"""Seal bounded whole-proof plans and their causal arbitration follow-up."""
from collections import Counter
from pathlib import Path
import re,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_whole_proof_reuse as study
base=study.base


def finalize(out):
    p=base.load(out/'protocol.json');v=base.load(out/'validation.json');cp=base.load(out/'checkpoint.json')
    assert v['passed'] and v['query_audits']==1728 and v['exploration_query_audits']==142
    assert v['previous_partition_records']==342
    assert (len(v['parent_manifests']),v['prior_artifacts_unchanged'])==(154,13713)
    for path,entry in v['parent_manifests'].items():
        assert base.sha(path)==entry['sha256']
        for f,h in base.load(path)['artifacts'].items():assert base.sha(f)==h,f
    sources={**v['source_fingerprints'],
        'experiments/profile_cnf_whole_proof_reuse.py':base.sha('experiments/profile_cnf_whole_proof_reuse.py'),
        'experiments/finalize_cnf_whole_proof_reuse.py':base.sha(__file__)}
    assert len(sources)==887
    for f,h in sources.items():assert base.sha(f)==h,f
    head='b7f4db11';paper='paper/bounded_domain_sat_and_amortized_reasoning.tex'
    old=subprocess.check_output(['git','show',head+':'+paper],text=True)
    pattern=r'\\begin\{proof\}.*?\\end\{proof\}'
    proofs=re.findall(pattern,old,re.S)
    assert len(proofs)==64 and proofs==re.findall(pattern,Path(paper).read_text(),re.S)
    full,focused=[(out/f).read_text() for f in ('full-tests.log','focused-tests.log')]
    assert re.search(r'Ran 1648 tests in .*\n\nOK',full)
    assert re.search(r'Ran 57 tests in .*\n\nOK',focused)
    warnings={k:len(re.findall('ResourceWarning: unclosed database',s)) for k,s in (('full',full),('focused',focused))}
    assert warnings['focused']==0
    latex=(out/'latex-final.log').read_text()
    assert not re.search(r'Warning|Overfull|Underfull|^!',latex,re.M)
    pages=int(re.search(r'\((\d+) pages,',latex)[1])
    coverage={};pairs=[];unresolved={}
    for split in study.SPLITS:
        cases=study.bound(p['cases'][split]);coverage[split]={}
        for mode in study.MODES:
            rows=base.load(out/f'{split}-{mode}-0/queries.json')
            roots={c['root'] for c,r in zip(cases,rows) if r['result'] is not None}
            allroots={c['root'] for c in cases};assert len(allroots)==48
            coverage[split][mode]=dict(completed_distinct_roots=len(roots),distinct_roots=len(allroots),
                unresolved_distinct_roots=sorted(allroots-roots),statuses=dict(Counter(r['status'] for r in rows)))
            if mode=='reuse':
                seen=set();unresolved[split]=[]
                for c,r in zip(cases,rows):
                    if c['root'] not in roots and c['root'] not in seen:
                        seen.add(c['root']);unresolved[split].append(dict(case=c,attempt=r))
        for repeat in range(4):
            x,y=[base.load(out/f'{split}-{mode}-{repeat}/report.json')['summary'] for mode in ('completion','reuse')]
            pairs.append(dict(split=split,repeat=repeat,solve_change=y['solve_seconds']/x['solve_seconds']-1,
                query_change=y['query_seconds']/x['query_seconds']-1,
                worker_change=y['complete_worker_seconds']/x['complete_worker_seconds']-1))
    assert [coverage['exposed'][m]['completed_distinct_roots'] for m in study.MODES]==[38,38,39]
    assert [coverage['holdout'][m]['completed_distinct_roots'] for m in study.MODES]==[40,42,42]
    assert not any(r['known_in_parent'] for r in p['novelty']['holdout'])
    prior,after=[base.load(out/f'exposed-{m}-0/queries.json') for m in ('completion','reuse')]
    assert prior[70]['status']=='unresolved' and after[70]['status']=='unsat'
    r=after[70];assert r['metrics']['expanded_nodes']==223
    assert r['result']['whole_plan']['origin']==study.bound(p['cases']['exposed'])[69]['root']
    intact=r['result']['whole_plan']['outcome']['intact'];assert len(intact)==27 and sum(intact)==22
    profile=base.load(out/'profiling.json');assert len(profile['records'])==6 and len(profile['pool_checks'])==3
    assert {(r['split'],r['case']):r['route'] for r in profile['pool_checks']}=={
        ('exposed',70):None,('holdout',31):'negative-pool',('holdout',34):'negative-pool'}
    assert all(r['counts'].get('expanded_nodes',0)==0 for r in profile['pool_checks'])
    for r in profile['records']:
        assert base.sha(r['profile']['path'])==r['profile']['sha256']
        row=base.load(out/f"{r['split']}-{r['mode']}-0/queries.json")[r['case']]
        assert (row['status'],row['metrics'])==(r['result']['status'],r['result']['metrics'])
    diagnostic=base.load(out/'exploration/inspection.json')
    assert [r['reason'] for r in diagnostic['trials']]==['Node occurrence budget','Unresolved cover branch']
    frontier=dict(protocol=study.binding(out/'protocol.json'),analysis=study.binding(out/'analysis.json'),
        profiling=study.binding(out/'profiling.json'),coverage=coverage,pairs=pairs,unresolved=unresolved,
        plan_audits=v['plan_audits'],pool_checks=profile['pool_checks'],
        decision='Keep optional: partial proof frontiers add exposed coverage, but recognition and poor priority can displace cheaper complete reuse. Preserve the fresh regressions.',
        next_question='Use the existing cnf_pool_priority.try_pools before committing to a partial plan. Fresh edits 31/34 previously took one dispatch and now take 57/58; exact-prefix probes confirm complete negative-pool results already exist without search. The exposed case-70 pool probe misses and adds work. Preserve its partial transfer, charge those misses, and test arbitration on new inputs.',
        limitations=p['limitations']+profile['limitations']+v['limitations']+[
            'The finite branch plan retains open SAT obligations; bounded discovery does not make those residuals tractable.',
            'The exposed target is certified by ordinary native proofs. Uncovered branches are never inferred negative from the old origin.',
            'The larger and default-budget exploration records are diagnostic; their valid proof nodes are preserved without adding their outcomes to the matched coverage counts.',
            'All 64 previous proof environments remain unchanged; the full suite retains pre-existing SQLite ResourceWarnings.'])
    base.write(out/'next-target.json',frontier)
    cp['source_fingerprints']=sources
    cp['whole_proof_reuse'].update(next_target=study.binding(out/'next-target.json'),
        profile=study.binding(out/'profiling.json'),decision=frontier['decision'])
    base.write(out/'checkpoint.json',cp)
    v.update(source_fingerprints=sources,checkpoint=study.binding(out/'checkpoint.json'))
    base.write(out/'validation.json',v)
    base.write(out/'checks.json',dict(passed=True,baseline_commit=head,prior_sources=879,final_sources=len(sources),
        prior_artifacts=13713,prior_manifests=154,full_tests=1648,focused_tests=57,warnings=warnings,
        manuscript_pages=pages,paper_sha256=base.sha(paper),proof_blocks_unchanged=64,
        source_fingerprints=sources,final_union_tables=v['preserved_tables'],
        final_checkpoint=study.binding(out/'checkpoint.json'),limitations=frontier['limitations']))
    assert base.sha(cp['reference_union']['path'])==cp['reference_union']['sha256']
    files=sorted(f for f in out.rglob('*') if f.is_file() and f.name!='manifest.json')
    base.write(out/'manifest.json',dict(artifacts={str(f):base.sha(f) for f in files}))
    print(base.encode(dict(passed=True,artifacts=len(files),next_artifacts=13713+len(files),next_manifests=155,
        sources=len(sources),pages=pages,warnings=warnings,tables=v['preserved_tables'])),flush=True)


if __name__=='__main__':finalize(Path(sys.argv[1]))
