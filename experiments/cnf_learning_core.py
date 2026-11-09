"""Consume checked learned hints locally, then acquire the original-source core.

The full parent implication/continuation proofs remain persistent. Hints support
that local propagation but are not inherited by child recognition or identity.
Descendants discover their own hints. This deliberately limited scope avoids
sharing a discovery plan under an unchecked inherited hint context.
"""
from experiments.cnf_learning_fixed_order import FixedOrderLearningInventory, check_fixed_order_probes
from experiments.cnf_probe_equivalence import substitute_block
from experiments.cnf_residual_dag import restrict


def core_after_checked_continuation(cnf, result, augmented_target, fixed, counts):
    """Internal transformation after full source/entailment/continuation checks.

Never call this on an unvalidated persisted result. Keep a checked conflict as
false; otherwise project only the original clauses using the proved assignment
or signed substitution. The parent keeps all proof dependencies and local hints.
"""
    if result['status'] != 'learned':
        return augmented_target, fixed
    if any(not clause for clause in augmented_target):
        counts['core_preserved_conflicts'] += 1
        return augmented_target, fixed
    continuation = result['continuation']
    if continuation['status'] == 'equivalence':
        core = substitute_block(cnf, continuation['witness'], counts)
    else:
        core = restrict(cnf, fixed, counts)
    if not {abs(l) for c in core for l in c} < {abs(l) for c in cnf for l in c}:
        raise ValueError('Core projection must strictly reduce source support')
    counts['core_projection_checks'] += 1
    counts['core_excluded_clause_occurrences'] += len(augmented_target) - len(core)
    counts['core_excluded_literal_occurrences'] += sum(map(len, augmented_target)) - sum(map(len, core))
    return core, fixed


def check_core_probes(cnf, result, probe_limit, learn_limit, counts):
    target, fixed = check_fixed_order_probes(cnf, result, probe_limit, learn_limit, counts)
    return core_after_checked_continuation(cnf, result, target, fixed, counts)


class CoreLearningInventory(FixedOrderLearningInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['probe_learning'] = 'closure-core16-v1'

    def _check_probes(self, cnf, result):
        return check_core_probes(cnf, result, self.config['probe_limit'], self.config['learn_limit'], self.counts)
