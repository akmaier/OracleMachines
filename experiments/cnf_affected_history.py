"""Checked one-variable model repair over versioned affected-clause counts.

Experimental Python/SQLite implementation, outside Lean's kernel boundary.
Counts use distinct signed literals, including both signs of a tautology.
All derived indexes are reconstructed from checked source/history records.
"""
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.cnf_repair_history import RepairHistory


class AffectedRepairHistory(RepairHistory):
    def __init__(self, archive=':memory:', *, repair_budget=4096):
        if type(repair_budget) is not int or repair_budget < 0:
            raise ValueError('repair_budget must be a nonnegative integer')
        super().__init__(archive)
        self.repair_budget = repair_budget
        self.clause_states, self.base_clause_states = {}, {}

    def _index_clause(self, index, root, clause):
        postings, counts, next_id = index
        signs = {}
        for lit in clause:
            self.counts['index_literal_visits'] += 1
            var = abs(lit)
            signs[var] = signs.get(var, 0) | (1 if lit > 0 else 2)
        true_count = 0
        for var, mask in signs.items():
            value = bool(self._get(root, var) & 4)
            true_count += bool(mask & (1 if value else 2))
            old = self._get(postings, var)
            postings = self._set(postings, var, (next_id, mask, old))
            self.counts['posting_nodes_allocated'] += 1
        if true_count == 0:
            raise ValueError('Indexed clause is not satisfied')
        counts = self._set(counts, next_id, true_count)
        self.counts['indexed_clauses'] += 1
        return postings, counts, next_id + 1

    def _initial_index(self, base_id, base, root):
        if base_id not in self.base_clause_states:
            index = (None, None, 1)
            for clause in base['source']:
                index = self._index_clause(index, root, clause)
            self.base_clause_states[base_id] = index
        return self.base_clause_states[base_id]

    def _can_flip(self, index, lit, remaining):
        """Budget candidate occurrence visits; failure never implies UNSAT."""
        postings, counts, _ = index
        entry = self._get(postings, abs(lit))
        opposite = 2 if lit > 0 else 1
        while entry:
            if remaining == 0:
                self.counts['repair_budget_exhaustions'] += 1
                return False, remaining
            remaining -= 1
            self.counts['candidate_clause_visits'] += 1
            cid, mask, entry = entry
            # Both signs leave the count unchanged; the opposite sign alone
            # can destroy satisfaction only if it is the last true literal.
            if mask == opposite and self._get(counts, cid) <= 1:
                return False, remaining
        return True, remaining

    def _flip_counts(self, index, lit):
        postings, counts, next_id = index
        entry = self._get(postings, abs(lit))
        sign, opposite = (1, 2) if lit > 0 else (2, 1)
        while entry:
            self.counts['checked_affected_clauses'] += 1
            cid, mask, entry = entry
            delta = int(bool(mask & sign)) - int(bool(mask & opposite))
            if delta:
                new_count = self._get(counts, cid) + delta
                if new_count <= 0:
                    raise ValueError('Repair invalidates a parent clause')
                counts = self._set(counts, cid, new_count)
                self.counts['changed_clause_counts'] += 1
        return postings, counts, next_id

    def _check_version(self, version, base_id, base, parent, payload):
        affected = type(payload) is dict and payload.get('kind') == 'append-affected'
        if not affected:
            # Retain all legacy validation, including the older purity rule.
            super()._check_version(version, base_id, base, parent, payload)
            if not base['answer']:
                self.clause_states[version] = None
            elif parent is None:
                self.clause_states[version] = self._initial_index(base_id, base, self.states[version])
            else:
                index = self.clause_states[parent]
                if payload.get('kind') == 'append-pure' and payload['repair'] is not None:
                    index = self._flip_counts(index, payload['repair'])
                self.clause_states[version] = self._index_clause(index, self.states[version], payload['clause'])
            return
        if parent is None or not base['answer'] or set(payload) != {'kind', 'clause', 'repair'}:
            raise ValueError('Invalid affected-repair record or non-SAT base')
        self._clause(payload['clause'])
        root, index = self.states[parent], self.clause_states[parent]
        lit = payload['repair']
        if lit is not None:
            if type(lit) is not int or lit == 0 or lit not in payload['clause']:
                raise ValueError('Repair literal must occur in the new clause')
            flags = self._get(root, abs(lit))
            if bool(flags & 4) == (lit > 0):
                raise ValueError('Repair does not change the assignment')
            # Cold checking is independent of the discovery budget. No derived
            # counts or claimed list of affected clauses is read from storage.
            index = self._flip_counts(index, lit)
            root = self._set(root, abs(lit), flags | 4 if lit > 0 else flags & ~4)
            self.counts['verified_affected_repairs'] += 1
        if not self._holds(root, payload['clause']):
            raise ValueError('Version model does not satisfy the added clause')
        index = self._index_clause(index, root, payload['clause'])
        self.states[version] = self._occurrences(root, payload['clause'])
        self.clause_states[version] = index

    def _append_current(self, parent, clause, allow_repair):
        started = self._begin()
        base_id, _, _ = self._load(parent)
        base = self.bases[base_id]
        self._clause(clause)
        if not base['answer']:
            payload = dict(kind='append-unsat', clause=list(clause))
        else:
            root, repair, remaining = self.states[parent], None, self.repair_budget
            if not self._holds(root, clause):
                if allow_repair:
                    for lit in dict.fromkeys(clause):
                        self.counts['repair_candidates'] += 1
                        safe, remaining = self._can_flip(self.clause_states[parent], lit, remaining)
                        if safe:
                            repair = lit
                            break
                if repair is None:
                    raise UnsupportedExpansion('No surviving model or checked single-variable repair within budget')
            payload = dict(kind='append-affected', clause=list(clause), repair=repair)
        version = self._put_version(base_id, parent, payload)
        return self._result(version, started)

    def storage(self):
        result = super().storage()
        import time
        started = time.perf_counter()
        map_seen, posting_seen = set(), set()
        for is_posting in (False, True):
            pending = [index[0 if is_posting else 1]
                       for index in self.clause_states.values() if index is not None]
            while pending:
                node = pending.pop()
                if node is None or id(node) in map_seen:
                    continue
                map_seen.add(id(node))
                pending.extend(node[1:])
                if is_posting:
                    entry = node[0]
                    while entry and id(entry) not in posting_seen:
                        posting_seen.add(id(entry))
                        entry = entry[2]
        result.update(resident_clause_index_nodes=len(map_seen),
                      resident_posting_nodes=len(posting_seen),
                      clause_index_scan_seconds=time.perf_counter() - started)
        return result
