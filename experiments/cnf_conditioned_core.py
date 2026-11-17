"""Condition checked negative cores and acquire missing two-CNF certificates.

A parent proof is provenance, not a replacement for a missing native cofactor
certificate. Existing cofactor roots are reused; fresh acquisition is restricted
to two-CNF. Ordinary partition composition consumes the resulting native root.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_residual_dag import restrict

FORMAT='checked-conditioned-core-v1'


def assignment(value):
    if type(value) is not list:raise ValueError('Expected assignment pairs')
    fixed={}
    for pair in value:
        if type(pair) is not list or len(pair)!=2:raise ValueError('Invalid assignment pair')
        var,bit=pair
        if type(var) is not int or var<=0 or type(bit) is not bool or var in fixed:raise ValueError('Invalid fixed variable')
        fixed[var]=bit
    return fixed


def project_core(solver,core,fixed,counts=None):
    counts=Counter() if counts is None else counts
    if type(fixed) is not dict:raise ValueError('Expected variable map')
    fixed=assignment([[v,b] for v,b in fixed.items()]);pairs=[[v,b] for v,b in sorted(fixed.items())]
    cnf,_,root=solver._canonical(core['source'])
    if root!=core['root']:raise ValueError('Unbound conditioning parent')
    parent=solver._read(root,cnf,purpose='conditioning_parent')
    if parent is None or parent['answer'] is not False:raise ValueError('Checked negative parent required')
    residual=restrict(core['source'],fixed,counts);_,_,child=solver._canonical(residual)
    counts['conditioned_cores']+=1
    return dict(format=FORMAT,parent_source=deepcopy(core['source']),parent_root=root,assignment=pairs,source=[list(c) for c in residual],root=child)


def acquire_core(solver,record):
    """Reuse an existing root or solve a two-CNF cofactor with the frozen solver."""
    solver.counts=Counter();fixed=assignment(record['assignment']);solver.counts['conditioning_assignment_pairs']+=len(fixed);residual=restrict(record['parent_source'],fixed,solver.counts)
    cnf,_,key=solver._canonical(residual)
    if record['format']!=FORMAT or record['source']!=[list(c) for c in residual] or key!=record['root'] or solver._canonical(record['source'])[2]!=key:raise ValueError('Unbound cofactor')
    parent,_,root=solver._canonical(record['parent_source']);node=solver._read(root,parent,purpose='conditioning_parent')
    if root!=record['parent_root'] or node is None or node['answer'] is not False:raise ValueError('Checked negative parent required')
    cached=solver._read(key,cnf,purpose='conditioning_existing')
    if cached is None and any(len(c)>2 for c in cnf):raise ValueError('Fresh conditioning acquisition is restricted to two-CNF')
    checks=dict(solver.counts);child=solver.solve(record['source']);child['conditioning_check_metrics']=checks
    if child['answer'] is not False:raise ValueError('Conditioned negative core became positive')
    return child


def check_record(solver,record,counts=None):
    counts=Counter() if counts is None else counts
    fields={'format','parent_source','parent_root','assignment','source','root'}
    if type(record) is not dict or set(record)!=fields or record['format']!=FORMAT:raise ValueError('Invalid conditioned-core record')
    fixed=assignment(record['assignment']);parent,_,root=solver._canonical(record['parent_source']);node=solver._read(root,parent,purpose='conditioning_parent')
    if root!=record['parent_root'] or node is None or node['answer'] is not False:raise ValueError('Missing negative parent')
    residual=restrict(record['parent_source'],fixed,counts);cnf,_,key=solver._canonical(residual)
    # Match in source coordinates before accepting the canonical native identity.
    actual=[list(c) for c in residual]
    if record['source']!=actual or record['root']!=key:raise ValueError('Wrong conditioned source')
    node=solver._read(key,cnf,purpose='conditioning_child')
    if node is None or node['answer'] is not False:raise ValueError('Missing native conditioned-core proof')
    counts['checked_conditioned_cores']+=1
    return dict(source=deepcopy(record['source']),root=key)
