"""Bounded wide-clause discovery over tentative binary guard consequences.

Discovery is only a proposal. Compilation checks every selected support against
actual source clauses, then refutes the source with ordinary native splits and
unit proofs. Synthetic graph clause numbers never become native reason indices.
"""
from collections import deque
from experiments import cnf_residual_dag as native
from experiments.cnf_conditional_unit_support import check_template, materialize
from experiments.cnf_guard_certificate_solver import transport_checked


def discover(source, graph, model, counts, *, width_limit=8, root_limit=8,
             edge_limit=4096, path_limit=256):
    if any(type(x) is not int or x < 1 for x in (width_limit, root_limit, edge_limit, path_limit)):
        raise ValueError('Positive discovery bounds required')
    graph = tuple(map(tuple, graph))
    if any(not 1 <= len(cl) <= 2 or list(cl) != sorted(set(cl)) or
           any(type(l) is not int or not l or -l in cl for l in cl) for cl in graph):
        raise ValueError('Expected nonempty binary clauses')
    variables = {abs(l) for cl in graph for l in cl}
    if any(type(model.get(v)) is not bool for v in variables) or not native.holds(graph, model):
        raise ValueError('Expected a checked graph model')
    counts['graphs'] += 1
    adjacency = {}
    for cid, cl in enumerate(graph):
        a, b = cl[0], cl[-1]
        adjacency.setdefault(-a, []).append((b, cid))
        counts['graph_edges'] += 1
        if a != b:
            adjacency.setdefault(-b, []).append((a, cid))
            counts['graph_edges'] += 1
    cache = {}; roots = 0; visits = 0
    for cid, clause in enumerate(source):
        counts['source_clauses'] += 1
        counts['source_literals'] += len(clause)
        if not 3 <= len(clause) <= width_limit:
            continue
        counts['wide_clauses'] += 1
        if any(abs(l) not in variables for l in clause):
            counts['missing_graph_variables'] += 1
            continue
        if any(model[abs(l)] == (l > 0) for l in clause):
            counts['model_satisfied_clauses'] += 1
            continue
        counts['screened_clauses'] += 1
        paths = []
        for root in clause:
            if root in cache:
                counts['root_reuses'] += 1
            else:
                if roots >= root_limit:
                    counts['root_limit_stops'] += 1
                    return None
                roots += 1; counts['reach_roots'] += 1
                parents = {root: None}; queue = deque([root])
                while queue and -root not in parents:
                    current = queue.popleft()
                    for nxt, edge in adjacency.get(current, ()):
                        if visits >= edge_limit:
                            counts['edge_limit_stops'] += 1
                            return None  # A stopped traversal is never cached as absence.
                        visits += 1; counts['reach_edge_visits'] += 1
                        if nxt not in parents:
                            parents[nxt] = (current, edge); queue.append(nxt)
                counts['peak_reach_vertices'] = max(counts['peak_reach_vertices'], len(parents))
                path = None
                if -root in parents:
                    path = []; current = -root
                    while current != root:
                        prev, edge = parents[current]
                        path.append([current, edge]); current = prev
                    path.reverse()
                    if len(path) > path_limit:
                        counts['path_limit_stops'] += 1
                        return None
                else:
                    counts['unreachable_roots'] += 1
                cache[root] = path
            if cache[root] is None:
                break
            paths.append(cache[root])
        if len(paths) == len(clause):
            counts['candidate_covers'] += 1
            counts['witness_edges'] += sum(map(len, paths))
            return dict(clause_index=cid, clause=list(clause), paths=paths)
    return None


def compile_cover(solver, source, hints, graph, cover, counts, *, width_limit=8, path_limit=256):
    """Refute source, validating all evidence before any new native write.

    For each literal of the actual wide clause, refute its true branch under
    the preceding false prefix. The final all-false branch empties that clause.
    Supports can overlap and need not be independent.
    """
    if any(type(x) is not int or x < 1 for x in (width_limit, path_limit)):
        raise ValueError('Positive compilation bounds required')
    source = tuple(map(tuple, source)); graph = tuple(map(tuple, graph))
    if native.normalize(source, counts)[0] != source:
        raise ValueError('Canonical source required')
    cid = cover['clause_index']
    if type(cid) is not int or not 0 <= cid < len(source):
        raise ValueError('Invalid source clause index')
    clause = source[cid]; paths = cover['paths']
    if list(clause) != cover['clause'] or not 3 <= len(clause) <= width_limit or len(paths) != len(clause):
        raise ValueError('Changed or oversized source clause')
    members = set(source); bank = {}
    for hint in hints:
        template = hint['template']
        if not check_template(template, counts) <= members:
            raise ValueError('Missing local source support')
        expected = sorted(-v if b else v for v, b in template['assumptions'])
        if hint['clause'] != expected:
            raise ValueError('Wrong guard clause')
        bank.setdefault(tuple(expected), template)
    for cl in source:
        if len(cl) in (1, 2):
            bank[cl] = dict(clauses=[list(cl)], assumptions=sorted([[abs(l), l < 0] for l in cl]),
                            trace=[], conflict=0)
    for literal, path in zip(clause, paths):
        if not path or len(path) > path_limit:
            raise ValueError('Missing or oversized path')
        current = literal
        for nxt, edge in path:
            if (type(nxt) is not int or not nxt or type(edge) is not int or not 0 <= edge < len(graph)
                    or graph[edge] != tuple(sorted({-current, nxt})) or graph[edge] not in bank):
                raise ValueError('Unsupported or invalid graph edge')
            current = nxt
        if current != -literal:
            raise ValueError('Wrong path endpoint')
    counts['validated_covers'] += 1

    def prepared(context):
        return solver._canonical(native.restrict_scan(source, context, counts))

    def save(child, key, proof):
        solver._store(key, dict(format=native.FORMAT, cnf=[list(cl) for cl in child], answer=False, proof=proof))
        counts['published_nodes'] += 1
        return key

    def ready(context):
        child, names, key = prepared(context)
        old = solver._read(key, child, purpose='guard_cover_existing')
        if old is not None:
            if old['answer']:
                raise ValueError('Contradictory saved cofactor')
            counts['existing_nodes'] += 1
            return child, names, key, True
        if () in child:
            save(child, key, dict(kind='empty'))
            return child, names, key, True
        return child, names, key, False

    def leaf(template, context):
        child, names, key, done = ready(context)
        if done:
            return key
        proof = transport_checked(template, context, {v: i+1 for i, v in enumerate(names)}, child, counts)
        if proof is None:
            counts['support_propagation_fallbacks'] += 1
            return materialize(solver, source, template, context=sorted([list(p) for p in context.items()]), counts=counts)['root']
        counts['transported_leaves'] += 1
        return save(child, key, proof)

    def path_walk(path, index, context):
        child, names, key, done = ready(context)
        if done:
            return key
        for i in range(index, len(path)):
            nxt, edge = path[i]; variable = abs(nxt); value = nxt > 0; template = bank[graph[edge]]
            if variable in context:
                if context[variable] == value:
                    continue
                return leaf(template, context)
            excluded = leaf(template, {**context, variable: not value})
            if variable not in names:
                if excluded != key:
                    raise ValueError('Absent-variable lift changed cofactor')
                counts['absent_variable_lifts'] += 1
                return key
            live = path_walk(path, i+1, {**context, variable: value})
            counts['path_splits'] += 1
            return save(child, key, dict(kind='split', variable=names.index(variable)+1,
                        low=excluded if value else live, high=live if value else excluded))
        raise ValueError('Path did not close its premise')

    def cover_walk(index, context):
        child, names, key, done = ready(context)
        if done:
            return key
        if index == len(clause):
            raise ValueError('False clause failed to close')
        literal = clause[index]; variable = abs(literal); value = literal > 0
        excluded = path_walk(paths[index], 0, {**context, variable: value})
        if variable not in names:
            if excluded != key:
                raise ValueError('Absent cover variable changed cofactor')
            counts['absent_variable_lifts'] += 1
            return key
        live = cover_walk(index+1, {**context, variable: not value})
        counts['cover_splits'] += 1
        return save(child, key, dict(kind='split', variable=names.index(variable)+1,
                    low=live if value else excluded, high=excluded if value else live))

    return cover_walk(0, {})
