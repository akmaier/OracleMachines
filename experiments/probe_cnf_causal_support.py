#!/usr/bin/env python3
"""Read-only support comparison on the previously identified negative cases."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_causal_support as study
from experiments.cnf_deferred_support import SupportIndexExtractor
from experiments.cnf_causal_support import CausalSupportExtractor
from experiments.cnf_clause_deletion_guard import check_guard,clause_set
base=study.base


def run(out):
    out.mkdir(exist_ok=False);start=time.perf_counter();parent=base.load(study.PARENT/'checkpoint.json');records=base.load(parent['witness_signatures_decisions']['path']);selected=(123,189,74,106,42,157,175);items=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'proofs';base.restore_archive(parent['reference_union'],path);solver=study.ResidualSolver(path)
        try:
            solver.db.execute('PRAGMA query_only=ON');old=SupportIndexExtractor(solver);new=CausalSupportExtractor(solver,materialize=False)
            with patch.object(solver,'_expand',side_effect=AssertionError('Fresh probe solving')),patch.object(solver,'_store',side_effect=AssertionError('Probe publication')):
                for case in selected:
                    row=records[case];assignment,target=check_guard(solver,row['source'],row['guard']);a=old.source_core(target);b=new.source_core(target)
                    assert clause_set(b['source'],Counter())<=clause_set(a['source'],Counter())<=clause_set(target,Counter())
                    items.append(dict(case=case,target=[list(c) for c in target],guard=row['guard'],old=a,causal=b,old_clauses=len(a['source']),causal_clauses=len(b['source'])))
        finally:solver.close();assert base.sha(path)==parent['reference_union']['database_sha256']
    cross=[]
    for a in items:
        for b in items:
            if a['case']==b['case']:continue
            target=clause_set(b['target'],Counter())
            cross.append(dict(origin=a['case'],target=b['case'],old=clause_set(a['old']['source'],Counter())<=target,causal=clause_set(a['causal']['source'],Counter())<=target))
    report=dict(parent=study.binding(study.PARENT/'checkpoint.json'),decisions=parent['witness_signatures_decisions'],items=items,cross_containment=cross,
        old_counts=dict(old.counts),causal_counts=dict(new.counts),seconds=time.perf_counter()-start,sources={f:base.sha(f) for f in study.FILES},
        limitation='Historical, read-only extraction of proposals from checked proofs. No new derived certificate is published here; actual transfers still require checked materialization. Not a timing comparison or minimum-core claim.')
    base.write(out/'report.json',report);print(base.encode(dict(sizes=[(r['case'],r['old_clauses'],r['causal_clauses']) for r in items],extra_cross_pairs=[r for r in cross if r['causal'] and not r['old']])))


if __name__=='__main__':run(Path(sys.argv[1]))
