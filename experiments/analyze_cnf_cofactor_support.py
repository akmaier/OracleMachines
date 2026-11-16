#!/usr/bin/env python3
"""Separate cofactor transfer gains from preparation and retained-proof costs."""
from collections import Counter
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cofactor_support as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');catalog=base.load(out/'cases.json');protocol=base.load(out/'protocol.json');summary=report['summary']
    current=base.load(out/'current-0/queries.json');candidate=base.load(out/'cofactor-0/queries.json');data=base.load(out/'cofactor-0/report.json');prepared=base.load(data['cofactor_bank']['path'])
    inherited={(name,r['case']):r for name,entry in zip(study.FIELDS,protocol['prior_decision_catalogs']) for r in base.load(entry['path'])}
    entries=[];used=Counter();different_guards=0
    for case in catalog['cases']:
        a,b=current[case['case']],candidate[case['case']];assert a['answer']==b['answer']
        entry=dict(case=case['case'],template_case=case['template_case'],removed=case['removed'],answer=a['answer'],
            query_sha256=base.key_sha(case['root']),current_expanded=a['child']['metrics'].get('expanded_nodes',0),
            cofactor_expanded=b['child']['metrics'].get('expanded_nodes',0),cofactor=b['cofactor'],target_known=b['target_known'])
        entry['saved_expansions']=entry['current_expanded']-entry['cofactor_expanded']
        if b['cofactor']:
            index=b['cofactor']['core'];used[index]+=1;all_index=prepared['retained_indices'][index]
            origins=[o for o in prepared['origins'] if o['core']==all_index];origin=origins[0];old=inherited[(origin['catalog'],origin['case'])]
            entry['first_origin']=dict(catalog=origin['catalog'],case=origin['case'],removed_clause=old['guard']['removed_clause'])
            entry['query_guard_clause']=b['guard']['removed_clause'];entry['different_first_guard']=old['guard']['removed_clause']!=b['guard']['removed_clause']
            different_guards+=entry['different_first_guard']
        entries.append(entry)
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'candidate';base.restore_archive(data['archive'],path);solver=study.ResidualSolver(path)
        try:saved=study.rows(solver)
        finally:solver.close()
        nodes={k:base.load_json(v) for k,v in saved.items()};hashed={base.key_sha(k):k for k in saved};prep={hashed[k] for k in data['setup_ids']}
        def closure(roots):
            seen=set();stack=list(roots)
            while stack:
                key=stack.pop()
                if key in seen:continue
                seen.add(key);node=nodes[key]
                if not node['answer']:
                    proof=node['proof'];stack.extend(proof[f] for f in ('child','low','high') if f in proof)
            return seen
        retained=closure(c['root'] for c in prepared['cores']);matched=closure(prepared['cores'][i]['root'] for i in used)
        query=closure(r['child']['root'] for r in candidate)
        storage=dict(preparation_nodes=len(prep),needed_by_retained_bank=len(prep&retained),needed_by_matched_cores=len(prep&matched),
            needed_by_trial_queries=len(prep&query),needed_by_bank_or_queries=len(prep&(retained|query)),
            unused_by_bank_or_queries=len(prep-(retained|query)),unused_ids=sorted(map(base.key_sha,prep-(retained|query))))
    changes={k:100*(summary['cofactor'][k]/summary['current'][k]-1) for k in
        ('expanded_nodes','query_new_nodes','new_nodes','mean_query_seconds','mean_wall_seconds','mean_peak_rss_bytes','database_bytes','compressed_bytes')}
    trials=[]
    for repeat in range(4):
        a=base.load(out/f'current-{repeat}/report.json')['summary'];b=base.load(out/f'cofactor-{repeat}/report.json')['summary']
        trials.append(dict(repeat=repeat,whole_change_percent=100*(b['wall_seconds']/a['wall_seconds']-1),query_change_percent=100*(b['query_seconds']/a['query_seconds']-1)))
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,trials=trials,
        attribution=entries,used_core_counts=dict(used),different_first_guard_hits=different_guards,proof_storage=storage,
        search_regressions=[e for e in entries if e['saved_expansions']<0],
        remaining_expansions_by_answer={str(value):sum(e['cofactor_expanded'] for e in entries if e['answer']==value) for value in (True,False)},
        hit_saved_expansions=sum(e['saved_expansions'] for e in entries if e['cofactor']),other_saved_expansions=sum(e['saved_expansions'] for e in entries if not e['cofactor']),
        first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        limitations=['Post-hoc attribution, not a tested support-selection or projection policy. No historical row was deleted.',
            'Selecting only cores used on these queries would use future workload information and can lose coverage. The containment antichain alone preserves every superset match.',
            'Existing archived parents cannot depend on fresh preparation nodes. New query roots and the retained bank determine which preparation nodes remain live here.',
            'Whole preparation, checking, persistence and cold replay are charged. Saving expansions alone is not an end-to-end speedup.',
            'Cofactor hits remain bound to the source and checked guard, not standalone full-query roots. Constructed neighbouring inputs do not establish unrestricted-SAT efficiency.'])
    base.write(out/'cost-attribution.json',result);print(base.encode({k:result[k] for k in ('relative_change_percent','different_first_guard_hits','remaining_expansions_by_answer','hit_saved_expansions','other_saved_expansions','proof_storage')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
