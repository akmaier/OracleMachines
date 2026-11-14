"""One bounded discovery step in a retained, caller-budgeted inventory.

Clear probes are saved and resumed. Only exhaustion of the bounded ordinary pool
permits a new saved-trace split. Pending splits resume their exact two targets.
The caller refreshes the COMPLETE route catalog and coverage graph after each
step. This module neither resets admission accounting nor infers global closure.
"""
from experiments.cnf_source_local import SourceProbeRoutes, advance_one
from experiments.cnf_trace_split import candidates
from experiments.cnf_split_batch import acquire_pair
from experiments.cnf_variable_elimination import _limit


class WarmExpansion:
    def __init__(self, h, *, state_limit=32, pair_limit=32, candidate_limit=64):
        for limit in (state_limit, pair_limit, candidate_limit): _limit(limit)
        self.h = h
        self.state_limit, self.pair_limit, self.candidate_limit = state_limit, pair_limit, candidate_limit
        self.local_routes = {}

    def advance(self, source, routes, counts, *, pending_split=None):
        h = self.h
        if not hasattr(h, 'admitted') or h.admission_limit != self.state_limit:
            raise ValueError('Caller must establish the shared batch allowance')
        before = set(h.admitted)
        if pending_split is not None:
            if pending_split['source'] != source:
                raise ValueError('Pending split source mismatch')
            record = pending_split; operation = None; ranking = []
            mode = 'resume_split'
        else:
            if source not in self.local_routes:
                self.local_routes[source] = SourceProbeRoutes(h, source)
            operation = advance_one(h, self.local_routes[source], source, counts)
            if operation['record'] is not None:
                return dict(mode='ordinary', source=source, operation=operation,
                    added=sorted(h.admitted-before), pending=operation['admission_stopped'])
            ranked = candidates(h, source, routes, counts, candidate_limit=self.candidate_limit)
            if not ranked:
                return dict(mode='no_saved_pair', source=source, operation=operation,
                    added=[], pending=False)
            record = ranked[0]['record']; ranking = [r['rank'] for r in ranked]
            mode = 'split_after_ordinary_exhaustion'
        result = acquire_pair(h, record, state_limit=self.state_limit, pair_limit=self.pair_limit)
        if not before <= h.admitted or len(h.admitted) > self.state_limit:
            raise ValueError('Shared admission accounting was lost')
        return dict(mode=mode, source=source, operation=operation, record=record,
            ranked_pairs=ranking, acquisition=result, added=sorted(h.admitted-before),
            pending=any(b['pending'] for b in result['branches']))
