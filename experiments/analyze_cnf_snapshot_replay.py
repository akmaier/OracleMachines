#!/usr/bin/env python3
"""Attribute cold metadata savings without claiming new structural coverage."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_snapshot_replay as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');summary=report['summary'];a=summary['ordinary_audit'];b=summary['snapshot_audit']
    catalog=base.load(out/'cases.json');records=base.load(out/'snapshot_audit-0/queries.json');first=[r for r in records if r['visit']==0]
    changes={k:100*(b[k]/a[k]-1) for k in ('mean_wall_seconds','mean_cold_seconds','mean_query_seconds','mean_peak_rss_bytes','database_bytes','compressed_bytes')}
    phases={f:dict(seconds=b['mean_'+f],percent=100*b['mean_'+f]/b['mean_wall_seconds']) for f in ('setup_seconds','query_seconds','cold_seconds','compression_seconds')}
    other=b['mean_wall_seconds']-sum(x['seconds'] for x in phases.values());phases['other_worker_seconds']=dict(seconds=other,percent=100*other/b['mean_wall_seconds'])
    cases=[];templates={}
    for case,row in zip(catalog['cases'],first):
        assert case['case']==row['case'];expanded=row['child']['metrics'].get('expanded_nodes',0)
        entry=dict(case=row['case'],template_case=case['template_case'],removed=case['removed'],query_sha256=base.key_sha(case['root']),
            answer=row['answer'],expanded=expanded,new_nodes=row['new_nodes'],core_hit=row['core'] is not None,
            witness_hit=row['witness'] is not None,guard_used=row['guard'] is not None)
        cases.append(entry);totals=templates.setdefault(case['template_case'],Counter())
        totals.update(queries=1,positive=int(row['answer']),expanded=expanded,queries_with_fresh_search=int(expanded>0),
            new_nodes=row['new_nodes'],core_hits=int(entry['core_hit']),guard_uses=int(entry['guard_used']))
    trials=[]
    for repeat in range(4):
        x=base.load(out/f'ordinary_audit-{repeat}/report.json')['summary'];y=base.load(out/f'snapshot_audit-{repeat}/report.json')['summary']
        trials.append(dict(repeat=repeat,ordinary_wall_seconds=x['wall_seconds'],snapshot_wall_seconds=y['wall_seconds'],
            wall_reduction_percent=100*(1-y['wall_seconds']/x['wall_seconds']),cold_reduction_percent=100*(1-y['cold_seconds']/x['cold_seconds']),
            rss_change_percent=100*(y['peak_rss_bytes']/x['peak_rss_bytes']-1)))
    assert sum(c['expanded'] for c in cases)==b['expanded_nodes']
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,phase_costs=phases,trials=trials,
        attribution=cases,by_template=templates,queries_with_fresh_search=sum(c['expanded']>0 for c in cases),
        remaining_expansions_by_answer={str(value):sum(c['expanded'] for c in cases if c['answer']==value) for value in (True,False)},
        largest_expansion_cases=sorted(cases,key=lambda c:(-c['expanded'],c['case']))[:10],
        first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        limitations=['Post-hoc arithmetic on frozen matched trials; no profiler overlaps the timed workers.',
            'The census is independently computed from the pinned snapshot, not trusted from the persisted ledger. Every proof and query is still checked.',
            'Same search counts, proof rows and archives in both modes. No broader structural coverage, proof compression or arbitrary-SAT efficiency result.',
            'New constructed neighbouring edits with all 384 earlier answered queries excluded. Earlier acquisition remains charged separately.',
            'Peak RSS is whole-process high-water memory, not a phase-specific allocation trace.'])
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('relative_change_percent','phase_costs','queries_with_fresh_search','remaining_expansions_by_answer','by_template')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
