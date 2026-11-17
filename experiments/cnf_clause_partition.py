"""Exact disjoint branching by the first falsified missing clause.

A checked UNSAT T AND C1 ... AND Ck covers T by the alternatives in which
C1,...,C(i-1) hold and Ci is false. No simultaneous-falsification inference is
permitted. Native nodes remain unchanged; composition is a checked sidecar.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_clause_deletion_guard import clause_set,check_guard,lift
from experiments.cnf_guard_chain import _model
from experiments.cnf_residual_dag import restrict,holds
from experiments.cnf_unsat_support import checked_subset

FORMAT='checked-first-false-partition-v1'


def branch_sources(target,missing,counts=None):
    counts=Counter() if counts is None else counts
    if type(missing) is not list or not missing:raise ValueError('Nonempty ordered missing clauses required')
    members=clause_set(target,counts);extra=clause_set(missing,counts);variables={abs(l) for c in members for l in c}
    if len(extra)!=len(missing) or extra&members or any(not c for c in extra):raise ValueError('Missing clauses must be distinct, nonempty and absent')
    if not {abs(l) for c in extra for l in c}<=variables:raise ValueError('Missing variables outside target')
    normalized=[list(next(iter(clause_set([c],counts)))) for c in missing]
    prefix=[list(c) for c in target];branches=[]
    for clause in normalized:
        fixed={abs(l):l<0 for l in clause};residual=restrict(prefix,fixed,counts)
        branches.append((deepcopy(prefix),fixed,residual));prefix.append(clause)
    counts['partition_branches_built']+=len(branches)
    return normalized,branches


def publish_premise(solver,target,core,missing,counts=None):
    counts=Counter() if counts is None else counts
    ordered,_=branch_sources(target,missing,counts);outer=clause_set(target,counts);wanted=clause_set(core['source'],counts)
    if not wanted&outer or wanted-outer!=clause_set(ordered,counts):raise ValueError('Unbound missing-clause core')
    stronger=[list(c) for c in target]+ordered;cnf,_,root=solver._canonical(stronger)
    node=solver._read(root,cnf,purpose='partition_premise')
    if node is not None:
        if node['answer'] is not False:raise ValueError('Negative strengthened premise required')
        return False,root
    _,_,key=solver._canonical(core['source'])
    if key!=core['root']:raise ValueError('Wrong core root')
    return checked_subset(solver,stronger,core['source'],counts)


def _structure(solver,source,guards,missing,stronger_root,counts):
    current=source;steps=[]
    for guard in guards:
        fixed,target=check_guard(solver,current,guard,counts);steps.append((current,fixed));current=target
    ordered,branches=branch_sources(current,missing,counts)
    cnf,_,root=solver._canonical([list(c) for c in current]+ordered)
    if root!=stronger_root:raise ValueError('Partition premise identity mismatch')
    node=solver._read(root,cnf,purpose='partition_premise')
    if node is None or node['answer'] is not False:raise ValueError('Existing checked negative partition premise required')
    return steps,branches


def make_record(solver,source,guards,missing,stronger_root,children):
    steps,branches=_structure(solver,source,guards,missing,stronger_root,Counter())
    if not children or len(children)>len(branches):raise ValueError('Invalid branch prefix')
    model=None;answer=children[-1]['answer']
    if answer:
        prefix,fixed,_=branches[len(children)-1];model=lift(prefix,fixed,children[-1]['model'])
        for parent,assignment in reversed(steps):model=lift(parent,assignment,model)
    result=dict(format=FORMAT,source=deepcopy(source),query_root=solver._canonical(source)[2],guards=deepcopy(guards),
        missing_clauses=deepcopy(missing),stronger_root=stronger_root,children=[{k:deepcopy(c[k]) for k in ('root','answer','model')} for c in children],answer=answer,model=model)
    check_record(solver,result);return result


def check_record(solver,record,counts=None):
    counts=Counter() if counts is None else counts
    fields={'format','source','query_root','guards','missing_clauses','stronger_root','children','answer','model'}
    if type(record) is not dict or set(record)!=fields or record['format']!=FORMAT or type(record['guards']) is not list or type(record['answer']) is not bool:
        raise ValueError('Invalid partition record')
    _,_,root=solver._canonical(record['source'])
    if root!=record['query_root']:raise ValueError('Wrong partition source')
    steps,branches=_structure(solver,record['source'],record['guards'],record['missing_clauses'],record['stronger_root'],counts)
    children=record['children']
    if type(children) is not list or not children or len(children)>len(branches):raise ValueError('Invalid branch prefix')
    if not record['answer'] and len(children)!=len(branches):raise ValueError('UNSAT needs every partition branch')
    model=None
    for i,child in enumerate(children):
        if type(child) is not dict or set(child)!={'root','answer','model'} or type(child['answer']) is not bool:raise ValueError('Invalid partition child')
        prefix,fixed,target=branches[i];cnf,names,key=solver._canonical(target)
        if key!=child['root']:raise ValueError('Wrong partition branch root')
        node=solver._read(key,cnf,purpose='partition_child')
        if node is None:raise ValueError('Missing checked partition child')
        expected=dict(zip(names,node['model'])) if node['answer'] else None
        if child['answer']!=node['answer'] or _model(child['model'])!=expected:raise ValueError('Wrong partition child result')
        if node['answer']:
            if i!=len(children)-1 or not record['answer']:raise ValueError('SAT branch must end the recorded prefix')
            model=lift(prefix,fixed,expected)
            for parent,assignment in reversed(steps):model=lift(parent,assignment,model)
        elif i==len(children)-1 and record['answer']:raise ValueError('Missing SAT witness branch')
    if _model(record['model'])!=model:raise ValueError('Wrong partition witness')
    counts['checked_partitions']+=1;counts['checked_partition_children']+=len(children)
    return dict(answer=record['answer'],model=model,root=root)


class PartitionBank:
    """Load/check once; reuse in an exclusively owned immutable/append-only session."""
    def __init__(self,solver,records):
        self.solver=solver;self.entries={};self.counts=Counter()
        for record in deepcopy(records):
            result=check_record(solver,record,self.counts);_,names,key=solver._canonical(record['source'])
            entry=dict(answer=result['answer'],model=None if result['model'] is None else [result['model'][v] for v in names])
            if key in self.entries and self.entries[key]['answer']!=entry['answer']:raise ValueError('Conflicting checked partition conclusions')
            self.entries.setdefault(key,entry)

    def lookup(self,source):
        _,names,key=self.solver._canonical(source);self.counts['partition_lookups']+=1;entry=self.entries.get(key)
        if entry is None:return None
        model=None if entry['model'] is None else dict(zip(names,entry['model']))
        if model is not None and not holds(source,model):raise ValueError('Partition model transport failed')
        self.counts['partition_hits']+=1
        return dict(answer=entry['answer'],model=model,root=key)
