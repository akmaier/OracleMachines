#!/usr/bin/env python3
"""Account for common-consequence rewrites and retain unresolved probe patterns."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from analyze_cnf_conditioning import load_nodes


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'))


def shape_key(n):
    return encode([n['depth'],n['cnf']])


def equivalences(n):
    """Candidate signed equalities certified by opposite branch implications.

Only measure the opportunity; do not rewrite, claim closure or skip checks.
"""
    p=n['profile'].get('probing',{})
    if p.get('status')!='clear':return []
    relations=set();clauses={tuple(c) for c in n['cnf']}
    for low,high in zip(p['attempts'][::2],p['attempts'][1::2]):
        x=low['variable'];a={lit for lit,_ in low['certificate']['units']}
        b={lit for lit,_ in high['certificate']['units']}
        for lit in a:
            if -lit not in b:continue
            y=abs(lit);same=lit<0
            u,v=sorted((x,y));relations.add((u,v,same))
    out=[]
    for x,y,same in sorted(relations):
        right=y if same else -y
        explicit=tuple(sorted((-x,right))) in clauses and tuple(sorted((x,-right))) in clauses
        out.append(dict(x=x,y=y,same=same,explicit_binary_pair=explicit))
    return out


def analyze(directory):
    report=json.loads((directory/'report.json').read_text());stats={};baseline={};shared=0
    for entry in report['archives']:
        if entry['mode']=='solver_only':continue
        nodes=load_nodes(directory,entry);kinds=Counter();sizes=Counter();statuses=Counter()
        attempts=conflicts=trace_bytes=inconclusive_bytes=common_literals=common_bytes=0
        depths=Counter();opportunities=[];misses=[]
        if entry['mode']=='baseline':baseline={shape_key(n):n for n in nodes.values()}
        for key,n in nodes.items():
            kinds[n['kind']]+=1;sizes[n['kind']]+=len(key.encode())+len(encode(n).encode())
            p=n['profile'].get('probing',{});statuses[p.get('status','absent')]+=1
            for a in p.get('attempts',[]):
                attempts+=1;failed=a['certificate']['conflict'] is not None;conflicts+=failed
                size=len(encode(a).encode());trace_bytes+=size
                if not failed:inconclusive_bytes+=size
            if p.get('status')=='common':
                common_literals+=len(p['witness']['literals']);depths[n['depth']]+=1
                common_bytes+=len(encode(p['witness']).encode())+len(encode(p['closure']).encode())
                old=baseline.get(shape_key(n))
                if old is not None:
                    assert old['profile']['probing']['status']=='clear'
                    assert old['profile']['probing']['attempts']==p['attempts']
                    shared+=1
            if n['kind']=='unresolved':
                eq=equivalences(n)
                if eq:opportunities.append(dict(key_sha256=hashlib.sha256(key.encode()).hexdigest(),
                    depth=n['depth'],shape=n['profile']['shape'],relations=eq))
                misses.append(dict(depth=n['depth'],shape=n['profile']['shape'],
                    binary_variables=len({abs(l) for c in n['cnf'] if len(c)==2 for l in c})))
        stats[entry['mode']]=dict(kinds=dict(kinds),logical_node_bytes=dict(sizes),statuses=dict(statuses),
            stored_attempts=attempts,stored_conflicts=conflicts,attempt_json_bytes=trace_bytes,
            inconclusive_attempt_json_bytes=inconclusive_bytes,common_literals=common_literals,
            common_witness_and_closure_bytes=common_bytes,common_nodes_by_depth=dict(depths),
            unresolved_nodes=misses,equivalence_opportunities=opportunities)
    paired={(r['mode'],r['case']):r for r in report['records']};gains=[];losses=[];misses=[]
    for i,c in enumerate(report['cases']):
        a=paired['baseline',i]['discovery'];b=paired['common',i]['discovery']
        item=dict(case=i,group=c['group'],label=c.get('label'),answer=paired['common',i]['answer'],
                  before_summary=a['summary'],after_summary=b['summary'])
        if b['summary']['closed'] and not a['summary']['closed']:gains.append(item)
        if a['summary']['closed'] and not b['summary']['closed']:losses.append(item)
        if not b['summary']['closed']:misses.append(item)
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),nodes=stats,gains=gains,losses=losses,misses=misses,
        unchanged_probe_lists_on_shared_common_nodes=shared,
        limitations=['Shared-node checks are corpus evidence, not a universal implementation proof',
                     'Signed-equivalence opportunities include unselected alternatives; no new rewrite or coverage is claimed'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'mechanisms.json'
    if out.exists():raise ValueError('Preserve the earlier analysis')
    out.write_text(json.dumps(analyze(directory),indent=2)+'\n')
