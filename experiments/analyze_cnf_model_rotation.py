#!/usr/bin/env python3
"""Post-hoc cost attribution, preserved regressions and remaining rotation work."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_model_rotation as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');catalog=base.load(out/'cases.json');cases=catalog['cases'];streams={}
    for mode in study.MODES:
        streams[mode]=base.load(out/f'{mode}-0/queries.json')[:len(cases)]
    state=base.load(out/'rotation-0/rotation.json');groups=[]
    for ti,template in enumerate(catalog['templates']):
        group=dict(template_case=template['case'],modes={})
        for mode,stream in streams.items():
            rows=[r for r in stream if cases[r['case']]['template']==ti]
            group['modes'][mode]=dict(queries=len(rows),sat=sum(r['answer'] for r in rows),
                expanded=sum(r['child']['metrics'].get('expanded_nodes',0) for r in rows),
                unsat_expanded=sum(r['child']['metrics'].get('expanded_nodes',0) for r in rows if not r['answer']))
        t=state['templates'][ti];remaining=sum(len(t['source'][m['clause']]) for m in t['models'][t['cursor']:])-t['next_literal']
        group['rotation']=dict(models=len(t['models']),origins=dict(Counter(m['origin']['kind'] for m in t['models'])),
            attempts=len(t['attempts']),successful_flips=sum(len(a['falsified'])==1 for a in t['attempts']),
            false_clause_histogram=dict(Counter(len(a['falsified']) for a in t['attempts'])),
            publications=sum(a['published'] for a in t['attempts']),remaining_queued_flips=remaining)
        groups.append(group)
    rows=streams['rotation'];regressions=[];top=[]
    for row in rows:
        case=cases[row['case']];ordinary=streams['ordinary'][row['case']];guard=streams['guarded'][row['case']]
        assert row['answer']==ordinary['answer']==guard['answer']
        item=dict(case=row['case'],template_case=case['template_case'],removed_clause=case['removed_clause'],
            source_root_sha256=base.key_sha(case['root']),target_root_sha256=base.key_sha(row['child']['root']),
            answer=row['answer'],expanded=row['child']['metrics'].get('expanded_nodes',0),
            guarded_expanded=guard['child']['metrics'].get('expanded_nodes',0),splits=row['child']['metrics'].get('split_nodes',0))
        top.append(item)
        if item['expanded']>item['guarded_expanded']:regressions.append(item)
    summary=report['summary'];g=summary['guarded'];r=summary['rotation']
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),groups=groups,
        remaining_by_answer={str(a):dict(queries=sum(x['answer']==a for x in rows),expanded=sum(x['child']['metrics'].get('expanded_nodes',0) for x in rows if x['answer']==a)) for a in (True,False)},
        regression_queries=regressions,largest_remaining=sorted(top,key=lambda x:(-x['expanded'],x['case']))[:20],
        guarded_to_rotation_reductions_percent={k:100*(1-r[k]/g[k]) for k in ('expanded_nodes','new_nodes','mean_wall_seconds','mean_peak_rss_bytes','database_bytes','compressed_bytes')},
        total_first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        next_target='Extract and independently check reusable UNSAT proof supports or common negative cofactors before further increasing rotation effort. Never treat a failed rotation as UNSAT.',
        limitations=['Post-hoc attribution, not an independently selected validation corpus.',
            'Cold engine state and all failures are saved, but no engine-state import/resume API is implemented or claimed.',
            'One witness per clause and two exhausted per-template flip budgets leave alternative paths unexplored. The third queue is exhausted only for its chosen representatives.',
            'Query order and cache interaction can redistribute work; per-query regressions are retained.',
            'Reference SAT decisions do not expand the separate structural-family coverage catalog.'])
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('remaining_by_answer','guarded_to_rotation_reductions_percent','total_first_trial_storage_bytes')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
