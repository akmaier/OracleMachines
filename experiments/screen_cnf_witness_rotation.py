#!/usr/bin/env python3
"""Post-hoc one-variable model-rotation screen; no new reference search."""
from pathlib import Path
import sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_clause_witness_reuse as study
from experiments.cnf_clause_deletion_guard import removed_clause
from experiments.cnf_residual_dag import holds
base=study.base


def run(out):
    started=time.perf_counter();protocol=base.load(out/'protocol.json');cases=base.load(protocol['cases']['path'])
    seed=base.load(protocol['seed']['path']);decisions=base.load(out/'union-decisions.json');checkpoint=base.load(out/'checkpoint.json')
    attempts=[];candidates=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'reference';base.restore_archive(checkpoint['reference_union'],path);solver=study.ResidualSolver(path)
        try:
            solver.db.execute('PRAGMA query_only=ON')
            with patch.object(solver,'_expand',side_effect=AssertionError('Fresh rotation search')):
                for case,old,decision in zip(cases[1::2],seed['records'],decisions,strict=True):
                    assert decision['case']==case['case']
                    if old['answer'] or not decision['answer']:continue
                    strong=old['source'];normalized,_,root=solver._canonical(strong)
                    assert root==old['child']['root'] and solver._read(root,normalized)['answer'] is False
                    m={int(k):v for k,v in decision['model'].items()};assert holds(case['source'],m)
                    deleted=removed_clause(strong,case['source'])
                    bad=[sorted(c) for c in strong if not holds([c],m)];assert bad==[deleted]
                    for literal in deleted:
                        variable=abs(literal);model={**m,variable:not m[variable]}
                        violated=[sorted(c) for c in strong if not holds([c],model)]
                        row=dict(case=case['case'],variable=variable,falsified_clauses=violated)
                        if len(violated)==1:
                            target=[c for c in strong if sorted(c)!=violated[0]];assert holds(target,model)
                            _,_,key=solver._canonical(target);present=solver._read(key) is not None
                            candidate=dict(source=target,model=model,root=key,present=present,
                                stronger_root=root,from_case=case['case'],flipped_variable=variable,removed_clause=violated[0])
                            row['candidate_root']=key;candidates.append(candidate)
                        attempts.append(row)
        finally:solver.close();assert base.sha(path)==checkpoint['reference_union']['database_sha256']
    result=dict(checkpoint=study.binding(out/'checkpoint.json'),decisions=study.binding(out/'union-decisions.json'),
        analyzer=study.binding(__file__),attempts=attempts,candidates=candidates,no_acquisition=True,seconds=time.perf_counter()-started,
        limitation='Post-hoc full-clause scans on three known SAT deletion witnesses, not a timed algorithm comparison. Candidates are verified SAT models, not published cache rows.')
    base.write(out/'rotation-screen.json',result);print(base.encode(dict(attempts=len(attempts),candidates=len(candidates),previously_absent=sum(not c['present'] for c in candidates),seconds=result['seconds'])))


if __name__=='__main__':run(Path(sys.argv[1]))
