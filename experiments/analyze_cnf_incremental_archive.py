#!/usr/bin/env python3
"""Separate accounting savings from unchanged search and retained proof space."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_incremental_archive as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');summary=report['summary'];catalog=base.load(out/'cases.json')
    rows=base.load(out/'delta-0/queries.json');first=[r for r in rows if r['visit']==0]
    changes={}
    for old,new in (('scanned','ledger'),('ledger','delta'),('scanned','delta')):
        changes[old+' -> '+new]={k:100*(summary[new][k]/summary[old][k]-1) for k in
            ('mean_wall_seconds','mean_query_seconds','mean_repeat_query_seconds','mean_peak_rss_bytes','database_bytes','compressed_bytes')}
    attribution=[];by_template={}
    for case,row in zip(catalog['cases'],first):
        assert case['case']==row['case']
        entry=dict(case=row['case'],template_case=case['template_case'],removed=case['removed'],answer=row['answer'],
            query_sha256=base.key_sha(case['root']),expanded=row['child']['metrics'].get('expanded_nodes',0),new_nodes=row['new_nodes'],
            core_hit=row['core'] is not None,witness_hit=row['witness'] is not None,guard_used=row['guard'] is not None)
        attribution.append(entry);totals=by_template.setdefault(case['template_case'],Counter())
        totals.update(queries=1,positive=int(row['answer']),expanded=entry['expanded'],new_nodes=entry['new_nodes'],
            core_hits=int(entry['core_hit']),witness_hits=int(entry['witness_hit']),guard_uses=int(entry['guard_used']))
    assert sum(a['expanded'] for a in attribution)==summary['delta']['expanded_nodes']
    delta=summary['delta'];phase_fields=('setup_seconds','query_seconds','cold_seconds','compression_seconds')
    phases={f:dict(seconds=delta['mean_'+f],percent=100*delta['mean_'+f]/delta['mean_wall_seconds']) for f in phase_fields}
    phases['other_worker_seconds']=dict(seconds=delta['mean_wall_seconds']-sum(v['seconds'] for v in phases.values()))
    phases['other_worker_seconds']['percent']=100*phases['other_worker_seconds']['seconds']/delta['mean_wall_seconds']
    runs=[]
    for repeat in range(3):
        trial={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        runs.append(dict(repeat=repeat,wall_seconds={m:t['wall_seconds'] for m,t in trial.items()},
            delta_wall_reduction_percent=100*(1-trial['delta']['wall_seconds']/trial['scanned']['wall_seconds']),
            delta_rss_change_percent=100*(trial['delta']['peak_rss_bytes']/trial['scanned']['peak_rss_bytes']-1)))
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,
        delta_phase_costs=phases,balanced_trials=runs,attribution=attribution,by_template=by_template,
        remaining_expansions_by_answer={str(a):sum(r['expanded'] for r in attribution if r['answer']==a) for a in (True,False)},
        largest_expansion_cases=sorted(attribution,key=lambda r:(-r['expanded'],r['case']))[:10],
        full_row_snapshots={m:base.load(out/f'{m}-0/report.json')['accounting']['full_row_snapshots'] for m in study.MODES},
        first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        limitations=['Post-hoc arithmetic on frozen matched runs; no profiler overlaps timed workers.',
            'Same persisted cores and initial union in all modes. Earlier support extraction and historical acquisition remain separately charged; no cumulative break-even result.',
            'All query answers, certificates and search counters are identical. This is bookkeeping acceleration, not better SAT search or broader certified structural closure.',
            'Peak RSS is a process high-water mark including construction and cold replay. Its regression is measured but not attributed to a specific allocation phase here.',
            'Cold audit and compression still touch the full history. The cursor assumes an exclusively owned append-only session and retains full initial/final preservation checks.',
            'Constructed neighbouring deletions, not a blind or independent arbitrary-SAT sample.'])
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('relative_change_percent','delta_phase_costs','by_template','remaining_expansions_by_answer')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
