"""CNF-derived demand/capacity refutations, with independently checked cores.

This optional recognizer proves UNSAT only. A matching or a failed search never
proves SAT. Discovery is heuristic; verification does not call discovery or
matching. Source-clause containment permits reuse under conjunctive additions.
"""
from collections import Counter, deque
from itertools import combinations

FORMAT = 'cnf-disjoint-demand-capacity-v1'
WORK_LIMIT = 300000


def canonical(source, counts):
    if type(source) not in (list, tuple):
        raise ValueError('CNF must be a sequence of clauses')
    clauses = set()
    for clause in source:
        if type(clause) not in (list, tuple):
            raise ValueError('Invalid clause')
        counts['input_literals'] += len(clause)
        if any(type(v) is not int or v == 0 for v in clause):
            raise ValueError('Invalid literal')
        items = set(clause)
        if not any(-v in items for v in items):
            clauses.add(tuple(sorted(items)))
    return tuple(sorted(clauses))


def check(source, proof, counts=None):
    """Check a refuting subset against the current source, without search."""
    counts = Counter() if counts is None else counts
    clauses = set(canonical(source, counts))
    if (type(proof) is not dict or set(proof) != {'format', 'demands', 'groups'}
            or proof['format'] != FORMAT
            or type(proof['demands']) is not list
            or type(proof['groups']) is not list):
        raise ValueError('Invalid capacity certificate')
    vertices = set(); demands = set()
    for clause in proof['demands']:
        if (type(clause) is not list
                or any(type(v) is not int or v == 0 for v in clause)
                or clause != sorted(set(clause))):
            raise ValueError('Invalid demand clause')
        key = tuple(clause)
        if key not in clauses or key in demands or vertices.intersection(clause):
            raise ValueError('Missing, repeated or overlapping demand')
        demands.add(key); vertices.update(clause)
        counts['checked_demand_literals'] += len(clause)
    covered = set()
    for group in proof['groups']:
        if (type(group) is not list or not group
                or any(type(v) is not int or v == 0 for v in group)
                or group != sorted(set(group)) or covered.intersection(group)):
            raise ValueError('Invalid capacity partition')
        covered.update(group)
        for a, b in combinations(group, 2):
            counts['checked_exclusion_pairs'] += 1
            if a != -b and tuple(sorted((-a, -b))) not in clauses:
                raise ValueError('Missing binary exclusion')
    if covered != vertices or len(demands) <= len(proof['groups']):
        raise ValueError('Incomplete partition or no strict deficiency')
    return dict(answer=False, model=None)


class _Stopped(Exception):
    pass


def discover(source, counts=None, *, work_limit=WORK_LIMIT):
    """Two fixed greedy demand selections, clique partition, Hall subset.

    The allowance charges search probes, not input scanning, sorting, adjacency
    construction, certificate checking or total memory. All are timed externally.
    """
    counts = Counter() if counts is None else counts
    if type(work_limit) is not int or work_limit < 0:
        raise ValueError('Invalid capacity work limit')
    clauses = canonical(source, counts); spent = 0; attempts = []

    def tick():
        nonlocal spent
        if spent == work_limit:
            raise _Stopped
        spent += 1; counts['capacity_search_probes'] += 1

    def finish(demands, groups):
        proof = dict(format=FORMAT, demands=[list(c) for c in demands],
                     groups=[sorted(g) for g in groups])
        check(source, proof, counts)
        return proof, dict(reason='deficiency', spent=spent, attempts=attempts)

    if () in clauses:
        return finish([()], [])
    # Binary clauses certify conflicts between their negated literals. Literal
    # complements also conflict independently of the formula.
    conflict = {}
    for clause in clauses:
        if len(clause) == 2:
            a, b = (-v for v in clause)
            conflict.setdefault(a, set()).add(b)
            conflict.setdefault(b, set()).add(a)
    try:
        for minimum_width in (3, 1):
            used = set(); demands = []
            for clause in sorted(clauses, key=lambda c: (-len(c), c)):
                tick()
                if len(clause) >= minimum_width and not used.intersection(clause):
                    demands.append(clause); used.update(clause)
            adjacency = {v: (conflict.get(v, set()) | {-v}) & used for v in used}
            groups = []
            for v in sorted(used, key=lambda v: (-len(adjacency[v]), v)):
                for group in groups:
                    compatible = True
                    for w in group:
                        tick()
                        if w not in adjacency[v]:
                            compatible = False; break
                    if compatible:
                        group.append(v); break
                else:
                    groups.append([v])
            owner = {v: i for i, group in enumerate(groups) for v in group}
            neighbors = [sorted({owner[v] for v in c}) for c in demands]
            # Augmenting paths yield a maximum matching. If one demand cannot
            # augment, its alternating reachable set already gives a deficiency.
            matching = {}
            for start in range(len(demands)):
                queue = deque([start]); left = {start}; via = {}; free = None
                while queue and free is None:
                    d = queue.popleft()
                    for g in neighbors[d]:
                        tick()
                        if g in via:
                            continue
                        via[g] = d
                        if g not in matching:
                            free = g; break
                        other = matching[g]
                        if other not in left:
                            left.add(other); queue.append(other)
                if free is None:
                    selected = [demands[d] for d in sorted(left)]
                    selected_vertices = set(v for c in selected for v in c)
                    selected_groups = [set(groups[g]) & selected_vertices for g in sorted(via)]
                    attempts.append(dict(minimum_width=minimum_width, demands=len(demands),
                                         groups=len(groups), deficient_demands=len(selected),
                                         deficient_groups=len(selected_groups)))
                    return finish(selected, selected_groups)
                # Reconstruct the alternating path; each reached matched demand
                # has exactly one old occupied group in this partial matching.
                inverse = {d: g for g, d in matching.items()}
                while free is not None:
                    d = via[free]; old = inverse.get(d)
                    matching[free] = d; free = old
            attempts.append(dict(minimum_width=minimum_width, demands=len(demands),
                                 groups=len(groups), matched=len(matching)))
    except _Stopped:
        return None, dict(reason='work-limit', spent=spent, attempts=attempts)
    return None, dict(reason='no-deficiency-found', spent=spent, attempts=attempts)


def pipeline(source, counts=None, *, enabled=True):
    """Optional UNSAT gate before the unchanged external cutset pipeline."""
    from experiments import cnf_external_cutsets as external
    counts = Counter() if counts is None else counts
    if type(enabled) is not bool:
        raise ValueError('Invalid capacity gate')
    proof = None; diagnostic = None
    if enabled:
        proof, diagnostic = discover(source, counts)
    if proof is not None:
        return dict(kind='capacity', proof=proof), dict(capacity=diagnostic)
    previous, details = external.discover(source, counts, expand=True)
    return dict(kind='external', proof=previous), dict(capacity=diagnostic, external=details)


def check_pipeline(source, proof, counts=None):
    from experiments import cnf_external_cutsets as external
    if type(proof) is not dict or set(proof) != {'kind', 'proof'}:
        raise ValueError('Invalid pipeline certificate')
    if proof['kind'] == 'capacity':
        return check(source, proof['proof'], counts)
    if proof['kind'] == 'external':
        return external.check(source, proof['proof'], counts)
    raise ValueError('Invalid pipeline certificate kind')
