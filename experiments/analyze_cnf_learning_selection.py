#!/usr/bin/env python3
"""Retain selection effects, local two-by-two controls, misses and cost profile."""
from collections import Counter
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_learning_selection import SelectedLearningInventory, discover_selected_probes, check_selected_probes
from experiments.cnf_probe_learning import learning_batch, augment
from experiments.cnf_failed_literal import probe_choices
from experiments.analyze_cnf_conditioning import load_nodes
from experiments.analyze_cnf_probe_equivalence import selected
from experiments.analyze_cnf_learning_mechanisms import replay_choices_without_additions as replay_fixed_choices


def analyze(directory):
    start=time.perf_counter();report=json.loads((directory/'report.json').read_text())
    rows={(r['mode'],r['case']):r for r in report['records']}
    stores={a['mode']:load_nodes(directory,a) for a in report['archives'] if a['mode']!='solver_only'}
    current=stores['selection'];hashes={hashlib.sha256(k.encode()).hexdigest():k for k in current}
    gains=[];losses=[];misses=[];paths={};leaves=set()
    for i,c in enumerate(report['cases']):
        old,new=rows['baseline',i]['discovery'],rows['selection',i]['discovery']
        path=selected(current,hashes[new['root_hash']]);paths[i]=path
        item=dict(case=i,original_case=c.get('original_case',i),group=c['group'],label=c.get('label'),
                  answer=rows['selection',i]['answer'],before=old['summary'],after=new['summary'])
        if new['summary']['closed'] and not old['summary']['closed']:gains.append(item)
        if old['summary']['closed'] and not new['summary']['closed']:losses.append(item)
        if not new['summary']['closed']:
            misses.append(item);leaves.update(k for k in path if current[k]['kind']=='unresolved')
    stats={}
    for mode,nodes in stores.items():
        sizes=Counter();statuses=Counter();continuations=Counter()
        for k,n in nodes.items():
            sizes[n['kind']]+=len(k.encode())+len(encode(n).encode());p=n['profile']['probing'];statuses[p['status']]+=1
            if 'continuation' in p:continuations[p['continuation']['status']]+=1
        stats[mode]=dict(nodes=len(nodes),logical_bytes_by_kind=dict(sizes),statuses=dict(statuses),continuations=dict(continuations))
    baseline={encode([n['cnf'],n['depth']]):n for n in stores['baseline'].values()}
    diagnostics=[];matrix=Counter();changed_sets=reorder_only=shared_changed=0
    for key,n in current.items():
        p=n['profile']['probing']
        if p['status'] not in ('learned','learning_clear'):continue
        counts=Counter();old_batch=learning_batch(n['cnf'],p['attempts'],4,counts)
        if old_batch==p['batch']:continue
        old=baseline.get(encode([n['cnf'],n['depth']]))
        if old is not None:
            assert old['profile']['probing']['attempts']==p['attempts'];shared_changed+=1
        changed_set={tuple(b['clause']) for b in old_batch}!={tuple(b['clause']) for b in p['batch']}
        changed_sets+=changed_set;reorder_only+=not changed_set
        a=augment(n['cnf'],old_batch);b=augment(n['cnf'],p['batch'])
        old_choices=probe_choices(a,4,counts);new_choices=probe_choices(b,4,counts)
        controls={}
        for label,cnf,choices in (('old_old',a,old_choices),('old_new',a,new_choices),
                                  ('new_old',b,old_choices),('new_new',b,new_choices)):
            controls[label]=replay_fixed_choices(cnf,choices,counts)
        assert controls['new_new']['status']==p['continuation']['status']
        matrix['/'.join(controls[x]['status'] for x in ('old_old','old_new','new_old','new_new'))]+=1
        diagnostics.append(dict(key_sha256=hashlib.sha256(key.encode()).hexdigest(),shape=n['profile']['shape'],
            depth=n['depth'],shared_baseline=old is not None,changed_clause_set=changed_set,
            old_batch=old_batch,new_batch=p['batch'],old_choices=old_choices,new_choices=new_choices,
            controls=controls,counters=dict(counts),
            gained_source_paths=[i['original_case'] for i in gains if key in paths[i['case']]],
            lost_source_paths=[i['original_case'] for i in losses if key in paths[i['case']]]))
    olddir=Path('experiments/results/cnf-probe-closure-compact');oldreport=json.loads((olddir/'report.json').read_text())
    frontier=json.loads((olddir/'learning-frontier.json').read_text())
    oldnodes=load_nodes(olddir,next(a for a in oldreport['archives'] if a['mode']=='compact'))
    oldhashes={hashlib.sha256(k.encode()).hexdigest():k for k in oldnodes};oldleaves=[];leaf_status=Counter()
    for entry in frontier['records']:
        n=oldnodes[oldhashes[entry['key_sha256']]];counts=Counter()
        result=discover_selected_probes(n['cnf'],4,4,counts);check_selected_probes(n['cnf'],result,4,4,counts)
        leaf_status[result['status']+':'+result.get('continuation',{}).get('status','')]+=1
        oldleaves.append(dict(key_sha256=entry['key_sha256'],source_cases=entry['source_cases'],shape=entry['shape'],
                              result=result,counters=dict(counts)))
    worst=max((r for r in report['records'] if r['mode']=='selection' and not r['discovery']['summary']['closed']),
              key=lambda r:r['discovery']['seconds'])['case']
    with tempfile.TemporaryDirectory() as tmp:
        h=SelectedLearningInventory(Path(tmp)/'profile.db',max_depth=2,probe_limit=4,learn_limit=4)
        profiler=cProfile.Profile();profiler.enable();result=h.inspect(report['cases'][worst]['source']);profiler.disable();h.close()
        functions=[dict(file=f,line=line,name=name,primitive_calls=pr,calls=ca,own_seconds=own,cumulative_seconds=cu)
                   for (f,line,name),(pr,ca,own,cu,_) in pstats.Stats(profiler).stats.items()]
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),nodes=stats,gains=gains,losses=losses,misses=misses,
        changed_clause_sets=changed_sets,reorder_only=reorder_only,shared_changed_parents=shared_changed,
        control_status_matrix=dict(matrix),changed_nodes=diagnostics,old_selected_leaf_statuses=dict(leaf_status),
        old_selected_leaves=oldleaves,selected_unresolved_nodes=len(leaves),
        selected_leaf_statuses=dict(Counter(current[k]['profile']['probing']['status'] for k in leaves)),
        selected_unresolved_literals=sum(current[k]['profile']['shape']['literals'] for k in leaves),
        profile=dict(case=worst,original_case=report['cases'][worst].get('original_case',worst),
                     instrumented_seconds=result['seconds'],metrics=result['metrics'],
                     functions=sorted(functions,key=lambda f:-f['own_seconds'])[:40]),
        diagnostic_seconds=time.perf_counter()-start,
        limitations=['Local controls do not establish whole-source counterfactual closure',
          'Control order: old batch/old choices, old batch/new choices, new batch/old choices, new batch/new choices',
          'Every counterfactual unit trace is checked, but variable selection is supplied by the compared policies and is not free',
          'Activation is a syntactic heuristic, not an optimal or complete predictor of propagation or closure',
          'Old-leaf replay, control runs and profile are separate from primary operation timings'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'mechanisms.json'
    if out.exists():raise ValueError('Preserve earlier analysis')
    out.write_text(json.dumps(analyze(directory),indent=2)+'\n')
