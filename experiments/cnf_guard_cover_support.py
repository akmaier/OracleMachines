"""Compile a wide-clause cover on its actual support, then lift its refutation.

The selected subset need not be an independent component. Exact membership and
negative native component certificates justify reuse across enclosing contexts.
This does not find a minimum support or minimize a proof globally.
"""
from experiments import cnf_residual_dag as native
from experiments.cnf_conditional_unit_support import check_template, transport
from experiments.cnf_guard_clause_cover import compile_cover


def select_support(source, hints, graph, cover, counts, *, width_limit=8, path_limit=256):
    if any(type(v) is not int or v < 1 for v in (width_limit, path_limit)):
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
    positions = {cl: i for i, cl in enumerate(source)}; bank = {}
    counts['support_source_clauses'] += len(source)
    counts['support_source_literals'] += sum(map(len, source))
    for hint in hints:
        template = hint['template']
        if not check_template(template, counts) <= positions.keys():
            raise ValueError('Missing local source support')
        expected = sorted(-v if b else v for v, b in template['assumptions'])
        if hint['clause'] != expected:
            raise ValueError('Wrong guard clause')
        bank.setdefault(tuple(expected), hint)
    used = set()
    for literal, path in zip(clause, paths):
        if not path or len(path) > path_limit:
            raise ValueError('Missing or oversized path')
        current = literal
        for nxt, edge in path:
            if (type(nxt) is not int or not nxt or type(edge) is not int or not 0 <= edge < len(graph)
                    or graph[edge] != tuple(sorted({-current, nxt}))
                    or (graph[edge] not in positions and graph[edge] not in bank)):
                raise ValueError('Unsupported or invalid graph edge')
            used.add(graph[edge]); current = nxt
        if current != -literal:
            raise ValueError('Wrong path endpoint')
    wanted = {clause}; needed = []
    for edge in sorted(used):
        if edge in positions:
            wanted.add(edge)
        else:
            hint = bank[edge]; needed.append(hint)
            wanted.update(tuple(cl) for cl in hint['template']['clauses'])
    ids = sorted(positions[cl] for cl in wanted)
    support = tuple(source[i] for i in ids)
    counts['support_selected_clauses'] += len(support)
    counts['support_selected_literals'] += sum(map(len, support))
    counts['support_selected_hints'] += len(needed)
    return support, ids, needed, used


def compile_support_cover(solver, source, hints, graph, cover, counts, *, width_limit=8, path_limit=256):
    """Check a support-bound cover; reuse/compile its root and publish a subset lift.

    Nonessential path/assumption variables absent from the selected support use
    the frozen full-context compiler. This explicit fallback avoids inventing a
    coordinate map for absent variables. No private preparation object is proof
    authority; both the inner refutation and outer wrapper use native checking.
    """
    source = tuple(map(tuple, source)); graph = tuple(map(tuple, graph))
    limits = dict(width_limit=width_limit, path_limit=path_limit)
    support, ids, needed, used = select_support(source, hints, graph, cover, counts, **limits)
    full, _, root = solver._canonical(source)
    known = solver._read(root, full, purpose='cover_enclosing_root')
    if known is not None:
        if known['answer']:
            raise ValueError('Contradictory enclosing root')
        counts['enclosing_root_hits'] += 1
        return root
    if support == source:
        counts['full_support_fallbacks'] += 1
        return compile_cover(solver, source, needed, graph, cover, counts, **limits)
    child, names, key = solver._canonical(support)
    missing = ({abs(l) for cl in used for l in cl} |
               {v for h in needed for v, _ in h['template']['assumptions']}) - set(names)
    if missing:
        counts['absent_coordinate_fallbacks'] += 1
        return compile_cover(solver, source, needed, graph, cover, counts, **limits)
    known = solver._read(key, child, purpose='cover_support_root')
    if known is not None:
        if known['answer']:
            raise ValueError('Contradictory support root')
        counts['support_root_hits'] += 1
    else:
        mapping = {v: i+1 for i, v in enumerate(names)}
        def literal(lit):
            return mapping[abs(lit)] * (1 if lit > 0 else -1)
        def clause(cl):
            return tuple(sorted(literal(lit) for lit in cl))
        compact_graph = sorted(clause(cl) for cl in used)
        positions = {cl: i for i, cl in enumerate(compact_graph)}
        compact_hints = []
        for hint in needed:
            lifted = transport(hint['template'], mapping, counts)
            compact_hints.append(dict(clause=list(clause(hint['clause'])), template=lifted))
        compact_cover = dict(clause_index=child.index(clause(cover['clause'])),
            clause=list(clause(cover['clause'])),
            paths=[[[literal(nxt), positions[clause(graph[edge])]] for nxt, edge in path] for path in cover['paths']])
        counts['coordinate_path_edges'] += sum(map(len, compact_cover['paths']))
        # Increasing variable renaming preserves literal order and path pairing.
        actual = compile_cover(solver, child, compact_hints, compact_graph, compact_cover, counts, **limits)
        if actual != key or solver._read(key, child, purpose='cover_compiled_support') is None:
            raise ValueError('Compiled support identity changed')
        counts['support_root_publications'] += 1
    solver._store(root, dict(format=native.FORMAT, cnf=[list(cl) for cl in source], answer=False,
                            proof=dict(kind='component', clauses=ids, child=key)))
    counts['support_wrappers'] += 1
    return root
