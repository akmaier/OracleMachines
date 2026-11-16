#!/usr/bin/env python3
"""Attribute incremental discovery, additional matches and remaining expansion work."""
from collections import Counter
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_incremental_support as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');summary=report['summary'];catalog=base.load(out/'cases.json')
    data={m:base.load(out/f'{m}-0/report.json') for m in study.MODES}
    queries={m:base.load(data[m]['queries']['path']) for m in study.MODES}
    prepared=base.load(data['incremental']['cofactor_bank']['path']);entries=[];used={m:Counter() for m in ('rebuild','incremental')}
    protocol=base.load(out/'protocol.json')
    inherited={(name,r['case']):r for name,entry in zip(study.FIELDS,protocol['prior_decision_catalogs']) for r in base.load(entry['path'])}
    for case in catalog['cases']:
        index=case['case'];rs={m:queries[m][index] for m in study.MODES}
        assert len({r['answer'] for r in rs.values()})==1
        entry=dict(case=index,template_case=case['template_case'],answer=rs['ready']['answer'],
            expanded={m:r['child']['metrics'].get('expanded_nodes',0) for m,r in rs.items()},
            hits={m:rs[m]['cofactor'] for m in ('rebuild','incremental')},
            target_known={m:r['target_known'] for m,r in rs.items()})
        for m in used:
            if rs[m]['cofactor']:used[m][rs[m]['cofactor']['core']]+=1
        if rs['incremental']['cofactor']:
            core=rs['incremental']['cofactor']['core'];origin=next(o for o in prepared['origins'] if o['core']==prepared['retained_indices'][core])
            old=inherited[(origin['catalog'],origin['case'])]
            entry['different_first_guard']=old['guard']['removed_clause']!=rs['incremental']['guard']['removed_clause']
        entries.append(entry)
    metrics=('expanded_nodes','new_nodes','mean_complete_worker_seconds','mean_query_seconds',
        'mean_complete_peak_rss_bytes','database_bytes','compressed_bytes')
    changes={f'{b}_versus_{a}':{k:100*(summary[b][k]/summary[a][k]-1) for k in metrics}
        for a,b in (('ready','rebuild'),('ready','incremental'),('rebuild','incremental'))}
    pairs=[]
    for repeat in range(len(base.load(out/'protocol.json')['orders'])):
        trials={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        pairs.append(dict(repeat=repeat,complete_seconds={m:r['complete_worker_seconds'] for m,r in trials.items()},
            changes={f'{b}_versus_{a}':100*(trials[b]['complete_worker_seconds']/trials[a]['complete_worker_seconds']-1)
                for a,b in (('ready','rebuild'),('ready','incremental'),('rebuild','incremental'))}))
    storage={}
    with tempfile.TemporaryDirectory() as td:
        for m in ('rebuild','incremental'):
            path=Path(td)/m;base.restore_archive(data[m]['archive'],path);solver=study.ResidualSolver(path)
            try:saved=study.rows(solver)
            finally:solver.close()
            available=[c for c in prepared['cores'] if c['root'] in saved]
            storage[m]=dict(available_proposal_roots=len(available),pending_proposal_roots=len(prepared['cores'])-len(available),
                materialization_nodes=data[m]['cofactor_counts'].get('materialization_nodes',0),
                materialization_attempts=data[m]['cofactor_counts'].get('materialization_attempts',0))
    additional=[e['case'] for e in entries if queries['ready'][e['case']]['cofactor'] is None and queries['incremental'][e['case']]['cofactor'] is not None]
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,trials=pairs,
        attribution=entries,additional_support_hit_cases=additional,used_core_counts={m:dict(c) for m,c in used.items()},proof_storage=storage,
        remaining_expansions_by_answer={str(v):sum(e['expanded']['incremental'] for e in entries if e['answer']==v) for v in (True,False)},
        remaining_expansions_by_template={str(v):sum(e['expanded']['incremental'] for e in entries if e['template_case']==v) for v in sorted({e['template_case'] for e in entries})},
        different_first_guard_hits=sum(e.get('different_first_guard',False) for e in entries),
        search_regressions_against_rebuild=[e for e in entries if e['expanded']['incremental']>e['expanded']['rebuild']],
        search_regressions_against_ready=[e for e in entries if e['expanded']['incremental']>e['expanded']['ready']],
        differing_hit_cases=[e['case'] for e in entries if e['hits']['rebuild']!=e['hits']['incremental']],
        first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        limitations=['Every mode starts from the current 16760-key union and checks the already-ready bank. Extended frontiers use 99 newly acquired negative sources.',
            'Incremental and full rediscovery give identical frontiers, decisions and proof archives; provenance load/checking and raw-coordinate containment still cost work.',
            'No proposal is a certificate. Only a checked negative materialized core may publish a subset wrapper, with exact guarded composition still required.',
            'Matched neighbouring inputs do not establish broad cross-category coverage, unrestricted efficiency, or minimum expansion cost.',
            'Complete worker timing includes final digest/report generation; imports, CLI reads and wrapper report rewrite remain excluded.',
            'Profile ran separately from benchmark workers and overlapped the correctness suite; use its counts and call structure, not elapsed-time comparisons.'])
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('relative_change_percent','proof_storage','remaining_expansions_by_answer','additional_support_hit_cases','differing_hit_cases')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
