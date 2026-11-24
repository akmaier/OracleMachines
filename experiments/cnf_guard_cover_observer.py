"""Read-only, synchronous census of the existing gate's satisfiable graphs.

Requires the solver's existing exclusive session. The scoped hook observes only
calls using the gate's counter, restores the function even on failure, and never
publishes cover proofs or changes native decisions. Events retain exact local
bindings so an independent pass can check discovery and actual template support.
"""
from collections import Counter
from time import perf_counter
from unittest.mock import patch
from experiments import cnf_residual_dag as native
from experiments.cnf_guard_context_solver import ContextGuardClosureSolver
from experiments.cnf_guard_clause_cover import discover


class CoverObserver(ContextGuardClosureSolver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cover_events = []
        self.cover_seconds = 0.0

    def _guard_closure(self, cnf):
        parent = self.guard_parents[-1] if self.guard_parents else None
        if parent is None or parent['cnf'] is not cnf:
            return super()._guard_closure(cnf)
        original = native.two_cnf; events = []
        def observe(graph, counts):
            result = original(graph, counts)
            if counts is self.closure_counts and result[1] is None and result[0] is not None:
                started = perf_counter(); c = Counter()
                cover = discover(cnf, graph, result[0], c)
                events.append(dict(root=native.token(cnf, Counter()),
                    mapping=sorted([list(p) for p in parent['mapping'].items()]),
                    fixed=sorted([list(p) for p in parent['fixed'].items()]),
                    graph=[list(cl) for cl in graph], model=sorted([v, b] for v, b in result[0].items()),
                    cover=cover, counts=dict(c)))
                self.cover_seconds += perf_counter()-started
            return result
        with patch.object(native, 'two_cnf', observe):
            proof = super()._guard_closure(cnf)
        for event in events:
            event['site_closed'] = proof is not None
        self.cover_events.extend(events)
        return proof
