"""Validate a supplied donor's checked SAT model against a complete target CNF.

Candidate discovery is deliberately outside this helper. Shared original variable
IDs bind the assignments; absent variables are tried as false and fully checked.
A miss means only this candidate failed, never UNSAT. No fresh search is called.
"""
from collections import Counter
import time
from experiments.cnf_residual_dag import FORMAT,holds


def reuse_checked_model(solver,donor_source,target_source):
    if solver.db.in_transaction or getattr(solver.db,'active',False):
        raise RuntimeError('Model publication requires an idle owned solver')
    tick=time.perf_counter();solver.counts=Counter()
    donor,names,donor_key=solver._canonical(donor_source)
    target,target_names,target_key=solver._canonical(target_source)
    node=solver._read(donor_key,donor,purpose='model_reuse')
    if node is None or not node['answer']:
        return dict(status='miss',reason='no checked SAT donor',donor=donor_key,root=target_key,
                    metrics=dict(solver.counts),seconds=time.perf_counter()-tick)
    external={name:node['model'][i] for i,name in enumerate(names)}
    model={name:external.get(name,False) for name in target_names}
    solver.counts['model_reuse_target_literals']+=sum(map(len,target_source))
    if not holds(target_source,model):
        return dict(status='miss',reason='candidate violates target',donor=donor_key,root=target_key,
                    metrics=dict(solver.counts),seconds=time.perf_counter()-tick)
    local=[model[name] for name in target_names]
    solver._store(target_key,dict(format=FORMAT,cnf=[list(c) for c in target],answer=True,model=local))
    return dict(status='sat',answer=True,authority='native',donor=donor_key,root=target_key,model=model,
                metrics=dict(solver.counts),seconds=time.perf_counter()-tick)
