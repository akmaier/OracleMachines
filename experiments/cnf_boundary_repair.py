"""Exact conditional repair with proof-guided release of fixed outside variables.

The frozen disjoint traversal is copied below only to collect its best complete
proposal. Prefix flip/keep commitments are released before local repair. A local
exclusion rejects one outside assignment, never the whole original formula.
"""
from collections import Counter
from experiments import cnf_partition_repair as previous_search

previous = previous_search.previous
prepare = previous_search.prepare
proposal = previous_search.proposal
NODE_LIMIT = previous_search.NODE_LIMIT
PREFIX_LIMIT = 10000
MAX_ROUNDS = 8
EXCLUSION = previous_search.EXCLUSION
CONDITIONAL = 'cnf-outside-context-exclusion-v1'
EVIDENCE = 'cnf-boundary-repair-evidence-v1'


def collect(source, seed, radius, counts=None, *, node_limit=NODE_LIMIT, record=False):
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
    near = dict(format=previous.FORMAT, names=names, values=[model[v] for v in names])
    counts['boundary_model_values_copied'] += len(names)
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
        return dict(witness=witness, exclusion=exclusion, diagnostic=diagnostic, near_model=near)

    while pending:
        action, mask, kept, variable = pending.pop()
        if action == 'undo':
            flip(variable); used.remove(variable); continue
        if variable is not None:
            used.add(variable); flip(variable)
            pending.append(('undo', mask, kept, variable))
        if expanded == node_limit:
            return result('budget')
        expanded += 1; counts['partition_states'] += 1
        if len(bad) < best:
            best = len(bad)
            near = dict(format=previous.FORMAT, names=names, values=[model[v] for v in names])
            counts['boundary_model_values_copied'] += len(names)
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



def selected_set(selected, names):
    if (type(selected) is not list or any(type(v) is not int for v in selected)
            or selected != sorted(set(selected)) or not set(selected) <= set(names)):
        raise ValueError('Invalid free variable set')
    return set(selected)


def cofactor(source, seed, selected, counts=None):
    """Independent direct reconstruction; no incremental discovery index."""
    counts = Counter() if counts is None else counts
    clauses, names, model = prepare(source, seed, 0, counts)
    free = selected_set(selected, names); parents = {}
    for clause in clauses:
        counts['boundary_direct_literal_charge'] += len(clause)
        if any(abs(lit) not in free and model[abs(lit)] == (lit > 0) for lit in clause):
            continue
        projected = tuple(lit for lit in clause if abs(lit) in free)
        parents.setdefault(projected, []).append(clause)
    return tuple(sorted(parents)), parents


class ConditionalIndex:
    """Reuse source occurrences and outside satisfaction as the free set grows."""
    def __init__(self, source, seed, counts=None):
        self.counts = Counter() if counts is None else counts
        self.clauses, self.names, self.model = prepare(source, seed, 0, self.counts)
        self.selected = set(); self.occurrence = {v: [] for v in self.names}
        self.outside_true = []; self.projected = []; self.active = set()
        for i, clause in enumerate(self.clauses):
            self.outside_true.append(sum(self.model[abs(v)] == (v > 0) for v in clause))
            self.projected.append(set())
            if not self.outside_true[-1]: self.active.add(i)
            for lit in clause:
                self.occurrence[abs(lit)].append((i, lit))
                self.counts['boundary_index_occurrences'] += 1

    def extend(self, selected):
        free = selected_set(selected, self.names)
        if not self.selected <= free: raise ValueError('Free set cannot shrink')
        for v in sorted(free - self.selected):
            for i, lit in self.occurrence[v]:
                self.counts['boundary_update_occurrences'] += 1
                self.projected[i].add(lit)
                self.outside_true[i] -= self.model[v] == (lit > 0)
                if not self.outside_true[i]: self.active.add(i)
        self.selected = free

    def snapshot(self):
        parents = {}
        for i in sorted(self.active):
            self.counts['boundary_active_clause_scans'] += 1
            self.counts['boundary_projection_literal_charge'] += len(self.projected[i])
            projected = tuple(sorted(self.projected[i]))
            parents.setdefault(projected, []).append(self.clauses[i])
        return tuple(sorted(parents)), parents


def local_seed(clauses, seed):
    model = dict(zip(seed['names'], seed['values']))
    names = sorted({abs(lit) for clause in clauses for lit in clause})
    return dict(format=previous.FORMAT, names=names, values=[model[v] for v in names])


def check_conditional(source, certificate, counts=None):
    counts = Counter() if counts is None else counts
    if (type(certificate) is not dict
            or set(certificate) != {'format', 'seed', 'selected', 'proof'}
            or certificate['format'] != CONDITIONAL):
        raise ValueError('Invalid conditional exclusion')
    local, _ = cofactor(source, certificate['seed'], certificate['selected'], counts)
    conclusion = previous_search.check_exclusion(local, certificate['proof'], counts)
    if not conclusion['global_unsat']: raise ValueError('Incomplete local exclusion')
    if certificate['proof']['seed'] != local_seed(local, certificate['seed']):
        raise ValueError('Wrong local seed binding')
    return dict(outside_context_excluded=True)


def proof_boundary(local, parents, proof, selected, counts=None):
    """Call only after checking the local exclusion; choose one parent per use."""
    counts = Counter() if counts is None else counts
    referenced = set()
    for node in proof['nodes'].values():
        counts['boundary_support_nodes'] += 1
        if 'clause' in node: referenced.add(node['clause'])
        elif 'blocked' in node: referenced.add(node['blocked'])
        else: referenced.update(node['packing'])
    free = set(selected); result = set(free)
    for i in sorted(referenced):
        candidates = parents[local[i]]
        counts['boundary_parent_literal_charge'] += sum(map(len, candidates))
        parent = min(candidates, key=lambda c: (sum(abs(v) not in free for v in c), c))
        result.update(abs(v) for v in parent)
    return sorted(result)


def check_evidence(source, evidence, counts=None):
    """Recheck every retained conditional proof and any lifted full witness."""
    counts = Counter() if counts is None else counts
    if (type(evidence) is not dict or set(evidence) != {'format', 'seed', 'rounds'}
            or evidence['format'] != EVIDENCE or type(evidence['rounds']) is not list):
        raise ValueError('Invalid boundary evidence')
    clauses, _, model = prepare(source, evidence['seed'], 0, counts)
    expected = sorted({abs(v) for c in clauses
                       if not any(model[abs(v)] == (v > 0) for v in c) for v in c})
    excluded = 0
    for j, record in enumerate(evidence['rounds']):
        if (type(record) is not dict or set(record) != {'selected', 'exclusion', 'witness'}
                or record['selected'] != expected):
            raise ValueError('Invalid conditional round')
        local, parents = cofactor(source, evidence['seed'], record['selected'], counts)
        if record['exclusion'] is not None:
            if record['witness'] is not None: raise ValueError('Conflicting local conclusions')
            certificate = dict(format=CONDITIONAL, seed=evidence['seed'],
                               selected=record['selected'], proof=record['exclusion'])
            check_conditional(source, certificate, counts); excluded += 1
            expected = proof_boundary(local, parents, record['exclusion'], expected, counts)
        else:
            if j != len(evidence['rounds']) - 1: raise ValueError('Unclosed intermediate round')
            if record['witness'] is not None:
                result = previous.check(source, record['witness'], counts)
                if any(result['model'][v] != model[v] for v in model if v not in expected):
                    raise ValueError('Lift changed a fixed outside value')
    return dict(conditional_exclusions=excluded)


def repair(source, counts=None, *, node_limit=NODE_LIMIT, prefix_limit=PREFIX_LIMIT,
           max_rounds=MAX_ROUNDS):
    counts = Counter() if counts is None else counts
    if any(type(v) is not int or v < 0 for v in (node_limit, prefix_limit, max_rounds)):
        raise ValueError('Invalid boundary budget')
    seed = proposal(source, counts)
    first = collect(source, seed, len(seed['names']), counts,
                    node_limit=min(prefix_limit, node_limit))
    used = first['diagnostic']['expanded']; near = first['near_model']
    evidence = dict(format=EVIDENCE, seed=near, rounds=[])
    diagnostics = []; witness = first['witness']
    # A complete first-phase exclusion or a zero remainder needs no recentering.
    if witness is None and first['diagnostic']['reason'] == 'budget' and used < node_limit and max_rounds:
        index = ConditionalIndex(source, near, counts)
        selected = sorted({abs(v) for i in index.active for v in index.clauses[i]})
        for _ in range(max_rounds):
            index.extend(selected); local, parents = index.snapshot()
            seed_local = local_seed(local, near)
            result = previous_search.search(local, seed_local, len(seed_local['names']), counts,
                                            node_limit=node_limit-used, record=True)
            used += result['diagnostic']['expanded']
            record = dict(selected=selected, exclusion=result['exclusion'], witness=None)
            evidence['rounds'].append(record)
            diagnostics.append(dict(selected_variables=len(selected), active_clauses=len(index.active),
                                    local_clauses=len(local), search=result['diagnostic']))
            if result['witness'] is not None:
                model = dict(index.model)
                model.update(zip(result['witness']['names'], result['witness']['values']))
                witness = dict(format=previous.FORMAT, names=seed['names'],
                               values=[model[v] for v in seed['names']])
                previous.check(source, witness, counts); record['witness'] = witness
                break
            if result['exclusion'] is None: break
            certificate = dict(format=CONDITIONAL, seed=near, selected=selected, proof=result['exclusion'])
            check_conditional(source, certificate, counts)
            expanded = proof_boundary(local, parents, result['exclusion'], selected, counts)
            if expanded == selected or used == node_limit: break
            selected = expanded
    return dict(witness=witness, evidence=evidence,
                diagnostic=dict(prefix=first['diagnostic'], rounds=diagnostics, expanded=used,
                                reason='sat' if witness is not None else 'unknown'))
