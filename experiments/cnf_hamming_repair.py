"""Bounded exact repair of complete proposals, with independently checked output.

States flip a set of seed variables at most once. A false clause forces every
successful extension to flip one of its remaining variables. Branches can
overlap; a mask memo shares those identical states. Budget exhaustion is unknown.
"""
from collections import Counter
from experiments import cnf_choice_witness as previous

EXCLUSION = 'cnf-hamming-ball-exclusion-v1'
NODE_LIMIT = 20000


def proposal(source, counts=None):
    """Wide-first disjoint choices, without assuming compatibility of clauses."""
    counts = Counter() if counts is None else counts
    clauses = previous.capacity.canonical(source, counts)
    names = sorted({abs(v) for c in source for v in c})
    model = dict.fromkeys(names, False); used = set()
    for c in sorted(clauses, key=lambda c: (-len(c), c)):
        counts['repair_seed_literal_charge'] += len(c)
        support = {abs(v) for v in c}
        if not c or used.intersection(support):
            continue
        used.update(support)
        for v in c:
            model[abs(v)] = v < 0
        model[abs(c[0])] = c[0] > 0
    return dict(format=previous.FORMAT, names=names, values=[model[v] for v in names])


def prepare(source, seed, radius, counts):
    clauses = previous.capacity.canonical(source, counts)
    names = sorted({abs(v) for c in source for v in c})
    if (type(seed) is not dict or set(seed) != {'format', 'names', 'values'}
            or seed['format'] != previous.FORMAT or type(seed['names']) is not list
            or any(type(v) is not int for v in seed['names']) or seed['names'] != names
            or type(seed['values']) is not list or len(seed['values']) != len(names)
            or any(type(v) is not bool for v in seed['values'])
            or type(radius) is not int or not 0 <= radius <= len(names)):
        raise ValueError('Invalid complete repair seed or radius')
    return clauses, names, dict(zip(names, seed['values']))


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
            counts['repair_index_occurrences'] += 1
    bad = {i for i, n in enumerate(satisfied) if not n}
    initial = len(bad); best = initial; used = set(); seen = set(); nodes = {}
    # Explicit enter/undo tasks avoid a recursion-depth admission restriction.
    pending = [('enter', 0, None)]

    def flip(v):
        model[v] = not model[v]
        for i, positive in occurrence[v]:
            counts['repair_update_occurrences'] += 1
            satisfied[i] += 1 if model[v] == positive else -1
            if satisfied[i]:
                bad.discard(i)
            else:
                bad.add(i)

    def result(reason, witness=None):
        diagnostic = dict(reason=reason, radius=radius, node_limit=node_limit,
                          expanded=len(seen), initial_failed=initial, best_failed=best)
        if witness is not None:
            diagnostic['distance'] = sum(a != b for a, b in zip(seed['values'], witness['values']))
        exclusion = None
        if reason == 'radius-exhausted' and record:
            exclusion = dict(format=EXCLUSION, seed=seed, radius=radius, nodes=nodes)
        return dict(witness=witness, exclusion=exclusion, diagnostic=diagnostic)

    while pending:
        action, mask, variable = pending.pop()
        if action == 'undo':
            flip(variable); used.remove(variable); continue
        if variable is not None:
            used.add(variable); flip(variable)
            pending.append(('undo', mask, variable))
        if mask in seen:
            counts['repair_memo_hits'] += 1; continue
        if len(seen) == node_limit:
            return result('budget')
        seen.add(mask); counts['repair_states'] += 1; best = min(best, len(bad))
        if not bad:
            witness = dict(format=previous.FORMAT, names=names, values=[model[v] for v in names])
            previous.check(source, witness, counts)
            return result('sat', witness)
        remaining = radius - len(used)
        choices = []
        for i in sorted(bad):
            counts['repair_false_literal_charge'] += len(clauses[i])
            available = tuple(sorted({abs(v) for v in clauses[i]} - used))
            choices.append((len(available), available, i))
        choices.sort()
        if not choices[0][0]:
            if record: nodes[str(mask)] = dict(blocked=choices[0][2])
            counts['repair_blocked_prunes'] += 1; continue
        packed = set(); packing = []
        for _, available, i in choices:
            counts['repair_packing_variable_charge'] += len(available)
            if not packed.intersection(available):
                packed.update(available); packing.append(i)
        if len(packing) > remaining:
            if record: nodes[str(mask)] = dict(packing=packing)
            counts['repair_packing_prunes'] += 1; continue

        def gain(v):
            score = 0
            for i, positive in occurrence[v]:
                counts['repair_gain_occurrences'] += 1
                if model[v] != positive: score += satisfied[i] == 0
                else: score -= satisfied[i] == 1
            return score

        if record: nodes[str(mask)] = dict(clause=choices[0][2])
        order = sorted(choices[0][1], key=lambda v: (-gain(v), v))
        for v in reversed(order):
            pending.append(('enter', mask | bits[v], v))
            counts['repair_branch_edges'] += 1
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
    records = proof['nodes']; masks = {}
    for key in records:
        if type(key) is not str or not key.isascii() or not key.isdecimal():
            raise ValueError('Invalid state mask')
        mask = int(key)
        if str(mask) != key or mask >= 1 << len(names) or mask.bit_count() > radius:
            raise ValueError('Out-of-ball state')
        masks[mask] = records[key]
    if 0 not in masks: raise ValueError('Missing ball root')
    referenced = {0}
    for mask in sorted(masks, key=lambda x: (-x.bit_count(), x)):
        record = masks[mask]; counts['exclusion_states_checked'] += 1
        if type(record) is not dict or len(record) != 1:
            raise ValueError('Invalid exclusion node')

        def available(index):
            if type(index) is not int or not 0 <= index < len(clauses):
                raise ValueError('Invalid false clause index')
            c = clauses[index]; counts['exclusion_literal_charge'] += len(c)
            if any((seed[abs(v)] ^ bool(mask & bits[abs(v)])) == (v > 0) for v in c):
                raise ValueError('Referenced clause is satisfied')
            return {abs(v) for v in c if not mask & bits[abs(v)]}

        if 'blocked' in record:
            if available(record['blocked']): raise ValueError('Unblocked clause')
        elif 'packing' in record:
            packing = record['packing']
            if type(packing) is not list or len(packing) <= radius - mask.bit_count():
                raise ValueError('Insufficient lower bound')
            used = set(); indices = set()
            for index in packing:
                variables = available(index)
                if index in indices or not variables or used.intersection(variables):
                    raise ValueError('Invalid disjoint false-clause packing')
                used.update(variables); indices.add(index)
        elif 'clause' in record:
            variables = available(record['clause'])
            if not variables or mask.bit_count() >= radius:
                raise ValueError('Invalid split')
            for v in variables:
                child = mask | bits[v]
                if child not in masks: raise ValueError('Missing repair branch')
                referenced.add(child)
        else:
            raise ValueError('Unknown exclusion node')
    if referenced != set(masks): raise ValueError('Unreachable exclusion nodes')
    return dict(no_model_within_radius=True, radius=radius, global_unsat=radius == len(names))


def pipeline(source, counts=None, *, enabled=True):
    counts = Counter() if counts is None else counts
    if type(enabled) is not bool: raise ValueError('Invalid repair policy')
    proof, prior = previous.pipeline(source, counts)
    repair = None
    # This status is only a scheduling hint from the unchanged, internally
    # checked portfolio. It supplies no authority to the independent SAT check.
    unresolved = (proof['kind'] == 'previous' and proof['proof']['kind'] == 'external'
                  and proof['proof']['proof']['status'] == 'unresolved')
    if enabled and unresolved:
        seed = proposal(source, counts)
        attempt = search(source, seed, len(seed['names']), counts)
        repair = dict(seed=seed, **attempt['diagnostic'])
        if attempt['witness'] is not None:
            return dict(kind='repair', proof=attempt['witness']), dict(previous=prior, repair=repair)
    return dict(kind='previous', proof=proof), dict(previous=prior, repair=repair)


def check_pipeline(source, proof, counts=None):
    if type(proof) is not dict or set(proof) != {'kind', 'proof'}:
        raise ValueError('Invalid repair pipeline certificate')
    if proof['kind'] == 'repair': return previous.check(source, proof['proof'], counts)
    if proof['kind'] == 'previous': return previous.check_pipeline(source, proof['proof'], counts)
    raise ValueError('Unknown repair pipeline certificate')
