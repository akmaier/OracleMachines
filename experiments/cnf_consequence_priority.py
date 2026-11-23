"""Prefer a checked ordinary cofactor before a single late binary consequence.

This bounded experimental arbitration reuses the existing two-polarity probe.
It makes no prediction of optimal continuation cost and changes no proof format.
"""
from collections import Counter
from experiments.cnf_joint_backbone import discover,force_all,JointBackboneMixin
from experiments.cnf_targeted_backbone import TargetedBackboneMixin
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_binary_backbone import check_path
from experiments.cnf_binary_clause_cover import compile_cover
from experiments.cnf_bipolar_routing import probe_child
from experiments.cnf_residual_dag import restrict


def prefer_ordinary(solver,cnf,parts):
    c=solver.counts
    if len(parts)!=1:
        c['priority_joint_skips']+=1;return None
    binary=Counter(abs(l) for cl in cnf if len(cl)==2 for l in cl)
    c['priority_binary_scan_literals']+=sum(map(len,cnf))
    first=min(binary,key=lambda v:(-binary[v],v));selected=abs(parts[0]['literal'])
    if selected==first:
        c['priority_first_target_skips']+=1;return None
    frequency=Counter(abs(l) for cl in cnf for l in cl);size=sum(map(len,cnf))
    c['priority_full_scan_literals']+=size;ordinary=min(frequency,key=lambda v:(-frequency[v],v))
    if ordinary==selected:
        c['priority_same_variable_skips']+=1;return None
    if len(frequency)>256 or len(cnf)>4096 or size>16384:
        c['priority_size_skips']+=1;return None
    c['priority_candidates']+=1
    # Misses convey no SAT/UNSAT authority. The existing compiler checks a
    # negative cached cofactor or publishes a checked source-bound unit proof.
    for value in (False,True):
        excluded=probe_child(solver,cnf,ordinary,value)
        if excluded is None:continue
        c['priority_selections']+=1
        model,live=solver._visit(restrict(cnf,{ordinary:not value},c))
        if model is not None:
            c['priority_positive_lifts']+=1;return {ordinary:not value,**model},None
        return None,dict(kind='split',variable=ordinary,
            low=live if value else excluded,high=excluded if value else live)
    c['priority_misses']+=1;return None


class ConsequencePriorityMixin(JointBackboneMixin):
    def _expand(self,cnf):
        if self.leaves:
            proof,cover,parts=discover(cnf,self.counts)
            if proof is not None:return None,proof
            if cover is not None:return None,compile_cover(self,cnf,cover)
            if parts:
                for evidence in parts:check_path(cnf,evidence,self.counts)
                preferred=prefer_ordinary(self,cnf,parts)
                if preferred is not None:return preferred
                return force_all(self,cnf,parts)
        return super(TargetedBackboneMixin,self)._expand(cnf)


class ConsequencePrioritySolver(InputSafeAffineProbeSolver,ConsequencePriorityMixin):pass
