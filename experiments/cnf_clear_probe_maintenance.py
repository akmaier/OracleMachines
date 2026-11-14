"""Retain a complete route catalog across an exclusively clear probe append.

This is an in-process optimization for one append-only SQLite inventory, not a
serialized trust cache. The caller supplies the complete route builder and all
five evidence lists plus bridges. Every other transition rebuilds that catalog.
External writers or schema changes require reopening the inventory: rebuilding
routes alone would not invalidate the inventory's own checked-node caches.
"""
from collections import Counter
import json

from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_window import verify_window, record_key as window_key
from experiments.cnf_probe_continuation import record_key as continuation_key

TABLES = {'probe_window': 'cnf_probe_windows_v1',
          'probe_continuation': 'cnf_probe_continuations_v1'}


class ClearProbeMaintenance:
    def __init__(self, h, evidence, bridges, builder):
        self.h, self.builder = h, builder
        self.routes = builder(h, evidence, bridges)
        self.sidecars = encode([evidence, bridges])
        self._snapshot()

    def _snapshot(self):
        db = self.h.db
        self.changes = db.total_changes
        self.version = db.execute('PRAGMA data_version').fetchone()[0]
        self.schema = db.execute('PRAGMA schema_version').fetchone()[0]
        self.admitted = set(self.h.admitted)
        self.last_rows = {kind: db.execute(f'SELECT coalesce(max(rowid),0) FROM {table}').fetchone()[0]
                          for kind, table in TABLES.items()}

    def refresh(self, operation, evidence, bridges):
        """Check the persisted delta, update clear metadata, or rebuild fully.

        Between snapshots, only the reported new clear row may be written for
        the fast path. A reused row must already match the complete catalog.
        total_changes also charges rolled-back writes, conservatively forcing a
        rebuild. No newly admitted node or changed sidecar can use the fast path.
        """
        h, db = self.h, self.h.db
        if (db.execute('PRAGMA data_version').fetchone()[0] != self.version or
                db.execute('PRAGMA schema_version').fetchone()[0] != self.schema):
            raise ValueError('Inventory changed externally or structurally; reopen checked state')
        sidecars = encode([evidence, bridges]); counts = Counter()
        inner = operation.get('operation') or {}
        kind, record = inner.get('kind'), inner.get('record')
        eligible = (operation.get('mode') == 'ordinary' and kind in TABLES and
                    isinstance(record, dict) and record.get('edge') is None and
                    record.get('probing', {}).get('status') == 'clear' and
                    operation.get('source') == record.get('source') and
                    not operation.get('added') and not operation.get('pending') and
                    h.admitted == self.admitted and sidecars == self.sidecars)
        if eligible:
            identity = (window_key if kind == 'probe_window' else continuation_key)(record)
            table = TABLES[kind]
            row = db.execute(f'SELECT rowid,payload FROM {table} WHERE id=?', (identity,)).fetchone()
            if row is None or row[1] != encode(record):
                raise ValueError('Reported clear row is not persisted exactly')
            records = self.routes.windows if kind == 'probe_window' else self.routes.continuations
            delta = db.total_changes - self.changes
            appended = delta == 1 and row[0] > self.last_rows[kind] and identity not in records
            reused = delta == 0 and records.get(identity) == record
            if appended or reused:
                # Use the original checkers, including every clear predecessor.
                if kind == 'probe_window':
                    verify_window(h, record, counts)
                else:
                    self.routes.verify(h, record, counts)
                records[identity] = json.loads(row[1])
                if kind == 'probe_continuation': self.routes.verified.add(identity)
                self._snapshot()
                return dict(mode='clear_append' if appended else 'clear_reuse', counts=dict(counts),
                            sidecar_snapshot_bytes=len(self.sidecars.encode()))
        self.routes = self.builder(h, evidence, bridges)
        self.sidecars = sidecars
        self._snapshot()
        return dict(mode='full_rebuild', counts=dict(self.routes.counts),
                    sidecar_snapshot_bytes=len(self.sidecars.encode()))
