"""Unit closure inside exact first-flip partitions, with source-checkable proofs.

Both flip and keep commitments participate in propagation. Occurrence lists,
fixed satisfaction, unassigned counts and full-proposal counts share one undo
trail. This is ordinary unit propagation and exhaustive case search, not a new
tractable SAT class. The cap bounds entered contexts, not total work.
"""
from collections import Counter
from experiments import cnf_partition_repair as prior

EXCLUSION = 'cnf-unit-closed-partition-v1'
NODE_LIMIT = prior.NODE_LIMIT


def search(source, seed, counts=None, *, node_limit=NODE_LIMIT, record=True):
    counts = Counter() if counts is None else counts
    if type(node_limit) is not int or node_limit < 0 or type(record) is not bool:
        raise ValueError('Invalid unit-partition policy')
    clauses, names, model = prior.prepare(source, seed, 0, counts)
    initial_model = dict(model); bits = {v: 1 << j for j, v in enumerate(names)}
    occurrence = {v: [] for v in names}; satisfied = []; free_count = []; fixed_true = []
    for i, clause in enumerate(clauses):
        satisfied.append(sum(model[abs(v)] == (v > 0) for v in clause))
        free_count.append(len(clause)); fixed_true.append(0)
        for lit in clause:
            occurrence[abs(lit)].append((i, lit > 0)); counts['unit_index_occurrences'] += 1
    bad = {i for i, n in enumerate(satisfied) if not n}
    agenda = {i for i, n in enumerate(free_count) if n <= 1}
    committed = set(); trail = []; mask = kept = expanded = 0; nodes = {}
    initial_failed = best_failed = len(bad); maximum_committed = 0

    def refresh(i):
        if not fixed_true[i] and free_count[i] <= 1: agenda.add(i)
        else: agenda.discard(i)
        if satisfied[i]: bad.discard(i)
        else: bad.add(i)

    def assign(v, value):
        nonlocal mask, kept
        assert v not in committed
        committed.add(v); trail.append(v); model[v] = value
        flipped = value != initial_model[v]
        if flipped: mask |= bits[v]
        else: kept |= bits[v]
        for i, positive in occurrence[v]:
            counts['unit_assignment_occurrences'] += 1
            free_count[i] -= 1; fixed_true[i] += value == positive
            if flipped: satisfied[i] += 1 if value == positive else -1
            refresh(i)

    def undo(mark):
        nonlocal mask, kept
        while len(trail) > mark:
            v = trail.pop(); value = model[v]; flipped = value != initial_model[v]
            committed.remove(v); mask &= ~bits[v]; kept &= ~bits[v]; model[v] = initial_model[v]
            for i, positive in occurrence[v]:
                counts['unit_undo_occurrences'] += 1
                free_count[i] += 1; fixed_true[i] -= value == positive
                if flipped: satisfied[i] += -1 if value == positive else 1
                refresh(i)

    def result(reason, witness=None):
        proof = dict(format=EXCLUSION, seed=seed, nodes=nodes) if reason == 'exhausted' and record else None
        return dict(witness=witness, exclusion=proof, diagnostic=dict(reason=reason, node_limit=node_limit,
                    expanded=expanded, initial_failed=initial_failed, best_failed=best_failed,
                    maximum_committed=maximum_committed))

    pending = [('enter', ())]
    while pending:
        action, payload = pending.pop()
        if action == 'undo': undo(payload); continue
        mark = len(trail)
        for v, value in payload: assign(v, value)
        pending.append(('undo', mark))
        if expanded == node_limit: return result('budget')
        expanded += 1; counts['unit_states'] += 1
        key = f'{mask}:{kept}'; units = []; blocked = None
        if not bad:
            best_failed = 0; maximum_committed = max(maximum_committed, len(committed))
            witness = dict(format=prior.previous.FORMAT, names=names, values=[model[v] for v in names])
            prior.previous.check(source, witness, counts)
            return result('sat', witness)
        while agenda:
            counts['unit_agenda_scan_candidates'] += len(agenda)
            i = min(agenda); counts['unit_agenda_selections'] += 1
            if free_count[i] == 0: blocked = i; break
            counts['unit_clause_literal_charge'] += len(clauses[i])
            lit = next(v for v in clauses[i] if abs(v) not in committed)
            if record: units.append(i)
            counts['unit_forced_flips' if (lit > 0) != initial_model[abs(lit)] else 'unit_forced_keeps'] += 1
            assign(abs(lit), lit > 0)
        best_failed = min(best_failed, len(bad)); maximum_committed = max(maximum_committed, len(committed))
        if blocked is not None:
            if record: nodes[key] = dict(units=units, blocked=blocked)
            counts['unit_conflicts'] += 1; continue
        if not bad:
            witness = dict(format=prior.previous.FORMAT, names=names, values=[model[v] for v in names])
            prior.previous.check(source, witness, counts)
            return result('sat', witness)
        choices = []
        for i in sorted(bad):
            counts['unit_false_literal_charge'] += len(clauses[i])
            available = tuple(sorted(abs(v) for v in clauses[i] if abs(v) not in committed))
            choices.append((len(available), available, i))
        choices.sort()
        assert choices[0][0] >= 2

        def gain(v):
            score = 0
            for i, positive in occurrence[v]:
                counts['unit_gain_occurrences'] += 1
                if model[v] != positive: score += satisfied[i] == 0
                else: score -= satisfied[i] == 1
            return score

        order = sorted(choices[0][1], key=lambda v: (-gain(v), v))
        if record: nodes[key] = dict(units=units, clause=choices[0][2], order=order)
        children = []; prefix = []
        for v in order:
            children.append(('enter', tuple(prefix + [(v, not initial_model[v])])))
            counts['unit_branch_assignment_values'] += len(prefix) + 1
            prefix.append((v, initial_model[v])); counts['unit_branch_edges'] += 1
        pending.extend(reversed(children))
    return result('exhausted')


def check_exclusion(source, proof, counts=None):
    """Independently replay source-clause unit deductions and complete partitions."""
    counts = Counter() if counts is None else counts
    if type(proof) is not dict or set(proof) != {'format', 'seed', 'nodes'} or proof['format'] != EXCLUSION or type(proof['nodes']) is not dict:
        raise ValueError('Invalid unit-partition certificate')
    # Validate the seed shape before reading names to determine full support.
    clauses, names, seed = prior.prepare(source, proof['seed'], 0, counts)
    bits = {v: 1 << j for j, v in enumerate(names)}; states = {}
    for key, node in proof['nodes'].items():
        if type(key) is not str or len(parts := key.split(':')) != 2 or any(not p.isascii() or not p.isdecimal() for p in parts):
            raise ValueError('Invalid context key')
        mask, kept = map(int, parts)
        if key != f'{mask}:{kept}' or mask & kept or (mask | kept) >= 1 << len(names):
            raise ValueError('Invalid flip/keep masks')
        if type(node) is not dict or type(node.get('units')) is not list:
            raise ValueError('Missing unit trace')
        states[mask, kept] = node
    if (0, 0) not in states: raise ValueError('Missing root')
    reached = {(0, 0)}
    for (entry_mask, entry_kept), node in states.items():
        mask, kept = entry_mask, entry_kept; counts['unit_contexts_checked'] += 1

        def clause(index):
            if type(index) is not int or not 0 <= index < len(clauses): raise ValueError('Invalid clause index')
            counts['unit_check_literal_charge'] += len(clauses[index]); return clauses[index]

        def partial(index):
            c = clause(index); free = []
            for lit in c:
                bit = bits[abs(lit)]
                if not (mask | kept) & bit: free.append(lit)
                elif (seed[abs(lit)] ^ bool(mask & bit)) == (lit > 0):
                    raise ValueError('Unit or conflict premise already satisfied')
            return free

        for index in node['units']:
            free = partial(index)
            if len(free) != 1: raise ValueError('Not a unit clause under fixed context')
            lit = free[0]; v = abs(lit)
            if (lit > 0) != seed[v]: mask |= bits[v]
            else: kept |= bits[v]
            counts['unit_deductions_checked'] += 1
        if set(node) == {'units', 'blocked'}:
            if partial(node['blocked']): raise ValueError('Unblocked leaf')
        elif set(node) == {'units', 'clause', 'order'}:
            c = clause(node['clause'])
            if any((seed[abs(v)] ^ bool(mask & bits[abs(v)])) == (v > 0) for v in c):
                raise ValueError('Split clause is satisfied by current proposal')
            available = {abs(v) for v in c if not (mask | kept) & bits[abs(v)]}
            order = node['order']
            if type(order) is not list or any(type(v) is not int for v in order) or not available or len(order) != len(available) or set(order) != available:
                raise ValueError('Incomplete split order')
            prefix = kept
            for v in order:
                child = (mask | bits[v], prefix)
                if child not in states: raise ValueError('Missing child')
                reached.add(child); prefix |= bits[v]
        else: raise ValueError('Invalid exclusion node')
    if reached != set(states): raise ValueError('Unreachable contexts')
    return dict(answer=False, model=None)


def discover(source, counts=None, *, node_limit=NODE_LIMIT):
    counts = Counter() if counts is None else counts
    seed = prior.proposal(source, counts)
    return search(source, seed, counts, node_limit=node_limit)


def check_result(source, proof, counts=None):
    counts = Counter() if counts is None else counts
    if type(proof) is not dict or set(proof) != {'format', 'kind', 'certificate'} or proof['format'] != 'cnf-unit-partition-result-v1':
        raise ValueError('Invalid unit-partition result')
    if proof['kind'] == 'sat': return prior.previous.check(source, proof['certificate'], counts)
    if proof['kind'] == 'unsat': return check_exclusion(source, proof['certificate'], counts)
    if proof['kind'] == 'unknown' and proof['certificate'] is None:
        prior.previous.capacity.canonical(source, counts)
        return dict(answer=None, model=None)
    raise ValueError('Invalid unit-partition verdict')


def solve(source, counts=None):
    counts = Counter() if counts is None else counts
    result = discover(source, counts)
    kind = 'sat' if result['witness'] is not None else ('unsat' if result['exclusion'] is not None else 'unknown')
    proof = dict(format='cnf-unit-partition-result-v1', kind=kind,
                 certificate=result['witness'] if kind == 'sat' else result['exclusion'])
    check_result(source, proof, counts)
    return proof, result['diagnostic']
