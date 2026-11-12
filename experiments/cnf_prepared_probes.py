"""Reuse checked probe evidence even when an earlier structural plan is open.

An unclosed exact-source row is already read by retained-plan lookup. Its probe
trace can replace a new probe acquisition, after the existing source-bound
checker validates it under matching probe settings. No old closure, classification
or descendant is inferred from this hint. All ordinary recognition and new
planning still run. The pending hint is scoped to one discovery call, and the
existing bounded check cache supplies subsequent local replay reuse.
"""
from experiments.cnf_retained_plans import RetainedPlanInventory


class PreparedProbeInventory(RetainedPlanInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Same persisted certificate/policy contract, like the existing checked
        # probe cache. Only acquisition of already-checkable evidence changes.
        self._pending_probe = None

    def _discover(self, cnf, depth):
        previous = self._pending_probe
        self._pending_probe = None
        try:
            return super()._discover(cnf, depth)
        finally:
            self._pending_probe = previous

    def _unclosed_hint(self, cnf, depth, hint):
        # The old key binds the same normalized source and depth. Do not trust
        # any old profile outcome or summary as a certificate of its content.
        if any(self.config.get(k) != v for k, v in self.prepared.config.items()):
            self.counts['prepared_probe_incompatible'] += 1
            return
        saved = hint.get('profile', {}).get('probing')
        if type(saved) is dict and saved.get('status') != 'skipped':
            self._pending_probe = (cnf, saved)
            self.counts['prepared_probe_hints'] += 1

    def _discover_probes(self, cnf):
        pending = self._pending_probe
        if pending is None:
            return super()._discover_probes(cnf)
        self.counts['prepared_probe_binding_literal_payload'] += sum(map(len, cnf))
        if cnf != pending[0]:
            return super()._discover_probes(cnf)
        self._pending_probe = None
        # This checks every source reason, fixed point, learned implication,
        # continuation and policy obligation required by the original checker.
        # An exception admits neither a saved result nor an inferred SAT verdict.
        saved = pending[1]
        self._check_probes(cnf, saved)
        self.counts['prepared_probe_reuses'] += 1
        self.counts['prepared_probe_attempts_reused'] += len(saved.get('attempts', []))
        return saved
