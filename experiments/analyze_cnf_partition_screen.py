#!/usr/bin/env python3
"""Attribute frozen matched costs without treating wrapper bypass as solving gain."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_partition_screen as study
from experiments.validate_cnf_unsat_support import bound
base=study.base


def run(out):
    report=base.load(out/'report.json');trials={m:bound(next(e for e in report['samples'] if e['mode']==m and e['repeat']==0)) for m in study.MODES};records={m:bound(t['queries']) for m,t in trials.items()};cases=[];costs={}
    for a,b in zip(records['single'],records['screened']):
        exp=lambda row:sum(c['metrics'].get('expanded_nodes',0) for c in row['children'])
        if a['new_nodes']!=b['new_nodes'] or exp(a)!=exp(b) or b['screen'] is not None:
            cases.append(dict(case=a['case'],baseline_expansions=exp(a),screened_expansions=exp(b),baseline_rows=a['new_nodes'],screened_rows=b['new_nodes'],plan=None if b['plan'] is None else {k:b['plan'][k] for k in ('core','order','terminal','remaining','residual_literals')},baseline_unit_conflict=None if b['screen'] is None else b['screen']['baseline']['conflict'] is not None))
    for mode,data in trials.items():
        propagation=sum(c['metrics'].get('propagation_literal_visits',0) for r in records[mode] for c in r['children']);screen=data['screen_counts'].get('propagation_literal_visits',0)
        costs[mode]=dict(child_propagation_literal_visits=propagation,screen_propagation_literal_visits=screen,combined_propagation_literal_visits=propagation+screen,
            trace_check_literals=sum(c['metrics'].get('screen_trace_check_literals',0) for r in records[mode] for c in r['children']),screen_counts=data['screen_counts'],child_metrics=data['child_metrics'])
    pairs=[]
    for repeat in range(len(base.load(out/'protocol.json')['orders'])):
        samples={m:bound(next(e for e in report['samples'] if e['mode']==m and e['repeat']==repeat))['summary'] for m in study.MODES}
        pairs.append(dict(repeat=repeat,**{k:dict(single=samples['single'][k],screened=samples['screened'][k],delta=samples['screened'][k]-samples['single'][k]) for k in ('complete_worker_seconds','query_seconds','cold_seconds','peak_rss_bytes')}))
    a=report['summary']['single'];b=report['summary']['screened'];result=dict(passed=True,report=study.binding(out/'report.json'),changed_or_screened_cases=cases,costs=costs,pairs=pairs,
        payload_change_percent=100*(b['new_payload_units']/a['new_payload_units']-1),complete_mean_change_percent=100*(b['mean_complete_worker_seconds']/a['mean_complete_worker_seconds']-1),
        conclusion='Optional prototype only. A terminal unsplit baseline is a counterexample to selecting an all-terminal partition: fewer expanded_nodes can coexist with extra proof rows, payload and propagation. Reuse the already computed baseline conflict trace before considering partitions. This experiment does not establish a runtime or live-memory improvement.')
    result['remaining_expansion_cases']=[dict(case=r['case'],template_case=r['template_case'],expanded_nodes=sum(c['metrics'].get('expanded_nodes',0) for c in r['children']),split_nodes=sum(c['metrics'].get('split_nodes',0) for c in r['children']),new_nodes=r['new_nodes'],choice=r['choice'],screen_called=r['screen'] is not None) for r in sorted(records['screened'],key=lambda r:sum(c['metrics'].get('expanded_nodes',0) for c in r['children']),reverse=True) if any(c['metrics'].get('expanded_nodes',0) for c in r['children'])]
    base.write(out/'cost-attribution.json',result);print(base.encode({k:result[k] for k in ('changed_or_screened_cases','payload_change_percent','complete_mean_change_percent')}),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
