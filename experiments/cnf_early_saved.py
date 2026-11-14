"""Try the best checked saved pair before extending an ordinary probe prefix.

This scheduling experiment retains pending/known-forced priority and both
cofactor obligations. It does not treat a clear probe as a semantic exclusion,
reset admission accounting, or claim that splitting is cheaper than probing.
"""
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.cnf_trace_split import candidates
from experiments.cnf_split_batch import acquire_pair


class EarlySavedExpansion(WarmExpansion):
    def advance(self, source, routes, counts, *, pending_split=None):
        h = self.h
        if not hasattr(h, 'admitted') or h.admission_limit != self.state_limit:
            raise ValueError('Caller must establish the shared batch allowance')
        if pending_split is not None:
            return super().advance(source, routes, counts, pending_split=pending_split)
        for records in (routes.windows, routes.continuations):
            for record in records.values():
                counts['early_saved_forced_records_scanned'] += 1
                if record['source'] == source and record['edge'] is not None:
                    counts['early_saved_forcing_resumed'] += 1
                    return super().advance(source, routes, counts)
        ranked = candidates(h, source, routes, counts, candidate_limit=self.candidate_limit)
        if not ranked:
            counts['early_saved_pair_misses'] += 1
            return super().advance(source, routes, counts)
        chosen = ranked[0]; record = chosen['record']; before = set(h.admitted)
        result = acquire_pair(h, record, state_limit=self.state_limit, pair_limit=self.pair_limit)
        if not before <= h.admitted or len(h.admitted) > self.state_limit:
            raise ValueError('Shared admission accounting was lost')
        counts['early_saved_pair_hits'] += 1
        return dict(mode='early_saved_split', source=source, operation=None, record=record,
            ranked_pairs=[row['rank'] for row in ranked], selected_rank=chosen['rank'],
            closed_children=chosen['closed'], acquisition=result, added=sorted(h.admitted-before),
            pending=any(branch['pending'] for branch in result['branches']))
