#!/usr/bin/env python3
"""Account for bounded-learning successes, failed attempts and repeated probes."""
from collections import Counter
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_probe_learning import ProbeLearningInventory
from analyze_cnf_conditioning import load_nodes
from analyze_cnf_probe_equivalence import selected


def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':'))
def digest(value):return hashlib.sha256(value.encode()).hexdigest()


def analyze(directory):
    report=json.loads((directory/'report.json').read_text());rows={(r['mode'],r['case']):r for r in report['records']}
    stats={};baseline={};shared=0;current=None;examples=[]
    for entry in report['archives']:
        if entry['mode']=='solver_only':continue
        nodes=load_nodes(directory,entry)
        if entry['mode']=='baseline':baseline={encode([n['depth'],n['cnf']]):n for n in nodes.values()}
        sizes=Counter();statuses=Counter();continuations=Counter();children=Counter()
        attempts=clauses=extra_bytes=additional_probes=repeated_assumptions=identical_certificates=old_units=new_units=0
        for k,n in nodes.items():
            sizes[n['kind']]+=len(k.encode())+len(encode(n).encode());p=n['profile']['probing'];statuses[p['status']]+=1
            if p['status'] not in ('learned','learning_clear'):continue
            attempts+=1;clauses+=len(p['batch']);continuations[p['continuation']['status']]+=1
            extra_bytes+=len(encode(p['batch']).encode())+len(encode(p['continuation']).encode())
            old=baseline.get(encode([n['depth'],n['cnf']]))
            if old is not None:
                assert old['profile']['probing']['status']=='clear'
                assert old['profile']['probing']['attempts']==p['attempts'];shared+=1
            original={(a['variable'],a['value']):a for a in p['attempts']}
            for a in p['continuation']['attempts']:
                additional_probes+=1;b=original.get((a['variable'],a['value']))
                if b is not None:
                    repeated_assumptions+=1;old_units+=len(b['certificate']['units']);new_units+=len(a['certificate']['units'])
                    identical_certificates+=a['certificate']==b['certificate']
            if p['status']=='learned':
                child=nodes[n['edge']['key']];children[child['kind']]+=1
                examples.append(dict(key_sha256=digest(k),shape=n['profile']['shape'],depth=n['depth'],
                    continuation=p['continuation']['status'],child_shape=child['profile']['shape'],child_kind=child['kind']))
        stats[entry['mode']]=dict(kinds=dict(Counter(n['kind'] for n in nodes.values())),logical_node_bytes=dict(sizes),
            statuses=dict(statuses),learning_attempts=attempts,proposed_clauses=clauses,continuations=dict(continuations),
            successful_child_kinds=dict(children),batch_and_continuation_json_bytes=extra_bytes,
            continuation_probes=additional_probes,repeated_assumptions=repeated_assumptions,
            identical_certificates=identical_certificates,original_units_on_repeated=old_units,continuation_units_on_repeated=new_units)
        if entry['mode']=='learning':current=nodes
    hashes={digest(k):k for k in current};gains=[];losses=[];misses=[];leaves=set()
    for i,c in enumerate(report['cases']):
        a=rows['baseline',i]['discovery'];b=rows['learning',i]['discovery'];path=selected(current,hashes[b['root_hash']])
        item=dict(case=i,group=c['group'],label=c.get('label'),answer=rows['learning',i]['answer'],
            before=a['summary'],after=b['summary'],selected_learning_nodes=sum(
                current[k]['profile']['probing']['status']=='learned' for k in path))
        if b['summary']['closed'] and not a['summary']['closed']:gains.append(item)
        if a['summary']['closed'] and not b['summary']['closed']:losses.append(item)
        if not b['summary']['closed']:
            misses.append(item);leaves.update(k for k in path if current[k]['kind']=='unresolved')
    worst=max((r for r in report['records'] if r['mode']=='learning' and not r['discovery']['summary']['closed']),
              key=lambda r:r['discovery']['seconds'])['case']
    with tempfile.TemporaryDirectory() as tmp:
        h=ProbeLearningInventory(Path(tmp)/'profile.sqlite3',max_depth=2,probe_limit=4,learn_limit=4)
        profiler=cProfile.Profile();profiler.enable();result=h.inspect(report['cases'][worst]['source']);profiler.disable();h.close()
        functions=[dict(file=f,line=line,name=name,primitive_calls=pr,calls=ca,own_seconds=own,cumulative_seconds=cu)
                   for (f,line,name),(pr,ca,own,cu,_) in pstats.Stats(profiler).stats.items()]
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),nodes=stats,gains=gains,losses=losses,misses=misses,
        shared_learning_nodes_with_identical_original_attempts=shared,successful_reductions=examples,
        selected_unresolved_nodes=len(leaves),selected_unresolved_literals=sum(current[k]['profile']['shape']['literals'] for k in leaves),
        selected_leaf_statuses=dict(Counter(current[k]['profile']['probing']['status'] for k in leaves)),
        profile=dict(case=worst,instrumented_seconds=result['seconds'],metrics=result['metrics'],
                     functions=sorted(functions,key=lambda f:-f['own_seconds'])[:40]),
        limitations=['Repeated assumptions may require new propagation after clause addition; do not skip them without checks',
          'Identical saved certificates establish an opportunity to share/recheck traces, not a measured speedup',
          'Profile is separate from uninstrumented comparisons; no change to the independent solver'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'mechanisms.json'
    if out.exists():raise ValueError('Preserve earlier analysis')
    out.write_text(json.dumps(analyze(directory),indent=2)+'\n')
