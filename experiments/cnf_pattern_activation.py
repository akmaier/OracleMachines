"""Activate only routes affected by checked, append-only pattern acquisition.

This optional in-process helper binds the complete bridge-aware route builder.
Only pattern inserts and the reported split addition may use its fast path.
Other transitions retain the existing maintenance policy. Initial checking,
cold reconstruction and implicit node rules are unchanged. Single-writer,
immutable-row and caller-owned catalog contracts are required.
"""
from collections import Counter, defaultdict
import json

from experiments.compare_cnf_projection_bridge import routes_for
from experiments.cnf_pending_split_maintenance import PendingSplitMaintenance
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_trace_split import verify, record_key
from experiments.continue_cnf_original_splits import add_splits
from experiments.cnf_clear_probe_maintenance import TABLES
from experiments.cnf_probe_window import record_key as window_key
from experiments.cnf_probe_continuation import record_key as continuation_key

KINDS = ('pivot', 'coupled', 'growth', 'probe_window', 'probe_continuation',
         'trace_rewrite', 'trace_learning', 'learning_continuation', 'trace_split',
         'affine_clause', 'projection_bridge')
RANK = {kind: i for i, kind in enumerate(KINDS)}
SPLITS = ('early_saved_split', 'early_closed_split', 'split_after_ordinary_exhaustion', 'resume_split')


class PatternActivationMaintenance(PendingSplitMaintenance):
    def __init__(self, h, evidence, bridges, builder=routes_for):
        if builder is not routes_for:
            raise ValueError('Activation requires the complete supported route builder')
        super().__init__(h, evidence, bridges, builder)
        self._index(evidence)

    def _snapshot(self):
        super()._snapshot()
        self.pattern_rowid = self.h.db.execute('SELECT coalesce(max(rowid),0) FROM cnf_patterns_v1').fetchone()[0]

    def _track(self, kind, identity, source, children, ordinal, *, initial=False):
        token = (kind, identity)
        if token in self.order:
            return 0
        self.order[token] = (RANK[kind], ordinal)
        item = (dict(kind=kind, id=identity), children)
        missing = {key for key in children if self.h._load(key) is None}
        present = item in self.routes.by_source.get(source, [])
        if initial and present != (not missing):
            raise ValueError('Builder availability differs from activation contract')
        if missing:
            self.pending[token] = (source, item, missing)
            for key in missing:
                self.waiting[key].add(token)
            return 0
        if not initial:
            return self._attach(source, item)
        return 0

    def _attach(self, source, item):
        rows = self.routes.by_source[source]
        if item in rows:
            return 0
        rows.append(item)
        # Composition ties depend on the original builder's ordering.
        rows.sort(key=lambda row: self.order[(row[0]['kind'], row[0]['id'])])
        return 1

    def _index(self, evidence):
        self.order = {}; self.pending = {}; self.waiting = defaultdict(set)
        fixed = Counter()
        for rows in self.routes.by_source.values():
            for rule, _ in rows:
                kind = rule['kind']
                if kind not in RANK:
                    raise ValueError('Unsupported route kind')
                if kind in ('pivot', 'coupled', 'growth', 'affine_clause', 'projection_bridge'):
                    self.order[(kind, rule['id'])] = (RANK[kind], fixed[kind]); fixed[kind] += 1
        for kind, records in (
                ('probe_window', self.routes.windows),
                ('probe_continuation', self.routes.continuations),
                ('trace_rewrite', self.routes.rewrites),
                ('trace_learning', self.routes.learning),
                ('learning_continuation', self.routes.learned_blocks.records)):
            for i, (identity, record) in enumerate(records.items()):
                if record['edge'] is None:
                    continue
                source = (self.routes.learned_blocks.bases[record['base_sha256']]['source']
                          if kind == 'learning_continuation' else record['source'])
                self._track(kind, identity, source, [record['edge']['key']], i, initial=True)
        for i, record in enumerate(evidence[3]):
            self._track('trace_split', record_key(record), record['source'],
                        [e['key'] for e in record['edges']], i, initial=True)

    def statistics(self):
        return dict(indexed_routes=len(self.order), pending_routes=len(self.pending),
                    waiting_targets=len(self.waiting), waiting_links=sum(map(len, self.waiting.values())))

    def refresh(self, operation, evidence, bridges):
        h, db = self.h, self.h.db
        if (db.execute('PRAGMA data_version').fetchone()[0] != self.version or
                db.execute('PRAGMA schema_version').fetchone()[0] != self.schema):
            raise ValueError('Inventory changed externally or structurally; reopen checked state')
        added = operation.get('added'); mode = operation.get('mode')
        admission_ok = (self.admitted <= h.admitted and isinstance(added, list) and
            all(isinstance(key, str) for key in added) and len(added) == len(set(added)) and
            set(added) == h.admitted-self.admitted)
        old_evidence, old_bridges = json.loads(self.sidecars)
        supplied = encode([evidence, bridges]); counts = Counter(); record = operation.get('record')
        eligible = False
        if admission_ok and mode in SPLITS and isinstance(record, dict) and operation.get('source') == record.get('source'):
            verify(h, record, counts)
            eligible = supplied == encode([add_splits(old_evidence, [record]), old_bridges])
        elif admission_ok and mode == 'ordinary' and supplied == self.sidecars:
            inner = operation.get('operation') or {}; kind = inner.get('kind'); ordinary = inner.get('record')
            if kind in TABLES and isinstance(ordinary, dict) and operation.get('source') == ordinary.get('source'):
                identity = (window_key if kind == 'probe_window' else continuation_key)(ordinary)
                records = self.routes.windows if kind == 'probe_window' else self.routes.continuations
                eligible = records.get(identity) == ordinary
        rows = []
        if eligible:
            rows = list(db.execute('SELECT id FROM cnf_patterns_v1 WHERE rowid>? ORDER BY rowid', (self.pattern_rowid,)))
            keys = {row[0] for row in rows}
            # total_changes charges every insert/update/delete, including rolled
            # back writes. Equality excludes other writes on this connection.
            eligible = (db.total_changes-self.changes == len(rows) and keys <= h.admitted)
        if eligible:
            for key, in rows:
                if h._load(key) is None:
                    raise ValueError('Missing inserted pattern')
                counts['checked_inserted_patterns'] += 1
            affected = set()
            for key, in rows:
                affected.update(self.waiting.get(key, ()))
            activated = 0
            for token in sorted(affected, key=self.order.__getitem__):
                source, item, missing = self.pending[token]
                acquired = {key for key in missing if h._load(key) is not None}
                for key in acquired:
                    self.waiting[key].remove(token)
                    if not self.waiting[key]:
                        del self.waiting[key]
                missing.difference_update(acquired)
                if not missing:
                    del self.pending[token]; activated += self._attach(source, item)
            if mode in SPLITS:
                activated += self._track('trace_split', record_key(record), record['source'],
                    [e['key'] for e in record['edges']], len(old_evidence[3]))
            self.sidecars = supplied; self._snapshot()
            return dict(mode='pattern_activation', counts=dict(counts), inserted_patterns=len(rows),
                affected_routes=len(affected), activated_routes=activated,
                sidecar_snapshot_bytes=len(supplied.encode()), **self.statistics())
        result = super().refresh(operation, evidence, bridges)
        # Fallback may add probe metadata or arbitrary checked sidecars.
        self._index(evidence)
        return dict(result, **self.statistics())
