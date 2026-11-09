"""Opt-in ordered occurrence propagation, keeping all persisted proofs intact."""
from experiments.cnf_checked_probe_reuse import CheckedProbeReuseInventory
from experiments.cnf_ordered_propagation import discovery_propagation, propagate_ordered


class OrderedPropagationInventory(CheckedProbeReuseInventory):
    # Scope all ordinary/probe discovery and the ordinary rediscovery in _check.
    # A nested direct probe call restores the surrounding scope on return. No
    # process-global monkeypatch or proof/policy identity change is necessary.
    def _profile(self, cnf):
        with discovery_propagation(propagate_ordered):
            return super()._profile(cnf)

    def _discover_probes(self, cnf):
        with discovery_propagation(propagate_ordered):
            return super()._discover_probes(cnf)

    def _check(self, key, node):
        with discovery_propagation(propagate_ordered):
            return super()._check(key, node)
