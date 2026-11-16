#!/usr/bin/env python3
"""Preserve cost regressions and diagnostic support/derived-proof redundancy."""
from pathlib import Path
import sys,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_unsat_support as study
base=study.base


def analyze(out):
    report=base.load(out/'report.json');catalog=base.load(out/'cases.json');data=base.load(out/'all-0/report.json');cores=base.load(data['cores']['path'])
    members=[{tuple(c) for c in x['source']} for x in cores];kept=[];dominance=[]
    for i,items in enumerate(members):
        match=next((j for j in kept if members[j]<=items),None)
        if match is None:kept.append(i);match=i
        dominance.append(dict(core=i,retained=match))
    assert all(members[d['retained']]<=members[d['core']] for d in dominance)
    coverage=[]
    for case in catalog['cases']:
        source={tuple(c) for c in case['source']};full=any(c<=source for c in members);thin=any(members[i]<=source for i in kept)
        assert full==thin;coverage.append(full)
    streams={m:base.load(out/f'{m}-0/queries.json') for m in study.MODES};regressions=[];attribution=[]
    for case in catalog['cases']:
        entry=dict(case=case['case'],template_case=case['template_case'],removed=case['removed'],answer=streams['guarded'][case['case']]['answer'],modes={})
        for m,records in streams.items():
            row=records[case['case']];assert row['answer']==entry['answer']
            entry['modes'][m]=dict(expanded=row['child']['metrics'].get('expanded_nodes',0),new_nodes=row['new_nodes'],core=row['core'])
        if entry['modes']['all']['expanded']>entry['modes']['guarded']['expanded']:regressions.append(entry)
        attribution.append(entry)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);parent=base.load(base.load(out/'protocol.json')['parent']['path'])
        base.restore_archive(parent['reference_union'],tmp/'parent');s=study.ResidualSolver(tmp/'parent')
        try:initial=study.rows(s)
        finally:s.close()
        base.restore_archive(data['archive'],tmp/'all');s=study.ResidualSolver(tmp/'all')
        try:saved=study.rows(s)
        finally:s.close()
        parsed={k:base.load_json(v) for k,v in saved.items()};hashed={base.key_sha(k):k for k in saved};assert len(hashed)==len(saved)
        prep={hashed[h] for h in data['setup_ids']};assert len(prep)==4102
        def closure(roots):
            seen=set();stack=list(roots)
            while stack:
                k=stack.pop()
                if k in seen:continue
                seen.add(k);node=parsed[k]
                if node['answer']:continue
                proof=node['proof']
                stack.extend(proof[f] for f in ('child','low','high') if f in proof)
            return seen
        full=closure(c['root'] for c in cores);thin=closure(cores[i]['root'] for i in kept)
        query_roots={r['child']['root'] for r in streams['all']}
        active=closure(set(initial)|query_roots|{c['root'] for c in cores});unused=prep-active
        proof_storage=dict(preparation_nodes=len(prep),needed_by_all_cores=len(prep&full),needed_by_antichain_cores=len(prep&thin),
            unused_preparation_nodes_for_all_current_roots=len(unused),unused_preparation_key_payload_bytes=sum(len(k)+len(saved[k]) for k in unused),
            unused_preparation_ids=sorted(map(base.key_sha,unused)),all_current_roots_live_nodes=len(active))
    summary=report['summary'];g=summary['guarded'];changes={}
    for m in ('three','all'):
        changes[m]={k:100*(summary[m][k]/g[k]-1) for k in ('expanded_nodes','new_nodes','mean_wall_seconds','mean_peak_rss_bytes','database_bytes','compressed_bytes')}
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),relative_change_percent=changes,attribution=attribution,
        query_expansion_regressions=regressions,support_antichain=dict(original=len(cores),retained=len(kept),indices=kept,dominance=dominance,coverage=sum(coverage),
            coverage_equal_for_every_superset=True,reason='Every discarded core contains a retained checked core; all retained cores belonged to the original bank.'),
        proof_storage=proof_storage,child_solver_seconds_first_trial={m:sum(r['child']['seconds'] for r in records) for m,records in streams.items()},
        total_first_trial_storage_bytes={m:summary[m]['compressed_bytes']+summary[m]['sidecar_bytes'][0] for m in study.MODES},
        remaining_by_answer={str(a):sum(x['modes']['all']['expanded'] for x in attribution if x['answer']==a) for a in (True,False)},
        limitations=['Post-hoc diagnostics, not measured optimization results. No archive row has been deleted.',
            'A live-proof projection would require independently checked rewriting/selection and preservation of all historical certificates outside the active view.',
            'The harness scans the full database before and after each query; child solve timings also include full-table archive-size accounting. Do not attribute all query time to SAT branching.',
            'No support is claimed minimal. Unknown clauses, renamings and negative inputs outside the bank still require checked fallback.'])
    base.write(out/'cost-attribution.json',result)
    print(base.encode(dict(relative_change_percent=changes,antichain=len(kept),proof_storage={k:v for k,v in proof_storage.items() if not k.endswith('_ids')},remaining_by_answer=result['remaining_by_answer'])))


if __name__=='__main__':analyze(Path(sys.argv[1]))
