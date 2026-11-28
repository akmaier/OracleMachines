"""Select surviving resolution derivations after edits and compose fresh search.

Survival is syntactic reachability in the supplied proof DAG, not semantic
entailment completeness. Target conclusions use the unchanged source checker.
"""
from collections import Counter
from experiments import cnf_resolution_learning as prior


def canonical(source, counts):
    return prior.prior.prior.previous.capacity.canonical(source,counts)


def transport(source, proof, target, counts=None):
    """Keep exactly records whose recorded original-premise paths survive."""
    counts=Counter() if counts is None else counts
    prior.check_result(source,proof,counts)
    old=canonical(source,counts);new=canonical(target,counts);where={c:i for i,c in enumerate(new)}
    mapping=[];missing=[]
    for i,c in enumerate(old):
        counts['selective_guard_literals']+=len(c);mapping.append(where.get(c))
        if mapping[-1] is None:missing.append(i)
    kept=[];discarded=[];records=[]
    for i,(start,steps,clause) in enumerate(proof['derivations']):
        counts['selective_parent_edges']+=1+len(steps)
        if mapping[start] is None or any(mapping[parent] is None for _,parent in steps):
            mapping.append(None);discarded.append(i);counts['selective_discarded']+=1
        else:
            mapping.append(len(new)+len(records));kept.append(i)
            records.append([mapping[start],[[v,mapping[parent]] for v,parent in steps],clause[:]])
            counts['selective_retained']+=1;counts['selective_copied_literals']+=len(clause)
    empty=next((i for i,c in enumerate(new) if not c),None)
    if empty is None:empty=next((len(new)+i for i,r in enumerate(records) if not r[2]),None)
    result=dict(format=prior.FORMAT,kind='unsat' if empty is not None else 'unknown',witness=None,derivations=records,conclusion=empty)
    prior.check_result(target,result,counts)
    return result,dict(missing_source_indices=missing,retained_indices=kept,discarded_indices=discarded)


def expand(target, knowledge, counts=None, *, node_limit=prior.NODE_LIMIT):
    """Search an equivalent augmented CNF; substitute checked premises back."""
    counts=Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit<0:raise ValueError('Invalid expansion budget')
    got=prior.check_result(target,knowledge,counts)
    if got['answer'] is False:
        return knowledge,dict(reason='retained-refutation',expanded=0,node_limit=node_limit,reused=len(knowledge['derivations']))
    base=canonical(target,counts);records=[[a,[[v,p] for v,p in steps],c[:]] for a,steps,c in knowledge['derivations']]
    where={c:i for i,c in enumerate(base)}
    for i,record in enumerate(records):where.setdefault(tuple(record[2]),len(base)+i)
    augmented=[list(c) for c in target]+[r[2][:] for r in records]
    counts['selective_augmented_literals']+=sum(len(c) for c in augmented)
    inputs=canonical(augmented,counts);mapping=[where[c] for c in inputs]
    # Keep the ordinary target proposal fixed. Learned constraints affect search,
    # not the proposal policy; their variables occur in retained target premises.
    seed=prior.prior.prior.proposal(target,counts)
    discovered,diag=prior.search(augmented,seed,counts,node_limit=node_limit)
    for start,steps,clause in discovered['derivations']:
        counts['selective_composition_edges']+=1+len(steps)
        mapping.append(len(base)+len(records))
        records.append([mapping[start],[[v,mapping[parent]] for v,parent in steps],clause[:]])
    result=dict(format=prior.FORMAT,kind=discovered['kind'],witness=discovered['witness'],derivations=records,conclusion=mapping[discovered['conclusion']] if discovered['conclusion'] is not None else None)
    prior.check_result(target,result,counts)
    return result,dict(diag,reused=len(knowledge['derivations']))


def solve(source, proof, target, counts=None, *, node_limit=prior.NODE_LIMIT):
    counts=Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit<0:raise ValueError('Invalid expansion budget')
    knowledge,survival=transport(source,proof,target,counts)
    result,diag=expand(target,knowledge,counts,node_limit=node_limit)
    return result,dict(survival=survival,expansion=diag)
