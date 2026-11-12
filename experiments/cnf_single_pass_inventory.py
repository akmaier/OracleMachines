"""Optional one-pass independent simplification reconstruction."""
from experiments.cnf_indexed_restriction_inventory import IndexedRestrictionInventory
from experiments.cnf_single_pass_check import reconstruct_single_pass
from experiments.cnf_simplification import simplification_reconstruction


class SinglePassCheckInventory(IndexedRestrictionInventory):
    def _reconstruction(self):
        return getattr(self, '_checked_reconstruction', reconstruct_single_pass)

    def inspect(self, source):
        with simplification_reconstruction(self._reconstruction()):
            return super().inspect(source)

    def _load(self, key):
        with simplification_reconstruction(self._reconstruction()):
            return super()._load(key)

    def _discover_probes(self, cnf):
        with simplification_reconstruction(self._reconstruction()):
            return super()._discover_probes(cnf)

    def _check_probes(self, cnf, result):
        with simplification_reconstruction(self._reconstruction()):
            return super()._check_probes(cnf, result)

    def lift(self, key, child_model):
        with simplification_reconstruction(self._reconstruction()):
            return super().lift(key, child_model)
