"""Preserve immutable restricted sources so independent checks can reuse them.

Restriction results are memoized only after the existing discovery index has
validated the actual immutable source. The checker still builds its own source
index and validates every reason/fixed point. No discovery postings are trusted
by the checker. Neither memo table is persisted.
"""
from collections import Counter, OrderedDict

from experiments.cnf_indexed_check import IndexedCheckInventory
from experiments.cnf_indexed_restriction import IndexedRestriction


class SharedRestriction(IndexedRestriction):
    def __init__(self, unit_limit=32768, result_units=32768):
        if type(result_units) is not int or result_units < 0:
            raise ValueError('Restriction result limit must be a nonnegative integer')
        super().__init__(unit_limit)
        self.result_limit = result_units
        self._results = OrderedDict()
        self._result_units = self._result_peak = 0

    def result_state(self):
        # Source/result/assignment slots, not Python bytes or process RSS.
        return dict(entries=len(self._results), units=self._result_units,
                    peak_units=self._result_peak, limit_units=self.result_limit)

    def clear(self):
        self._results.clear()
        self._result_units = 0
        super().clear()

    def __call__(self, cnf, assignment, counts=None):
        if counts is None:
            counts = Counter()
        if (not self.result_limit or type(assignment) is not dict or not assignment or
                any(type(v) is not int or v <= 0 or type(b) is not bool
                    for v, b in assignment.items())):
            return super().__call__(cnf, assignment, counts)
        fixed = tuple(sorted(assignment.items()))
        counts['shared_restriction_assignment_entries'] += len(fixed)
        key = (id(cnf), fixed)
        counts['shared_restriction_lookups'] += 1
        saved = self._results.get(key)
        if saved is not None and saved[0] is cnf:
            self._results.move_to_end(key)
            counts['shared_restriction_hits'] += 1
            return saved[1]
        result = super().__call__(cnf, assignment, counts)
        entry = self._entries.get(id(cnf))
        if entry is None or entry.source is not cnf:
            # The original engine did not admit this exact immutable source.
            counts['shared_restriction_unadmitted'] += 1
            return result
        # Full source/result slots are conservatively charged for each memo
        # entry, even where object references are physically shared.
        size = 3 + len(cnf) + sum(map(len, cnf)) + len(result) + sum(map(len, result)) + 2*len(fixed)
        counts['shared_restriction_measure_clauses'] += len(cnf) + len(result)
        if size > self.result_limit:
            counts['shared_restriction_oversize'] += 1
            return result
        while self._result_units + size > self.result_limit:
            _, old = self._results.popitem(last=False)
            self._result_units -= old[2]
            counts['shared_restriction_evictions'] += 1
        self._results[key] = (cnf, result, size)
        self._result_units += size
        self._result_peak = max(self._result_peak, self._result_units)
        counts['shared_restriction_admissions'] += 1
        return result


class SharedReconstructionInventory(IndexedCheckInventory):
    def __init__(self, *args, restriction_result_units=32768, **kwargs):
        if type(restriction_result_units) is not int or restriction_result_units < 0:
            raise ValueError('Restriction result limit must be a nonnegative integer')
        super().__init__(*args, **kwargs)
        self._restriction = SharedRestriction(self._restriction.limit, restriction_result_units)
        self.prepared._restriction = self._restriction

    def sharing_state(self):
        return dict(restriction_index=self._restriction.state(),
                    restriction_results=self._restriction.result_state(),
                    checker_index=self.reconstruction_state())
