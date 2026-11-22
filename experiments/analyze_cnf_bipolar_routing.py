#!/usr/bin/env python3
"""Summarize paired native-target policies without selecting a winning order."""
from collections import Counter
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_bipolar_routing as study


def analyze(out):
    base=study.base;p=base.load(out/'protocol.json');report=base.load(out/'report.json');summary={};attempts=[]
    measures=('query_seconds','complete_worker_seconds','expanded_nodes','new_payload_bytes','checked_python_bytes',
        'database_bytes','proof_delta_compressed_bytes','partition_bytes','warm_setup_seconds','warm_seconds','cold_seconds',
        'reconstruction_seconds','persistence_seconds','peak_rss_bytes')
    for split in dict.fromkeys(s['split'] for s in report['samples']):
        summary[split]={}
        for mode in study.MODES:
            by_order=[];metrics=Counter();statuses=Counter()
            for repeat in range(2):
                selected=[study.bound(s) for s in report['samples'] if (s['split'],s['mode'],s['repeat'])==(split,mode,repeat)]
                by_order.append({m:sum(r['summary'][m] for r in selected) for m in measures})
                for data in selected:
                    for r in study.bound(data['queries']):
                        if repeat:continue
                        statuses[r['status']]+=1
                        if study.native_split(split):metrics.update(r['metrics'])
                        else:
                            if r['probe'] is not None:metrics.update(r['probe']['metrics'])
                            for b in r['branches']:metrics.update(b['metrics'])
                        attempts.append(dict(split=split,case=data['summary']['case'],variant=r['variant'],mode=mode,
                            status=r['status'],route=r['route'],expanded_nodes=r['expanded_nodes'],
                            branch_expansions=[b['metrics'].get('expanded_nodes',0) for b in r.get('branches',[])],
                            seconds=r['seconds']))
            summary[split][mode]=dict(mean={m:sum(x[m] for x in by_order)/2 for m in measures},orders=by_order,statuses=dict(statuses),metrics=dict(metrics))
        baseline=summary[split]['baseline']
        for mode in study.MODES[1:]:
            r=summary[split][mode]
            r['change_vs_baseline']={m:r['mean'][m]-baseline['mean'][m] for m in measures}
            r['paired_query_changes']=[r['orders'][i]['query_seconds']-baseline['orders'][i]['query_seconds'] for i in range(2)]
            r['paired_complete_changes']=[r['orders'][i]['complete_worker_seconds']-baseline['orders'][i]['complete_worker_seconds'] for i in range(2)]
    base.write(out/'analysis.json',dict(protocol=study.binding(out/'protocol.json'),summary=summary,attempts=attempts,
        limitations=['Means sum separate case streams, averaging two orders. Endpoint object/RSS sums are not a joint or peak-memory bound.',
        'The three sign variants are exposed and the six novel edits are nearby residual controls. Candidate selection/maps and prior acquisition remain sunk.',
        'All individual regressions and both order signs remain visible. Policy changes can change branches, proof shapes and future reuse; counts do not prove causal wall-time attribution.']))
    for split,modes in summary.items():
        print(split,{m:{k:round(v['mean'][k],6) for k in ('expanded_nodes','query_seconds','complete_worker_seconds')} for m,v in modes.items()},flush=True)


if __name__=='__main__':analyze(Path(sys.argv[1]))
