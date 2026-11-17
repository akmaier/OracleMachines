#!/usr/bin/env python3
"""Attribute fresh chain-policy costs, including per-query regressions."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_premise_guard as study
from experiments.validate_cnf_unsat_support import bound
base=study.base


def analyze(out):
    report=base.load(out/'report.json');trials={m:[bound(e) for e in report['samples'] if e['mode']==m] for m in study.MODES};first={m:ts[0] for m,ts in trials.items()};records={m:bound(t['queries']) for m,t in first.items()};cases=[]
    for rows in zip(*(records[m] for m in study.MODES)):
        arms=dict(zip(study.MODES,rows));a=arms['premise-first'];assert len({r['chain']['answer'] for r in rows})==1
        cases.append(dict(case=a['case'],template_case=a['template_case'],answer=a['chain']['answer'],
            expansions={m:r['child_metrics'].get('expanded_nodes',0) for m,r in arms.items()},new_nodes={m:r['new_nodes'] for m,r in arms.items()},
            choices={m:r['choice'] for m,r in arms.items()},extra_solver_counts={m:r['extra_solver_counts'] for m,r in arms.items()},recognition_counts={m:r['counts'] for m,r in arms.items()}))
    totals={}
    for m in study.MODES:
        recognition=Counter();checking=Counter();templates=Counter()
        for r in records[m]:recognition.update(r['counts']);checking.update(r['extra_solver_counts']);templates[r['template_case']]+=r['child_metrics'].get('expanded_nodes',0)
        totals[m]=dict(summary=report['summary'][m],recognition=dict(recognition),extra_checking=dict(checking),template_expansions=dict(templates),
            retained_trial_bytes=first[m]['summary']['compressed_bytes']+first[m]['summary']['sidecar_bytes'],near_setup_counts=first[m]['near_setup_counts'])
    comparisons={}
    for left,right in [('plain','core-first'),('plain','premise-first'),('core-first','premise-first')]:
        key=left+' -> '+right;percent={}
        for k in ('expanded_nodes','new_nodes','new_payload_units','mean_query_seconds','mean_complete_worker_seconds','mean_peak_rss_bytes'):
            a=report['summary'][left][k];b=report['summary'][right][k];percent[k]=None if a==0 else 100*(b/a-1)
        a=totals[left]['retained_trial_bytes'];b=totals[right]['retained_trial_bytes'];percent['retained_trial_bytes']=100*(b/a-1)
        comparisons[key]=dict(relative_change_percent=percent,
            paired_complete_percent=[100*(b['summary']['complete_worker_seconds']/a['summary']['complete_worker_seconds']-1) for a,b in zip(trials[left],trials[right])],
            expansion_regressions=[c['case'] for c in cases if c['expansions'][right]>c['expansions'][left]],
            publication_regressions=[c['case'] for c in cases if c['new_nodes'][right]>c['new_nodes'][left]])
    result=dict(report=study.binding(out/'report.json'),analyzer=study.binding(__file__),totals=totals,comparisons=comparisons,cases=cases,
        next_expansion_targets=sorted([c for c in cases if c['expansions']['premise-first']],key=lambda c:(-c['expansions']['premise-first'],c['case'])),
        limitations=['Two reversed-order triplets, six fresh processes. Per-query counts and failures are retained; timings have limited replication and cover only the selected three neighbouring-input families.',
            'All modes use checked conclusion-bank replay on repeat visits and identical ordinary preparation. Plain is an adapted symmetric pipeline; frozen-worker parity is a separate check, not part of the timed comparison.',
            'Native payload is identifier plus ASCII JSON length. Retained trial size includes one full compressed native archive and first-trial query/warm sidecars, not all historical indices/results or live memory.',
            'Prepared postings trade copied membership storage and setup for avoided per-query normalization/scans. Worst-case posting visits can remain linear in total core memberships. Checked premise priority may accept a clause suggested by a pending core, but only the actual checked negative strengthened formula authorizes it.',
            'Full cold audit, setup, serialization and compression are included in complete worker time; original acquisition, input selection, independent validation and imported-module startup are separate. No arbitrary-SAT or optimal-cost guarantee.'])
    base.write(out/'cost-attribution.json',result);print(base.encode(dict(comparisons=comparisons,next_expansion_targets=[{k:r[k] for k in ('case','template_case','expansions','choices')} for r in result['next_expansion_targets'][:12]])))


if __name__=='__main__':analyze(Path(sys.argv[1]))
