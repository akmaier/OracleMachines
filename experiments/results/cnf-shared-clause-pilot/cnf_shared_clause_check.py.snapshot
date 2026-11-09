"""Checker-owned immutable clause supports, independent of discovery indexes.

Only representation facts are cached: an exact tuple of nonzero exact ints and
its variable support. Every unit reason, fixed point, pure round and conflict is
still checked. Untouched clauses can be shared; affected clauses use the original
direct reconstruction. No checked verdict, assignment or source is cached.
"""
from collections import OrderedDict
from dataclasses import dataclass

from experiments.cnf_simplification import reconstruct_simplification_scan


@dataclass(frozen=True)
class _Clause:
    clause: tuple
    support: frozenset
    units: int


class SharedClauseReconstruction:
    def __init__(self, unit_limit=32768):
        if type(unit_limit) is not int or unit_limit < 0:
            raise ValueError('Clause-support limit must be a nonnegative integer')
        self.limit = unit_limit
        self._entries = OrderedDict()
        self._units = self._peak = 0

    def state(self):
        # Charges clause + literal occurrences + distinct variables, not bytes.
        return dict(entries=len(self._entries), units=self._units,
                    peak_units=self._peak, limit_units=self.limit)

    def clear(self):
        self._entries.clear()
        self._units = 0

    def __call__(self, cnf, assigned, counts, *, units):
        counts['clause_check_calls'] += 1
        if (not self.limit or type(assigned) is not dict or
                any(type(v) is not int or v <= 0 or type(b) is not bool
                    for v, b in assigned.items())):
            counts['clause_check_fallback_calls'] += 1
            return reconstruct_simplification_scan(cnf, assigned, counts, units=units)
        counts['clause_check_assignment_entries'] += len(assigned)
        fixed = frozenset(assigned)
        current = []
        positions = hits = tests = shared = shared_literals = affected = 0
        try:
            for clause in cnf:
                positions += 1
                identity = id(clause)
                entry = self._entries.get(identity)
                if entry is not None and entry.clause is clause:
                    hits += 1
                    self._entries.move_to_end(identity)
                else:
                    counts['clause_check_misses'] += 1
                    if type(clause) is not tuple:
                        counts['clause_check_mutable_or_unusual'] += 1
                        current.extend(reconstruct_simplification_scan((clause,), assigned, counts, units=units))
                        continue
                    valid = True
                    for lit in clause:
                        counts['clause_check_validation_literals'] += 1
                        if type(lit) is not int or not lit:
                            valid = False
                            break
                    if not valid:
                        counts['clause_check_mutable_or_unusual'] += 1
                        current.extend(reconstruct_simplification_scan((clause,), assigned, counts, units=units))
                        continue
                    support = frozenset(map(abs, clause))
                    counts['clause_check_support_literals'] += len(clause)
                    weight = 1 + len(clause) + len(support)
                    if weight > self.limit:
                        counts['clause_check_oversize'] += 1
                        current.extend(reconstruct_simplification_scan((clause,), assigned, counts, units=units))
                        continue
                    entry = _Clause(clause, support, weight)
                    while self._units + weight > self.limit:
                        _, old = self._entries.popitem(last=False)
                        self._units -= old.units
                        counts['clause_check_evictions'] += 1
                    self._entries[identity] = entry
                    self._units += weight
                    self._peak = max(self._peak, self._units)
                    counts['clause_check_admissions'] += 1
                tests += 1
                if entry.support.isdisjoint(fixed):
                    # The checked assignment cannot satisfy or erase any occurrence.
                    # Recheck the fixed-point obligation; support is not a verdict.
                    if units and len(clause) <= 1:
                        raise ValueError('Incomplete unit fixed point')
                    current.append(clause)
                    shared += 1
                    shared_literals += len(clause)
                else:
                    affected += 1
                    current.extend(reconstruct_simplification_scan((clause,), assigned, counts, units=units))
        finally:
            counts.update(clause_check_positions=positions, clause_check_hits=hits,
                          clause_check_support_tests=tests, clause_check_shared_clauses=shared,
                          clause_check_shared_literals=shared_literals,
                          clause_check_affected_clauses=affected)
        return current
