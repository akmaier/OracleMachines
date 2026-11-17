"""Acquire conditioned negatives when unit propagation exposes a cheap residual."""
from collections import Counter
from experiments.cnf_conditioned_core import assignment,project_core
from experiments.cnf_partition_screen import screen_branch,publish_screened_branch
from experiments.cnf_residual_dag import restrict


def acquire_core(solver,record):
    solver.counts=Counter();counts=Counter();fixed=assignment(record['assignment'])
    expected=project_core(solver,dict(source=record['parent_source'],root=record['parent_root']),fixed,counts)
    if record!=expected:raise ValueError('Unbound conditioned core')
    cnf,_,key=solver._canonical(record['source']);cached=solver._read(key,cnf,purpose='conditioning_existing');screen=None
    if cached is None:
        screen=screen_branch(solver,record['source'],counts);units={abs(l):l>0 for l,_ in screen['trace']}
        residual=restrict(cnf,units,counts)
        if screen['conflict'] is None and any(len(c)>2 for c in residual):raise ValueError('Propagation did not expose a two-CNF residual')
    checks=dict(solver.counts)
    child=solver.solve(record['source']) if screen is None else publish_screened_branch(solver,record['source'],screen)
    if child['answer'] is not False:raise ValueError('Conditioned negative core became positive')
    child.update(conditioning_check_metrics=checks,conditioning_screen_counts=dict(counts),conditioning_screen=screen)
    return child
