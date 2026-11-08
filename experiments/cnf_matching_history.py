"""Lazy matching-state reuse with bounded alternating-path proposals.

This stricter recognizer covers whole bases of disjoint positive choices and
complete disjoint negative exclusion cliques, with one variable per choice /
resource pair and no variables outside choices (apart from tautologies).
Added constraints need not stay in that class: the inherited joint checker
checks every affected clause. New graph edges/choices are not discovered.
"""
from collections import deque
import time

from experiments.cnf_equivalence_history import EquivalenceRepairHistory
from experiments.cnf_positive_history import UnsupportedExpansion
from experiments.cnf_residual_dag import matching_structure


class MatchingRepairHistory(EquivalenceRepairHistory):
    def __init__(self, archive=':memory:', *, repair_budget=4096):
        super().__init__(archive, repair_budget=repair_budget)
        self.matching_structures, self.matching_states = {}, {}

    def _matching_structure(self, base_id):
        if base_id in self.matching_structures:
            return self.matching_structures[base_id]
        clauses = set()
        for clause in self.bases[base_id]['source']:
            self.counts['matching_source_literals'] += len(clause)
            members = set(clause)
            if any(-lit in members for lit in members):
                continue
            clauses.add(tuple(sorted(members)))
        cnf = tuple(sorted(clauses))
        domains = matching_structure(cnf, self.counts)
        structure = None
        if domains:
            edges, adjacency = {}, {}
            for cid, domain in domains.items():
                left = cid + 1  # positive trie keys, independent of variable IDs
                adjacency[left] = tuple(sorted(domain.items()))
                for right, var in domain.items():
                    edges[var] = (left, right)
            support = {abs(lit) for clause in cnf for lit in clause}
            # The residual recognizer may collapse parallel indicators or
            # leave optional variables outside positive choices. This adapter
            # deliberately rejects both; it must bind every graph indicator.
            if set(edges) == support:
                structure = dict(edges=edges, adjacency=adjacency,
                                 units=tuple(abs(c[0]) for c in cnf if len(c) == 1))
        self.counts['matching_structure_builds'] += 1
        self.matching_structures[base_id] = structure
        return structure

    def _initial_matching_state(self, structure, root, pins=None):
        lefts, rights = None, None
        for var in structure['units']:
            pins = self._set(pins, var, 1)
        valid, selected = True, 0
        for var, (left, right) in structure['edges'].items():
            self.counts['matching_model_entries'] += 1
            if not self._get(root, var) & 4:
                continue
            if self._get(lefts, left) or self._get(rights, right):
                valid = False
            selected += 1
            lefts = self._set(lefts, left, var)
            rights = self._set(rights, right, var)
        self.counts['matching_state_reconstructions'] += 1
        if not valid or selected != len(structure['adjacency']):
            self.counts['matching_nonmatching_models'] += 1
            return None, None, pins
        return lefts, rights, pins

    @staticmethod
    def _changed_variables(payload):
        if payload['kind'] == 'append-joint':
            return payload['variables']
        if payload['kind'] in ('append-affected', 'append-pure') and payload['repair'] is not None:
            return (abs(payload['repair']),)
        return ()

    def _advance_matching_state(self, state, structure, root, payload):
        lefts, rights, pins = state
        clause = payload['clause']
        self.counts['matching_unit_literal_visits'] += len(clause)
        members = set(clause)
        if len(members) == 1:
            var = abs(next(iter(members)))
            if var in structure['edges']:
                pins = self._set(pins, var, 1)
        if lefts is None:
            return None, None, pins
        updates = ({}, {})
        for var in self._changed_variables(payload):
            self.counts['matching_changed_variables'] += 1
            endpoints = structure['edges'].get(var)
            if endpoints is None:
                continue
            added = bool(self._get(root, var) & 4)
            for groups, original, key in zip(updates, (lefts, rights), endpoints):
                if key not in groups:
                    old = self._get(original, key)
                    groups[key] = {old} if old else set()
                if added:
                    groups[key].add(var)
                else:
                    groups[key].discard(var)
        # Validate only after all removals/insertions, never an intermediate
        # scalar state. A CNF model can have multiple true choices if resources
        # are spare; such a model is valid but outside this matching view.
        if (any(len(v) != 1 for v in updates[0].values()) or
                any(len(v) > 1 for v in updates[1].values())):
            self.counts['matching_view_invalidations'] += 1
            return None, None, pins
        for groups, original in zip(updates, (lefts, rights)):
            for key, values in groups.items():
                original = self._set(original, key, next(iter(values), 0))
                self.counts['matching_endpoint_updates'] += 1
            if groups is updates[0]:
                lefts = original
            else:
                rights = original
        return lefts, rights, pins

    def _check_version(self, version, base_id, base, parent, payload):
        super()._check_version(version, base_id, base, parent, payload)
        # Derived matching views are optional. Cold certificate replay depends
        # only on the inherited complete occurrence/count checker.
        if parent in self.matching_states:
            self.matching_states[version] = self._advance_matching_state(
                self.matching_states[parent], self.matching_structures[base_id],
                self.states[version], payload)

    def _matching_state(self, version, structure):
        if version in self.matching_states:
            return self.matching_states[version]
        pending, current = [], version
        while current not in self.matching_states:
            _, parent, payload = self.checked[current]
            self.counts['matching_history_visits'] += 1
            if parent is None:
                self.matching_states[current] = self._initial_matching_state(structure, self.states[current])
                break
            pending.append((current, payload))
            current = parent
        state = self.matching_states[current]
        for child, payload in reversed(pending):
            state = self._advance_matching_state(state, structure, self.states[child], payload)
            self.matching_states[child] = state
        if state[0] is None:
            # An earlier scalar change can leave the one-edge-per-choice view.
            # Recover from the exact requested model once during lazy loading;
            # an already cached invalid view remains a conservative rejection.
            state = self._initial_matching_state(structure, self.states[version], state[2])
            self.matching_states[version] = state
        return state

    def _alternating_move(self, structure, state, literal, remaining):
        edges, adjacency = structure['edges'], structure['adjacency']
        target = abs(literal)
        if target not in edges or state[0] is None:
            return None, remaining
        lefts, rights, pins = state
        root, target_right = edges[target]
        selected = self._get(lefts, root)
        if self._get(pins, selected) or self._get(pins, target):
            self.counts['matching_pinned_rejections'] += 1
            return None, remaining
        queue, seen, previous = deque([root]), {root}, {}
        free = None
        while queue and free is None:
            left = queue.popleft()
            candidates = ((target_right, target),) if left == root and literal > 0 else adjacency[left]
            for right, var in candidates:
                if remaining == 0:
                    self.counts['repair_budget_exhaustions'] += 1
                    return None, remaining
                remaining -= 1
                self.counts['matching_search_edges'] += 1
                if right in previous or (literal < 0 and var == target):
                    continue
                if self._get(pins, var):
                    continue
                owner_var = self._get(rights, right)
                if owner_var and self._get(pins, owner_var):
                    continue
                previous[right] = (left, var)
                if not owner_var or edges[owner_var][0] == root:
                    free = right
                    break
                owner = edges[owner_var][0]
                if owner not in seen:
                    seen.add(owner)
                    queue.append(owner)
        if free is None:
            self.counts['matching_no_path'] += 1
            return None, remaining
        changes, right = set(), free
        while True:
            left, var = previous[right]
            old = self._get(lefts, left)
            changes.symmetric_difference_update((old, var))
            self.counts['matching_path_choices'] += 1
            if left == root:
                break
            right = edges[old][1]
        return tuple(sorted(changes)), remaining

    def _append_current(self, parent, clause, allow_repair):
        started = time.perf_counter()
        try:
            return super()._append_current(parent, clause, allow_repair)
        except UnsupportedExpansion:
            if not allow_repair:
                raise
        # Keep all earlier recognition/candidate counters and elapsed time.
        # Cold checks use different counters and do not consume proposal budget.
        remaining = self.repair_budget - sum(self.counts[k] for k in
                    ('candidate_clause_visits', 'candidate_joint_variables', 'candidate_joint_postings'))
        if remaining <= 0:
            raise UnsupportedExpansion('Repair proposal budget exhausted before matching search')
        base_id = self.checked[parent][0]
        structure = self._matching_structure(base_id)
        if structure is not None:
            state = self._matching_state(parent, structure)
            for literal in dict.fromkeys(clause):
                self.counts['matching_repair_candidates'] += 1
                move, remaining = self._alternating_move(structure, state, literal, remaining)
                if move is None:
                    continue
                changes, remaining = self._joint_deltas(self.clause_states[parent], self.states[parent],
                                                        move, remaining, checking=False)
                if changes is not None and self._joint_safe(self.clause_states[parent], changes):
                    payload = dict(kind='append-joint', clause=list(clause), variables=list(move))
                    version = self._put_version(base_id, parent, payload)
                    self.counts['matching_repairs'] += 1
                    return self._result(version, started)
                self.counts['matching_rejected_paths'] += 1
        raise UnsupportedExpansion('No checked scalar, equivalence or matching-path repair within budget')

    def storage(self):
        result = super().storage()
        structures = [s for s in self.matching_structures.values() if s is not None]
        pending = [root for state in self.matching_states.values() for root in state]
        seen = set()
        while pending:
            node = pending.pop()
            if node is not None and id(node) not in seen:
                seen.add(id(node))
                pending.extend(node[1:])
        result.update(resident_matching_structures=len(structures),
                      resident_matching_edges=sum(len(s['edges']) for s in structures),
                      resident_matching_state_nodes=len(seen))
        return result
