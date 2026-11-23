"""Fuse restriction, canonical clause order and parent-origin lookup.

Internal precondition: cnf is the immutable canonical CNF of a checked parent;
ids/assignments are drawn from its checked proof. Selected child indices are
validated here. No external input normalization or native proof check is replaced.
"""
from contextlib import contextmanager
from unittest.mock import patch
from experiments.cnf_causal_support import CausalSupportExtractor
from experiments.cnf_residual_dag import token


def fused_preimage(self,cnf,ids,assignment,child,selected):
    c=self.counts;c['preimage_calls']+=1;origin={}
    for cid in ids:
        if type(cid) is not int or not 0<=cid<len(cnf):raise ValueError('Invalid parent clause index')
        clause=cnf[cid];c['restriction_literal_visits']+=len(clause);kept=None;satisfied=False
        for index,literal in enumerate(clause):
            c['preimage_scanned_literals']+=1;variable=abs(literal)
            if variable in assignment:
                if assignment[variable]==(literal>0):satisfied=True;break
                # Copy only after the first deletion. Untouched immutable
                # clauses are reused directly, with their checked literal order.
                if kept is None:kept=list(clause[:index])
            elif kept is not None:kept.append(literal)
        if satisfied:
            c['preimage_satisfied_clauses']+=1;continue
        reduced=clause if kept is None else tuple(kept)
        if kept is None:
            c['preimage_unchanged_clauses']+=1;c['preimage_reused_literals']+=len(clause)
        else:c['preimage_shortened_clauses']+=1
        if reduced in origin:c['preimage_duplicate_clauses']+=1
        else:origin[reduced]=cid
    # Restriction preserves checked within-clause order and cannot introduce
    # a tautology or duplicate literal. Monotone compaction also preserves
    # signed literal order and lexicographic clause order.
    if () in origin:
        ordered=[()];normalized=((),);c['preimage_empty_collapses']+=1
    else:
        ordered=sorted(origin);names=sorted({abs(l) for cl in ordered for l in cl})
        rename={v:i+1 for i,v in enumerate(names)}
        normalized=tuple(tuple(rename[abs(l)]*(1 if l>0 else -1) for l in cl) for cl in ordered)
        c['preimage_name_variables']+=len(names);c['preimage_renamed_literals']+=sum(map(len,ordered))
    c['preimage_unique_clauses']+=len(ordered)
    # Keep the complete serialized key comparison: no digest/injectivity
    # assumption and no answer authority from the construction itself.
    if token(normalized,self.solver.counts)!=child:raise ValueError('Wrong parent-to-child edge')
    selected=tuple(selected)
    if any(type(i) is not int or not 0<=i<len(ordered) for i in selected):raise ValueError('Invalid child clause index')
    c['preimage_selected_indices']+=len(selected)
    return {origin[ordered[i]] for i in selected}


@contextmanager
def fused_preimages():
    """Scoped serial experiment; not safe for overlapping threads in one process."""
    with patch.object(CausalSupportExtractor,'_preimage',fused_preimage):yield
