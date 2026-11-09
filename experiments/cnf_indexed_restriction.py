"""Bounded occurrence indexes for exact, immutable source CNFs.

Identity is used only after checking exact tuple/tuple/int immutability. Each
entry holds its source alive, checks `is` on lookup and counts all retained
source/occurrence slots. Mutable or unusual inputs take the original scan path.
No proof result or assignment is cached, and the checker reconstructs independently.
"""
from collections import Counter, OrderedDict
from dataclasses import dataclass

from experiments.cnf_residual_dag import restrict_scan


@dataclass(frozen=True)
class _Prepared:
    source: tuple
    occurrences: dict
    units: int


class IndexedRestriction:
    def __init__(self, unit_limit=32768):
        if type(unit_limit) is not int or unit_limit < 0:
            raise ValueError('Restriction index limit must be a nonnegative integer')
        self.limit = unit_limit
        self._entries = OrderedDict()
        self._units = self._peak = 0

    def state(self):
        # One unit per source, clause or literal occurrence; object overhead and
        # integer bit lengths are additional. This is not a byte or RSS cap.
        return dict(entries=len(self._entries), units=self._units,
                    peak_units=self._peak, limit_units=self.limit)

    def clear(self):
        self._entries.clear()
        self._units = 0

    def __call__(self, cnf, assignment, counts=None):
        if counts is None:
            counts = Counter()
        counts['indexed_restriction_calls'] += 1
        if (not self.limit or type(assignment) is not dict or
                any(type(v) is not int or v <= 0 or type(b) is not bool
                    for v, b in assignment.items())):
            counts['indexed_restriction_fallbacks'] += 1
            return restrict_scan(cnf, assignment, counts)
        counts['indexed_restriction_assignment_entries'] += len(assignment)
        identity = id(cnf)
        entry = self._entries.get(identity)
        if entry is not None and entry.source is cnf:
            counts['indexed_restriction_hits'] += 1
            self._entries.move_to_end(identity)
        else:
            # A tuple subclass, mutable clause, int subclass, bool or zero must
            # never inherit the validated immutable-source identity shortcut.
            if type(cnf) is not tuple:
                counts['indexed_restriction_fallbacks'] += 1
                return restrict_scan(cnf, assignment, counts)
            literals = 0
            for clause in cnf:
                counts['indexed_restriction_validation_clauses'] += 1
                if type(clause) is not tuple:
                    counts['indexed_restriction_fallbacks'] += 1
                    return restrict_scan(cnf, assignment, counts)
                for lit in clause:
                    counts['indexed_restriction_validation_literals'] += 1
                    if type(lit) is not int or not lit:
                        counts['indexed_restriction_fallbacks'] += 1
                        return restrict_scan(cnf, assignment, counts)
                literals += len(clause)
            if not assignment:
                counts['indexed_restriction_empty_assignments'] += 1
                return cnf
            weight = 1 + len(cnf) + literals
            if weight > self.limit:
                counts['indexed_restriction_oversize'] += 1
                return restrict_scan(cnf, assignment, counts)
            postings = {}
            for cid, clause in enumerate(cnf):
                for lit in clause:
                    postings.setdefault(lit, []).append(cid)
            counts['indexed_restriction_preparation_literals'] += literals
            entry = _Prepared(cnf, {lit: tuple(ids) for lit, ids in postings.items()}, weight)
            while self._units + weight > self.limit:
                _, old = self._entries.popitem(last=False)
                self._units -= old.units
                counts['indexed_restriction_evictions'] += 1
            self._entries[identity] = entry
            self._units += weight
            self._peak = max(self._peak, self._units)
            counts['indexed_restriction_admissions'] += 1

        satisfied, touched = set(), set()
        for variable, value in assignment.items():
            lit = variable if value else -variable
            positive = entry.occurrences.get(lit, ())
            negative = entry.occurrences.get(-lit, ())
            counts['indexed_restriction_posting_visits'] += len(positive) + len(negative)
            satisfied.update(positive)
            touched.update(negative)
        patches = dict.fromkeys(satisfied)
        for cid in touched - satisfied:
            clause = cnf[cid]
            counts['indexed_restriction_rebuilt_literals'] += len(clause)
            patches[cid] = tuple(lit for lit in clause if abs(lit) not in assignment)
        counts['indexed_restriction_affected_clauses'] += len(patches)
        counts['indexed_restriction_assembly_clauses'] += len(cnf)
        # Original clause order, empty clauses and repeated occurrences survive.
        # Unchanged immutable tuples are shared; no mutable cache object escapes.
        return tuple(value for cid, clause in enumerate(cnf)
                     if (value := patches.get(cid, clause)) is not None)
