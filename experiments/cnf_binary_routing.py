"""Prefer a checked easy default cofactor before a different binary backbone.

Only a completed negative native child (cached or unit-refuted) changes routing.
The existing split/model verifier remains the authority. This process-local
experimental expansion adapter changes no solver defaults.
"""
from collections import Counter
from experiments.cnf_residual_dag import FORMAT,propagate,restrict
from experiments.cnf_ranked_binary_targets import discover
from experiments.cnf_binary_backbone import check_path,excluded_child
from experiments.cnf_binary_clause_cover import compile_cover
from experiments.cnf_targeted_backbone import TargetedBackboneMixin


def default_false_child(solver,cnf,variable):
    """One bounded-shape probe; absence of a conflict is inconclusive."""
    counts=solver.counts;counts['routing_false_probes']+=1
    child,names,key=solver._canonical(restrict(cnf,{variable:False},counts))
    old=solver._read(key,child,purpose='routing_cofactor') if solver.reuse else None
    if old is not None:
        counts['routing_cached_negative' if not old['answer'] else 'routing_cached_positive']+=1
        return key if old['answer'] is False else None
    local=Counter();fixed,trace,conflict=propagate(child,local)
    counts.update({'routing_'+k:v for k,v in local.items()})
    counts['routing_probe_trace_entries']+=len(trace)
    if conflict is None:
        counts['routing_no_conflict']+=1;return None
    # The independent native checker binds every retained reason to the exact
    # canonical cofactor before this node can support a split.
    solver._store(key,dict(format=FORMAT,cnf=[list(c) for c in child],answer=False,
        proof=dict(kind='units',trace=trace,conflict=conflict)))
    counts['routing_compiled_children']+=1
    return key


def priority_expand(self,cnf):
    if self.leaves:
        proof,cover,partials=discover(cnf,self.counts,policy='binary1')
        if proof is not None:return None,proof
        if cover is not None:return None,compile_cover(self,cnf,cover)
        evidence=partials[0] if partials else None
        if evidence is not None:
            check_path(cnf,evidence,self.counts)
            literal=evidence['literal'];variable=abs(literal)
            frequencies=Counter(abs(l) for c in cnf for l in c);literals=sum(map(len,cnf))
            self.counts['routing_ranking_literals']+=literals
            default=min(frequencies,key=lambda v:(-frequencies[v],v))
            if default!=variable:
                if len(frequencies)<=256 and len(cnf)<=4096 and literals<=16384:
                    excluded=default_false_child(self,cnf,default)
                    if excluded is not None:
                        self.counts['routing_default_selections']+=1
                        model,live=self._visit(restrict(cnf,{default:True},self.counts))
                        if model is not None:
                            self.counts['routing_positive_lifts']+=1
                            return {default:True,**model},None
                        return None,dict(kind='split',variable=default,low=excluded,high=live)
                else:self.counts['routing_size_skips']+=1
            else:self.counts['routing_same_variable_skips']+=1
            self.counts['binary_backbone_selections']+=1
            model,live=self._visit(restrict(cnf,{variable:literal<0},self.counts))
            if model is not None:
                self.counts['binary_backbone_positive_lifts']+=1
                return {variable:literal<0,**model},None
            excluded=excluded_child(self,cnf,evidence)
            self.counts['binary_backbone_negative_splits']+=1
            return None,dict(kind='split',variable=variable,low=live if literal>0 else excluded,high=excluded if literal>0 else live)
    return super(TargetedBackboneMixin,self)._expand(cnf)
