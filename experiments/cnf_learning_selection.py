"""Select a bounded learned batch by saved-closure activation and diversity.

Candidates come only from already proved original-source implications. A fixed
pool cap of sixteen bounds selection breadth; it is not exhaustive or optimal.
The retained clause/probe caps and all earlier reductions are unchanged. Both
useful and unsuccessful attempts retain enough evidence for independent replay.
"""
from experiments.cnf_probe_closure_compact import CompactProbeClosureInventory
from experiments.cnf_probe_closure_reuse import discover_reuse_probes, check_reuse_probes
from experiments.cnf_probe_learning import learning_batch


def activation_masks(pool, attempts, counts):
    assignments = []
    for attempt in attempts:
        assigned = {attempt['variable']: attempt['value']}
        assigned.update((abs(lit), lit > 0) for lit, _ in attempt['certificate']['units'])
        counts['selection_assignment_entries'] += len(assigned)
        assignments.append(assigned)
    masks = []
    for candidate in pool:
        mask = 0
        for i, assigned in enumerate(assignments):
            satisfied, pending = False, 0
            for lit in candidate['clause']:
                counts['selection_delta_literal_visits'] += 1
                value = assigned.get(abs(lit))
                if value is None:
                    pending += 1
                elif value == (lit > 0):
                    satisfied = True
                    break
            if not satisfied and pending < 2:
                mask |= 1 << i
        masks.append(mask)
    return masks


def activation_batch(cnf, attempts, limit, counts):
    if not limit:
        return []
    # Pool filtering may use edges of candidates not ultimately retained.
    # This can miss useful alternatives, but every selected reason still comes
    # from the original source, so it cannot introduce circular justification.
    pool = learning_batch(cnf, attempts, 16, counts)
    counts['selection_pool_clauses'] += len(pool)
    if len(pool) <= limit:
        return pool
    masks = activation_masks(pool, attempts, counts)
    remaining = list(range(len(pool)))
    selected, origins, covered = [], set(), 0
    while remaining and len(selected) < limit:
        counts['selection_candidate_scores'] += len(remaining)
        best = max(remaining, key=lambda i: (
            (masks[i] & ~covered).bit_count(),
            pool[i]['attempt'] not in origins,
            masks[i].bit_count(), -i))
        selected.append(pool[best]); origins.add(pool[best]['attempt'])
        covered |= masks[best]; remaining.remove(best)
    counts['selection_changed_batches'] += selected != pool[:limit]
    counts['selection_covered_closures'] += covered.bit_count()
    counts['selection_distinct_origins'] += len(origins)
    return selected


def discover_selected_probes(cnf, probe_limit, learn_limit, counts):
    return discover_reuse_probes(cnf, probe_limit, learn_limit, counts, _select_batch=activation_batch)


def check_selected_probes(cnf, result, probe_limit, learn_limit, counts):
    return check_reuse_probes(cnf, result, probe_limit, learn_limit, counts, _select_batch=activation_batch)


class SelectedLearningInventory(CompactProbeClosureInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['probe_learning'] = 'closure-activate16-v3'

    def _discover_probes(self, cnf):
        return discover_selected_probes(cnf, self.config['probe_limit'], self.config['learn_limit'], self.counts)

    def _check_probes(self, cnf, result):
        return check_selected_probes(cnf, result, self.config['probe_limit'], self.config['learn_limit'], self.counts)
