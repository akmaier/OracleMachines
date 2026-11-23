"""Bounded failed-literal probing after binary structural discovery misses.

Experimental policy only. All exclusions are published with the existing native
unit certificate; misses are inconclusive. No new proof rule or default change.
"""
from collections import Counter
from experiments.cnf_consequence_priority import prefer_ordinary
from experiments.cnf_joint_backbone import discover, force_all, JointBackboneMixin
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_binary_backbone import check_path
from experiments.cnf_binary_clause_cover import compile_cover
from experiments.cnf_targeted_backbone import TargetedBackboneMixin
from experiments.cnf_bipolar_routing import probe_child
from experiments.cnf_residual_dag import restrict


def lookahead(solver, cnf):
    counts = solver.counts
    # Leave constants and ordinary propagation to the native kernel.
    if not cnf or any(len(c) < 2 for c in cnf):
        counts['whole_probe_unit_skips'] += 1
        return None
    size = sum(map(len, cnf))
    counts['whole_probe_size_literals'] += size
    if len(cnf) > 4096 or size > 16384:
        counts['whole_probe_size_skips'] += 1
        return None
    frequency = Counter(abs(l) for c in cnf for l in c)
    counts['whole_probe_ranking_literals'] += size
    if len(frequency) > 256:
        counts['whole_probe_size_skips'] += 1
        return None
    variable = min(frequency, key=lambda v: (-frequency[v], v))
    counts['whole_probe_candidates'] += 1
    for value in (False, True):
        excluded = probe_child(solver, cnf, variable, value)
        if excluded is None:
            continue
        counts['whole_probe_selections'] += 1
        model, live = solver._visit(restrict(cnf, {variable: not value}, counts))
        if model is not None:
            counts['whole_probe_positive_lifts'] += 1
            return {variable: not value, **model}, None
        return None, dict(kind='split', variable=variable,
            low=live if value else excluded, high=excluded if value else live)
    counts['whole_probe_misses'] += 1
    return None


class WholeLookaheadMixin(JointBackboneMixin):
    def _expand(self, cnf):
        if self.leaves:
            proof, cover, parts = discover(cnf, self.counts)
            if proof is not None:
                return None, proof
            if cover is not None:
                return None, compile_cover(self, cnf, cover)
            if parts:
                for evidence in parts:
                    check_path(cnf, evidence, self.counts)
                preferred = prefer_ordinary(self, cnf, parts)
                if preferred is not None:
                    return preferred
                return force_all(self, cnf, parts)
            preferred = lookahead(self, cnf)
            if preferred is not None:
                return preferred
        return super(TargetedBackboneMixin, self)._expand(cnf)


class WholeLookaheadSolver(InputSafeAffineProbeSolver, WholeLookaheadMixin):
    pass
