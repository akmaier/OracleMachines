"""Resume untried binary-frequency probes without changing old plan identities.

Records certify a bounded probe window, including inconclusive attempts. A forced
record binds an exact residual even if admission stops before acquiring its plan.
Only a present, checked residual can become a coverage-route premise.
"""
from collections import Counter, deque
import json
from experiments.cnf_coupled_pivots import AdmissionExhausted, FrontierIndex
from experiments.cnf_failed_literal import probe_choices, discover_probes, check_probes
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_route_composition import CheckedRoutes
from experiments.cnf_variable_elimination import _limit

TABLE = 'cnf_probe_windows_v1'


def record_key(record): return encode([record['source'], record['width']])


def choices(h, source, width, counts):
    _limit(width)
    if type(source) is not str: raise ValueError('Invalid probe-window source')
    node = h._load(source)
    if node is None or node['kind'] != 'unresolved': raise ValueError('Expected unresolved source')
    tried = {a['variable'] for a in node['profile']['probing'].get('attempts', [])}
    # This is a bounded continuation of the original binary-frequency ordering;
    # the cap of 64 is explicit, even on arbitrarily larger variable sets.
    ranked = probe_choices(node['cnf'], 64, counts)
    counts['saved_probe_variables'] += len(tried)
    return node, [v for v in ranked if v not in tried][:width]


def verify_window(h, record, counts, *, width=4):
    if type(record) is not dict or set(record) != {'source','width','probing','edge'}:
        raise ValueError('Invalid probe-window fields')
    if type(record['width']) is not int or record['width'] != width:
        raise ValueError('Incorrect probe-window policy')
    node, selected = choices(h, record['source'], width, counts)
    target, _ = check_probes(node['cnf'], record['probing'], width, counts, _choices=selected)
    if record['probing']['status'] == 'forced':
        _, names, key = h._canonical(target, node['depth'])
        if encode(record['edge']) != encode(dict(key=key, names=names)):
            raise ValueError('Incorrect probe-window residual binding')
    elif record['edge'] is not None:
        raise ValueError('Inconclusive probing cannot create a residual route')
    counts['verified_probe_windows'] += 1
    return target


def acquire_record(h, source, known, counts, *, width=4):
    identity = encode([source, width])
    if identity in known:
        record = known[identity]
        if record_key(record) != identity: raise ValueError('Incorrect cached probe-window identity')
        target = verify_window(h, record, counts, width=width)
        counts['reused_probe_windows'] += 1
        return record, target
    node, selected = choices(h, source, width, counts)
    probing = discover_probes(node['cnf'], width, counts, _choices=selected)
    target, _ = check_probes(node['cnf'], probing, width, counts, _choices=selected)
    edge = None
    if probing['status'] == 'forced':
        _, names, key = h._canonical(target, node['depth']); edge = dict(key=key,names=names)
    record = dict(source=source, width=width, probing=probing, edge=edge)
    verify_window(h, record, counts, width=width)
    with h.db: h.db.execute(f'INSERT INTO {TABLE} VALUES (?,?)', (identity, encode(record)))
    known[identity] = record; counts['new_probe_windows'] += 1
    return record, target


class WindowRoutes(CheckedRoutes):
    def __init__(self, h):
        super().__init__(h); self.windows = {}
        for identity, payload in h.db.execute(f'SELECT id,payload FROM {TABLE} ORDER BY id'):
            record = json.loads(payload)
            if record_key(record) != identity: raise ValueError('Incorrect probe-window identity')
            verify_window(h, record, self.counts)
            self.windows[identity] = record
            self.add_window(h, record)

    def add_window(self, h, record):
        # Caller supplies a just-verified immutable record. A missing child is
        # pending acquisition, never an inferred closed/UNSAT endpoint.
        if record['edge'] is None: return
        if h._load(record['edge']['key']) is None:
            self.counts['pending_probe_windows'] += 1; return
        item = (dict(kind='probe_window',id=record_key(record)), [record['edge']['key']])
        if item not in self.by_source[record['source']]: self.by_source[record['source']].append(item)


def search(h, root, routes, counts, *, source_limit=4, state_limit=32, width=4):
    for limit in (source_limit,state_limit,width): _limit(limit)
    h.set_admission_budget(state_limit)
    index = FrontierIndex(h); todo = deque(sorted(index.frontier(root))); seen = set()
    visits = []; stop = None
    while todo and len(seen) < source_limit:
        source = todo.popleft()
        if source in seen: continue
        seen.add(source)
        record, target = acquire_record(h, source, routes.windows, counts, width=width)
        visits.append(record_key(record))
        if record['edge'] is None: continue
        node = h._load(source)
        try: edge = h._edge(target, node['depth'])
        except AdmissionExhausted:
            stop = dict(source=source, reason='admission_limit'); break
        if edge != record['edge']: raise ValueError('Acquired residual differs from checked window')
        routes.add_window(h, record)
        # Follow a successful forced-value continuation before another initial
        # leaf, while retaining a single source/admission scope for this input.
        todo.extendleft(reversed(sorted(index.frontier(edge['key']))))
    counts.update(index.counts)
    return dict(visits=visits, budget_stop=stop, remaining_queued_sources=len(todo))
