#!/usr/bin/env python3
"""Characterize final unresolved roots without supplying construction labels."""
from collections import Counter
from pathlib import Path
import sys, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_ordered_probe as study
from experiments.cnf_residual_dag import normalize, token
from experiments.cnf_affine_patterns import extract_affine, check_affine
base=study.base


def inspect(out):
    p=base.load(out/'protocol.json'); cases=study.bound(p['cases']['holdout'])
    rows=base.load(out/'holdout-ordered-0/queries.json')
    completed={c['root'] for c,r in zip(cases,rows) if r['result'] is not None}
    seen=set(); records=[]
    for c in cases:
        if c['root'] in completed or c['root'] in seen:continue
        seen.add(c['root']); counts=Counter(); tick=time.perf_counter()
        cnf,names=normalize(c['source'],counts);assert token(cnf,counts)==c['root']
        affine=extract_affine(cnf,counts);summary=check_affine(cnf,affine,counts)
        counts['frontier_leftover_literals']=sum(len(cnf[i]) for i in affine['leftovers'])
        support={abs(l) for i in affine['leftovers'] for l in cnf[i]}
        records.append(dict(case=c['case'],root=c['root'],variables=len(names),clauses=len(cnf),
            affine=affine,summary=summary,free=len(names)-summary['rank'],
            leftover_variables=len(support),seconds=time.perf_counter()-tick,counts=dict(counts)))
    base.write(out/'frontier-inspection.json',dict(protocol=study.binding(out/'protocol.json'),records=records,
        limitations=['Posthoc diagnostic of distinct roots with no completed answer in the ordered-policy chronological stream.',
            'Only direct CNF XOR extraction and its independent checker are used; no family label chooses a recognizer or proves a verdict.',
            'A consistent affine subsystem constrains candidates but does not decide the leftover CNF. No model enumeration or new SAT/UNSAT authority is produced.']))
    print(base.encode([dict(case=r['case'],equations=r['summary']['equation_count'],free=r['free'],
        leftovers=r['summary']['leftover_clauses'],leftover_variables=r['leftover_variables']) for r in records]),flush=True)


if __name__=='__main__':inspect(Path(sys.argv[1]))
