"""Optional mixed-CNF refutation from its binary subset.

Only negative binary decisions are used. A satisfiable subset says nothing
about the remaining clauses. Source-indexed implication paths use the existing
native checker and archive format. Units and existing all-binary leaves retain
their original priority; failed recognition falls back to the original search.
"""
from collections import Counter

from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_residual_dag import ResidualSolver, two_cnf


def refute_binary_subset(cnf, counts):
    """Return a source-bound native proof, or None (inconclusive).

    The caller supplies a normalized CNF. The uniform-assignment filter is a
    necessary condition for binary UNSAT: without a positive-only binary clause
    all-false works, and without a negative-only one all-true works.
    """
    counts['binary_subset_calls'] += 1
    ids = []
    wide = positive = negative = False
    for cid, clause in enumerate(cnf):
        counts['binary_subset_width_checks'] += 1
        if len(clause) < 2:
            counts['binary_subset_unit_skips'] += 1
            return None
        if len(clause) == 2:
            ids.append(cid)
            counts['binary_subset_sign_literals'] += 2
            positive |= clause[0] > 0 and clause[1] > 0
            negative |= clause[0] < 0 and clause[1] < 0
        else:
            wide = True
    if not wide or not ids:
        counts['binary_subset_shape_skips'] += 1
        return None
    if not (positive and negative):
        counts['binary_subset_uniform_skips'] += 1
        return None
    local = Counter()
    model, proof = two_cnf(tuple(cnf[i] for i in ids), local)
    counts.update({'binary_subset_' + k: v for k, v in local.items()})
    counts['binary_subset_scc_calls'] += 1
    if model is not None:
        counts['binary_subset_satisfiable_misses'] += 1
        return None
    counts['binary_subset_refutations'] += 1
    for name in ('forward', 'backward'):
        proof[name] = [[lit, ids[cid]] for lit, cid in proof[name]]
        counts['binary_subset_path_steps'] += len(proof[name])
    return proof


class BinarySubsetMixin:
    def _expand(self, cnf):
        if self.leaves:
            proof = refute_binary_subset(cnf, self.counts)
            if proof is not None:
                return None, proof
        return super()._expand(cnf)


class BinarySubsetSolver(BinarySubsetMixin, ResidualSolver):
    pass


class AccountedBinarySubsetSolver(BinarySubsetMixin, AccountedResidualSolver):
    pass
