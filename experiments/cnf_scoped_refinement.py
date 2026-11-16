"""Root-complete split checking over the full authoritative inventory.

Scan every split identity, but check its semantic certificate only when its
source is reachable from a requested root. All pattern lookups still use the
full database. This is a query view, not a whole-archive validity certificate.
Use the frozen independent full checker at the persistence boundary.
"""
from collections import Counter, defaultdict, deque
import json
from experiments.cnf_nested_refinement import NestedRefinement, base, FrontierIndex
from experiments.cnf_incremental_coverage import CoverageIndex
from experiments.cnf_route_composition import options
from experiments.cnf_split_registry import SplitRegistry


class ScopedSplitRegistry(SplitRegistry):
    def __init__(self, h, roots):
        self.roots = tuple(roots)
        self.index = defaultdict(list)
        self.indexed = set()
        super().__init__(h)

    def _register(self, identity, payload):
        # Index the whole append suffix, including currently unreachable pairs.
        record = json.loads(payload)
        if (type(record) is not dict or type(record.get('source')) is not str or
                type(record.get('variable')) is not int or
                base.split.record_key(record) != identity or identity in self.indexed):
            raise ValueError('Foreign or duplicate scoped split identity')
        self.index[record['source']].append(identity)
        self.indexed.add(identity)
        self.counts['scoped_indexed_records'] += 1
        self.counts['scoped_index_read_bytes'] += len(identity.encode()) + len(payload.encode())

    def refresh(self):
        # Retain the existing append-only, policy, schema and writer guards.
        super().refresh()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            if (self.db.execute('PRAGMA data_version').fetchone()[0] != self._version or
                    self.db.execute('PRAGMA schema_version').fetchone()[0] != self._schema):
                raise ValueError('Writer changed history between scope checks')
            todo = deque(self.roots); seen = set()
            while todo:
                source = todo.popleft()
                if source in seen:
                    continue
                seen.add(source)
                if self.h._load(source) is None:
                    raise ValueError('Missing scoped root or premise')
                for identity in self.index.get(source, ()):
                    if identity not in self._records:
                        row = self.db.execute(f'SELECT payload FROM {base.split.TABLE} WHERE id=?', (identity,)).fetchone()
                        if row is None:
                            raise ValueError('Missing indexed split')
                        SplitRegistry._register(self, identity, row[0])
                for _, children in options(self.h, source, self):
                    todo.extend(children)
            self.counts['scoped_reachable_visits'] += len(seen)
            self.reachable = seen
        except BaseException:
            self._valid = False
            raise
        finally:
            self.db.rollback()
        return self

    def statistics(self):
        data = super().statistics()
        data.update(indexed_records=len(self.indexed), reachable_sources=len(self.reachable),
                    deferred_records=len(self.indexed)-len(self._records),
                    index_json_bytes=len(base.encode(dict(self.index)).encode()))
        return data


class ScopedNestedRefinement(NestedRefinement):
    """Same scheduling and acquisition, with a root-complete checked catalog."""
    def __init__(self, h, root, decisions=None):
        self.h, self.root = h, root
        self.registry = ScopedSplitRegistry(h, [root])
        self.counts = Counter()
        self.coverage = CoverageIndex(h, [root], self.registry, self.counts)
        self.records = {}; self.by_source = defaultdict(list)
        self._sync_records()
        self.decisions = dict(decisions or {})
        for source, identity in self.decisions.items():
            if identity not in self.records or self.records[identity]['source'] != source:
                raise ValueError('Unbound saved refinement choice')
            if h._load(source)['kind'] != 'unresolved':
                raise ValueError('Refinement choice must name an unresolved source')
        self.internal = FrontierIndex(h)

    def _sync_records(self):
        for identity in self.registry._records:
            if identity not in self.records:
                row = self.h.db.execute(f'SELECT payload FROM {base.split.TABLE} WHERE id=?', (identity,)).fetchone()
                if row is None:
                    raise ValueError('Missing checked refinement record')
                self._remember(identity, json.loads(row[0]))

    def refresh(self):
        super().refresh()
        self._sync_records()
