#!/usr/bin/env python3
"""Distinguish added propagation strength from changed continuation choices.

Counterfactual local diagnostics, not another whole-source coverage policy.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_probe_learning import augment, discover_learning_probes, check_learning_probes
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_common_consequence import first_common_pair
from experiments.cnf_probe_equivalence import first_equivalence_pair
from experiments.cnf_residual_dag import restrict
from experiments.cnf_simplification import discover_simplification, check_simplification
from analyze_cnf_conditioning import load_nodes
from analyze_cnf_probe_equivalence import selected


def replay_choices_without_additions(cnf, choices, counts):
    attempts=[]
    for x in choices:
        for value in (False,True):
            branch=restrict(cnf,{x:value},counts);cert=discover_simplification(branch,counts,pure=False)
            check_simplification(branch,cert,counts,pure=False)
            attempts.append(dict(variable=x,value=value,certificate=cert))
            if cert['conflict'] is not None:return dict(status='forced',attempts=attempts)
    common=first_common_pair(attempts,counts)
    if common is not None:return dict(status='common',attempts=attempts,witness=common)
    eq=first_equivalence_pair(attempts,counts)
    if eq is not None:return dict(status='equivalence',attempts=attempts,witness=eq)
    return dict(status='clear',attempts=attempts)


def analyze(directory):
    start=time.perf_counter();r=json.loads((directory/'report.json').read_text());records=[];totals=Counter()
    nodes=load_nodes(directory,next(a for a in r['archives'] if a['mode']=='learning'))
    hashes={hashlib.sha256(k.encode()).hexdigest():k for k in nodes};rows={(a['mode'],a['case']):a for a in r['records']}
    gained_paths={}
    for i in range(len(r['cases'])):
        if rows['learning',i]['discovery']['summary']['closed'] and not rows['baseline',i]['discovery']['summary']['closed']:
            gained_paths[i]=selected(nodes,hashes[rows['learning',i]['discovery']['root_hash']])
    for key,n in nodes.items():
        p=n['profile']['probing']
        if p['status']!='learned':continue
        counts=Counter();choices=probe_choices(augment(n['cnf'],p['batch']),4,counts)
        alternate=replay_choices_without_additions(n['cnf'],choices,counts)
        totals[alternate['status']]+=1
        records.append(dict(key_sha256=hashlib.sha256(key.encode()).hexdigest(),shape=n['profile']['shape'],
            added_status=p['continuation']['status'],without_additions=alternate,choices=choices,metrics=dict(counts),
            selected_gain_cases=[i for i,path in gained_paths.items() if key in path]))
    olddir=Path('experiments/results/cnf-probe-equivalence');old=json.loads((olddir/'report.json').read_text())
    gaps=json.loads((olddir/'implication-boundaries.json').read_text())
    oldnodes=load_nodes(olddir,next(a for a in old['archives'] if a['mode']=='equivalence'))
    oldhashes={hashlib.sha256(k.encode()).hexdigest():k for k in oldnodes};leaves=[];leaf_counts=Counter()
    for item in gaps['nodes']:
        n=oldnodes[oldhashes[item['key_sha256']]];counts=Counter()
        result=discover_learning_probes(n['cnf'],4,4,counts);check_learning_probes(n['cnf'],result,4,4,counts)
        leaf_counts[result['status']+':'+result.get('continuation',{}).get('status','')]+=1
        leaves.append(dict(key_sha256=item['key_sha256'],shape=item['shape'],result=result,metrics=dict(counts)))
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        original_gap_sha256=hashlib.sha256((olddir/'implication-boundaries.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),counterfactual_statuses=dict(totals),
        counterfactual_nodes=records,old_selected_leaf_statuses=dict(leaf_counts),old_selected_leaves=leaves,
        diagnostic_seconds=time.perf_counter()-start,
        limitations=['Fixed augmented-source choices may require learning/discovery to obtain; this is not a free baseline',
          'A local reduction without additions does not establish counterfactual whole-source closure',
          'A clear counterfactual only means this bounded unit pass is inconclusive, not semantic necessity of learned clauses',
          'All local traces checked; diagnostic costs are outside primary operation timings'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'learning-mechanisms.json'
    if out.exists():raise ValueError('Preserve earlier mechanism diagnostic')
    out.write_text(json.dumps(analyze(directory),indent=2)+'\n')
