"""Affected-clause propagation with the original scan order of proof reasons.

The optional engine applies only to simplification discovery. Independent proof
checking and the residual SAT decider are unchanged. Indexes are fresh per call;
there is no reuse across different CNFs or assumptions yet.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from heapq import heapify, heappop, heappush

from experiments.cnf_residual_dag import propagate


_discovery_engine = ContextVar('cnf_discovery_propagation', default=propagate)


@contextmanager
def discovery_propagation(engine):
    """Scope an engine to this execution context; restore it even on errors."""
    token = _discovery_engine.set(engine)
    try:
        yield
    finally:
        _discovery_engine.reset(token)


def propagate_for_discovery(cnf, counts):
    return _discovery_engine.get()(cnf, counts)


def propagate_ordered(cnf, counts):
    """Return exactly the repeated-scan assignment, reason trace and conflict.

Clauses become actionable once: when at most one unassigned occurrence remains.
An event is ordered by (scan round, clause index). A newly actionable clause
behind the current scan position waits until the next round. Satisfied stale
events are discarded. Repeated literals and tautologies retain scan semantics.
"""
    counts['ordered_propagation_calls'] += 1
    pending = []
    for cid, clause in enumerate(cnf):
        counts['ordered_propagation_clause_checks'] += 1
        if len(clause) <= 1:
            # Before the first unit, an empty clause is the original first
            # conflict. Avoid building an index that cannot be used.
            if not clause and not pending:
                return {}, [], cid
            pending.append((0, cid))
    if not pending:
        counts['ordered_propagation_no_units'] += 1
        return {}, [], None

    occurrences = {}
    remaining, sums = [], []
    for cid, clause in enumerate(cnf):
        counts['ordered_propagation_index_literals'] += len(clause)
        remaining.append(len(clause))
        total = 0
        for lit in clause:
            occurrences.setdefault(lit, []).append(cid)
            total += lit
        sums.append(total)
    satisfied = [False] * len(cnf)
    queued = [False] * len(cnf)
    for _, cid in pending:
        queued[cid] = True
    heapify(pending)
    counts['ordered_propagation_peak_occurrences'] = max(
        counts['ordered_propagation_peak_occurrences'], sum(remaining))
    counts['ordered_propagation_peak_events'] = max(
        counts['ordered_propagation_peak_events'], len(pending))
    assignment, trace = {}, []
    while pending:
        scan_round, cid = heappop(pending)
        counts['ordered_propagation_events'] += 1
        if satisfied[cid]:
            continue
        if remaining[cid] == 0:
            return assignment, trace, cid
        lit = sums[cid]
        assignment[abs(lit)] = lit > 0
        trace.append([lit, cid])
        # Mark every true occurrence first, including opposite-polarity
        # tautologies, before considering falsified occurrences.
        positive = occurrences.get(lit, ())
        negative = occurrences.get(-lit, ())
        counts['ordered_propagation_occurrence_updates'] += len(positive) + len(negative)
        for other in positive:
            satisfied[other] = True
        for other in negative:
            if satisfied[other]:
                continue
            remaining[other] -= 1
            sums[other] += lit
            if remaining[other] <= 1 and not queued[other]:
                queued[other] = True
                heappush(pending, (scan_round + (other <= cid), other))
        counts['ordered_propagation_peak_events'] = max(
            counts['ordered_propagation_peak_events'], len(pending))
    return assignment, trace, None
