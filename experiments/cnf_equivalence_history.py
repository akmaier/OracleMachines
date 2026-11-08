"""Checked simultaneous repair, proposed by explicit binary-equivalence blocks.

Recognition is lazy, once per SAT base, and uses complementary binary clause
pairs only. Added clauses do not enlarge the discovered blocks. The independent
joint checker uses the complete current occurrence/count index, including every
addition: neither the recognizer nor a serialized block claim is trusted.
"""
from experiments.cnf_affected_history import AffectedRepairHistory
from experiments.cnf_positive_history import UnsupportedExpansion


class EquivalenceRepairHistory(AffectedRepairHistory):
    def __init__(self, archive=':memory:', *, repair_budget=4096):
        super().__init__(archive, repair_budget=repair_budget)
        self.equivalence_blocks = {}

    def _blocks(self, base_id):
        if base_id in self.equivalence_blocks:
            return self.equivalence_blocks[base_id]
        pairs, parent, size = set(), {}, {}

        def find(var):
            while parent[var] != var:
                self.counts['equivalence_find_steps'] += 1
                parent[var] = parent[parent[var]]
                var = parent[var]
            return var

        for clause in self.bases[base_id]['source']:
            self.counts['equivalence_source_clauses'] += 1
            self.counts['equivalence_source_literals'] += len(clause)
            literals = set(clause)
            if len(literals) != 2:
                continue
            a, b = sorted(literals)
            if a == -b:
                continue
            # (a OR b) AND (NOT a OR NOT b) fixes the relative
            # truth values of the two variables, for either sign pattern.
            opposite = tuple(sorted((-a, -b)))
            if opposite in pairs:
                self.counts['equivalence_pairs'] += 1
                for var in (abs(a), abs(b)):
                    if var not in parent:
                        parent[var], size[var] = var, 1
                x, y = find(abs(a)), find(abs(b))
                if x != y:
                    if size[x] < size[y]:
                        x, y = y, x
                    parent[y] = x
                    size[x] += size[y]
            pairs.add((a, b))
        groups = {}
        for var in parent:
            groups.setdefault(find(var), []).append(var)
        blocks = {}
        for group in groups.values():
            block = tuple(sorted(group))
            for var in block:
                blocks[var] = block
        self.counts['equivalence_index_builds'] += 1
        self.equivalence_blocks[base_id] = blocks
        return blocks

    def _joint_deltas(self, index, root, variables, remaining, *, checking):
        """Aggregate before testing; scalar intermediate states can be invalid.

        Discovery charges one visit per moved variable and per posting. None
        means unlimited *checking*, not unlimited proposal search. A budget
        failure returns no partial candidate and never changes any state.
        """
        postings = index[0]
        changes = {}
        prefix = 'checked' if checking else 'candidate'
        for var in variables:
            if remaining is not None:
                if remaining == 0:
                    self.counts['repair_budget_exhaustions'] += 1
                    return None, remaining
                remaining -= 1
            self.counts[prefix + '_joint_variables'] += 1
            old_sign = 1 if self._get(root, var) & 4 else 2
            new_sign = 3 ^ old_sign
            entry = self._get(postings, var)
            while entry:
                if remaining is not None:
                    if remaining == 0:
                        self.counts['repair_budget_exhaustions'] += 1
                        return None, remaining
                    remaining -= 1
                self.counts[prefix + '_joint_postings'] += 1
                cid, mask, entry = entry
                delta = int(bool(mask & new_sign)) - int(bool(mask & old_sign))
                changes[cid] = changes.get(cid, 0) + delta
        self.counts[prefix + '_joint_clauses'] += len(changes)
        return changes, remaining

    def _joint_safe(self, index, changes):
        return all(not delta or self._get(index[1], cid) + delta > 0
                   for cid, delta in changes.items())

    def _check_version(self, version, base_id, base, parent, payload):
        if type(payload) is not dict or payload.get('kind') != 'append-joint':
            return super()._check_version(version, base_id, base, parent, payload)
        if parent is None or not base['answer'] or set(payload) != {'kind', 'clause', 'variables'}:
            raise ValueError('Invalid joint-repair record or non-SAT base')
        self._clause(payload['clause'])
        variables = payload['variables']
        if (type(variables) is not list or len(variables) < 2 or
                any(type(v) is not int or v <= 0 for v in variables) or
                any(a >= b for a, b in zip(variables, variables[1:]))):
            raise ValueError('Joint variables must be distinct increasing positive integers')
        root, index = self.states[parent], self.clause_states[parent]
        changes, _ = self._joint_deltas(index, root, variables, None, checking=True)
        postings, counts, next_id = index
        for cid, delta in changes.items():
            if delta:
                new_count = self._get(counts, cid) + delta
                if new_count <= 0:
                    raise ValueError('Joint repair invalidates a parent clause')
                counts = self._set(counts, cid, new_count)
                self.counts['changed_joint_clause_counts'] += 1
        for var in variables:
            root = self._set(root, var, self._get(root, var) ^ 4)
        if not self._holds(root, payload['clause']):
            raise ValueError('Joint repair does not satisfy the added clause')
        index = self._index_clause((postings, counts, next_id), root, payload['clause'])
        self.states[version] = self._occurrences(root, payload['clause'])
        self.clause_states[version] = index
        self.counts['verified_joint_repairs'] += 1

    def _append_current(self, parent, clause, allow_repair):
        started = self._begin()
        base_id, _, _ = self._load(parent)
        base = self.bases[base_id]
        self._clause(clause)
        if not base['answer']:
            payload = dict(kind='append-unsat', clause=list(clause))
        else:
            root, index = self.states[parent], self.clause_states[parent]
            payload = dict(kind='append-affected', clause=list(clause), repair=None)
            if not self._holds(root, clause):
                if not allow_repair:
                    raise UnsupportedExpansion('Current model does not survive')
                remaining = self.repair_budget
                for lit in dict.fromkeys(clause):
                    self.counts['repair_candidates'] += 1
                    safe, remaining = self._can_flip(index, lit, remaining)
                    if safe:
                        payload['repair'] = lit
                        break
                else:
                    # Old base equalities persist under conjunctive additions.
                    # New equalities are deliberately not discovered here.
                    blocks, tried = self._blocks(base_id), set()
                    for lit in dict.fromkeys(clause):
                        block = blocks.get(abs(lit))
                        if block is None or block[0] in tried:
                            continue
                        tried.add(block[0])
                        self.counts['joint_repair_candidates'] += 1
                        changes, remaining = self._joint_deltas(index, root, block, remaining, checking=False)
                        if changes is not None and self._joint_safe(index, changes):
                            payload = dict(kind='append-joint', clause=list(clause), variables=list(block))
                            break
                    else:
                        raise UnsupportedExpansion('No checked single-variable or base-equivalence repair within budget')
        version = self._put_version(base_id, parent, payload)
        return self._result(version, started)

    def storage(self):
        result = super().storage()
        blocks = {id(block): block for index in self.equivalence_blocks.values() for block in index.values()}
        result.update(resident_equivalence_indexes=len(self.equivalence_blocks),
                      resident_equivalence_blocks=len(blocks),
                      resident_equivalence_members=sum(map(len, blocks.values())),
                      resident_equivalence_lookup_entries=sum(map(len, self.equivalence_blocks.values())))
        return result
