"""Finite structural-coverage witnesses through checked retained alternatives.

These witnesses certify availability of a complete recognition plan, not a SAT
truth value. In particular, conditioning requires coverage of both branches.
"""
from collections import Counter, defaultdict, deque
import json
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_pivot_alternatives import verify_trial
from experiments.cnf_coupled_pivots import coupled_key, verify_coupled
from experiments.cnf_growth_escape import TABLE, trial_key, verify_escape


class CheckedRoutes:
    """Recheck serialized records before exposing their exact projection edges."""
    def __init__(self, h):
        self.by_source = defaultdict(list); self.counts = Counter()
        first = {}
        for key, payload in h.db.execute('SELECT id,payload FROM cnf_pivot_trials_v1 ORDER BY id'):
            record = json.loads(payload)
            if key != encode([record['source'], record['variable']]):
                raise ValueError('Incorrect pivot identity')
            verify_trial(h, record, self.counts); first[key] = record
            self._add('pivot', key, record)
        for key, payload in h.db.execute('SELECT id,payload FROM cnf_coupled_trials_v1 ORDER BY id'):
            record = json.loads(payload)
            if key != coupled_key(record): raise ValueError('Incorrect coupled identity')
            verify_coupled(h, record, first, self.counts); self._add('coupled', key, record)
        for key, payload in h.db.execute(f'SELECT id,payload FROM {TABLE} ORDER BY id'):
            record = json.loads(payload)
            if key != trial_key(record): raise ValueError('Incorrect escape identity')
            verify_escape(h, record, self.counts); self._add('growth', key, record)

    def _add(self, kind, key, record):
        self.by_source[record['source']].append((dict(kind=kind, id=key), [record['edge']['key']]))


def options(h, source, checked_routes):
    node = h._load(source)
    if node is None: raise ValueError('Missing route source')
    if node['summary']['closed']:
        return [(dict(kind='base'), [])]
    rows = []
    if node['kind'] == 'and':
        rows.append((dict(kind='components'), [e['key'] for e in node['edges']]))
    elif node['kind'] == 'or':
        rows.extend((dict(kind='conditioning', index=i), [e['key'] for e in a['edges']])
                    for i, a in enumerate(node['alternatives']))
    elif 'edge' in node:
        rows.append((dict(kind='edge'), [node['edge']['key']]))
    elif node['kind'] != 'unresolved':
        raise ValueError('Unknown open route source')
    return rows + checked_routes.by_source.get(source, [])


def compose(h, roots, checked_routes, counts):
    """Least fixed point of finite AND rules; old/trial alternatives supply OR.

    No unsuccessful memo is finalized while an alternative is still open. A
    cycle alone cannot create a zero-premise base. Multiplicity is retained when
    two edges share a canonical child; variable bindings were checked separately.
    """
    todo = deque(roots); seen = set(); rules = []; waiting = defaultdict(list)
    while todo:
        source = todo.popleft()
        if source in seen: continue
        seen.add(source); counts['reachable_nodes'] += 1
        for rule, children in options(h, source, checked_routes):
            i = len(rules); rules.append((source, rule, children))
            counts['rules'] += 1; counts['premises'] += len(children)
            for child in children: waiting[child].append(i); todo.append(child)
    remaining = [len(children) for _, _, children in rules]
    ready = deque(i for i, n in enumerate(remaining) if n == 0)
    justified = {}; order = []
    while ready:
        i = ready.popleft(); source, rule, children = rules[i]
        if source in justified: continue
        justified[source] = (rule, children); order.append(source)
        for dependent in waiting[source]:
            remaining[dependent] -= 1
            if remaining[dependent] == 0: ready.append(dependent)
    closed = [root in justified for root in roots]
    needed = set(); todo = deque(root for root in roots if root in justified)
    while todo:
        source = todo.popleft()
        if source in needed: continue
        needed.add(source); todo.extend(justified[source][1])
    steps = [dict(source=source, rule=justified[source][0]) for source in order if source in needed]
    counts['justified_nodes'] += len(justified); counts['witness_steps'] += len(steps)
    return closed, dict(roots=[root for root in roots if root in justified], steps=steps)


def verify_plan(h, certificate, claimed_roots, checked_routes, counts):
    """Replay only finite ordered premises; forbid circular or omitted support."""
    if type(certificate) is not dict or set(certificate) != {'roots', 'steps'}:
        raise ValueError('Invalid coverage certificate fields')
    if certificate['roots'] != claimed_roots or type(certificate['steps']) is not list:
        raise ValueError('Incorrect claimed coverage roots')
    justified = set()
    for step in certificate['steps']:
        if type(step) is not dict or set(step) != {'source', 'rule'} or type(step['source']) is not str:
            raise ValueError('Invalid coverage step')
        source = step['source']
        if source in justified: raise ValueError('Repeated coverage step')
        matches = [children for rule, children in options(h, source, checked_routes)
                   if encode(rule) == encode(step['rule'])]
        if len(matches) != 1 or not all(child in justified for child in matches[0]):
            raise ValueError('Unjustified coverage premises')
        justified.add(source); counts['verified_steps'] += 1
    if any(root not in justified for root in claimed_roots):
        raise ValueError('Missing claimed root')
    return True
