#!/usr/bin/env python3
"""Attribute fresh causal acquisition, coverage, retirement and complete costs."""
from collections import Counter
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_incremental_causal as study
base=study.base


def identity(core):return tuple(sorted(tuple(sorted(c)) for c in core['source']))


def analyze(out):
    report=base.load(out/'report.json');summary=report['summary'];catalog=base.load(out/'cases.json');protocol=base.load(out/'protocol.json')
    data={m:base.load(out/f'{m}-0/report.json') for m in study.MODES};queries={m:base.load(d['queries']['path']) for m,d in data.items()}
    legacy=base.load(protocol['support_index']['path']);causal={m:base.load(d['causal_index']['path']) for m,d in data.items()}
    inherited={(name,r['case']):r for name,entry in zip(study.FIELDS,protocol['prior_decision_catalogs']) for r in base.load(entry['path'])}
    entries=[];choices=Counter();used=Counter()
    for case in catalog['cases']:
        i=case['case'];rs={m:queries[m][i] for m in study.MODES};assert len({r['answer'] for r in rs.values()})==1
        e=dict(case=i,template_case=case['template_case'],answer=rs['fixed']['answer'],
            expanded={m:r['child']['metrics'].get('expanded_nodes',0) for m,r in rs.items()},new_rows={m:r['new_nodes'] for m,r in rs.items()},
            hits={m:r['cofactor'] is not None for m,r in rs.items()},
            materialization_rows={m:r['new_nodes']-int(r['cofactor']['inserted']) if r['cofactor'] else 0 for m,r in rs.items()})
        hit=rs['extended']['cofactor']
        if hit:
            choices[hit['bank']+'_'+hit['choice']]+=1;used[hit['core']]+=1
            bank=legacy if hit['bank']=='legacy' else causal['extended'];origin=next(o for o in bank['origins'] if o['core']==bank['retained_indices'][hit['local_core']])
            old=inherited[(origin['catalog'],origin['case'])]
            e.update(choice=hit['choice'],bank=hit['bank'],origin_catalog=origin['catalog'],
                different_first_guard=old['guard']['removed_clause']!=rs['extended']['guard']['removed_clause'])
        entries.append(e)
    metrics=('expanded_nodes','new_nodes','mean_complete_worker_seconds','mean_query_seconds','mean_complete_peak_rss_bytes','database_bytes','compressed_bytes')
    changes={k:100*(summary['extended'][k]/summary['fixed'][k]-1) for k in metrics}
    pairs=[]
    for repeat in range(len(protocol['orders'])):
        ts={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        pairs.append(dict(repeat=repeat,complete_seconds={m:r['complete_worker_seconds'] for m,r in ts.items()},
            relative_change_percent={k:100*(ts['extended'][k]/ts['fixed'][k]-1) for k in ('complete_worker_seconds','complete_peak_rss_bytes')}))
    retained={identity(c) for c in causal['extended']['cores']};retired=[c for c in causal['fixed']['cores'] if identity(c) not in retained]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'initial';base.restore_archive(base.load(protocol['parent']['path'])['reference_union'],path);s=study.ResidualSolver(path)
        try:initial={row[0] for row in s.db.execute('SELECT id FROM cnf_residual_v1')}
        finally:s.close()
    additional=[e['case'] for e in entries if e['hits']['extended'] and not e['hits']['fixed']]
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,trials=pairs,attribution=entries,
        proof_choices=dict(choices),used_core_counts=dict(used),additional_hit_cases=additional,
        additional_hit_saved_expansions=sum(e['expanded']['fixed']-e['expanded']['extended'] for e in entries if e['case'] in additional),
        expansion_regressions=[e['case'] for e in entries if e['expanded']['extended']>e['expanded']['fixed']],
        acquisition=dict(origin_records=causal['extended']['delta_origin_count'],extraction_counts=causal['extended']['extraction_counts'],merge_counts=causal['extended']['merge_counts']),
        frontiers={m:dict(raw=len(b['all_cores']),retained=len(b['cores']),origins=len(b['origins']),retained_clauses=sum(len(c['source']) for c in b['cores']),
            initial_ready=sum(c['root'] in initial for c in b['cores'])) for m,b in causal.items()},
        retired_prior_entries=dict(count=len(retired),initial_ready=sum(c['root'] in initial for c in retired)),
        remaining_expansions_by_answer={str(v):sum(e['expanded']['extended'] for e in entries if e['answer']==v) for v in (True,False)},
        remaining_expansions_by_template={str(v):sum(e['expanded']['extended'] for e in entries if e['template_case']==v) for v in sorted({e['template_case'] for e in entries})},
        different_first_guard_hits=sum(e.get('different_first_guard',False) for e in entries),
        hits_first_bound_to_new_catalog=sum(e.get('origin_catalog') in study.FIELDS[len(study.OLD_FIELDS):] for e in entries),
        first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        extended_complete_phase_percent={n:100*summary['extended']['mean_'+n+'_seconds']/summary['extended']['mean_complete_worker_seconds'] for n in ('preparation','query','cold','compression')},
        limitations=['All costs measured on the same 19543-key union and 192 novel neighbours, excluding 2112 prior sidecar answers and cached roots. Four alternating fresh-process pairs.',
            'Extended acquisition uses 137 new guarded negative records; its old dependencies may be visited. Original acquisition remains separately charged. Complete old and new lineage checks remain mandatory.',
            'Smaller supports do not necessarily mean cheaper proofs. Retired entries remain in raw history; the lookup frontier can omit a cheaper ready alternative.',
            'All new index serialization bytes are charged. No established amortization, cross-guard or arbitrary-SAT polynomial bound.'])
    result['identical_trial_proof_databases']=len({base.load(sample['path'])['archive']['database_sha256'] for sample in report['samples']})==1
    result['verification_placement']={m:dict(preparation_verified_nodes=data[m]['preparation_counts'].get('verified_nodes',0),
        query_verified_nodes=sum(r['premise_counts'].get('verified_nodes',0)+r['child']['metrics'].get('verified_nodes',0) for r in queries[m])) for m in study.MODES}
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('relative_change_percent','proof_choices','frontiers','retired_prior_entries','additional_hit_cases','remaining_expansions_by_answer','expansion_regressions')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
