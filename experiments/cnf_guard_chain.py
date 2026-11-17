"""Compose checked clause-deletion guards and retain reusable query sidecars.

Native proof nodes keep their existing format. Each guard premise and the final
child are ordinary checked nodes; a chain records their exact composition. The
optional bank verifies chains on load and reuses conclusions under identical
normalized CNFs in an exclusively owned, immutable/append-only proof session.
"""
from collections import Counter
from copy import deepcopy
from experiments.cnf_clause_deletion_guard import FORMAT as GUARD_FORMAT,check_guard,clause_set,lift
from experiments.cnf_residual_dag import restrict,holds
from experiments.cnf_unsat_support import checked_subset

FORMAT='checked-guard-chain-v1'


def propose_missing_clause(solver,source,cores,counts=None):
    """First ready core with exactly one missing, nonempty clause; no solving."""
    counts=Counter() if counts is None else counts
    members=clause_set(source,counts);variables={abs(l) for c in members for l in c}
    for index,core in enumerate(cores):
        wanted=clause_set(core['source'],counts);counts['near_core_candidates']+=1
        counts['near_core_comparison_clauses']+=len(wanted)
        if not wanted&members:continue
        missing=wanted-members
        if len(missing)!=1:continue
        clause=next(iter(missing))
        if not clause or not {abs(l) for l in clause}<=variables:continue
        fixed={abs(l):l<0 for l in clause};target=restrict(source,fixed,counts)
        if clause_set(target,counts)==members:continue
        cnf,_,root=solver._canonical(core['source'])
        if root!=core['root']:raise ValueError('Unbound near core')
        node=solver._read(root,cnf,purpose='near_core');counts['near_core_reads']+=1
        if node is None:counts['near_pending_skipped']+=1;continue
        if node['answer'] is not False:raise ValueError('Checked negative near core required')
        return dict(core=index,missing_clause=list(clause))
    return None


def publish_guard(solver,source,core,clause,counts=None):
    """Construct a native subset proof for source AND clause, then its guard."""
    counts=Counter() if counts is None else counts
    members=clause_set(source,counts);wanted=clause_set(core['source'],counts)
    candidate=clause_set([clause],counts)
    if len(candidate)!=1 or not clause or wanted-members!=candidate or not wanted&members:
        raise ValueError('Expected exactly one nonempty missing core clause')
    if not {abs(l) for l in clause}<={abs(l) for c in members for l in c}:
        raise ValueError('Guard variables must occur in the target')
    cnf,_,root=solver._canonical(core['source'])
    if root!=core['root']:raise ValueError('Unbound selected core')
    stronger=[list(c) for c in source]+[list(clause)]
    inserted,root=checked_subset(solver,stronger,core['source'],counts)
    guard=dict(format=GUARD_FORMAT,stronger=stronger,stronger_root=root,removed_clause=list(next(iter(candidate))))
    fixed,target=check_guard(solver,source,guard,counts)
    return guard,fixed,target,inserted


def _model(value):
    if value is None:return None
    if type(value) is not dict:raise ValueError('Model must be a variable map')
    result={}
    for key,bit in value.items():
        if type(key) is int and key>0:v=key
        elif type(key) is str and key.isdecimal() and str(int(key))==key and int(key)>0:v=int(key)
        else:raise ValueError('Invalid model variable')
        if type(bit) is not bool or v in result:raise ValueError('Invalid model value or duplicate variable')
        result[v]=bit
    return result


def make_record(solver,source,guards,child):
    targets=[];current=source
    for guard in guards:
        fixed,target=check_guard(solver,current,guard);targets.append((current,fixed));current=target
    model=child['model']
    if child['answer']:
        for parent,fixed in reversed(targets):model=lift(parent,fixed,model)
    record=dict(format=FORMAT,source=deepcopy(source),query_root=solver._canonical(source)[2],guards=deepcopy(guards),
        child={k:deepcopy(child[k]) for k in ('root','answer','model')},answer=child['answer'],model=model)
    check_record(solver,record)
    return record


def check_record(solver,record,counts=None):
    """Read/check only: never turn an absent child into a fresh solve."""
    counts=Counter() if counts is None else counts
    if (type(record) is not dict or set(record)!={'format','source','query_root','guards','child','answer','model'}
        or record['format']!=FORMAT or type(record['guards']) is not list or type(record['answer']) is not bool):
        raise ValueError('Invalid guard-chain record')
    _,_,root=solver._canonical(record['source'])
    if root!=record['query_root']:raise ValueError('Unbound chain query')
    current=record['source'];steps=[]
    for guard in record['guards']:
        fixed,target=check_guard(solver,current,guard,counts);steps.append((current,fixed));current=target
    child=record['child']
    if type(child) is not dict or set(child)!={'root','answer','model'} or type(child['answer']) is not bool:
        raise ValueError('Invalid chain child')
    cnf,names,key=solver._canonical(current)
    if child['root']!=key:raise ValueError('Chain child identity mismatch')
    node=solver._read(key,cnf,purpose='chain_child')
    if node is None:raise ValueError('Chain child requires an existing checked result')
    expected=dict(zip(names,node['model'])) if node['answer'] else None
    if child['answer']!=node['answer'] or _model(child['model'])!=expected:
        raise ValueError('Chain child answer or witness mismatch')
    model=expected
    if node['answer']:
        for parent,fixed in reversed(steps):model=lift(parent,fixed,model)
    if record['answer']!=node['answer'] or _model(record['model'])!=model:
        raise ValueError('Chain conclusion or lifted witness mismatch')
    counts['checked_chains']+=1;counts['checked_chain_steps']+=len(steps)
    return dict(answer=node['answer'],model=model,root=root)


class GuardChainBank:
    def __init__(self,solver,records):
        self.solver=solver;self.counts=Counter();self.entries={}
        for record in deepcopy(records):
            result=check_record(solver,record,self.counts);_,names,key=solver._canonical(record['source'])
            model=None if result['model'] is None else [result['model'][v] for v in names]
            entry=dict(answer=result['answer'],model=model)
            if key in self.entries and self.entries[key]['answer']!=entry['answer']:
                raise ValueError('Conflicting verified chain conclusions')
            self.entries.setdefault(key,entry)

    def lookup(self,source):
        _,names,key=self.solver._canonical(source);self.counts['chain_lookups']+=1
        entry=self.entries.get(key)
        if entry is None:return None
        model=None if entry['model'] is None else dict(zip(names,entry['model']))
        if model is not None and not holds(source,model):raise ValueError('Transported chain witness fails')
        self.counts['chain_hits']+=1
        return dict(answer=entry['answer'],model=model,root=key)
