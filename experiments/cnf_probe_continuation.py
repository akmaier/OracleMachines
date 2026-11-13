"""Advance immutable probe windows through checked, shared clear prefixes.

The predecessor is determined by (source, width, offset-width), with offset zero
denoting the old probe-window table. A numeric cursor alone is never evidence.
Only complete clear blocks can precede another block. Forced blocks instead
resume their exact residual, including after interrupted recognition admission.
"""
from collections import deque
import json

from experiments.cnf_coupled_pivots import AdmissionExhausted, FrontierIndex
from experiments.cnf_failed_literal import discover_probes, check_probes
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_window import WindowRoutes, choices, acquire_record
from experiments.cnf_variable_elimination import _limit

TABLE = 'cnf_probe_continuations_v1'
WIDTH = 4


def record_key(record):
    return encode([record['source'], record['width'], record['offset']])


class ContinuationRoutes(WindowRoutes):
    def __init__(self, h):
        super().__init__(h)
        self.continuations = {}
        self.verified = set()
        for identity, payload in h.db.execute(f'SELECT id,payload FROM {TABLE} ORDER BY id'):
            record = json.loads(payload)
            if record_key(record) != identity:
                raise ValueError('Incorrect continuation identity')
            self.continuations[identity] = record
        # SQL lexical order need not be predecessor order. Verification descends
        # through strictly smaller bounded offsets, never through arbitrary links.
        for identity in self.continuations:
            self._verify_saved(h, identity, self.counts)
        self.refresh(h)

    def _verify_saved(self, h, identity, counts):
        if identity not in self.verified:
            if identity not in self.continuations:
                raise ValueError('Missing continuation prefix')
            self.verify(h, self.continuations[identity], counts)
            self.verified.add(identity)
        else:
            counts['reused_checked_prefix_blocks'] += 1
        return self.continuations[identity]

    def verify(self, h, record, counts):
        if type(record) is not dict or set(record) != {'source','width','offset','probing','edge'}:
            raise ValueError('Invalid continuation fields')
        source, width, offset = record['source'], record['width'], record['offset']
        if (type(source) is not str or type(width) is not int or width != WIDTH or
                type(offset) is not int or not 0 < offset < 64 or offset % width):
            raise ValueError('Invalid continuation policy or offset')
        if offset == width:
            # WindowRoutes has independently checked these immutable records.
            parent = self.windows.get(encode([source, width]))
            counts['reused_checked_window_prefixes'] += 1
        else:
            parent = self._verify_saved(h, encode([source, width, offset-width]), counts)
        if (parent is None or parent['probing']['status'] != 'clear' or
                len(parent['probing']['attempts']) != 2*width):
            raise ValueError('Continuation requires a complete clear predecessor')
        node, ranked = choices(h, source, 64, counts)
        selected = ranked[offset:offset+width]
        if not selected:
            raise ValueError('Exhausted ranked pool cannot create a continuation')
        target, _ = check_probes(node['cnf'], record['probing'], width, counts, _choices=selected)
        if record['probing']['status'] == 'forced':
            _, names, key = h._canonical(target, node['depth'])
            if encode(record['edge']) != encode(dict(key=key, names=names)):
                raise ValueError('Incorrect continuation residual binding')
        elif record['edge'] is not None:
            raise ValueError('Clear continuation cannot create a residual route')
        counts['verified_probe_continuations'] += 1
        return target

    def add_continuation(self, h, record):
        # As with WindowRoutes.add_window, caller supplies a checked immutable row.
        if record['edge'] is None or h._load(record['edge']['key']) is None:
            return
        item = (dict(kind='probe_continuation', id=record_key(record)), [record['edge']['key']])
        if item not in self.by_source[record['source']]:
            self.by_source[record['source']].append(item)

    def refresh(self, h):
        # Another route may have acquired a previously pending target. Refresh
        # both kinds before composition so resident and cold availability agree.
        for record in self.windows.values():
            if record['edge'] is not None and h._load(record['edge']['key']) is not None:
                self.add_window(h, record)
        for record in self.continuations.values():
            self.add_continuation(h, record)

    def advance(self, h, source, counts):
        """Acquire at most one new block, or resume an existing forced block.

        Return (kind, record, target); exhausted clear prefixes return no record.
        Previously checked clear traces are referenced, not copied or rediscovered.
        """
        base = self.windows.get(encode([source, WIDTH]))
        if base is None or base['probing']['status'] == 'forced':
            record, target = acquire_record(h, source, self.windows, counts, width=WIDTH)
            return 'probe_window', record, target
        node, ranked = choices(h, source, 64, counts)
        offset = 0
        parent = base
        while parent['probing']['status'] == 'clear':
            counts['reused_prefix_attempts'] += len(parent['probing']['attempts'])
            offset += len(parent['probing']['attempts']) // 2
            if offset >= len(ranked):
                counts['exhausted_probe_sources'] += 1
                return None, None, None
            identity = encode([source, WIDTH, offset])
            if identity not in self.continuations:
                break
            parent = self._verify_saved(h, identity, counts)
        else:
            counts['reused_forced_continuations'] += 1
            return 'probe_continuation', parent, self.verify(h, parent, counts)
        selected = ranked[offset:offset+WIDTH]
        probing = discover_probes(node['cnf'], WIDTH, counts, _choices=selected)
        target, _ = check_probes(node['cnf'], probing, WIDTH, counts, _choices=selected)
        edge = None
        if probing['status'] == 'forced':
            _, names, key = h._canonical(target, node['depth'])
            edge = dict(key=key, names=names)
        record = dict(source=source, width=WIDTH, offset=offset, probing=probing, edge=edge)
        self.verify(h, record, counts)
        with h.db:
            h.db.execute(f'INSERT INTO {TABLE} VALUES (?,?)', (record_key(record), encode(record)))
        self.continuations[record_key(record)] = record
        self.verified.add(record_key(record))
        counts['new_probe_continuations'] += 1
        return 'probe_continuation', record, target


def search(h, root, routes, counts, *, source_limit=4, state_limit=32):
    for limit in (source_limit, state_limit):
        _limit(limit)
    h.set_admission_budget(state_limit)
    index = FrontierIndex(h)
    todo = deque(sorted(index.frontier(root)))
    seen = set(); visits = []; stop = None
    while todo and len(seen) < source_limit:
        source = todo.popleft()
        if source in seen:
            continue
        seen.add(source)
        kind, record, target = routes.advance(h, source, counts)
        visits.append(dict(source=source, kind=kind,
            offset=None if record is None else record.get('offset', 0)))
        if record is None or record['edge'] is None:
            continue
        try:
            edge = h._edge(target, h._load(source)['depth'])
        except AdmissionExhausted:
            stop = dict(source=source, reason='admission_limit'); break
        if edge != record['edge']:
            raise ValueError('Acquired residual differs from checked continuation')
        if kind == 'probe_window':
            routes.add_window(h, record)
        else:
            routes.add_continuation(h, record)
        todo.extendleft(reversed(sorted(index.frontier(edge['key']))))
    routes.refresh(h)
    counts.update(index.counts)
    return dict(visits=visits, budget_stop=stop, remaining_queued_sources=len(todo))
