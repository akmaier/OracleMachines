"""Checked single-variable repairs using persistent signed-occurrence summaries.

A changed value may only make literals already present in the parent true; no
opposite literal may occur there. This covers fresh variables and pure literals,
not arbitrary local model repair. Indexes are reconstructed from checked source
records, never trusted as serialized claims. Python/SQL remain outside Lean.
"""
from experiments.cnf_positive_history import PositiveHistory, UnsupportedExpansion


# Immutable binary trie: (value, zero_child, one_child). Positive integer keys
# use their low bits up to the leading one. Each path has key.bit_length nodes.
# No hashes, balancing promises, recursion, or full-map copies are required.
def map_get(root, key, counts):
    while root is not None:
        counts['map_node_visits'] += 1
        if key == 1:
            return root[0]
        root, key = root[1 + (key & 1)], key >> 1
    return 0


def map_set(root, key, value, counts):
    original, path = root, []
    while key > 1:
        counts['map_node_visits'] += 1
        bit = key & 1
        path.append((root, bit))
        root = root[1 + bit] if root is not None else None
        key >>= 1
    counts['map_node_visits'] += 1
    if (root[0] if root else 0) == value:
        return original
    root = (value, root[1], root[2]) if root else (value, None, None)
    counts['map_nodes_allocated'] += 1
    for old, bit in reversed(path):
        old = old or (0, None, None)
        root = (old[0], old[1], root) if bit else (old[0], root, old[2])
        counts['map_nodes_allocated'] += 1
    return root


class RepairHistory(PositiveHistory):
    """Same append-only source archive, with a checked model per version.

    Each variable's flags store positive occurrence (1), negative occurrence
    (2), and its current truth value (4). Immutable roots share unchanged paths.
    Original variables and every delta occurrence, even tautologies, are indexed.
    """
    def __init__(self, archive=':memory:'):
        super().__init__(archive)
        self.states, self.base_states = {}, {}

    def _get(self, root, var):
        return map_get(root, var, self.counts)

    def _set(self, root, var, flags):
        return map_set(root, var, flags, self.counts)

    def _occurrences(self, root, clause):
        for lit in clause:
            self.counts['support_literal_visits'] += 1
            var = abs(lit)
            old = self._get(root, var)
            flags = old | (1 if lit > 0 else 2)
            if flags != old:
                root = self._set(root, var, flags)
        return root

    def _initial_state(self, base_id, base):
        if base_id not in self.base_states:
            root = None
            for clause in base['source']:
                root = self._occurrences(root, clause)
            for var, value in base['model'].items():
                self.counts['model_build_entries'] += 1
                if value:
                    root = self._set(root, var, self._get(root, var) | 4)
            self.base_states[base_id] = root
        return self.base_states[base_id]

    def _holds(self, root, clause):
        for lit in clause:
            self.counts['repair_model_probes'] += 1
            if bool(self._get(root, abs(lit)) & 4) == (lit > 0):
                return True
        return False

    def _safe(self, root, lit):
        self.counts['purity_probes'] += 1
        flags = self._get(root, abs(lit))
        return not flags & (2 if lit > 0 else 1)

    def _check_version(self, version, base_id, base, parent, payload):
        if parent is None:
            super()._check_version(version, base_id, base, parent, payload)
            self.states[version] = self._initial_state(base_id, base) if base['answer'] else None
            return
        is_repair = type(payload) is dict and payload.get('kind') == 'append-pure'
        if not is_repair:
            super()._check_version(version, base_id, base, parent, payload)
            if not base['answer']:
                self.states[version] = None
                return
        elif set(payload) != {'kind', 'clause', 'repair'} or not base['answer']:
            raise ValueError('Invalid pure-repair record or non-SAT base')
        else:
            self._clause(payload['clause'])
        root = self.states[parent]
        if is_repair and payload['repair'] is not None:
            lit = payload['repair']
            if type(lit) is not int or lit == 0 or lit not in payload['clause']:
                raise ValueError('Repair literal must occur in the new clause')
            if not self._safe(root, lit):
                raise ValueError('Opposite literal occurs in the parent source')
            flags = self._get(root, abs(lit))
            if bool(flags & 4) == (lit > 0):
                raise ValueError('Repair does not change the assignment')
            root = self._set(root, abs(lit), flags | 4 if lit > 0 else flags & ~4)
            self.counts['verified_repairs'] += 1
        if not self._holds(root, payload['clause']):
            raise ValueError('Version model does not satisfy the added clause')
        self.states[version] = self._occurrences(root, payload['clause'])

    def _append_current(self, parent, clause, allow_repair):
        started = self._begin()
        base_id, _, _ = self._load(parent)
        base = self.bases[base_id]
        self._clause(clause)
        if not base['answer']:
            payload = dict(kind='append-unsat', clause=list(clause))
        else:
            root, repair = self.states[parent], None
            if not self._holds(root, clause):
                if allow_repair:
                    for lit in clause:
                        if self._safe(root, lit):
                            repair = lit
                            break
                if repair is None:
                    raise UnsupportedExpansion('No surviving model or safe pure-literal repair')
            payload = dict(kind='append-pure', clause=list(clause), repair=repair)
        version = self._put_version(base_id, parent, payload)
        return self._result(version, started)

    def append_repair(self, parent, clause):
        return self._append_current(parent, clause, allow_repair=True)

    def append_decision(self, parent, clause):
        # The inherited operation uses the fixed *base* model, which can cease
        # to satisfy this history after a repair. Always use the version model.
        return self._append_current(parent, clause, allow_repair=False)

    def witness(self, version):
        """Export the current sparse model: only true variables; omitted=false."""
        started = self._begin()
        base_id, _, _ = self._load(version)
        model = None
        if self.bases[base_id]['answer']:
            model, pending = {}, [(self.states[version], 0, 0)]
            while pending:
                node, low, depth = pending.pop()
                if node is None:
                    continue
                self.counts['model_export_nodes'] += 1
                if node[0] & 4:
                    model[low | (1 << depth)] = True
                pending.append((node[1], low, depth + 1))
                pending.append((node[2], low | (1 << depth), depth + 1))
        self.counts['copied_model_entries'] += len(model) if model is not None else 0
        import time
        return dict(model=model, seconds=time.perf_counter() - started,
                    metrics=dict(self.counts), solver_metrics=dict(self.solver.counts))

    def storage(self):
        result = super().storage()
        # Optional accounting of resident shared nodes; traversal is not append.
        import time
        started = time.perf_counter()
        pending, seen = list(self.states.values()) + list(self.base_states.values()), set()
        while pending:
            node = pending.pop()
            if node is not None and id(node) not in seen:
                seen.add(id(node))
                pending.extend(node[1:])
        result.update(resident_map_nodes=len(seen), resident_map_scan_seconds=time.perf_counter() - started)
        return result
