#!/usr/bin/env python3
"""Preserve the SCC-versus-path exploration that selected clause reduction."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_conditioning import shortest_balanced_choices
from experiments.cnf_residual_dag import restrict, two_cnf


def inspect(cnf):
    binary=[c for c in cnf if len(c)==2];graph={}
    for a,b in binary:
        graph.setdefault(-a,[]).append(b);graph.setdefault(-b,[]).append(a)
    reach={};cyclic=False
    for root in graph:
        seen=set();todo=graph[root][:]
        while todo:
            v=todo.pop()
            if v not in seen:seen.add(v);todo.extend(graph.get(v,()))
        reach[root]=seen;cyclic|=root in seen
    model,refutation=two_cnf([c for c in cnf if 0<len(c)<=2],Counter())
    removed=[i for i,c in enumerate(cnf) if len(c)>2 and any(b in reach.get(-a,set()) for a in c for b in c)]
    return dict(kind='conflict' if model is None else 'cycle' if cyclic else 'dag',
                forced_literals=sorted(v for v in graph if v in reach.get(-v,set())),removable_wide_clauses=removed)


def main(directory):
    target=directory/'exploration.json'
    if target.exists():raise FileExistsError(target)
    outputs=[]
    for filename,mode in [('cnf-polarity-horn','polarity'),('cnf-probe-rank-frontier','baseline'),('cnf-probe-rank-fresh','baseline')]:
        path=Path('experiments/results')/filename/'report.json';report=json.loads(path.read_text())
        rows=[];roots=Counter();branches=Counter()
        for i,row in enumerate(report['frontiers'][mode]):
            cnf=row['cnf'];original=inspect(cnf);roots[original['kind']]+=1;children=[]
            for v in shortest_balanced_choices(cnf,4,Counter()):
                for value in (False,True):
                    effect=inspect(restrict(cnf,{v:value}));branches[effect['kind']]+=1
                    if effect['kind']!='dag':children.append(dict(variable=v,value=value,**effect))
            rows.append(dict(case=i,cnf=cnf,original=original,conditioned_non_dag=children))
        outputs.append(dict(source=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),mode=mode,
            root_graphs=dict(roots),conditioned_graphs=dict(branches),rows=rows))
    target.write_text(json.dumps(dict(sources=outputs,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        limitations=['Read-only unbounded diagnostic, not an integrated extra search budget or acquisition benchmark',
        'Graphs use original binary clauses; raw restrictions retain units for the separate 2-CNF conflict test',
        'Cycles exposed before the existing reductions are opportunities, not additional coverage; many are already handled',
        'The implemented bounded deletion pass and its independently checked certificates are measured separately']),indent=2)+'\n')
    print([(r['source'],r['root_graphs'],r['conditioned_graphs']) for r in outputs],flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
