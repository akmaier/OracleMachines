#!/usr/bin/env python3
"""Attribute checked proof selection, expansion coverage and complete costs."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_proof_choice as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');summary=report['summary'];catalog=base.load(out/'cases.json');protocol=base.load(out/'protocol.json')
    data={m:base.load(out/f'{m}-0/report.json') for m in study.MODES};queries={m:base.load(d['queries']['path']) for m,d in data.items()}
    banks={n:base.load(protocol[f]['path']) for n,f in [('legacy','support_index'),('causal','causal_index')]}
    inherited={(name,r['case']):r for name,entry in zip(study.FIELDS,protocol['prior_decision_catalogs']) for r in base.load(entry['path'])}
    entries=[];choices=Counter();used=Counter()
    for case in catalog['cases']:
        i=case['case'];rs={m:queries[m][i] for m in study.MODES};assert len({r['answer'] for r in rs.values()})==1
        entry=dict(case=i,template_case=case['template_case'],answer=rs['legacy']['answer'],
            expanded={m:r['child']['metrics'].get('expanded_nodes',0) for m,r in rs.items()},
            new_rows={m:r['new_nodes'] for m,r in rs.items()},hits={m:r['cofactor'] is not None for m,r in rs.items()},
            materialization_rows={m:r['new_nodes']-int(r['cofactor']['inserted']) if r['cofactor'] else 0 for m,r in rs.items()})
        hit=rs['portfolio']['cofactor']
        if hit:
            choices[hit['bank']+'_'+hit['choice']]+=1;used[hit['core']]+=1
            bank=banks[hit['bank']];origin=next(o for o in bank['origins'] if o['core']==bank['retained_indices'][hit['local_core']])
            old=inherited[(origin['catalog'],origin['case'])]
            entry.update(choice=hit['choice'],bank=hit['bank'],different_first_guard=old['guard']['removed_clause']!=rs['portfolio']['guard']['removed_clause'])
        entries.append(entry)
    comparisons=(('legacy','causal'),('legacy','portfolio'),('causal','portfolio'))
    metrics=('expanded_nodes','new_nodes','mean_complete_worker_seconds','mean_query_seconds','mean_complete_peak_rss_bytes','database_bytes','compressed_bytes')
    changes={f'{b}_versus_{a}':{k:100*(summary[b][k]/summary[a][k]-1) for k in metrics} for a,b in comparisons}
    pairs=[]
    for repeat in range(len(protocol['orders'])):
        trials={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        pairs.append(dict(repeat=repeat,complete_seconds={m:r['complete_worker_seconds'] for m,r in trials.items()},
            relative_change_percent={f'{b}_versus_{a}':{k:100*(trials[b][k]/trials[a][k]-1) for k in ('complete_worker_seconds','complete_peak_rss_bytes')} for a,b in comparisons}))
    common=[e for e in entries if all(e['hits'].values())]
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,trials=pairs,attribution=entries,
        proof_choices=dict(choices),used_core_counts=dict(used),cofactor_counts={m:r['cofactor_counts'] for m,r in data.items()},
        overlapping_hits=dict(cases=[e['case'] for e in common],materialization_rows={m:sum(e['materialization_rows'][m] for e in common) for m in study.MODES}),
        additional_hit_cases={m:[e['case'] for e in entries if e['hits'][m] and not e['hits']['legacy']] for m in ('causal','portfolio')},
        expansion_regressions={m:[e['case'] for e in entries if e['expanded']['portfolio']>e['expanded'][m]] for m in ('legacy','causal')},
        remaining_expansions_by_answer={str(v):sum(e['expanded']['portfolio'] for e in entries if e['answer']==v) for v in (True,False)},
        remaining_expansions_by_template={str(v):sum(e['expanded']['portfolio'] for e in entries if e['template_case']==v) for v in sorted({e['template_case'] for e in entries})},
        different_first_guard_hits=sum(e.get('different_first_guard',False) for e in entries),
        first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        portfolio_complete_phase_percent={n:100*summary['portfolio']['mean_'+n+'_seconds']/summary['portfolio']['mean_complete_worker_seconds'] for n in ('preparation','query','cold','compression')},
        limitations=['Same acquired 19091-key union and eight-catalog 389-origin frontiers. 1920 earlier sidecar answers and all cached roots excluded. Historical acquisition remains charged.',
            'Portfolio references both immutable histories, audits both full lineages and checks every chosen proof. Compact provenance references do not remove earlier storage or checking costs.',
            'Ready-first followed by legacy-first fallback is a heuristic. Ready proof checking can be costly, and changed proof choices affect later sharing and retained space.',
            'All counters are workload observations. No general minimum-work, cross-guard, blind arbitrary-SAT or uniform-polynomial bound.'])
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('relative_change_percent','proof_choices','overlapping_hits','remaining_expansions_by_answer','additional_hit_cases','expansion_regressions')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
