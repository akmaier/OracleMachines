#!/usr/bin/env python3
"""Attribute demand-driven core checks while charging complete cold lineage audit."""
from collections import Counter
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_active_support as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');summary=report['summary'];catalog=base.load(out/'cases.json')
    data={m:base.load(out/f'{m}-0/report.json') for m in study.MODES}
    queries={m:base.load(data[m]['queries']['path']) for m in study.MODES}
    prepared=base.load(data['active']['cofactor_bank']['path']);entries=[];used={m:Counter() for m in ('eager','active')}
    protocol=base.load(out/'protocol.json')
    inherited={(name,r['case']):r for name,entry in zip(study.FIELDS,protocol['prior_decision_catalogs']) for r in base.load(entry['path'])}
    for case in catalog['cases']:
        index=case['case'];rs={m:queries[m][index] for m in study.MODES}
        assert len({r['answer'] for r in rs.values()})==1
        entry=dict(case=index,template_case=case['template_case'],answer=rs['loaded']['answer'],
            expanded={m:r['child']['metrics'].get('expanded_nodes',0) for m,r in rs.items()},
            hits={m:rs[m]['cofactor'] for m in ('eager','active')},
            target_known={m:r['target_known'] for m,r in rs.items()})
        for m in used:
            if rs[m]['cofactor']:used[m][rs[m]['cofactor']['core']]+=1
        if rs['active']['cofactor']:
            core=rs['active']['cofactor']['core'];origin=next(o for o in prepared['origins'] if o['core']==prepared['retained_indices'][core])
            old=inherited[(origin['catalog'],origin['case'])]
            entry['different_first_guard']=old['guard']['removed_clause']!=rs['active']['guard']['removed_clause']
        entries.append(entry)
    metrics=('expanded_nodes','new_nodes','mean_complete_worker_seconds','mean_query_seconds',
        'mean_complete_peak_rss_bytes','database_bytes','compressed_bytes')
    changes={f'{b}_versus_{a}':{k:100*(summary[b][k]/summary[a][k]-1) for k in metrics}
        for a,b in (('loaded','eager'),('loaded','active'),('eager','active'))}
    pairs=[]
    for repeat in range(len(base.load(out/'protocol.json')['orders'])):
        trials={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        pairs.append(dict(repeat=repeat,complete_seconds={m:r['complete_worker_seconds'] for m,r in trials.items()},
            changes={f'{b}_versus_{a}':100*(trials[b]['complete_worker_seconds']/trials[a]['complete_worker_seconds']-1)
                for a,b in (('loaded','eager'),('loaded','active'),('eager','active'))}))
    storage={}
    with tempfile.TemporaryDirectory() as td:
        for m in ('eager','active'):
            path=Path(td)/m;base.restore_archive(data[m]['archive'],path);solver=study.ResidualSolver(path)
            try:saved=study.rows(solver)
            finally:solver.close()
            available=[c for c in prepared['cores'] if c['root'] in saved]
            storage[m]=dict(available_proposal_roots=len(available),pending_proposal_roots=len(prepared['cores'])-len(available),
                materialization_nodes=data[m]['cofactor_counts'].get('materialization_nodes',0),
                materialization_attempts=data[m]['cofactor_counts'].get('materialization_attempts',0))
    additional=[e['case'] for e in entries if queries['loaded'][e['case']]['cofactor'] is None and queries['active'][e['case']]['cofactor'] is not None]
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,trials=pairs,
        attribution=entries,additional_support_hit_cases=additional,preparation_counts={m:r['preparation_counts'] for m,r in data.items()},used_core_counts={m:dict(c) for m,c in used.items()},proof_storage=storage,
        remaining_expansions_by_answer={str(v):sum(e['expanded']['active'] for e in entries if e['answer']==v) for v in (True,False)},
        remaining_expansions_by_template={str(v):sum(e['expanded']['active'] for e in entries if e['template_case']==v) for v in sorted({e['template_case'] for e in entries})},
        different_first_guard_hits=sum(e.get('different_first_guard',False) for e in entries),
        search_regressions_against_eager=[e for e in entries if e['expanded']['active']>e['expanded']['eager']],
        search_regressions_against_loaded=[e for e in entries if e['expanded']['active']>e['expanded']['loaded']],
        differing_hit_cases=[e['case'] for e in entries if e['hits']['eager']!=e['hits']['active']],
        first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        limitations=['All workers start from the same current 17161-key union and 151-entry index. Extension uses 42 newly acquired negative sources; all earlier acquisition remains charged.',
            'Both extension modes have identical frontiers, answers and proof archives. Active mode verifies actual matching cores online; all modes run complete cold proof/query and lineage checks.',
            'The joint cold auditor keeps the frozen audit snapshot open for provenance verification, then closes it even after failure; no persisted unchecked validation flags.',
            'The timed audit boundary now includes full proposal lineage, broader than the previous benchmark. Do not multiply historical percentages.',
            'Private append-only live ownership and pinned read-only cold snapshots; no claim for shared mutating services or hostile private connections.',
            'Matched neighbouring inputs do not establish cross-category or unrestricted-SAT efficiency, or minimum expansion work.',
            'Complete clock includes final digest/report generation; imports, CLI reads and wrapper rewrite remain excluded.'])
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('relative_change_percent','proof_storage','remaining_expansions_by_answer','additional_support_hit_cases','differing_hit_cases')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
