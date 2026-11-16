"""Incremental checked bootstrap routes on one exclusive append-only inventory.

No closure bit or serialized cache is trusted. Refresh before composing coverage;
the ordinary positive checker remains the cold authority. Mutation of inventory
objects, raw database files or SQLite pragmas is outside this live-cache contract.
Other writers, policy/schema changes and non-append SQL writes invalidate it.
"""
from collections import Counter, defaultdict
import json
from experiments import cnf_bootstrap_conditioning as split
from experiments.cnf_pattern_inventory import encode

PATTERNS = 'cnf_patterns_v1'
TABLES = (PATTERNS, split.TABLE)


class SplitRegistry:
    def __init__(self, h):
        self.h, self.db, self.policy = h, h.db, encode(h.config)
        self.by_source = defaultdict(list)
        self.counts = Counter()
        self._records = {}  # identity -> (insertion order, source, ordered children)
        self._missing = {}
        self._waiting = defaultdict(set)
        self._valid = True
        self._boundary = None
        self.refresh()

    def _register(self, identity, payload):
        record = json.loads(payload)
        if split.record_key(record) != identity or identity in self._records:
            raise ValueError('Duplicate or foreign persisted split')
        split.verify(self.h, record, self.counts)
        children = tuple(branch['edge']['key'] for branch in record['branches'])
        missing = {key for key in children if self.h._load(key) is None}
        self._records[identity] = (len(self._records), record['source'], children)
        self._missing[identity] = missing
        for key in missing:
            self._waiting[key].add(identity)
        self.counts['registry_verified_records'] += 1
        self.counts['registry_pair_read_bytes'] += len(identity.encode()) + len(payload.encode())
        if not missing:
            self._activate(identity)

    def _activate(self, identity):
        _, source, children = self._records[identity]
        self.by_source[source].append((dict(kind=split.KIND, id=identity), list(children)))
        # Preserve the frozen builder's insertion order even if an earlier pair
        # becomes available only after a later pair was activated.
        self.by_source[source].sort(key=lambda row: self._records[row[0]['id']][0])
        del self._missing[identity]
        self.counts['registry_activated_records'] += 1

    def refresh(self):
        """Audit the append suffix and check only newly persisted split records.

        Count/rowid guards still read table index pages. Recognizer work, ordinary
        plan composition and final proof replay are unchanged, not amortized away.
        Any failure invalidates this registry; reopen the checked inventory.
        """
        if not self._valid:
            raise ValueError('Invalidated split registry; reopen checked inventory')
        db = self.db
        if self.h.db is not db or encode(self.h.config) != self.policy or db.in_transaction:
            self._valid = False
            raise ValueError('Changed inventory/policy or uncommitted acquisition')
        db.execute('BEGIN IMMEDIATE')
        try:
            version = db.execute('PRAGMA data_version').fetchone()[0]
            schema = db.execute('PRAGMA schema_version').fetchone()[0]
            if self._boundary is not None and (version != self._version or schema != self._schema):
                raise ValueError('External writer or schema change; reopen checked inventory')
            boundaries = self._boundary or {t: 0 for t in TABLES}
            patterns = list(db.execute(f'SELECT rowid,id FROM {PATTERNS} WHERE rowid>? ORDER BY rowid',
                                       (boundaries[PATTERNS],)))
            pairs = list(db.execute(f'SELECT rowid,id,payload FROM {split.TABLE} WHERE rowid>? ORDER BY rowid',
                                    (boundaries[split.TABLE],)))
            totals = {t: db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES}
            added = {PATTERNS: len(patterns), split.TABLE: len(pairs)}
            if self._boundary is not None and (
                    db.total_changes - self._changes != sum(added.values()) or
                    any(totals[t] != self._totals[t] + added[t] for t in TABLES)):
                raise ValueError('Non-append or unrelated writes; reopen checked inventory')
            for _, identity, payload in pairs:
                self._register(identity, payload)
            for _, key in patterns:
                dependents = self._waiting.pop(key, ())
                if dependents and self.h._load(key) is None:
                    raise ValueError('Missing appended child')
                for identity in dependents:
                    self._missing[identity].remove(key)
                    self.counts['registry_pending_notifications'] += 1
                    if not self._missing[identity]:
                        self._activate(identity)
            self._boundary = {
                PATTERNS: patterns[-1][0] if patterns else boundaries[PATTERNS],
                split.TABLE: pairs[-1][0] if pairs else boundaries[split.TABLE],
            }
            self._totals, self._changes = totals, db.total_changes
            self._version, self._schema = version, schema
            self.counts['registry_refreshes'] += 1
            self.counts['registry_pattern_suffix_rows'] += len(patterns)
        except BaseException:
            self._valid = False
            raise
        finally:
            db.rollback()
        return self

    def statistics(self):
        """Logical live metadata size, not peak RAM or a trusted restore format."""
        payload = [list(self._records.items()), list(self._missing.items()),
                   list(self._waiting.items()), list(self.by_source.items())]
        encoded = json.dumps(payload, default=lambda value: sorted(value), sort_keys=True)
        return dict(records=len(self._records), active_records=len(self._records)-len(self._missing),
                    pending_records=len(self._missing), pending_child_keys=len(self._waiting),
                    pending_dependencies=sum(map(len, self._missing.values())),
                    metadata_json_bytes=len(encoded.encode()), counts=dict(self.counts))
