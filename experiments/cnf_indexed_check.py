"""Checker-owned occurrence indexes for immutable source reconstruction.

The index is constructed from the actual source, never from discovery state or
an untrusted saved index. It remembers no proof result. Unit reasons still pass
the original checker. Identity hits are allowed only for retained exact built-in
tuple/tuple/nonzero-int sources. Mutable and unusual inputs use the prior scan.
"""
from collections import OrderedDict
from dataclasses import dataclass

from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_single_pass_check import reconstruct_single_pass


@dataclass(frozen=True)
class _Source:
    cnf: tuple
    postings: dict
    short: frozenset
    units: int


class CheckedReconstruction:
    def __init__(self, unit_limit=32768):
        if type(unit_limit) is not int or unit_limit < 0:
            raise ValueError('Checked reconstruction limit must be a nonnegative integer')
        self.limit = unit_limit
        self._entries = OrderedDict()
        self._units = self._peak = 0

    def state(self):
        # Logical retained slots: source + clause refs + source literals +
        # posting positions + two slots per variable + short-clause indices.
        # Python containers and integer bit lengths are additional, not RSS.
        return dict(entries=len(self._entries), units=self._units,
                    peak_units=self._peak, limit_units=self.limit)

    def clear(self):
        self._entries.clear()
        self._units = 0

    def _prepare(self, cnf, counts):
        if type(cnf) is not tuple:
            return None
        postings, short = {}, set()
        weight = 1 + len(cnf)
        if weight > self.limit:
            counts['indexed_check_oversize'] += 1
            return None
        for cid, clause in enumerate(cnf):
            counts['indexed_check_preparation_clauses'] += 1
            if type(clause) is not tuple:
                return None
            if len(clause) <= 1:
                short.add(cid)
                weight += 1
            for lit in clause:
                counts['indexed_check_preparation_literals'] += 1
                if type(lit) is not int or not lit:
                    return None
                variable = abs(lit)
                if variable not in postings:
                    postings[variable] = []
                    weight += 2
                postings[variable].append(cid)
                weight += 2
                if weight > self.limit:
                    counts['indexed_check_oversize'] += 1
                    return None
            if weight > self.limit:
                counts['indexed_check_oversize'] += 1
                return None
        entry = _Source(cnf, {v: tuple(ids) for v, ids in postings.items()},
                        frozenset(short), weight)
        while self._units + weight > self.limit:
            _, old = self._entries.popitem(last=False)
            self._units -= old.units
            counts['indexed_check_evictions'] += 1
        self._entries[id(cnf)] = entry
        self._units += weight
        self._peak = max(self._peak, self._units)
        counts['indexed_check_admissions'] += 1
        return entry

    def __call__(self, cnf, assigned, counts, *, units):
        counts['indexed_check_calls'] += 1
        if (not self.limit or type(assigned) is not dict or
                any(type(v) is not int or v <= 0 or type(b) is not bool
                    for v, b in assigned.items())):
            counts['indexed_check_fallbacks'] += 1
            return reconstruct_single_pass(cnf, assigned, counts, units=units)
        counts['indexed_check_assignment_entries'] += len(assigned)
        entry = self._entries.get(id(cnf))
        if entry is not None and entry.cnf is cnf:
            self._entries.move_to_end(id(cnf))
            counts['indexed_check_hits'] += 1
        else:
            entry = self._prepare(cnf, counts)
            if entry is None:
                counts['indexed_check_fallbacks'] += 1
                return reconstruct_single_pass(cnf, assigned, counts, units=units)

        affected = set()
        for variable in assigned:
            ids = entry.postings.get(variable, ())
            counts['indexed_check_posting_visits'] += len(ids)
            affected.update(ids)
        # Unaffected clauses retain their original width. A previously present
        # short clause cannot disappear without an assignment touching it.
        counts['indexed_check_short_positions'] += len(entry.short)
        if units and not entry.short.issubset(affected):
            raise ValueError('Incomplete unit fixed point')
        current = []
        scanned = shared = rebuilt = dropped = 0
        try:
            for cid, clause in enumerate(cnf):
                if cid not in affected:
                    current.append(clause)
                    shared += 1
                    continue
                residual = []
                for lit in clause:
                    scanned += 1
                    value = assigned.get(abs(lit))
                    if value is None:
                        residual.append(lit)
                    elif value == (lit > 0):
                        dropped += 1
                        break
                else:
                    if units and len(residual) <= 1:
                        raise ValueError('Incomplete unit fixed point')
                    current.append(tuple(residual))
                    rebuilt += 1
        finally:
            counts['indexed_check_assembly_clauses'] += len(cnf)
            counts['indexed_check_affected_clauses'] += len(affected)
            counts['indexed_check_scanned_literals'] += scanned
            counts['indexed_check_shared_clauses'] += shared
            counts['indexed_check_rebuilt_clauses'] += rebuilt
            counts['indexed_check_dropped_clauses'] += dropped
        return current


class IndexedCheckInventory(PreparedProbeInventory):
    def __init__(self, *args, checked_reconstruction_units=32768, **kwargs):
        engine = CheckedReconstruction(checked_reconstruction_units)
        super().__init__(*args, **kwargs)
        self._checked_reconstruction = engine
        # Both checker views use the same source-only index budget. No policy,
        # proof verdict, assignment or discovery index is shared here.
        self.prepared._checked_reconstruction = engine

    def reconstruction_state(self):
        return self._checked_reconstruction.state()

    def close(self):
        self._checked_reconstruction.clear()
        super().close()
