#!/usr/bin/env python3
"""Separate non-binary implications from transitive binary redundancy.

Diagnostic only: this does not enable clause learning in the inventory.
"""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import time
from analyze_cnf_conditioning import load_nodes
from analyze_cnf_probe_equivalence import selected


def analyze(directory):
    start=time.perf_counter();report=json.loads((directory/'report.json').read_text())
    mechanisms=json.loads((directory/'mechanisms.json').read_text())
    nodes=load_nodes(directory,next(a for a in report['archives'] if a['mode']=='equivalence'))
    hashes={hashlib.sha256(k.encode()).hexdigest():k for k in nodes};records=[];counts=Counter()
    for item in mechanisms['unused_implication_opportunities']:
        node=nodes[hashes[item['key_sha256']]];graph=defaultdict(set)
        for clause in node['cnf']:
            if len(clause)==2:
                a,b=clause;graph[-a].add(b);graph[-b].add(a)
        relations=[]
        for candidate in item['implied_binary_clauses_absent']:
            a,b=candidate['clause'];seen=set();stack=[-a]
            while stack:
                v=stack.pop()
                if v in seen:continue
                seen.add(v);counts['reachability_vertices']+=1
                counts['reachability_edges']+=len(graph[v]);stack.extend(graph[v]-seen)
            redundant=b in seen;counts['binary_reachable' if redundant else 'beyond_binary_reachability']+=1
            relations.append(dict(candidate,binary_reachable=redundant))
        records.append(dict(key_sha256=item['key_sha256'],shape=item['shape'],relations=relations))
    novel={a['key_sha256'] for a in records if any(not c['binary_reachable'] for c in a['relations'])}
    affected=[]
    for row in report['records']:
        if row['mode']=='equivalence' and not row['discovery']['summary']['closed']:
            path=selected(nodes,hashes[row['discovery']['root_hash']])
            matches=sorted(hashlib.sha256(k.encode()).hexdigest() for k in path if hashlib.sha256(k.encode()).hexdigest() in novel)
            if matches:affected.append(dict(case=row['case'],selected_nodes=matches))
    return dict(report_sha256=hashlib.sha256((directory/'report.json').read_bytes()).hexdigest(),
        mechanisms_sha256=hashlib.sha256((directory/'mechanisms.json').read_bytes()).hexdigest(),
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),counts=dict(counts),
        diagnostic_seconds=time.perf_counter()-start,nodes=records,affected_roots=affected,
        limitations=['No clause is learned or propagated; this measures an opportunity, not a coverage gain',
          'Binary graph reachability does not exhaust all consequences of an inconsistent binary subformula',
          'No reachability only rules out this direct binary implication-path proof, not all redundancy',
          'Different residuals may contain the same clause; counts are node/clause pairs'])


if __name__=='__main__':
    directory=Path(sys.argv[1]);out=directory/'implication-boundaries.json'
    if out.exists():raise ValueError('Preserve earlier diagnostic')
    out.write_text(json.dumps(analyze(directory),indent=2)+'\n')
