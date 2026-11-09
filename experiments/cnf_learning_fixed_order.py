"""Test selected learned clauses with the baseline continuation variable order.

Reconstruct the first bounded batch solely to rank continuation variables. Apply
the selected batch to propagation. Both are derived from checked original-source
implications; no order, label or ranking hint is trusted from persistent input.
This isolates one selection effect, not all later first-conflict/path changes.
"""
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_learning_selection import SelectedLearningInventory, activation_batch
from experiments.cnf_probe_closure_reuse import discover_reuse_probes, check_reuse_probes
from experiments.cnf_probe_learning import learning_batch, augment


def baseline_continuation_choices(cnf, attempts, learn_limit, probe_limit, counts):
    counts['fixed_order_reconstructions'] += 1
    baseline = learning_batch(cnf, attempts, learn_limit, counts)
    choices = probe_choices(augment(cnf, baseline), probe_limit, counts)
    counts['fixed_order_candidates'] += len(choices)
    return choices


def discover_fixed_order_probes(cnf, probe_limit, learn_limit, counts):
    return discover_reuse_probes(cnf, probe_limit, learn_limit, counts,
        _select_batch=activation_batch, _continuation_choices=baseline_continuation_choices)


def check_fixed_order_probes(cnf, result, probe_limit, learn_limit, counts):
    return check_reuse_probes(cnf, result, probe_limit, learn_limit, counts,
        _select_batch=activation_batch, _continuation_choices=baseline_continuation_choices)


class FixedOrderLearningInventory(SelectedLearningInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['probe_learning'] = 'closure-fixed16-v1'

    def _discover_probes(self, cnf):
        return discover_fixed_order_probes(cnf, self.config['probe_limit'], self.config['learn_limit'], self.counts)

    def _check_probes(self, cnf, result):
        return check_fixed_order_probes(cnf, result, self.config['probe_limit'], self.config['learn_limit'], self.counts)
