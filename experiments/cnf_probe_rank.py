"""Reorder existing conditioning candidates using original checked unit traces.

No candidate, probe or structural recognizer is added. Unknown probe effects
remain unknown. Promote at most one existing candidate with units in both
branches, retaining the relative order of all other candidates. This is a
look-ahead heuristic, not a new recognized class or a SAT verdict.
"""
from contextlib import contextmanager

from experiments.cnf_conditioning import shortest_balanced_choices
from experiments.cnf_polarity_horn import PolarityHornInventory


def choices_after_checked_probes(cnf, probing, limit, counts):
    """Internal helper: original attempts must already be source-bound/checked.

    Discovery supplies freshly generated proofs; the inherited node checker
    verifies all original proofs before calling this helper during replay.
    Original units retain parent names. Learned continuations use a different
    source and are deliberately excluded. This helper is not a proof checker.
    """
    old = shortest_balanced_choices(cnf, limit, counts)
    counts['probe_rank_calls'] += 1
    if len(old) < 2 or probing['status'] not in ('clear', 'learning_clear'):
        counts['probe_rank_fallbacks'] += 1
        return old
    attempts = probing['attempts']
    sizes = {(a['variable'], a['value']): len(a['certificate']['units']) for a in attempts}
    counts['probe_rank_attempt_visits'] += len(attempts)
    eligible = []
    for position, variable in enumerate(old):
        low, high = sizes.get((variable, False)), sizes.get((variable, True))
        if low is None or high is None:
            counts['probe_rank_unknown_candidates'] += 1
            continue
        counts['probe_rank_measured_candidates'] += 1
        # A measured zero is distinct from missing evidence. Only positive
        # two-sided effects earn priority; ties retain the baseline ranking.
        if low > 0 and high > 0:
            eligible.append((min(low, high), low + high, -position, variable))
    if not eligible:
        counts['probe_rank_no_two_sided_effect'] += 1
        return old
    winner = max(eligible)[3]
    result = [winner] + [v for v in old if v != winner]
    counts['probe_rank_changed_lists'] += result != old
    counts['probe_rank_eligible_candidates'] += len(eligible)
    return result


class ProbeRankInventory(PolarityHornInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['conditioning_probe_rank'] = 'existing-two-sided-min-sum-v1'
        self._probe_rank_context = None

    @contextmanager
    def _rank_scope(self, cnf, profile):
        previous = self._probe_rank_context
        self._probe_rank_context = (cnf, profile['probing'])
        try:
            yield
        finally:
            self._probe_rank_context = previous

    def _choices(self, cnf):
        context = self._probe_rank_context
        if context is None or context[0] != cnf:
            raise ValueError('Probe ranking requires the exact active source')
        return choices_after_checked_probes(cnf, context[1], self.config['candidate_limit'], self.counts)

    def _discover_profile(self, cnf, depth, profile, groups):
        with self._rank_scope(cnf, profile):
            return super()._discover_profile(cnf, depth, profile, groups)

    def _check_profile(self, key, node, cnf, profile, groups):
        # The inherited _check has already verified this exact source's saved
        # profile, including every original trace. No second propagation pass
        # or duplicate evidence is needed to reconstruct the candidate order.
        with self._rank_scope(cnf, profile):
            return super()._check_profile(key, node, cnf, profile, groups)
