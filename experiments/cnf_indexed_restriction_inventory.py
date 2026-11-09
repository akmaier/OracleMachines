"""Exact prepared-source restriction for the ordered-propagation inventory."""
from experiments.cnf_indexed_restriction import IndexedRestriction
from experiments.cnf_ordered_propagation_inventory import OrderedPropagationInventory
from experiments.cnf_residual_dag import restriction_engine


class IndexedRestrictionInventory(OrderedPropagationInventory):
    def __init__(self, *args, restriction_units=32768, **kwargs):
        self._restriction = IndexedRestriction(restriction_units)
        super().__init__(*args, **kwargs)

    def restriction_state(self):
        return self._restriction.state()

    def inspect(self, source):
        with restriction_engine(self._restriction):
            return super().inspect(source)

    def _load(self, key):
        with restriction_engine(self._restriction):
            return super()._load(key)

    def _discover_probes(self, cnf):
        with restriction_engine(self._restriction):
            return super()._discover_probes(cnf)

    def _check_probes(self, cnf, result):
        with restriction_engine(self._restriction):
            return super()._check_probes(cnf, result)

    def lift(self, key, child_model):
        with restriction_engine(self._restriction):
            return super().lift(key, child_model)

    def close(self):
        self._restriction.clear()
        super().close()
