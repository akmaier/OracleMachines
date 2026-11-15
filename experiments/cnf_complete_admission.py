"""Optional complete acquisition-state admission for the retained planner.

The frozen legacy ledger gates only _discover. Fused conditioning also prepares
profiles directly, including transient restrictions that are never persisted.
Gate both entrances before recognition; retain the same proof policy and rows.
This is a bound on distinct (policy, depth, CNF) acquisition states per batch,
not on elapsed time, verification work, or repeated visits to an admitted state.
"""
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_coupled_pivots import AdmissionExhausted, BudgetedInventory
from experiments.cnf_residual_dag import restrict


class CompleteAdmissionInventory(BudgetedInventory):
    def _admit(self, key, entrance):
        if not hasattr(self, 'admission_limit'):
            raise ValueError('Set an explicit recognition admission budget')
        if key not in self.admitted:
            if len(self.admitted) >= self.admission_limit:
                self.admission_counts['denied_states'] += 1
                self.admission_counts['denied_' + entrance] += 1
                raise AdmissionExhausted('Recognition admission budget exhausted')
            self.admitted.add(key)
            self.admission_counts['entered_states'] += 1
            self.admission_counts['entered_' + entrance] += 1
        else:
            self.admission_counts['reentered_states'] += 1
        self.admission_counts['visits_' + entrance] += 1

    def _discover(self, cnf, depth):
        self._admit(self._canonical(cnf, depth)[2], 'discover')
        # Skip only the legacy admission override, retaining every inference and
        # prepared-proof layer in its original method resolution order.
        return AnchoredAdditiveInventory._discover(self, cnf, depth)

    def _conditioning_edge(self, cnf, variable, value, depth):
        raw = restrict(cnf, {variable: value}, self.counts)
        intermediate, names, key = self._canonical(raw, depth)
        existing = self._load(key)
        if existing is not None:
            if existing['kind'] != 'simplify':
                return dict(key=key, names=names)
            profile = existing['profile']
        else:
            self._admit(key, 'fused_profile')
            profile, groups = self._prepared(intermediate)
            if not self._uses_simplification(profile, groups):
                self._record_node(key, self._discover_profile(intermediate, depth, profile, groups))
                return dict(key=key, names=names)
        target, _ = self._simplified(intermediate, profile)
        child = self._edge(target, depth)
        self.counts['fused_conditioning_edges'] += 1
        return dict(key=child['key'], names=[names[v-1] for v in child['names']],
                    closure=profile['simplification']['certificate'])

    def _record_node(self, key, node):
        # A fail-closed audit for any future entrance that forgets the gate.
        # This guard alone is not a pre-computation budget enforcement mechanism.
        if key not in getattr(self, 'admitted', ()):
            raise ValueError('Cannot persist an unadmitted acquisition state')
        return super()._record_node(key, node)
