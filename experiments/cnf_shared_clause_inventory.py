"""Optional independent clause-support sharing during simplification checks."""
from experiments.cnf_indexed_restriction_inventory import IndexedRestrictionInventory
from experiments.cnf_shared_clause_check import SharedClauseReconstruction
from experiments.cnf_simplification import simplification_reconstruction


class SharedClauseCheckInventory(IndexedRestrictionInventory):
    def __init__(self, *args, clause_check_units=32768, **kwargs):
        self._clause_check = SharedClauseReconstruction(clause_check_units)
        super().__init__(*args, **kwargs)

    def clause_check_state(self):
        return self._clause_check.state()

    def inspect(self, source):
        with simplification_reconstruction(self._clause_check):
            return super().inspect(source)

    def _load(self, key):
        with simplification_reconstruction(self._clause_check):
            return super()._load(key)

    def _discover_probes(self, cnf):
        with simplification_reconstruction(self._clause_check):
            return super()._discover_probes(cnf)

    def _check_probes(self, cnf, result):
        with simplification_reconstruction(self._clause_check):
            return super()._check_probes(cnf, result)

    def lift(self, key, child_model):
        with simplification_reconstruction(self._clause_check):
            return super().lift(key, child_model)

    def close(self):
        self._clause_check.clear()
        super().close()
