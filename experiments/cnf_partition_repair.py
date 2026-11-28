"""Disjoint first-flip partitions for bounded repair of complete proposals.

At a false clause, branch j flips its j-th available variable and keeps all
previous candidates at their seed values. The resulting extension sets are
pairwise disjoint and cover the parent. Both masks are part of proof identity.
"""
from collections import Counter
from experiments import cnf_hamming_repair as baseline

previous = baseline.previous
proposal = baseline.proposal
prepare = baseline.prepare
NODE_LIMIT = baseline.NODE_LIMIT
EXCLUSION = 'cnf-disjoint-repair-ball-v1'


def search(source, seed, radius, counts=None, *, node_limit=NODE_LIMIT, record=False):
    counts = Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit < 0 or type(record) is not bool:
        raise ValueError('Invalid repair budget or recording policy')
    clauses, names, model = prepare(source, seed, radius, counts)
    bits = {v: 1 << j for j, v in enumerate(names)}
    occurrence = {v: [] for v in names}
    satisfied = []
    for i, c in enumerate(clauses):
        satisfied.append(sum(model[abs(v)] == (v > 0) for v in c))
        for v in c:
            occurrence[abs(v)].append((i, v > 0))
            counts['partition_index_occurrences'] += 1
    bad = {i for i, n in enumerate(satisfied) if not n}
    initial = len(bad); best = initial; used = set(); expanded = 0; nodes = {}; maximum_kept = 0
    # Explicit enter/undo tasks avoid a recursion-depth admission restriction.
    pending = [('enter', 0, 0, None)]

    def flip(v):
        model[v] = not model[v]
        for i, positive in occurrence[v]:
            counts['partition_update_occurrences'] += 1
            satisfied[i] += 1 if model[v] == positive else -1
            if satisfied[i]:
                bad.discard(i)
            else:
                bad.add(i)

    def result(reason, witness=None):
        diagnostic = dict(reason=reason, radius=radius, node_limit=node_limit,
                          expanded=expanded, initial_failed=initial, best_failed=best, maximum_kept=maximum_kept)
        if witness is not None:
            diagnostic['distance'] = sum(a != b for a, b in zip(seed['values'], witness['values']))
        exclusion = None
        if reason == 'radius-exhausted' and record:
            exclusion = dict(format=EXCLUSION, seed=seed, radius=radius, nodes=nodes)
        return dict(witness=witness, exclusion=exclusion, diagnostic=diagnostic)

    while pending:
        action, mask, kept, variable = pending.pop()
        if action == 'undo':
            flip(variable); used.remove(variable); continue
        if variable is not None:
            used.add(variable); flip(variable)
            pending.append(('undo', mask, kept, variable))
        if expanded == node_limit:
            return result('budget')
        expanded += 1; counts['partition_states'] += 1; best = min(best, len(bad))
        maximum_kept = max(maximum_kept, kept.bit_count())
        key = f'{mask}:{kept}'
        if not bad:
            witness = dict(format=previous.FORMAT, names=names, values=[model[v] for v in names])
            previous.check(source, witness, counts)
            return result('sat', witness)
        remaining = radius - len(used)
        choices = []
        for i in sorted(bad):
            counts['partition_false_literal_charge'] += len(clauses[i])
            available = tuple(sorted(abs(v) for v in clauses[i] if not (mask | kept) & bits[abs(v)]))
            choices.append((len(available), available, i))
        choices.sort()
        if not choices[0][0]:
            if record: nodes[key] = dict(blocked=choices[0][2])
            counts['partition_blocked_prunes'] += 1; continue
        packed = set(); packing = []
        for _, available, i in choices:
            counts['partition_packing_variable_charge'] += len(available)
            if not packed.intersection(available):
                packed.update(available); packing.append(i)
        if len(packing) > remaining:
            if record: nodes[key] = dict(packing=packing)
            counts['partition_packing_prunes'] += 1; continue

        def gain(v):
            score = 0
            for i, positive in occurrence[v]:
                counts['partition_gain_occurrences'] += 1
                if model[v] != positive: score += satisfied[i] == 0
                else: score -= satisfied[i] == 1
            return score

        order = sorted(choices[0][1], key=lambda v: (-gain(v), v))
        if record: nodes[key] = dict(clause=choices[0][2], order=order)
        children = []; prefix = kept
        for v in order:
            children.append(('enter', mask | bits[v], prefix, v))
            prefix |= bits[v]; counts['partition_branch_edges'] += 1
        pending.extend(reversed(children))
    return result('radius-exhausted')


def check_exclusion(source, proof, counts=None):
    """Check a complete radius refutation without the repair search or index.

The conclusion excludes only the stated ball. It is global UNSAT only when the
radius spans all source variables. Every referenced clause is freshly checked.
"""
    counts = Counter() if counts is None else counts
    if (type(proof) is not dict or set(proof) != {'format', 'seed', 'radius', 'nodes'}
            or proof['format'] != EXCLUSION or type(proof['nodes']) is not dict):
        raise ValueError('Invalid ball exclusion certificate')
    clauses, names, seed = prepare(source, proof['seed'], proof['radius'], counts)
    bits = {v: 1 << j for j, v in enumerate(names)}; radius = proof['radius']
    records = proof['nodes']; states = {}
    for key in records:
        if type(key) is not str or len(parts := key.split(':')) != 2:
            raise ValueError('Invalid partition state')
        if any(not p.isascii() or not p.isdecimal() for p in parts):
            raise ValueError('Invalid state mask')
        mask, kept = map(int, parts)
        if (f'{mask}:{kept}' != key or (mask | kept) >= 1 << len(names)
                or mask & kept or mask.bit_count() > radius):
            raise ValueError('Invalid flip/keep context')
        states[mask, kept] = records[key]
    if (0, 0) not in states: raise ValueError('Missing ball root')
    referenced = {(0, 0)}
    for mask, kept in sorted(states, key=lambda x: (-x[0].bit_count(), x)):
        record = states[mask, kept]; counts['partition_exclusion_states_checked'] += 1
        if type(record) is not dict:
            raise ValueError('Invalid exclusion node')

        def available(index):
            if type(index) is not int or not 0 <= index < len(clauses):
                raise ValueError('Invalid false clause index')
            c = clauses[index]; counts['partition_exclusion_literal_charge'] += len(c)
            if any((seed[abs(v)] ^ bool(mask & bits[abs(v)])) == (v > 0) for v in c):
                raise ValueError('Referenced clause is satisfied')
            return {abs(v) for v in c if not (mask | kept) & bits[abs(v)]}

        if set(record) == {'blocked'}:
            if available(record['blocked']): raise ValueError('Unblocked clause')
        elif set(record) == {'packing'}:
            packing = record['packing']
            if type(packing) is not list or len(packing) <= radius - mask.bit_count():
                raise ValueError('Insufficient lower bound')
            used = set(); indices = set()
            for index in packing:
                variables = available(index)
                if index in indices or not variables or used.intersection(variables):
                    raise ValueError('Invalid disjoint false-clause packing')
                used.update(variables); indices.add(index)
        elif set(record) == {'clause', 'order'}:
            variables = available(record['clause'])
            if not variables or mask.bit_count() >= radius:
                raise ValueError('Invalid split')
            order = record['order']
            if (type(order) is not list or any(type(v) is not int for v in order)
                    or len(order) != len(variables) or set(order) != variables):
                raise ValueError('Incomplete or repeated branch order')
            prefix = kept
            for v in order:
                child = (mask | bits[v], prefix)
                if child not in states: raise ValueError('Missing partition branch')
                referenced.add(child); prefix |= bits[v]
        else:
            raise ValueError('Unknown exclusion node')
    if referenced != set(states): raise ValueError('Unreachable exclusion nodes')
    return dict(no_model_within_radius=True, radius=radius, global_unsat=radius == len(names))
