#!/usr/bin/env python3
"""Separate changed branching from cofactor certificate reuse and publication."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditioned_core as study
from experiments.validate_cnf_unsat_support import bound
base=study.base


def run(out):
    report=base.load(out/'report.json');samples=[bound(e) for e in report['samples']];cases=[]
    for cid in dict.fromkeys(r['case'] for r in samples):
        arms={r['mode']:r for r in samples if r['case']==cid};summary={};pairs=[]
        for mode,r in arms.items():
            cofactor=r['cofactor'];screen={} if cofactor is None else cofactor.get('conditioning_screen_counts',{});cf_metrics={} if cofactor is None else cofactor['metrics']
            prop=sum(c['metrics'].get('propagation_literal_visits',0) for c in r['children'])+cf_metrics.get('propagation_literal_visits',0)+screen.get('propagation_literal_visits',0)+r['premise_metrics'].get('propagation_literal_visits',0)
            summary[mode]=dict(expanded_nodes=r['expanded_nodes'],child_expansions=sum(c['metrics'].get('expanded_nodes',0) for c in r['children']),cofactor_expansions=cf_metrics.get('expanded_nodes',0),cofactor_trace_publications=cf_metrics.get('screen_trace_publications',0),premise_expansions=r['premise_metrics'].get('expanded_nodes',0),premise_insertions=r['premise_metrics'].get('inserted_nodes',0),cofactor_insertions=cf_metrics.get('inserted_nodes',0),new_nodes=r['new_nodes'],new_payload_units=r['new_payload_units'],retained_bytes=r['retained_bytes'],total_propagation_literal_visits=prop,contained_clause=r['contained_clause'],
                preparation_seconds=r['preparation_seconds'],projection_seconds=r['projection_seconds'],cofactor_seconds=r['cofactor_seconds'],projection_check_seconds=r['projection_check_seconds'],premise_seconds=r['premise_seconds'],child_seconds=sum(c['seconds'] for c in r['children']),cold_seconds=r['cold']['seconds'],complete_seconds=r['seconds'])
        for order in ('forward','reverse'):
            a=arms['conditioned-'+order];b=arms['direct-'+order];same_roots=[c['root'] for c in a['children']]==[c['root'] for c in b['children']]
            da=dict(bound(a['delta']));db=dict(bound(b['delta']));payloads_equal=all(da.get(c['root'])==db.get(c['root']) for c in a['children'])
            pairs.append(dict(order=order,child_roots_equal=same_roots,child_delta_payloads_equal=payloads_equal,child_expansions_equal=summary[a['mode']]['child_expansions']==summary[b['mode']]['child_expansions'],conditioned_minus_direct_rows=a['new_nodes']-b['new_nodes'],conditioned_minus_direct_payload=a['new_payload_units']-b['new_payload_units']))
        baseline=arms['baseline'];best=min(arms,key=lambda m:(arms[m]['new_nodes'],arms[m]['new_payload_units'],m))
        cases.append(dict(case=cid,arms=summary,comparisons=pairs,posthoc_best_by_rows_then_payload=best,all_candidate_expansions=sum(r['expanded_nodes'] for m,r in arms.items() if m!='baseline'),baseline_expansions=baseline['expanded_nodes']))
    result=dict(passed=True,report=study.binding(out/'report.json'),cases=cases,baseline_expansions=sum(r['expanded_nodes'] for r in samples if r['mode']=='baseline'),all_candidate_expansions=sum(r['expanded_nodes'] for r in samples if r['mode']!='baseline'),
        limitations=['Best observed choices are post hoc, not a deployed selector. Trying all alternatives charges all candidate acquisition/solving. Child payload comparisons concern roots appearing in the arm delta; inherited roots are identical through the exact shared prefix.', 'Cofactor trace publication bypasses expansion calls but still acquires/stores/checks a proof. Direct-premise acquisition isolates the branch-plan effect. No fresh-coverage or stable total-time/peak-memory claim.'])
    base.write(out/'cost-attribution.json',result);print(base.encode(dict(cases=[dict(case=r['case'],best=r['posthoc_best_by_rows_then_payload'],comparisons=r['comparisons']) for r in cases],baseline_expansions=result['baseline_expansions'],all_candidate_expansions=result['all_candidate_expansions'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
