#!/usr/bin/env python3
"""Retain every partition order, its regressions, and the cost of trying plans."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_clause_partition as study
from experiments.validate_cnf_unsat_support import bound
base=study.base


def analyze(out):
    report=base.load(out/'report.json');rows=[bound(e) for e in report['samples']];cases=[]
    for cid in dict.fromkeys(r['plan']['case'] for r in rows):
        arms=[r for r in rows if r['plan']['case']==cid];baseline=next(r for r in arms if r['plan']['core'] is None);candidates=[r for r in arms if r['plan']['core'] is not None]
        measures=[]
        for row in arms:
            item={k:row[k] for k in ('plan','expanded_nodes','new_nodes','new_payload_units','retained_bytes','premise_inserted','preparation_seconds','premise_seconds','composition_seconds','warm_setup_seconds','warm_seconds','serialization_seconds')}
            item.update(branch_expansions=[b['metrics'].get('expanded_nodes',0) for b in row['branch_reports']],branch_new_nodes=[b['metrics'].get('inserted_nodes',0) for b in row['branch_reports']],
                branch_seconds=sum(b['seconds'] for b in row['branch_reports']),cold_seconds=row['cold']['seconds'],query_phase_seconds=row['premise_seconds']+row['construction_seconds']+sum(b['seconds'] for b in row['branch_reports'])+row['composition_seconds'])
            item['relative_change_percent']={k:100*(row[k]/baseline[k]-1) for k in ('expanded_nodes','new_nodes','new_payload_units','retained_bytes')}
            measures.append(item)
        cases.append(dict(case=cid,arms=measures,expansion_regressions=[r['plan']['mode'] for r in candidates if r['expanded_nodes']>baseline['expanded_nodes']],
            publication_regressions=[r['plan']['mode'] for r in candidates if r['new_nodes']>baseline['new_nodes']],
            best_observed_expansions=min(r['expanded_nodes'] for r in candidates),all_candidate_expansions=sum(r['expanded_nodes'] for r in candidates),
            all_candidate_new_nodes=sum(r['new_nodes'] for r in candidates)))
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),cases=cases,
        total_candidate_expansions=sum(c['all_candidate_expansions'] for c in cases),baseline_expansions=sum(r['expanded_nodes'] for r in rows if r['plan']['core'] is None),
        best_observed_expansions=sum(c['best_observed_expansions'] for c in cases),
        limitations=['Every candidate starts from the same per-case prefix; its branches share in-arm results. Summed candidate work charges trying both orders and all diagnosed cores, with no cross-plan sharing. Best observed cost is post-hoc, not an implemented selection policy.',
            'Historical cases and one sample per arm. Query-phase sum includes premise, branch construction/solving and composition; separately reported preparation, cold replay, serialization and warm-bank setup remain additional costs. No stable speedup or peak-memory claim.',
            'Added payload counts native identifier plus ASCII JSON length. Retained bytes count each delta plus its query sidecar, not SQLite pages, historical storage, indices or all experiment files.',
            'A correct first-false partition need not be beneficial: branches may duplicate work or lose propagation exposed in the unpartitioned target. No minimum-cost expansion or unrestricted-SAT bound.'])
    base.write(out/'cost-attribution.json',result);print(base.encode({k:result[k] for k in ('baseline_expansions','total_candidate_expansions','best_observed_expansions')}))
    for c in cases:print(base.encode(dict(case=c['case'],arms=[{k:r[k] for k in ('plan','expanded_nodes','new_nodes','new_payload_units','retained_bytes','branch_expansions')} for r in c['arms']],regressions=c['expansion_regressions'])))


if __name__=='__main__':analyze(Path(sys.argv[1]))
