"""Spend the existing continuation budget on changed or previously unprobed pairs.

Keep old-ranked candidates unless both original closures remain inactive under
the checked learned batch. Fill the freed positions with active core candidates.
The original pass and all reasons stay persistent. This cannot discard an old
local reduction, but changed reduction priorities can change descendant coverage.
"""
from experiments.cnf_learning_core import CoreLearningInventory, core_after_checked_continuation
from experiments.cnf_learning_fixed_order import baseline_continuation_choices
from experiments.cnf_learning_selection import activation_batch
from experiments.cnf_probe_closure_reuse import batch_inactive, discover_reuse_probes, check_reuse_probes


def activity_choices(cnf, attempts, batch, learn_limit, probe_limit, counts):
    """Internal: original complete-clear traces and selected batch are established.

    Original pair order and every reason must be discovered or checked first.
    The inactive test establishes unchanged unit sets, not general irrelevance
    of a variable. Old informative choices retain their order and fit the cap;
    additional active core choices may be truncated. No saved mask is trusted.
    """
    core, active = [], []
    for i in range(0, len(attempts), 2):
        pair = attempts[i:i+2]
        variable = pair[0]['variable']
        core.append(variable)
        inactive = [batch_inactive(a, batch, counts) for a in pair]
        if all(inactive):
            counts['activity_inactive_core_pairs'] += 1
        else:
            active.append(variable)
            counts['activity_active_core_pairs'] += 1
    old = baseline_continuation_choices(cnf, attempts, learn_limit, probe_limit, counts)
    core_set, active_set = set(core), set(active)
    kept = [v for v in old if v not in core_set or v in active_set]
    added = [v for v in active if v not in kept]
    choices = (kept + added)[:probe_limit]
    counts['activity_choice_calls'] += 1
    counts['activity_omitted_old_inactive'] += len(old) - len(kept)
    counts['activity_kept_old_candidates'] += len(kept)
    counts['activity_added_core_candidates'] += len(choices) - len(kept)
    counts['activity_overflow_candidates'] += len(kept) + len(added) - len(choices)
    counts['activity_empty_continuations'] += not choices
    return choices


def _callbacks():
    # One invocation-scoped batch, populated only after the ordinary original
    # discovery/check. No cross-source cache or persistent activity hints.
    batch = None

    def select(cnf, attempts, limit, counts):
        nonlocal batch
        batch = activation_batch(cnf, attempts, limit, counts)
        return batch

    def choices(cnf, attempts, learn_limit, probe_limit, counts):
        if batch is None:
            raise ValueError('Activity choices require the checked selected batch')
        return activity_choices(cnf, attempts, batch, learn_limit, probe_limit, counts)

    return select, choices


def discover_activity_probes(cnf, probe_limit, learn_limit, counts):
    select, choices = _callbacks()
    return discover_reuse_probes(cnf, probe_limit, learn_limit, counts,
        _select_batch=select, _continuation_choices=choices)


def check_activity_probes(cnf, result, probe_limit, learn_limit, counts):
    select, choices = _callbacks()
    target, fixed = check_reuse_probes(cnf, result, probe_limit, learn_limit, counts,
        _select_batch=select, _continuation_choices=choices)
    return core_after_checked_continuation(cnf, result, target, fixed, counts)


class ActivityLearningInventory(CoreLearningInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['probe_learning'] = 'closure-activity16-v1'

    def _discover_probes(self, cnf):
        return discover_activity_probes(cnf, self.config['probe_limit'], self.config['learn_limit'], self.counts)

    def _check_probes(self, cnf, result):
        return check_activity_probes(cnf, result, self.config['probe_limit'], self.config['learn_limit'], self.counts)
