"""One bounded retry of a recognized equivalence move cut short by the budget.

This experimental policy keeps the existing scalar/matching search budget. It
does not estimate optimal solve time: the retry can lose on expensive postings
or a coupling conflict. All earlier work is charged, and successful proposals
use the unchanged, independently checked append-joint archive format.
"""
import time

from experiments.cnf_matching_history import MatchingRepairHistory
from experiments.cnf_positive_history import UnsupportedExpansion


class BudgetedRepairHistory(MatchingRepairHistory):
    def __init__(self, archive=':memory:', *, repair_budget=4096,
                 escalation_budget=32768, max_block_variables=8192,
                 max_variable_bits=64):
        limits = dict(escalation_budget=escalation_budget,
                      max_block_variables=max_block_variables,
                      max_variable_bits=max_variable_bits)
        for name, value in limits.items():
            if type(value) is not int or value < 0:
                raise ValueError(f'{name} must be a nonnegative integer')
        super().__init__(archive, repair_budget=repair_budget)
        self.escalation_budget = escalation_budget
        self.max_block_variables = max_block_variables
        self.max_variable_bits = max_variable_bits
        self._exhausted_move = None

    def _joint_deltas(self, index, root, variables, remaining, *, checking):
        changes, remaining = super()._joint_deltas(
            index, root, variables, remaining, checking=checking)
        if not checking and changes is None and self._exhausted_move is None:
            # Retain the existing tuple, not a second model or partial count map.
            self._exhausted_move = variables
        return changes, remaining

    def _append_current(self, parent, clause, allow_repair):
        started = time.perf_counter()
        self._exhausted_move = None
        try:
            return super()._append_current(parent, clause, allow_repair)
        except UnsupportedExpansion:
            if not allow_repair or not self.repair_budget or not self.escalation_budget:
                raise
        block = self._exhausted_move
        base_id = self.checked[parent][0]
        blocks = self.equivalence_blocks.get(base_id, {})
        # Object identity confines retry to an existing recognized base block,
        # excluding a matching path or an arbitrary supplied joint proposal.
        if not block or blocks.get(block[0]) is not block:
            raise UnsupportedExpansion('No exhausted base-equivalence move to retry')
        self.counts['escalation_considered'] += 1
        if len(block) > self.max_block_variables:
            self.counts['escalation_size_rejections'] += 1
            raise UnsupportedExpansion('Equivalence retry exceeds variable limit')
        # Blocks are sorted positive integers: the last ID has the longest path.
        if block[-1].bit_length() > self.max_variable_bits:
            self.counts['escalation_identifier_rejections'] += 1
            raise UnsupportedExpansion('Equivalence retry exceeds identifier limit')
        budget = min(self.escalation_budget, 8 * len(block))
        self.counts['escalation_granted_visits'] += budget
        self.counts['escalation_attempts'] += 1
        index, root = self.clause_states[parent], self.states[parent]
        changes, remaining = self._joint_deltas(index, root, block, budget, checking=False)
        self.counts['escalation_used_visits'] += budget - remaining
        if changes is None or not self._joint_safe(index, changes):
            self.counts['escalation_failures'] += 1
            raise UnsupportedExpansion('Bounded equivalence retry did not certify a repair')
        payload = dict(kind='append-joint', clause=list(clause), variables=list(block))
        version = self._put_version(base_id, parent, payload)
        self.counts['escalation_repairs'] += 1
        return self._result(version, started)
