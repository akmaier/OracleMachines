#!/usr/bin/env python3
"""Posthoc matched cost attribution and concrete unresolved targets."""
from collections import Counter,defaultdict
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_subset as study
b=study.base


def analyze(out):
    report=b.load(out/'report.json');cases=b.load(out/'cases.json')['cases'];groups={};states={};targets=[];pairs=[]
    for repeat in range(2):
        policy={mode:b.load(out/f'{mode}-{repeat}/queries.json') for mode in study.MODES}
        assert all(x['admission']==y['admission'] for x,y in zip(policy['session'],policy['binary']))
        assert all(x['probe_counts']==y['probe_counts'] for x,y in zip(policy['session'],policy['binary']))
        stats={mode:b.load(out/f'{mode}-{repeat}/report.json')['summary'] for mode in study.MODES}
        pairs.append(dict(repeat=repeat,**{k:stats['binary'][k]-stats['session'][k] for k in ('query_seconds','cold_seconds','complete_worker_seconds')}))
        if repeat:continue
        for mode,rows in policy.items():
            g=defaultdict(Counter);statuses=Counter()
            for row,case in zip(rows,cases):
                admission=row['admission'];e=admission.get('affine_bridge') if admission else None
                if e:statuses[e['status']]+=1
                m=row['child']['metrics'];g[case['family']].update({k:v for k,v in m.items() if k.startswith('binary_subset_')});g[case['family']].update(native_nodes=row['new_nodes'],extension_nodes=m.get('affine_negative_inserted_nodes',0),
                    native_expanded=m.get('expanded_nodes',0),child_propagation=m.get('propagation_literal_visits',0),discovery_propagation=row['probe_counts'].get('propagation_literal_visits',0))
                if mode=='binary':
                    targets.append(dict(case=case['case'],family=case['family'],reason=None if admission is None else admission['reason'],
                        native_nodes=row['new_nodes'],native_expanded=m.get('expanded_nodes',0),child_propagation=m.get('propagation_literal_visits',0),
                        discovery_propagation=row['probe_counts'].get('propagation_literal_visits',0),extension=row['extension'],
                        binary_subset={k:v for k,v in m.items() if k.startswith('binary_subset_')},status=None if e is None else e['status'],free=None if e is None else e['free'],familiarity=row['familiarity']))
            groups[mode]={k:dict(v) for k,v in g.items()};states[mode]=dict(statuses)
    result=dict(groups=groups,statuses=states,targets=targets,admissions_unchanged=120,probe_counters_unchanged=120,
        pairs=pairs,largest_acquisition=sorted(targets,key=lambda r:r['child_propagation'],reverse=True)[:10],
        largest_discovery=sorted(targets,key=lambda r:r['discovery_propagation'],reverse=True)[:10],
        limitations=['Posthoc attribution is excluded from timing. Family labels never enter discovery.',
            'Propagation visits are one work counter, not total runtime. Complete worker, all persistence, cold replay and RSS are separately reported.',
            'Every binary-subset scan and failed SCC is included in child acquisition; counter reductions alone are not runtime evidence.',
            'Forty-eight generated family targets and twelve neighbours are a finite workload, not all SAT or all encodings of each family.'])
    b.write(out/'attribution.json',result)
    print(b.encode(dict(groups=groups,pairs=pairs)),flush=True)


if __name__=='__main__':analyze(Path(sys.argv[1]))
