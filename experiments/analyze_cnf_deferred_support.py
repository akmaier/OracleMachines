#!/usr/bin/env python3
"""Attribute a matched construction-policy study without future-aware selection."""
from collections import Counter
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_deferred_support as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');summary=report['summary'];catalog=base.load(out/'cases.json')
    data={m:base.load(out/f'{m}-0/report.json') for m in study.MODES}
    queries={m:base.load(data[m]['queries']['path']) for m in study.MODES}
    prepared=base.load(data['deferred']['cofactor_bank']['path']);entries=[];used={m:Counter() for m in ('eager','deferred')}
    protocol=base.load(out/'protocol.json')
    inherited={(name,r['case']):r for name,entry in zip(study.FIELDS,protocol['prior_decision_catalogs']) for r in base.load(entry['path'])}
    for case in catalog['cases']:
        index=case['case'];rs={m:queries[m][index] for m in study.MODES}
        assert len({r['answer'] for r in rs.values()})==1
        entry=dict(case=index,template_case=case['template_case'],answer=rs['current']['answer'],
            expanded={m:r['child']['metrics'].get('expanded_nodes',0) for m,r in rs.items()},
            hits={m:rs[m]['cofactor'] for m in ('eager','deferred')},
            target_known={m:r['target_known'] for m,r in rs.items()})
        for m in used:
            if rs[m]['cofactor']:used[m][rs[m]['cofactor']['core']]+=1
        if rs['deferred']['cofactor']:
            core=rs['deferred']['cofactor']['core'];origin=next(o for o in prepared['origins'] if o['core']==prepared['retained_indices'][core])
            old=inherited[(origin['catalog'],origin['case'])]
            entry['different_first_guard']=old['guard']['removed_clause']!=rs['deferred']['guard']['removed_clause']
        entries.append(entry)
    metrics=('expanded_nodes','new_nodes','mean_complete_worker_seconds','mean_query_seconds',
        'mean_complete_peak_rss_bytes','database_bytes','compressed_bytes')
    changes={f'{b}_versus_{a}':{k:100*(summary[b][k]/summary[a][k]-1) for k in metrics}
        for a,b in (('current','eager'),('current','deferred'),('eager','deferred'))}
    pairs=[]
    for repeat in range(len(base.load(out/'protocol.json')['orders'])):
        trials={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        pairs.append(dict(repeat=repeat,complete_seconds={m:r['complete_worker_seconds'] for m,r in trials.items()},
            changes={f'{b}_versus_{a}':100*(trials[b]['complete_worker_seconds']/trials[a]['complete_worker_seconds']-1)
                for a,b in (('current','eager'),('current','deferred'),('eager','deferred'))}))
    storage={}
    with tempfile.TemporaryDirectory() as td:
        for m in ('eager','deferred'):
            path=Path(td)/m;base.restore_archive(data[m]['archive'],path);solver=study.ResidualSolver(path)
            try:saved=study.rows(solver)
            finally:solver.close()
            nodes={k:base.load_json(v) for k,v in saved.items()};hashed={base.key_sha(k):k for k in saved}
            def closure(roots):
                seen=set();stack=list(roots)
                while stack:
                    key=stack.pop()
                    if key in seen:continue
                    seen.add(key);node=nodes[key]
                    if not node['answer']:
                        proof=node['proof'];stack.extend(proof[f] for f in ('child','low','high') if f in proof)
                return seen
            prep={hashed[k] for k in data['eager']['setup_ids'] if k in hashed}
            live=closure(r['child']['root'] for r in queries[m]);available=[c for c in prepared['cores'] if c['root'] in nodes]
            storage[m]=dict(eager_preparation_nodes_present=len(prep),eager_preparation_nodes_needed_by_queries=len(prep&live),
                eager_preparation_nodes_not_needed_by_queries=len(prep-live),available_proposal_roots=len(available),
                pending_proposal_roots=len(prepared['cores'])-len(available),materialization_nodes=data[m]['cofactor_counts'].get('materialization_nodes',0),
                materialization_attempts=data[m]['cofactor_counts'].get('materialization_attempts',0))
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,trials=pairs,
        attribution=entries,used_core_counts={m:dict(c) for m,c in used.items()},proof_storage=storage,
        remaining_expansions_by_answer={str(v):sum(e['expanded']['deferred'] for e in entries if e['answer']==v) for v in (True,False)},
        remaining_expansions_by_template={str(v):sum(e['expanded']['deferred'] for e in entries if e['template_case']==v) for v in sorted({e['template_case'] for e in entries})},
        different_first_guard_hits=sum(e.get('different_first_guard',False) for e in entries),
        search_regressions_against_eager=[e for e in entries if e['expanded']['deferred']>e['expanded']['eager']],
        search_regressions_against_current=[e for e in entries if e['expanded']['deferred']>e['expanded']['current']],
        differing_hit_cases=[e['case'] for e in entries if e['hits']['eager']!=e['hits']['deferred']],
        first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        limitations=['Historical pre-acquisition construction-policy ablation, not a comparison against loading the existing ready bank in the latest authority.',
            'No proposal is a certificate. Only a checked negative materialized core may publish a subset wrapper; exact guarded composition remains required.',
            'Matched neighbouring development queries do not establish cross-category generalization, unrestricted efficiency or minimal construction.',
            'Complete worker timing includes final digest/report generation, unlike older wall_seconds; imports, CLI reads and wrapper report rewrite remain excluded.',
            'Proof liveness is post-hoc attribution, not an online pruning policy. No previous result, proof or failed trial is deleted.'])
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('relative_change_percent','proof_storage','remaining_expansions_by_answer','differing_hit_cases')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
