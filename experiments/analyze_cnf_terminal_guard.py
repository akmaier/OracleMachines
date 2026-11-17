#!/usr/bin/env python3
"""Attribute bounded guard changes, repeated selection and full resource costs."""
from collections import Counter
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_terminal_guard as study
from experiments.cnf_clause_deletion_guard import check_guard,clause_set
base=study.base


def analyze(out):
    report=base.load(out/'report.json');summary=report['summary'];catalog=base.load(out/'cases.json');protocol=base.load(out/'protocol.json')
    data={m:base.load(out/f'{m}-0/report.json') for m in study.MODES};queries={m:base.load(d['queries']['path']) for m,d in data.items()}
    banks={n:base.load(protocol[f]['path']) for n,f in [('legacy','support_index'),('causal','causal_index')]}
    inherited={(name,r['case']):r for name,entry in zip(study.FIELDS,protocol['prior_decision_catalogs']) for r in base.load(entry['path'])}
    entries=[]
    for case in catalog['cases']:
        i=case['case'];rs={m:queries[m][i] for m in study.MODES};assert len({r['answer'] for r in rs.values()})==1
        r=rs['terminal'];trace=r['guard_choice'];entry=dict(case=i,template_case=case['template_case'],answer=r['answer'],
            expanded={m:x['child']['metrics'].get('expanded_nodes',0) for m,x in rs.items()},new_rows={m:x['new_nodes'] for m,x in rs.items()},
            hits={m:x['cofactor'] is not None for m,x in rs.items()},changed_guard=bool(trace and trace['selected']),
            selector_called=trace is not None,guard_equal_to_baseline=r['guard']==rs['ready']['guard'])
        if r['cofactor']:
            hit=r['cofactor'];bank=banks[hit['bank']];origin=next(o for o in bank['origins'] if o['core']==bank['retained_indices'][hit['local_core']]);old=inherited[(origin['catalog'],origin['case'])]
            entry.update(bank=hit['bank'],choice=hit['choice'],origin_catalog=origin['catalog'],
                different_first_guard=old['guard']['removed_clause']!=r['guard']['removed_clause'])
            origins=[o for o in bank['origins'] if o['core']==bank['retained_indices'][hit['local_core']]]
            entry['origin_records_for_selected_core']=len(origins)
            entry['different_all_recorded_guards']=all(inherited[(o['catalog'],o['case'])]['guard']['removed_clause']!=r['guard']['removed_clause'] for o in origins)
        entries.append(entry)
    metrics=('expanded_nodes','new_nodes','mean_complete_worker_seconds','mean_query_seconds','mean_repeat_query_seconds','mean_complete_peak_rss_bytes','database_bytes','compressed_bytes')
    changes={k:100*(summary['terminal'][k]/summary['ready'][k]-1) for k in metrics}
    pairs=[]
    for repeat in range(len(protocol['orders'])):
        ts={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        pairs.append(dict(repeat=repeat,complete_seconds={m:r['complete_worker_seconds'] for m,r in ts.items()},
            relative_change_percent={k:100*(ts['terminal'][k]/ts['ready'][k]-1) for k in ('complete_worker_seconds','complete_peak_rss_bytes')}))
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,trials=pairs,attribution=entries,
        changed_guard_cases=[e['case'] for e in entries if not e['guard_equal_to_baseline']],
        expansion_regressions=[e['case'] for e in entries if e['expanded']['terminal']>e['expanded']['ready']],
        different_first_guard_hits=sum(e.get('different_first_guard',False) for e in entries),
        different_all_recorded_guard_hits=sum(e.get('different_all_recorded_guards',False) for e in entries),
        remaining_expansions_by_answer={str(v):sum(e['expanded']['terminal'] for e in entries if e['answer']==v) for v in (True,False)},
        remaining_expansions_by_template={str(v):sum(e['expanded']['terminal'] for e in entries if e['template_case']==v) for v in sorted({e['template_case'] for e in entries})},
        selector_counts=data['terminal']['guard_choice_counts'],
        selector_calls_by_visit={str(v):sum(r['guard_choice'] is not None for r in queries['terminal'] if r['visit']==v) for v in range(protocol['visits'])},
        selected_status_counts=dict(Counter(a['status'] for r in queries['terminal'] if r['guard_choice'] and r['guard_choice']['selected'] for a in r['guard_choice']['attempts'] if a['status'] in ('known','ready','terminal'))),
        first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        alternative_complete_phase_percent={n:100*summary['terminal']['mean_'+n+'_seconds']/summary['terminal']['mean_complete_worker_seconds'] for n in ('preparation','query','cold','compression')},
        limitations=['Same acquired 20340-key union and old 389-origin portfolio, no new support discovery. The optional 526-origin bank remains preserved, unloaded.',
            'One additional matching extension hint checked per first-target miss; enumeration, support scans, terminal derivation, checks and publication are charged. Repeated queries may repeat guard choice.',
            'Measured neighbouring inputs do not establish broad arbitrary-SAT coverage, minimum-cost decomposition or uniform polynomial resource bounds.'])
    pending_cases=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'final';base.restore_archive(data['terminal']['archive'],path);solver=study.ResidualSolver(path)
        try:
            all_keys={base.key_sha(row[0]) for row in solver.db.execute('SELECT id FROM cnf_residual_v1')}
            inserted={key for row in queries['terminal'] for key in row['new_ids']};available=all_keys-inserted
            for row in queries['terminal']:
                trace=row['guard_choice'];matches=[]
                if trace and row['visit']==0:
                    for attempt in trace['attempts']:
                        if attempt['status']!='miss':continue
                        _,target=check_guard(solver,row['source'],attempt['guard']);members=clause_set(target,Counter())
                        for name,bank in banks.items():
                            for i,core in enumerate(bank['cores']):
                                if clause_set(core['source'],Counter())<=members and base.key_sha(core['root']) not in available:
                                    matches.append(dict(bank=name,index=i,clauses=len(core['source'])))
                if matches:pending_cases.append(dict(case=row['case'],expansions=row['child']['metrics'].get('expanded_nodes',0),matches=matches))
                available.update(row['new_ids'])
        finally:solver.close()
    result['pending_alternative_cases']=pending_cases
    base.write(out/'cost-attribution.json',result)
    print(base.encode({k:result[k] for k in ('relative_change_percent','changed_guard_cases','expansion_regressions','selector_calls_by_visit','different_first_guard_hits','remaining_expansions_by_answer')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
