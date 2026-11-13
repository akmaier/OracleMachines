"""Instrument the existing bounded search without resetting its queue or budget.

The sequential control rebuilds checked routes before each subsequent advance,
while keeping the inventory's verifier cache warm. This measures repeated route
preparation, not repeated cold database reconstruction or a competing SAT solver.
"""
from collections import Counter
import hashlib
import time

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_route_composition import compose


def digest(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


class ObservedRoutes:
    def __init__(self, h, routes, roots, rebuild=None):
        self.h = h
        self.current = routes
        self.roots = roots
        self.rebuild = rebuild
        self.records = []
        self.prefixes = []
        self.visits = 0
        self.preparations = []
        self.snapshot_seconds = 0.0

    def __getattr__(self, name):
        return getattr(self.current, name)

    def snapshot(self):
        if len(self.prefixes) == self.visits:
            return
        started = time.perf_counter()
        states = []
        for key in sorted(self.h.admitted):
            row = self.h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?', (key,)).fetchone()
            # An admission can be interrupted before its node is retained.
            states.append([digest(key), None if row is None else digest(row[0])])
        self.prefixes.append(dict(step=self.visits, records_sha256=digest(self.records),
                                  admitted_states=states,
                                  closed=compose(self.h, self.roots, self.current, Counter())[0]))
        self.snapshot_seconds += time.perf_counter() - started

    def advance(self, h, source, counts):
        if h is not self.h:
            raise ValueError('Instrumentation belongs to a different inventory')
        self.snapshot()
        if self.visits and self.rebuild is not None:
            started = time.perf_counter()
            admitted = set(h.admitted)
            allowance = h.admission_limit
            self.current = self.rebuild(h)
            compose(h, self.roots, self.current, Counter())
            if h.admitted != admitted or h.admission_limit != allowance:
                raise ValueError('Route preparation changed the shared admission budget')
            self.preparations.append(time.perf_counter() - started)
        result = self.current.advance(h, source, counts)
        kind, record, _ = result
        self.records.append(dict(source=source, kind=kind, record=record))
        self.visits += 1
        return result

    def finish(self):
        self.snapshot()
        return dict(prefixes=self.prefixes, repeated_preparation_seconds=self.preparations,
                    snapshot_seconds=self.snapshot_seconds)
