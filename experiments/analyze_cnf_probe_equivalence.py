#!/usr/bin/env python3
"""Explain signed-substitution gains and remaining selected-path interactions."""
from collections import Counter
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_probe_equivalence import ProbeEquivalenceInventory
from analyze_cnf_conditioning import load_nodes


def encode(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def digest(x):return hashlib.sha256(x.encode()).hexdigest()


def selected(nodes,key):
    stack=[key];seen=set()
    while stack:
        k=stack.pop()
        if k in seen:continue
        seen.add(k);n=nodes[k]
        edges=(n['edges'] if n['kind']=='and' else n['alternatives'][n['selected']]['edges'] if n['kind']=='or'
               else [n['edge']] if n['kind'] in ('project','simplify','probe') else [])
        stack.extend(e['key'] for e in edges)
    return seen


def unused_implications(node):
    """Diagnostic only: each checked unit under an assumption implies a binary.

    Retain exact attempt/reason dependencies and whether its reason was long in
    the parent. No learned clause is inserted; gains cannot be inferred here.
    """
    p=node['profile']['probing'];clauses={tuple(c) for c in node['cnf']};found={}
    for ai,a in enumerate(p.get('attempts',[])):
        x=a['variable'];value=a['value'];assumption=x if value else -x
        parent_ids=[i for i,c in enumerate(node['cnf']) if assumption not in c]
        for lit,cid in a['certificate']['units']:
            clause=tuple(sorted((-assumption,lit)))
            if clause in clauses:continue
            parent=parent_ids[cid]
            found.setdefault(clause,[]).append(dict(attempt=ai,parent_reason=parent,
                parent_reason_width=len(node['cnf'][parent])))
    return [dict(clause=list(c),reasons=rs) for c,rs in sorted(found.items())]


def run(directory):
    report=json.loads((directory/'report.json').read_text());rows={(r['mode'],r['case']):r for r in report['records']}
    stats={};baseline={};shared=0;current=None
    for entry in report['archives']:
        if entry['mode']=='solver_only':continue
        nodes=load_nodes(directory,entry);byshape={encode([n['depth'],n['cnf']]):n for n in nodes.values()}
        if entry['mode']=='baseline':baseline=byshape
        sizes=Counter();statuses=Counter();maps=merged=0
        for k,n in nodes.items():
            sizes[n['kind']]+=len(k.encode())+len(encode(n).encode());p=n['profile']['probing'];statuses[p['status']]+=1
            if p['status']=='equivalence':
                maps+=len(encode(p['witness']).encode());merged+=len(p['witness']['mapping'])-1
                old=baseline.get(encode([n['depth'],n['cnf']]))
                if old is not None:
                    assert old['profile']['probing']['status']=='clear'
                    assert old['profile']['probing']['attempts']==p['attempts'];shared+=1
        stats[entry['mode']]=dict(kinds=dict(Counter(n['kind'] for n in nodes.values())),
            logical_node_bytes=dict(sizes),probe_statuses=dict(statuses),signed_witness_bytes=maps,merged_variables=merged)
        if entry['mode']=='equivalence':current=nodes
    hashes={digest(k):k for k in current};gains=[];losses=[];misses=[];leaves=set()
    for i,c in enumerate(report['cases']):
        a=rows['baseline',i]['discovery'];b=rows['equivalence',i]['discovery'];path=selected(current,hashes[b['root_hash']])
        item=dict(case=i,group=c['group'],label=c.get('label'),answer=rows['equivalence',i]['answer'],
            before=a['summary'],after=b['summary'],selected_equivalence_nodes=sum(
                current[k]['profile']['probing']['status']=='equivalence' for k in path))
        if b['summary']['closed'] and not a['summary']['closed']:gains.append(item)
        if a['summary']['closed'] and not b['summary']['closed']:losses.append(item)
        if not b['summary']['closed']:
            misses.append(item);leaves.update(k for k in path if current[k]['kind']=='unresolved')
    opportunities=[]
    for k in sorted(leaves):
        n=current[k];p=n['profile']['probing'];facts=unused_implications(n)
        opportunities.append(dict(key_sha256=digest(k),shape=n['profile']['shape'],
            attempted_probes=len(p.get('attempts',[])),implied_binary_clauses_absent=facts))
    worst=max((r for r in report['records'] if r['mode']=='equivalence' and not r['discovery']['summary']['closed']),
              key=lambda r:r['discovery']['seconds'])['case']
    with tempfile.TemporaryDirectory() as tmp:
        h=ProbeEquivalenceInventory(Path(tmp)/'profile.sqlite3',max_depth=2,probe_limit=4)
        profiler=cProfile.Profile();profiler.enable();result=h.inspect(report['cases'][worst]['source']);profiler.disable();h.close()
        functions=[dict(file=f,line=line,name=name,primitive_calls=pr,calls=ca,own_seconds=own,cumulative_seconds=cu)
                   for (f,line,name),(pr,ca,own,cu,_) in pstats.Stats(profiler).stats.items()]
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),nodes=stats,gains=gains,losses=losses,misses=misses,
        shared_equivalence_nodes_with_identical_attempts=shared,selected_unresolved_nodes=len(leaves),
        selected_unresolved_literals=sum(current[k]['profile']['shape']['literals'] for k in leaves),
        unused_implication_opportunities=opportunities,
        profile=dict(case=worst,instrumented_seconds=result['seconds'],metrics=result['metrics'],
                     functions=sorted(functions,key=lambda f:-f['own_seconds'])[:40]),
        limitations=['Selected missing implied clauses are opportunities, not measured additional closure',
                     'Long parent reasons do not by themselves prove a learned clause useful or absent from binary transitive closure',
                     'Profiling is separate from uninstrumented comparisons; no new optimization is measured here'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'mechanisms.json'
    if out.exists():raise ValueError('Preserve earlier mechanism analysis')
    out.write_text(json.dumps(run(directory),indent=2)+'\n')
