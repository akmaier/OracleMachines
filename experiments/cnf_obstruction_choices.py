"""Optional conditioning ranked by checked Horn-renaming obstruction clauses.

Source-clause supports, not just pair endpoints, matter: satisfying a guard can
remove a whole clause. This is a heuristic, never a SAT verdict or pruning rule.
All candidates, branches and proof obligations retain their existing budgets.
"""
from collections import Counter
from contextlib import contextmanager

from experiments.cnf_conditioning import shortest_balanced_choices
from experiments.cnf_polarity_horn import PolarityHornInventory, discover_polarity, check_polarity


def obstruction_choices(cnf, certificate, limit, counts, *, pair_limit=65536):
    if type(limit) is not int or limit < 0:
        raise ValueError('Invalid obstruction choice limit')
    check_polarity(cnf, certificate, counts, pair_limit=pair_limit)
    support = {abs(lit) for clause in cnf for lit in clause}
    old = shortest_balanced_choices(cnf, len(support), counts)
    if certificate['outcome'] != 'excluded':
        counts['obstruction_rank_fallbacks'] += 1
        return old[:limit]
    # Repeated edges/clauses must not multiply a clause's influence.
    clauses = {edge[1] for name in ('forward', 'backward') for edge in certificate[name]}
    positive, negative = Counter(), Counter()
    for cid in sorted(clauses):
        for lit in cnf[cid]:
            (positive if lit > 0 else negative)[abs(lit)] += 1
            counts['obstruction_rank_literal_visits'] += 1
    counts['obstruction_rank_calls'] += 1
    counts['obstruction_rank_clauses'] += len(clauses)
    counts['obstruction_rank_variables'] += len(positive.keys() | negative.keys())
    # Stable sorting retains the old balanced-shortest ranking for exact ties.
    ranked = sorted(old, key=lambda v: (-positive[v]*negative[v], -(positive[v]+negative[v])))
    choices = ranked[:limit]
    counts['obstruction_changed_choice_lists'] += choices != old[:limit]
    counts['obstruction_new_candidates'] += len(set(choices)-set(old[:limit]))
    return choices


class ObstructionChoicesInventory(PolarityHornInventory):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config['conditioning_obstruction'] = 'balanced-source-path-v1'
        self._obstruction_context = None

    @contextmanager
    def _choice_scope(self, cnf, certificate=None):
        previous = self._obstruction_context
        context = [cnf, certificate]
        self._obstruction_context = context
        try:
            yield context
        finally:
            self._obstruction_context = previous

    def _choices(self, cnf):
        context = self._obstruction_context
        self.counts['obstruction_context_literal_payload'] += sum(map(len, cnf))
        if context is None or context[0] != cnf:
            raise ValueError('Obstruction choices require the exact active source')
        if context[1] is None:
            context[1] = discover_polarity(cnf, self.counts, pair_limit=self.config['polarity_pair_limit'])
            self.counts['obstruction_choice_discoveries'] += 1
        return obstruction_choices(cnf, context[1], self.config['candidate_limit'], self.counts,
                                   pair_limit=self.config['polarity_pair_limit'])

    def _discover_profile(self, cnf, depth, profile, groups):
        with self._choice_scope(cnf) as context:
            node = super()._discover_profile(cnf, depth, profile, groups)
            if node['kind'] == 'or':
                if context[1] is None:raise ValueError('Missing discovered conditioning obstruction')
                node['conditioning_obstruction'] = context[1]
            elif context[1] is not None:
                raise ValueError('Unexpected obstruction ranking outside conditioning')
            return node

    def _check_profile(self, key, node, cnf, profile, groups):
        if node.get('kind') != 'or':
            if 'conditioning_obstruction' in node:
                raise ValueError('Unexpected conditioning obstruction')
            return super()._check_profile(key, node, cnf, profile, groups)
        certificate = node.get('conditioning_obstruction')
        if certificate is None:raise ValueError('Missing checked conditioning obstruction')
        old = {k:v for k,v in node.items() if k != 'conditioning_obstruction'}
        # The inherited checker reconstructs the exact candidate sequence using
        # this source-bound certificate, then checks every branch and selection.
        with self._choice_scope(cnf, certificate):
            return super()._check_profile(key, old, cnf, profile, groups)
