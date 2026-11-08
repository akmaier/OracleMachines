"""Budgeted conditioning guided by balanced shortest-clause occurrences.

This is a MOMS-inspired branching policy, not a new recognition certificate.
Both Boolean branches and every retained alternative still use the exact
source-binding checker. No lookahead decisions or timing enter the ranking.
"""
from collections import Counter

from experiments.cnf_simplification import SimplifyingPatternInventory


def shortest_balanced_choices(cnf, limit, counts):
    shortest = min(map(len, cnf), default=0)
    frequencies, positive, negative = Counter(), Counter(), Counter()
    for clause in cnf:
        for lit in clause:
            counts['conditioning_rank_literal_visits'] += 1
            v = abs(lit)
            frequencies[v] += 1
            if len(clause) == shortest:
                (positive if lit > 0 else negative)[v] += 1
    counts['conditioning_rank_variables'] += len(frequencies)
    # Favor impact in both branches, then shortest-clause mass, then total
    # occurrence count. IDs break ties deterministically, not isomorphically.
    return sorted(frequencies, key=lambda v: (
        -positive[v]*negative[v], -(positive[v]+negative[v]), -frequencies[v], v))[:limit]


class ShortestClauseInventory(SimplifyingPatternInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['conditioning_policy'] = 'shortest-balanced-v1'

    def _choices(self, cnf):
        return shortest_balanced_choices(cnf, self.config['candidate_limit'], self.counts)
