#!/usr/bin/env python3
"""Diagnostic signed-subsumption witnesses; not an integrated planner policy."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_pattern_inventory import classify
from experiments.cnf_residual_dag import normalize
from experiments.analyze_cnf_conditioning import load_nodes
from experiments.analyze_cnf_probe_equivalence import selected


def analyze(directory):
    path=directory/'mechanisms.json';data=json.loads(path.read_text());records=[]
    for i,item in enumerate(data['frontier']):
        cnf=item['cnf'];sets=[set(c) for c in cnf];kept=[];removed=[];counts=Counter()
        for j in sorted(range(len(cnf)),key=lambda j:(len(cnf[j]),j)):
            witness=None
            for k in kept:
                counts['subset_tests']+=1
                if sets[k] <= sets[j]:witness=k;break
            if witness is None:kept.append(j)
            else:removed.append([j,witness])
        kept.sort()
        # Exact source-index coverage, retained witnesses and signed inclusion.
        assert sorted(kept+[j for j,_ in removed])==list(range(len(cnf)))
        for j,k in removed:assert k in kept and set(cnf[k]) <= set(cnf[j])
        raw=[cnf[j] for j in kept];core,names=normalize(raw,counts)
        classified=classify(core,8,counts)
        recognized=[k for k,v in classified['outcomes'].items() if v=='recognized']
        records.append(dict(frontier_index=i,source=cnf,depth=item['depth'],kept=kept,removed=removed,
            core=core,names=names,classification=classified,recognized=recognized,counts=dict(counts)))
    report_path=directory/'report.json';report=json.loads(report_path.read_text())
    nodes=load_nodes(directory,next(a for a in report['archives'] if a['mode']=='activity'))
    hashes={hashlib.sha256(k.encode()).hexdigest():k for k in nodes}
    binding=lambda cnf,depth:json.dumps([cnf,depth],separators=(',',':'))
    exposed={binding(r['source'],r['depth']) for r in records if r['recognized']}
    source_opportunities=[]
    for row in report['records']:
        if row['mode']!='activity' or row['discovery']['summary']['closed']:continue
        root=hashes[row['discovery']['root_hash']]
        leaves={binding(nodes[k]['cnf'],nodes[k]['depth']) for k in selected(nodes,root)
                if nodes[k]['kind']=='unresolved'}
        if leaves & exposed:
            source_opportunities.append(dict(case=row['case'],remaining_leaves=len(leaves),
                exposed_leaves=len(leaves & exposed),selected_plan_completable=leaves <= exposed))
    result=dict(mechanisms_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        report_sha256=hashlib.sha256(report_path.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),records=records,
        changed=sum(bool(r['removed']) for r in records),
        exposed=sum(bool(r['recognized']) for r in records),
        recognized_counts=dict(Counter(k for r in records for k in r['recognized'])),
        removed_clauses=sum(len(r['removed']) for r in records),
        removed_literals=sum(len(r['source'][j]) for r in records for j,_ in r['removed']),
        counts=dict(sum((Counter(r['counts']) for r in records),Counter())),
        source_opportunities=source_opportunities,
        limitations=['Offline diagnostic over distinct selected unresolved leaves, not new source closures',
          'Witness inclusion proves exact model equivalence with arbitrary values on disappearing variables',
          'Uses the existing basic classifier after normalization, not a new tractability class',
          'Selected-plan completion is conditional on integrating these exact reductions; it is not executed source coverage',
          'No integrated acquisition/recomposition, cold replay or full-workload cost result for this candidate',
          'Subset comparisons are counted, but this diagnostic supplies no wall-clock speed claim'])
    (directory/'frontier-subsumption.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','limitations')}))


if __name__=='__main__':analyze(Path(sys.argv[1]))
