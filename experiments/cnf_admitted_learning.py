"""Bound active learned-clause admission while preserving checked proof evidence.

Only the augmented search input is narrowed. All surviving derivations remain
available for proof substitution and persistence, so inactive is not invalid.
"""
from collections import Counter
from experiments import cnf_selective_learning as prior
CLAUSE_LIMIT=128


def _select(base, records, counts, clause_limit):
    present=set(base);candidates=[]
    # Newest duplicate wins; short clauses rank first, newest breaks equal widths.
    for i in range(len(records)-1,-1,-1):
        clause=tuple(records[i][2]);counts['admission_candidates']+=1;counts['admission_literal_charge']+=len(clause)
        if clause in present:counts['admission_redundant']+=1;continue
        present.add(clause);candidates.append((len(clause),-i,i))
    candidates.sort();selected=[i for _,_,i in candidates[:clause_limit]]
    counts['admission_eligible']+=len(candidates);counts['admission_active']+=len(selected)
    counts['admission_active_literals']+=sum(len(records[i][2]) for i in selected)
    return selected


def admit(target, knowledge, counts=None, *, clause_limit=CLAUSE_LIMIT):
    counts=Counter() if counts is None else counts
    if type(clause_limit) is not int or clause_limit<0:raise ValueError('Invalid clause admission budget')
    prior.prior.check_result(target,knowledge,counts)
    return _select(prior.canonical(target,counts),knowledge['derivations'],counts,clause_limit)


def expand(target, knowledge, counts=None, *, node_limit=prior.prior.NODE_LIMIT, clause_limit=CLAUSE_LIMIT):
    counts=Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit<0 or type(clause_limit) is not int or clause_limit<0:raise ValueError('Invalid admission or expansion budget')
    got=prior.prior.check_result(target,knowledge,counts)
    if got['answer'] is False:
        return knowledge,dict(reason='retained-refutation',expanded=0,node_limit=node_limit,reused=len(knowledge['derivations']),admitted=[])
    base=prior.canonical(target,counts);selected=_select(base,knowledge['derivations'],counts,clause_limit)
    records=[[a,[[v,p] for v,p in steps],c[:]] for a,steps,c in knowledge['derivations']]
    where={c:i for i,c in enumerate(base)}
    for i,record in enumerate(records):where.setdefault(tuple(record[2]),len(base)+i)
    augmented=[list(c) for c in target]+[records[i][2][:] for i in selected]
    counts['selective_augmented_literals']+=sum(len(c) for c in augmented)
    inputs=prior.canonical(augmented,counts);mapping=[where[c] for c in inputs]
    seed=prior.prior.prior.prior.proposal(target,counts)
    discovered,diag=prior.prior.search(augmented,seed,counts,node_limit=node_limit)
    for start,steps,clause in discovered['derivations']:
        counts['selective_composition_edges']+=1+len(steps);mapping.append(len(base)+len(records))
        records.append([mapping[start],[[v,mapping[parent]] for v,parent in steps],clause[:]])
    result=dict(format=prior.prior.FORMAT,kind=discovered['kind'],witness=discovered['witness'],derivations=records,conclusion=mapping[discovered['conclusion']] if discovered['conclusion'] is not None else None)
    prior.prior.check_result(target,result,counts)
    return result,dict(diag,reused=len(knowledge['derivations']),admitted=selected)


def solve(source, proof, target, counts=None, *, node_limit=prior.prior.NODE_LIMIT, clause_limit=CLAUSE_LIMIT):
    counts=Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit<0 or type(clause_limit) is not int or clause_limit<0:raise ValueError('Invalid admission or expansion budget')
    knowledge,survival=prior.transport(source,proof,target,counts)
    result,diag=expand(target,knowledge,counts,node_limit=node_limit,clause_limit=clause_limit)
    return result,dict(survival=survival,expansion=diag)
