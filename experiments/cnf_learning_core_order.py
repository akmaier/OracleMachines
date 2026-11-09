"""Reuse the original core's checked probe order for the existing continuation.

The selected batch, two bounded phases and original-core child representation
are unchanged. This is an optional heuristic: a different bounded choice can
lose discoveries. Persisted traces must pass the original complete-clear check
before their choices can be reused; an unchecked choice list is never accepted.
"""
from experiments.cnf_learning_core import CoreLearningInventory, core_after_checked_continuation
from experiments.cnf_learning_selection import activation_batch
from experiments.cnf_probe_closure_reuse import discover_reuse_probes, check_reuse_probes


def checked_core_choices(cnf, attempts, learn_limit, probe_limit, counts):
    """Internal callback after discovery or validation of a complete clear pass.

    Both callers in cnf_probe_closure_reuse establish that attempts contains
    exactly the deterministic core-ranked variables, false then true. Extracting
    those choices takes O(probe_limit), without rebuilding a second learned view
    just to rank it. Proof checking still reconstructs the original core ranking.
    """
    choices = [a['variable'] for a in attempts[::2]]
    counts['core_order_extractions'] += 1
    counts['core_order_candidates'] += len(choices)
    return choices


def discover_core_order_probes(cnf, probe_limit, learn_limit, counts):
    return discover_reuse_probes(cnf, probe_limit, learn_limit, counts,
        _select_batch=activation_batch, _continuation_choices=checked_core_choices)


def check_core_order_probes(cnf, result, probe_limit, learn_limit, counts):
    target, fixed = check_reuse_probes(cnf, result, probe_limit, learn_limit, counts,
        _select_batch=activation_batch, _continuation_choices=checked_core_choices)
    return core_after_checked_continuation(cnf, result, target, fixed, counts)


class CoreOrderLearningInventory(CoreLearningInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['probe_learning'] = 'closure-core-order16-v1'

    def _discover_probes(self, cnf):
        return discover_core_order_probes(cnf, self.config['probe_limit'], self.config['learn_limit'], self.counts)

    def _check_probes(self, cnf, result):
        return check_core_order_probes(cnf, result, self.config['probe_limit'], self.config['learn_limit'], self.counts)
