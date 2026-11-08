#!/usr/bin/env python3
"""Retain probe mechanisms, unresolved shapes and exact coverage changes."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

from analyze_cnf_conditioning import load_nodes


def encode(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'))


def analyze(directory):
    report=json.loads((directory/'report.json').read_text());result={}
    for entry in report['archives']:
        if entry['mode']=='solver_only':continue
        nodes=load_nodes(directory,entry);kinds=Counter();sizes=Counter();statuses=Counter()
        attempts=conflicts=units=trace_bytes=clear_bytes=closures=0;depths=Counter();misses=[]
        for key,n in nodes.items():
            kinds[n['kind']]+=1;sizes[n['kind']]+=len(key.encode())+len(encode(n).encode())
            p=n['profile'].get('probing',{});statuses[p.get('status','absent')]+=1
            for a in p.get('attempts',[]):
                attempts+=1;failed=a['certificate']['conflict'] is not None;conflicts+=failed
                units+=len(a['certificate']['units']);size=len(encode(a).encode());trace_bytes+=size
                if not failed:clear_bytes+=size
            if n['kind']=='probe':depths[n['depth']]+=1;closures+=len(encode(p['closure']).encode())
            if n['kind']=='unresolved':
                binary={abs(l) for c in n['cnf'] if len(c)==2 for l in c}
                misses.append(dict(depth=n['depth'],shape=n['profile']['shape'],binary_variables=len(binary),
                    attempted_variables=len({a['variable'] for a in p.get('attempts',[])}),
                    key_sha256=hashlib.sha256(key.encode()).hexdigest()))
        result[entry['mode']]=dict(kinds=dict(kinds),logical_node_bytes=dict(sizes),probe_statuses=dict(statuses),
            stored_attempts=attempts,stored_conflicts=conflicts,stored_unit_entries=units,
            attempt_json_bytes=trace_bytes,inconclusive_attempt_json_bytes=clear_bytes,closure_json_bytes=closures,
            forced_nodes_by_depth=dict(depths),unresolved_nodes=misses)
    paired={(r['mode'],r['case']):r for r in report['records']};changes={}
    for mode in ('probe1','probe4'):
        gains=[];losses=[];misses=[]
        for i,c in enumerate(report['cases']):
            before=paired['baseline',i]['discovery'];after=paired[mode,i]['discovery']
            item=dict(case=i,group=c['group'],label=c.get('label'),answer=paired[mode,i]['answer'],
                      before_summary=before['summary'],after_summary=after['summary'])
            if after['summary']['closed'] and not before['summary']['closed']:gains.append(item)
            if before['summary']['closed'] and not after['summary']['closed']:losses.append(item)
            if not after['summary']['closed']:misses.append(item)
        changes[mode]=dict(gains=gains,losses=losses,misses=misses)
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),nodes=result,changes=changes)


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'mechanisms.json'
    if out.exists():raise ValueError('Preserve previous analysis')
    out.write_text(json.dumps(analyze(directory),indent=2)+'\n')
