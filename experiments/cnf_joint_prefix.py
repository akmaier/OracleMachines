"""Reuse the already-live first cofactor while compiling two consequences.

The forward prefix lookup and backward parent publication use the same source
and first assignment. Native checking remains unchanged. No memo or extra CNF
is retained; this relies on the existing two-path bound and immutable triples.
"""
from contextlib import contextmanager
from unittest.mock import patch
from experiments import cnf_joint_backbone as joint,cnf_consequence_priority as priority
from experiments.cnf_joint_backbone import check_path,excluded_child,excluded_context,restrict,FORMAT


def reuse_prefix(solver,cnf,evidence):
    if not 1<=len(evidence)<=2:raise ValueError('One or two joint paths required')
    for e in evidence:check_path(cnf,e,solver.counts)
    if len({abs(e['literal']) for e in evidence})!=len(evidence):raise ValueError('Joint variables must differ')
    # Preserve the single-consequence implementation when no second additional
    # consequence was found; this also avoids a gratuitous prefix cache lookup.
    if len(evidence)==1:
        e=evidence[0];l=e['literal'];v=abs(l)
        model,live=solver._visit(restrict(cnf,{v:l<0},solver.counts))
        if model is not None:return {v:l<0,**model},None
        excluded=excluded_child(solver,cnf,e)
        return None,dict(kind='split',variable=v,low=live if l>0 else excluded,high=excluded if l>0 else live)
    fixed={};parents=[];model=None;live=None
    for index,e in enumerate(evidence):
        parents.append((dict(fixed),e));fixed[abs(e['literal'])]=e['literal']<0
        child=restrict(cnf,fixed,solver.counts)
        if index+1<len(evidence):
            local,names,key=solver._canonical(child);old=solver._read(key,local,purpose='joint_prefix')
            if old is not None:
                solver.counts['joint_prefix_hits']+=1;live=key
                if old['answer']:model={oldvar:old['model'][j] for j,oldvar in enumerate(names)}
                break
        else:model,live=solver._visit(child)
    if model is not None:
        solver.counts['joint_positive_lifts']+=1;return {**fixed,**model},None
    solver.counts['joint_negative_batches']+=1
    for index in range(len(parents)-1,-1,-1):
        context,e=parents[index]
        if index==0:
            raw=restrict(cnf,context,solver.counts)
            local,names,key=solver._canonical(raw)
        else:
            # With at most two paths, index 1 is exactly the first surviving
            # prefix. Its immutable canonical triple is still in these locals
            # from the forward lookup, across the recursive child visit.
            # Do not generalize this to larger batches without per-frame state.
            solver.counts['joint_prefix_construction_reuses']+=1
        v=abs(e['literal'])
        if v not in names:
            if live!=key:raise ValueError('Irrelevant joint variable changed residual')
            solver.counts['joint_irrelevant_variables']+=1;continue
        excluded=excluded_context(solver,cnf,e,context);variable=names.index(v)+1
        proof=dict(kind='split',variable=variable,low=live if e['literal']>0 else excluded,high=excluded if e['literal']>0 else live)
        if index==0:return None,proof
        solver._store(key,dict(format=FORMAT,cnf=[list(c) for c in local],answer=False,proof=proof))
        solver.counts['joint_compiled_parents']+=1;live=key
    raise ValueError('No joint root split')


@contextmanager
def reused_joint_prefix():
    """Optional serial experiment; not safe for overlapping threads."""
    with patch.object(joint,'force_all',reuse_prefix),patch.object(priority,'force_all',reuse_prefix):yield
