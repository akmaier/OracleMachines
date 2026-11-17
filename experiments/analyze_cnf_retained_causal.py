#!/usr/bin/env python3
"""Attribute retained frontier loading, proof costs and remaining coverage gaps."""
from collections import Counter
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_retained_causal as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');summary=report['summary'];catalog=base.load(out/'cases.json')
    data={m:base.load(out/f'{m}-0/report.json') for m in study.MODES}
    queries={m:base.load(data[m]['queries']['path']) for m in study.MODES}
    banks={m:base.load(data[m]['cofactor_bank']['path']) for m in study.MODES};prepared=banks['retained'];entries=[];used={m:Counter() for m in ('rebuilt','retained')}
    protocol=base.load(out/'protocol.json')
    inherited={(name,r['case']):r for name,entry in zip(study.FIELDS,protocol['prior_decision_catalogs']) for r in base.load(entry['path'])}
    for case in catalog['cases']:
        index=case['case'];rs={m:queries[m][index] for m in study.MODES}
        assert len({r['answer'] for r in rs.values()})==1
        entry=dict(case=index,template_case=case['template_case'],answer=rs['legacy']['answer'],
            expanded={m:r['child']['metrics'].get('expanded_nodes',0) for m,r in rs.items()},
            hits={m:rs[m]['cofactor'] for m in ('rebuilt','retained')},
            target_known={m:r['target_known'] for m,r in rs.items()})
        for m in used:
            if rs[m]['cofactor']:used[m][rs[m]['cofactor']['core']]+=1
        if rs['retained']['cofactor']:
            core=rs['retained']['cofactor']['core'];origin=next(o for o in prepared['origins'] if o['core']==prepared['retained_indices'][core])
            old=inherited[(origin['catalog'],origin['case'])]
            entry['different_first_guard']=old['guard']['removed_clause']!=rs['retained']['guard']['removed_clause']
        entries.append(entry)
    metrics=('expanded_nodes','new_nodes','mean_complete_worker_seconds','mean_query_seconds',
        'mean_complete_peak_rss_bytes','database_bytes','compressed_bytes')
    changes={f'{b}_versus_{a}':{k:100*(summary[b][k]/summary[a][k]-1) for k in metrics}
        for a,b in (('legacy','rebuilt'),('legacy','retained'),('rebuilt','retained'))}
    pairs=[]
    for repeat in range(len(base.load(out/'protocol.json')['orders'])):
        trials={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        pairs.append(dict(repeat=repeat,complete_seconds={m:r['complete_worker_seconds'] for m,r in trials.items()},
            changes={f'{b}_versus_{a}':100*(trials[b]['complete_worker_seconds']/trials[a]['complete_worker_seconds']-1)
                for a,b in (('legacy','rebuilt'),('legacy','retained'),('rebuilt','retained'))}))
    storage={}
    with tempfile.TemporaryDirectory() as td:
        for m in ('rebuilt','retained'):
            path=Path(td)/m;base.restore_archive(data[m]['archive'],path);solver=study.ResidualSolver(path)
            try:saved=study.rows(solver)
            finally:solver.close()
            available=[c for c in banks[m]['cores'] if c['root'] in saved]
            storage[m]=dict(available_proposal_roots=len(available),pending_proposal_roots=len(banks[m]['cores'])-len(available),
                materialization_nodes=data[m]['cofactor_counts'].get('materialization_nodes',0),
                materialization_attempts=data[m]['cofactor_counts'].get('materialization_attempts',0))
    additional=[e['case'] for e in entries if queries['legacy'][e['case']]['cofactor'] is None and queries['retained'][e['case']]['cofactor'] is not None]
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,trials=pairs,
        attribution=entries,additional_support_hit_cases=additional,preparation_counts={m:r['preparation_counts'] for m,r in data.items()},used_core_counts={m:dict(c) for m,c in used.items()},proof_storage=storage,
        remaining_expansions_by_answer={str(v):sum(e['expanded']['retained'] for e in entries if e['answer']==v) for v in (True,False)},
        remaining_expansions_by_template={str(v):sum(e['expanded']['retained'] for e in entries if e['template_case']==v) for v in sorted({e['template_case'] for e in entries})},
        different_first_guard_hits=sum(e.get('different_first_guard',False) for e in entries),
        search_regressions_against_rebuilt=[e for e in entries if e['expanded']['retained']>e['expanded']['rebuilt']],
        search_regressions_against_legacy=[e for e in entries if e['expanded']['retained']>e['expanded']['legacy']],
        differing_hit_cases=[e['case'] for e in entries if e['hits']['rebuilt']!=e['hits']['retained']],
        first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        extraction_counts={m:banks[m]['extraction_counts'] for m in study.MODES},
        core_clause_totals={m:dict(raw=sum(len(c['source']) for c in b['all_cores']),retained=sum(len(c['source']) for c in b['cores'])) for m,b in banks.items()},
        limitations=['Current 18672-key union; legacy loads the 207-entry frontier and retained loads the 176-entry causal frontier, both from the same 389 origins. No new negative sources are added.',
            'Rebuilt reconstructs the same causal frontier and proof archives as retained. Historical acquisition remains charged; loading a paid bank is not free original construction.',
            'All modes retain complete proof/query and used-index lineage checking. Ready roots still require ordinary proof checks; pending roots still require matching causal materialization.',
            'No general minimum-work, cross-guard or arbitrary-SAT bound. Complete clock includes final digest/report generation; imports, CLI reads and wrapper rewrite excluded.'])
    common=[e['case'] for e in entries if queries['legacy'][e['case']]['cofactor'] is not None and queries['retained'][e['case']]['cofactor'] is not None]
    result['overlapping_cofactor_hits']=dict(cases=common,new_rows={m:sum(queries[m][i]['new_nodes'] for i in common) for m in ('legacy','retained')},
        materialization_rows={m:sum(queries[m][i]['new_nodes']-int(queries[m][i]['cofactor']['inserted']) for i in common) for m in ('legacy','retained')})
    result['additional_hit_new_rows']=sum(queries['retained'][i]['new_nodes'] for i in additional)
    result['retained_complete_phase_percent']={name:100*summary['retained']['mean_'+name+'_seconds']/summary['retained']['mean_complete_worker_seconds'] for name in ('preparation','query','cold','compression')}
    result['identical_rebuilt_retained_database_bytes']=all(base.load(out/f'rebuilt-{i}/report.json')['archive']['database_sha256']==base.load(out/f'retained-{i}/report.json')['archive']['database_sha256'] for i in range(3))
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('relative_change_percent','proof_storage','remaining_expansions_by_answer','additional_support_hit_cases','differing_hit_cases')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
