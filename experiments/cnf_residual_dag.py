"""Research CNF decider with heterogeneous leaves and persistent residual reuse.

This is NOT a production trusted path or a polynomial-time SAT claim. Python
checks certificates independently of search; Lean does not verify this program.
Every UNSAT edge names an exact normalized residual. The SQLite archive is
append-only and separate from the production solver's database. All comparison,
normalization, checking and persistence work remains part of measured runtime.
"""
from collections import Counter, deque
import json
import sqlite3
import time


FORMAT = "cnf-residual-v1"


def normalize(cnf, counts=None):
    """Sort/deduplicate, remove tautologies, and compact sorted variable names.

    This recognizes order-preserving renamings, not all graph isomorphisms or
    semantic equivalences. The returned names map local IDs back to input IDs.
    """
    clauses = set()
    for clause in cnf:
        if counts is not None:
            counts["normalization_literal_visits"] += len(clause)
        if any(type(lit) is not int or lit == 0 for lit in clause):
            raise ValueError("CNF literals must be nonzero integers")
        items = set(clause)
        if not any(-lit in items for lit in items):
            clauses.add(tuple(sorted(items)))
    if () in clauses:
        return ((),), ()
    names = tuple(sorted({abs(lit) for clause in clauses for lit in clause}))
    rename = {v: i + 1 for i, v in enumerate(names)}
    result = tuple(sorted(tuple(sorted(rename[abs(lit)] * (1 if lit > 0 else -1)
                                       for lit in clause)) for clause in clauses))
    return result, names


def restrict(cnf, assignment, counts=None):
    result = []
    for clause in cnf:
        if counts is not None:
            counts["restriction_literal_visits"] += len(clause)
        if any(abs(lit) in assignment and assignment[abs(lit)] == (lit > 0)
               for lit in clause):
            continue
        result.append(tuple(lit for lit in clause if abs(lit) not in assignment))
    return tuple(result)


def holds(cnf, assignment):
    return all(any(assignment.get(abs(lit), False) == (lit > 0) for lit in clause)
               for clause in cnf)


def token(cnf, counts):
    # Full keys deliberately avoid a collision-free-hash assumption. Their
    # storage, comparison and copying costs are charged, including proof edges.
    payload = FORMAT + ":" + json.dumps(cnf, separators=(",", ":"))
    counts["key_serialized_bytes"] += len(payload.encode())
    return payload


def propagate(cnf, counts):
    """Repeated scans, at most v+1 passes: polynomial, not a linear UP engine."""
    assignment, trace = {}, []
    changed = True
    while changed:
        changed = False
        for cid, clause in enumerate(cnf):
            counts["propagation_literal_visits"] += len(clause)
            if any(abs(lit) in assignment and assignment[abs(lit)] == (lit > 0)
                   for lit in clause):
                continue
            pending = [lit for lit in clause if abs(lit) not in assignment]
            if not pending:
                return assignment, trace, cid
            if len(pending) == 1:
                lit = pending[0]
                assignment[abs(lit)] = lit > 0
                trace.append([lit, cid])
                changed = True
    return assignment, trace, None


def components(cnf, counts):
    parent = {}

    def find(v):
        parent.setdefault(v, v)
        while v != parent[v]:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for clause in cnf:
        counts["decomposition_literal_visits"] += len(clause)
        if clause:
            first = find(abs(clause[0]))
            for lit in clause[1:]:
                parent[find(abs(lit))] = first
    groups = {}
    for clause in cnf:
        root = find(abs(clause[0])) if clause else None
        groups.setdefault(root, []).append(clause)
    return list(groups.values())


def two_cnf(cnf, counts):
    """Iterative Kosaraju; negative answers include two explicit implication paths."""
    variables = sorted({abs(lit) for clause in cnf for lit in clause})
    graph = {sign * v: [] for v in variables for sign in (-1, 1)}
    reverse = {v: [] for v in graph}
    for cid, clause in enumerate(cnf):
        if len(clause) not in (1, 2):
            raise ValueError("2-CNF solver requires nonempty binary/unit clauses")
        a, b = (clause[0], clause[-1])
        edges = [(-a, b)] if a == b else [(-a, b), (-b, a)]
        for source, target in edges:
            graph[source].append((target, cid))
            reverse[target].append(source)
            counts["implication_edges"] += 1
    seen, order = set(), []
    for root in graph:
        if root in seen:
            continue
        seen.add(root)
        stack = [(root, iter(graph[root]))]
        while stack:
            vertex, edges = stack[-1]
            edge = next(edges, None)
            if edge is None:
                order.append(vertex)
                stack.pop()
            elif edge[0] not in seen:
                seen.add(edge[0])
                stack.append((edge[0], iter(graph[edge[0]])))
    scc = {}
    for root in reversed(order):
        if root in scc:
            continue
        label = len(scc)
        scc[root] = label
        stack = [root]
        while stack:
            for other in reverse[stack.pop()]:
                if other not in scc:
                    scc[other] = label
                    stack.append(other)

    def path(source, target):
        prev, queue = {source: None}, deque([source])
        while queue and target not in prev:
            vertex = queue.popleft()
            for other, cid in graph[vertex]:
                if other not in prev:
                    prev[other] = (vertex, cid)
                    queue.append(other)
        if target not in prev:
            raise ValueError("Missing SCC path")
        result, current = [], target
        while current != source:
            previous, cid = prev[current]
            result.append([current, cid])
            current = previous
        return list(reversed(result))

    for v in variables:
        if scc[v] == scc[-v]:
            return None, {"kind": "implications", "variable": v,
                          "forward": path(v, -v), "backward": path(-v, v)}
    return {v: scc[v] > scc[-v] for v in variables}, None


def matching_structure(cnf, counts):
    """Recognize disjoint positive choices and disjoint exclusion cliques.

    Optional variables with no positive occurrence may be set false. Missing
    clique edges or overlapping positive clauses invalidate this recognition.
    The input is already normalized, so clauses/literals/edges are distinct.
    """
    positive, owned, graph = {}, set(), {}
    for cid, clause in enumerate(cnf):
        counts["matching_recognition_literal_visits"] += len(clause)
        if not clause:
            return None
        for lit in clause:
            graph.setdefault(abs(lit), set())
        if all(lit > 0 for lit in clause):
            if owned.intersection(clause):
                return None
            owned.update(clause)
            positive[cid] = clause
        elif len(clause) == 2 and all(lit < 0 for lit in clause):
            a, b = map(abs, clause)
            graph[a].add(b)
            graph[b].add(a)
        else:
            return None
    component = {}
    for root in sorted(graph):
        if root in component:
            continue
        group, stack = [], [root]
        component[root] = root
        while stack:
            vertex = stack.pop()
            group.append(vertex)
            counts["matching_conflict_edge_visits"] += len(graph[vertex])
            for other in sorted(graph[vertex]):
                if other not in component:
                    component[other] = root
                    stack.append(other)
        if any(len(graph[v]) != len(group) - 1 for v in group):
            return None
    domains = {}
    for cid, clause in positive.items():
        domains[cid] = {}
        for variable in clause:
            domains[cid].setdefault(component[variable], variable)
    return domains


def solve_matching(domains, counts):
    """O(p*e) graph traversals after adjacency sorting; failed BFS gives a Hall set."""
    adjacency = {left: sorted(domain) for left, domain in domains.items()}
    left_to_right, right_to_left = {}, {}
    for root in domains:
        queue, seen_left, prev = deque([root]), {root}, {}
        free = None
        while queue and free is None:
            left = queue.popleft()
            for right in adjacency[left]:
                counts["matching_domain_edge_visits"] += 1
                if right in prev:
                    continue
                prev[right] = left
                if right not in right_to_left:
                    free = right
                    break
                owner = right_to_left[right]
                if owner not in seen_left:
                    seen_left.add(owner)
                    queue.append(owner)
        if free is None:
            return None, {"kind": "hall-v1", "groups": sorted(seen_left)}
        right = free
        while True:
            left = prev[right]
            old_right = left_to_right.get(left)
            left_to_right[left] = right
            right_to_left[right] = left
            if old_right is None:
                break
            right = old_right
    return {domains[left][right]: True for left, right in left_to_right.items()}, None


def positive_core(cnf, counts):
    """Delete positive supersets, retaining direct source-clause witnesses.

    Increasing length ensures a retained clause is inclusion-minimal. Index it
    at its least frequent literal: every superset must visit that posting. The
    index is a candidate filter only; literal containment is always checked.
    Worst case remains quadratic in positive clause count times clause width.
    """
    positive, frequencies = [], Counter()
    for cid, clause in enumerate(cnf):
        counts["subsumption_recognition_literal_payload"] += len(clause)
        if clause and all(lit > 0 for lit in clause):
            positive.append(cid)
            frequencies.update(clause)
    positive.sort(key=lambda cid: (len(cnf[cid]), cnf[cid]))
    postings, removed = {}, []
    for cid in positive:
        clause = cnf[cid]
        members = set(clause)
        witness = None
        for lit in clause:
            counts["subsumption_posting_lookups"] += 1
            for kept in postings.get(lit, ()):
                counts["subsumption_candidate_tests"] += 1
                contained = True
                for other in cnf[kept]:
                    counts["subsumption_membership_tests"] += 1
                    if other not in members:
                        contained = False
                        break
                if contained:
                    witness = kept
                    break
            if witness is not None:
                break
        if witness is None:
            anchor = min(clause, key=lambda lit: (frequencies[lit], lit))
            postings.setdefault(anchor, []).append(cid)
        else:
            removed.append([cid, witness])
    counts["subsumed_positive_clauses"] += len(removed)
    deleted = {cid for cid, _ in removed}
    return tuple(c for cid, c in enumerate(cnf) if cid not in deleted), removed


def check_positive_core(cnf, removed, counts):
    """Validate a reduction without rerunning the subsumption search.

    Every deleted clause must contain a retained positive clause. Requiring
    direct retained witnesses rules out circular justifications and makes the
    model-preserving invariant explicit, even though UNSAT alone needs only a
    contradictory subset. This does not certify discovery/runtime bounds.
    """
    if type(removed) is not list or not removed:
        raise ValueError("Empty or invalid positive subsumption certificate")
    deleted = set()
    for pair in removed:
        if (type(pair) is not list or len(pair) != 2
                or any(type(i) is not int or not 0 <= i < len(cnf) for i in pair)
                or pair[0] in deleted):
            raise ValueError("Invalid subsumption clause index")
        deleted.add(pair[0])
    for cid, kept in removed:
        clause, witness = cnf[cid], cnf[kept]
        counts["verified_subsumption_literal_payload"] += len(clause) + len(witness)
        if (kept in deleted or not witness
                or any(lit <= 0 for lit in clause + witness)
                or not set(witness).issubset(clause)):
            raise ValueError("Invalid retained subsumption witness")
    return tuple(c for cid, c in enumerate(cnf) if cid not in deleted)


class ResidualSolver:
    """Complete mathematical search; node budget raises, never guesses UNSAT.

    Full Python execution also has finite stack/memory limits. A budget failure
    preserves completed residuals. No native/Lean solver dispatch is changed.
    """
    def __init__(self, archive=":memory:", *, reuse=True, leaves=True,
                 decompose=True, matching=True, positive_subsumption=True, node_limit=100000):
        self.db = sqlite3.connect(archive)
        self.db.execute("""CREATE TABLE IF NOT EXISTS cnf_residual_v1 (
            id TEXT PRIMARY KEY, payload TEXT NOT NULL)""")
        self.db.commit()
        self.reuse, self.leaves, self.decompose = reuse, leaves, decompose
        self.matching = matching
        self.positive_subsumption = positive_subsumption
        self.node_limit = node_limit
        self.checked = {}
        self.counts = Counter()
        self.active_loads = set()

    def close(self):
        self.db.close()

    def _canonical(self, cnf):
        normalized, names = normalize(cnf, self.counts)
        return normalized, names, token(normalized, self.counts)

    def _read(self, key, expected=None, purpose="search"):
        if key in self.checked:
            self.counts[purpose + "_memory_hits"] += 1
            node = self.checked[key]
        else:
            if key in self.active_loads:
                raise ValueError("Cyclic residual certificate")
            self.counts["database_lookups"] += 1
            row = self.db.execute("SELECT payload FROM cnf_residual_v1 WHERE id=?", (key,)).fetchone()
            if row is None:
                return None
            self.counts["read_bytes"] += len(row[0].encode())
            self.active_loads.add(key)
            try:
                node = json.loads(row[0])
                self._verify(key, node)
                self.checked[key] = node
            finally:
                self.active_loads.remove(key)
            self.counts[purpose + "_disk_hits"] += 1
        if expected is not None and node["cnf"] != [list(c) for c in expected]:
            raise ValueError("Residual identity mismatch")
        return node

    def _negative_child(self, child_key, cnf):
        expected, _, key = self._canonical(cnf)
        if type(child_key) is not str or child_key != key:
            raise ValueError("Certificate references the wrong residual")
        child = self._read(key, expected, purpose="certificate")
        if child is None or child["answer"] is not False:
            raise ValueError("Missing checked UNSAT child")

    def _verify(self, key, node):
        if node.get("format") != FORMAT or type(node.get("answer")) is not bool:
            raise ValueError("Invalid residual certificate header")
        cnf, names, actual_key = self._canonical(node["cnf"])
        if key != actual_key or node["cnf"] != [list(c) for c in cnf]:
            raise ValueError("Noncanonical or mismatched residual")
        self.counts["verified_nodes"] += 1
        self.counts["verification_literal_payload"] += sum(map(len, cnf))
        if node["answer"]:
            model = node["model"]
            if (type(model) is not list or len(model) != len(names)
                    or any(type(b) is not bool for b in model)
                    or not holds(cnf, dict(enumerate(model, 1)))):
                raise ValueError("Invalid SAT witness")
            return
        proof = node["proof"]
        kind = proof.get("kind")
        if kind == "empty":
            if () not in cnf:
                raise ValueError("No empty clause")
        elif kind == "units":
            assignment = {}
            for lit, cid in proof["trace"]:
                if (type(lit) is not int or not lit or type(cid) is not int
                        or not 0 <= cid < len(cnf) or abs(lit) in assignment):
                    raise ValueError("Invalid unit trace index")
                clause = cnf[cid]
                if lit not in clause or any(
                        abs(other) not in assignment or assignment[abs(other)] == (other > 0)
                        for other in clause if other != lit):
                    raise ValueError("Non-forced unit in certificate")
                self.counts["verification_trace_literals"] += len(clause)
                assignment[abs(lit)] = lit > 0
            conflict = proof.get("conflict")
            if conflict is not None:
                if (type(conflict) is not int or not 0 <= conflict < len(cnf)
                        or any(abs(lit) not in assignment or assignment[abs(lit)] == (lit > 0)
                               for lit in cnf[conflict])):
                    raise ValueError("Invalid unit conflict")
                self.counts["verification_trace_literals"] += len(cnf[conflict])
            else:
                if not assignment:
                    raise ValueError("Unit reduction must make progress")
                self._negative_child(proof["child"], restrict(cnf, assignment, self.counts))
        elif kind == "implications":
            v = proof["variable"]
            if type(v) is not int or v not in names:
                raise ValueError("Invalid contradictory variable")
            for source, target, path in [(v, -v, proof["forward"]),
                                         (-v, v, proof["backward"])]:
                current = source
                for next_lit, cid in path:
                    if (type(next_lit) is not int or type(cid) is not int
                            or not 0 <= cid < len(cnf)):
                        raise ValueError("Invalid implication index")
                    clause = cnf[cid]
                    allowed = ((-current,) if next_lit == -current
                               else tuple(sorted((-current, next_lit))))
                    if clause != allowed:
                        raise ValueError("Implication not supported by a clause")
                    current = next_lit
                    self.counts["verified_implication_edges"] += 1
                if current != target:
                    raise ValueError("Implication path has wrong endpoint")
        elif kind == "hall-v1":
            domains = matching_structure(cnf, self.counts)
            selected = proof["groups"]
            if (domains is None or type(selected) is not list or not selected
                    or any(type(i) is not int or i not in domains for i in selected)
                    or len(set(selected)) != len(selected)):
                raise ValueError("Invalid Hall group selection")
            neighbors = {right for left in selected for right in domains[left]}
            self.counts["verified_hall_edges"] += sum(len(domains[left]) for left in selected)
            if len(neighbors) >= len(selected):
                raise ValueError("Hall set is not deficient")
        elif kind == "positive-subsumption-v1":
            core = check_positive_core(cnf, proof["removed"], self.counts)
            self._negative_child(proof["child"], core)
        elif kind == "component":
            ids = proof["clauses"]
            if not ids or any(type(i) is not int or not 0 <= i < len(cnf) for i in ids):
                raise ValueError("Invalid component subset")
            # Any contradictory subset refutes the whole conjunction; independent
            # support is needed for SAT joining, whose full model is checked above.
            self._negative_child(proof["child"], [cnf[i] for i in ids])
        elif kind == "split":
            v = proof["variable"]
            if type(v) is not int or v not in names:
                raise ValueError("Invalid split variable")
            self._negative_child(proof["low"], restrict(cnf, {v: False}, self.counts))
            self._negative_child(proof["high"], restrict(cnf, {v: True}, self.counts))
        else:
            raise ValueError("Unknown negative certificate kind")

    def _store(self, key, node):
        self._verify(key, node)
        payload = json.dumps(node, separators=(",", ":"), sort_keys=True)
        self.counts["certificate_serialized_bytes"] += len(payload.encode())
        with self.db:
            cursor = self.db.execute("INSERT OR IGNORE INTO cnf_residual_v1 VALUES (?,?)", (key, payload))
        if cursor.rowcount:
            self.counts["inserted_nodes"] += 1
            self.counts["inserted_bytes"] += len(key) + len(payload.encode())
        self.checked[key] = node

    def _visit(self, cnf):
        self.counts["visits"] += 1
        normalized, names, key = self._canonical(cnf)
        node = self._read(key, normalized) if self.reuse else None
        if node is None:
            if self.counts["expanded_nodes"] >= self.node_limit:
                raise RuntimeError("Residual expansion budget exhausted; no verdict")
            self.counts["expanded_nodes"] += 1
            model, proof = self._expand(normalized)
            node = {"format": FORMAT, "cnf": [list(c) for c in normalized],
                    "answer": model is not None}
            if model is not None:
                local_count = max((abs(lit) for c in normalized for lit in c), default=0)
                node["model"] = [model.get(i, False) for i in range(1, local_count + 1)]
            else:
                node["proof"] = proof
            self._store(key, node)
        model = ({old: node["model"][i] for i, old in enumerate(names)}
                 if node["answer"] else None)
        return model, key

    def _expand(self, cnf):
        if not cnf:
            self.counts["constant_leaves"] += 1
            return {}, None
        if () in cnf:
            self.counts["constant_leaves"] += 1
            return None, {"kind": "empty"}
        assignment, trace, conflict = propagate(cnf, self.counts)
        if conflict is not None:
            self.counts["unit_conflicts"] += 1
            return None, {"kind": "units", "trace": trace, "conflict": conflict}
        if assignment:
            self.counts["forced_variables"] += len(assignment)
            model, child = self._visit(restrict(cnf, assignment, self.counts))
            if model is not None:
                return {**assignment, **model}, None
            return None, {"kind": "units", "trace": trace, "child": child}
        if self.leaves:
            self.counts["class_literal_payload"] += sum(map(len, cnf))
            # UP has removed all units. Default false satisfies every remaining
            # Horn clause; default true satisfies every remaining dual-Horn one.
            if all(sum(lit > 0 for lit in c) <= 1 for c in cnf):
                self.counts["horn_leaves"] += 1
                return {}, None
            if all(sum(lit < 0 for lit in c) <= 1 for c in cnf):
                self.counts["dual_horn_leaves"] += 1
                return {abs(lit): True for c in cnf for lit in c}, None
            if all(len(c) <= 2 for c in cnf):
                self.counts["two_cnf_leaves"] += 1
                return two_cnf(cnf, self.counts)
        if self.positive_subsumption:
            core, removed = positive_core(cnf, self.counts)
            if removed:
                self.counts["subsumption_nodes"] += 1
                model, child = self._visit(core)
                if model is not None:
                    # Missing variables can be false: each deleted clause has
                    # a retained subset. The full source witness is checked.
                    return model, None
                return None, {"kind": "positive-subsumption-v1",
                              "removed": removed, "child": child}
        if self.leaves:
            if self.matching:
                domains = matching_structure(cnf, self.counts)
                if domains is not None:
                    self.counts["matching_leaves"] += 1
                    return solve_matching(domains, self.counts)
        if self.decompose:
            groups = components(cnf, self.counts)
            if len(groups) > 1:
                self.counts["component_nodes"] += 1
                joined = {}
                for group in groups:
                    model, child = self._visit(group)
                    if model is None:
                        positions = {c: i for i, c in enumerate(cnf)}
                        return None, {"kind": "component", "child": child,
                                      "clauses": [positions[c] for c in group]}
                    joined.update(model)
                return joined, None
        frequencies = Counter(abs(lit) for c in cnf for lit in c)
        variable = min(frequencies, key=lambda v: (-frequencies[v], v))
        self.counts["split_nodes"] += 1
        low, low_key = self._visit(restrict(cnf, {variable: False}, self.counts))
        if low is not None:
            return {variable: False, **low}, None
        high, high_key = self._visit(restrict(cnf, {variable: True}, self.counts))
        if high is not None:
            return {variable: True, **high}, None
        return None, {"kind": "split", "variable": variable, "low": low_key, "high": high_key}

    def solve(self, cnf):
        self.counts = Counter()
        started = time.perf_counter()
        model, key = self._visit(cnf)
        # Check against the original input too, including removed tautologies.
        if model is not None and not holds(cnf, model):
            raise ValueError("Reconstructed source model failed")
        self.counts["source_witness_literal_payload"] += sum(map(len, cnf)) if model is not None else 0
        rows, payload = self.db.execute(
            "SELECT count(*), coalesce(sum(length(payload)+length(id)),0) FROM cnf_residual_v1").fetchone()
        elapsed = time.perf_counter() - started
        return {"answer": model is not None, "model": model, "root": key,
                "metrics": dict(self.counts), "seconds": elapsed,
                "archive_nodes": rows, "archive_payload_bytes": payload}
