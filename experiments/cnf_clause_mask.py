"""Bounded, checker-owned clause masks for related residuals.

Only immutable representation facts are retained. A zero intersection of the
64-bit variable masks proves that a clause is untouched. Collisions only cause
an ordinary literal scan; they never license a proof or skip a fixed-point check.
FIFO admission avoids per-hit LRU maintenance. All work remains independent of
discovery's indexes, assignments and results.
"""
from collections import OrderedDict

from experiments.cnf_prepared_probes import PreparedProbeInventory
from experiments.cnf_single_pass_check import reconstruct_single_pass


class ClauseMaskReconstruction:
    def __init__(self, unit_limit=32768):
        if type(unit_limit) is not int or unit_limit < 0:
            raise ValueError('Clause mask budget must be a nonnegative integer')
        self.limit = unit_limit
        self._entries = OrderedDict()
        self._units = self._peak = 0

    def state(self):
        # One identity slot, clause reference, fixed-size mask, and the retained
        # literal slots. Python container overhead and integer bit sizes remain
        # additional. This is a logical-slot bound, not bytes or process RSS.
        return dict(entries=len(self._entries), units=self._units,
                    peak_units=self._peak, limit_units=self.limit)

    def clear(self):
        self._entries.clear()
        self._units = 0

    def __call__(self, cnf, assigned, counts, *, units):
        if (not self.limit or type(assigned) is not dict or
                any(type(v) is not int or v <= 0 or type(b) is not bool
                    for v, b in assigned.items())):
            counts['clause_mask_fallback_calls'] += 1
            return reconstruct_single_pass(cnf, assigned, counts, units=units)
        counts['clause_mask_calls'] += 1
        counts['clause_mask_assignment_entries'] += len(assigned)
        fixed = 0
        for v in assigned:
            fixed |= 1 << (v & 63)
        current = []
        positions = hits = admissions = prepared = evictions = oversized = fallbacks = 0
        skips = skipped_literals = scanned = copied = rebuilt = dropped = collisions = 0
        try:
            for clause in cnf:
                positions += 1
                identity = id(clause)
                entry = self._entries.get(identity)
                if entry is not None and entry[0] is clause:
                    hits += 1
                    mask = entry[1]
                else:
                    if type(clause) is not tuple:
                        fallbacks += 1
                        current.extend(reconstruct_single_pass((clause,), assigned, counts, units=units))
                        continue
                    mask = 0
                    valid = True
                    for lit in clause:
                        prepared += 1
                        if type(lit) is not int or not lit:
                            valid = False
                            break
                        mask |= 1 << (abs(lit) & 63)
                    if not valid:
                        fallbacks += 1
                        current.extend(reconstruct_single_pass((clause,), assigned, counts, units=units))
                        continue
                    size = 3 + len(clause)
                    if size <= self.limit:
                        while self._units + size > self.limit:
                            _, old = self._entries.popitem(last=False)
                            self._units -= 3 + len(old[0])
                            evictions += 1
                        self._entries[identity] = (clause, mask)
                        self._units += size
                        self._peak = max(self._peak, self._units)
                        admissions += 1
                    else:
                        oversized += 1
                if not (mask & fixed):
                    if units and len(clause) <= 1:
                        raise ValueError('Incomplete unit fixed point')
                    current.append(clause)
                    skips += 1
                    skipped_literals += len(clause)
                    continue
                # Possible overlap, including mask collisions: inspect every
                # required actual literal. This source tuple is already validated.
                residual = None
                satisfied = touched = False
                for i, lit in enumerate(clause):
                    scanned += 1
                    value = assigned.get(abs(lit))
                    if value is None:
                        if residual is not None:
                            residual.append(lit)
                            copied += 1
                    elif value == (lit > 0):
                        touched = satisfied = True
                        break
                    else:
                        touched = True
                        if residual is None:
                            residual = list(clause[:i])
                            copied += i
                if satisfied:
                    dropped += 1
                    continue
                if not touched:
                    collisions += 1
                result = clause if residual is None else tuple(residual)
                rebuilt += residual is not None
                if units and len(result) <= 1:
                    raise ValueError('Incomplete unit fixed point')
                current.append(result)
        finally:
            counts.update(clause_mask_positions=positions, clause_mask_hits=hits,
                          clause_mask_admissions=admissions, clause_mask_preparation_literals=prepared,
                          clause_mask_evictions=evictions, clause_mask_oversize=oversized,
                          clause_mask_fallback_clauses=fallbacks, clause_mask_skipped_clauses=skips,
                          clause_mask_skipped_literals=skipped_literals, clause_mask_scanned_literals=scanned,
                          clause_mask_copied_literals=copied, clause_mask_rebuilt_clauses=rebuilt,
                          clause_mask_dropped_clauses=dropped, clause_mask_false_positives=collisions)
        return current


class ClauseMaskInventory(PreparedProbeInventory):
    def __init__(self, *args, clause_mask_units=32768, **kwargs):
        engine = ClauseMaskReconstruction(clause_mask_units)
        super().__init__(*args, **kwargs)
        self._checked_reconstruction = engine
        self.prepared._checked_reconstruction = engine

    def reconstruction_state(self):
        return self._checked_reconstruction.state()

    def close(self):
        self._checked_reconstruction.clear()
        super().close()
