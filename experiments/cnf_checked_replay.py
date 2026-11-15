"""Reuse checked immutable rows across conflict-checked checkpoint appends.

The caller supplies a reconstructed, identity-bound parent and exclusively owns
the database and checked objects. This is live reuse, not a persisted trust bit.
Full report/archive/table digests and positive coverage checks remain external.
"""
from collections import Counter
import json
from pathlib import Path
import sqlite3

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_expanded_coverage import verifier_views
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_source_local import TABLES, SourceProbeRoutes, window_key, verify_window, continuation_key
from experiments.compare_cnf_probe_continuation import TABLES as DELTA_TABLES


def check_delta_in_inventory(h, delta):
    """Same obligations as the frozen cold checker, against a live inventory."""
    counts = Counter()
    db = sqlite3.connect(Path(delta).resolve().as_uri()+'?mode=ro', uri=True)
    try:
        for table in TABLES:
            for key, payload in db.execute(f'SELECT id,payload FROM {table} ORDER BY id'):
                actual = h.db.execute(f'SELECT payload FROM {table} WHERE id=?', (key,)).fetchone()
                if actual != (payload,):
                    raise ValueError('Delta differs from merged row')
                record = json.loads(payload)
                if table == 'cnf_patterns_v1':
                    if h._load(key) is None:
                        raise ValueError('Missing new node')
                elif table == 'cnf_probe_windows_v1':
                    if window_key(record) != key:
                        raise ValueError('Invalid window identity')
                    verify_window(h, record, counts)
                elif table == 'cnf_probe_continuations_v1':
                    if continuation_key(record) != key:
                        raise ValueError('Invalid continuation identity')
                    SourceProbeRoutes(h, record['source'])._verify_saved(h, key, counts)
                else:
                    raise ValueError('Unsupported new source-local record kind')
                counts['checked_delta_rows'] += 1
        for table in set(DELTA_TABLES)-set(TABLES):
            if db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]:
                raise ValueError('Source-local delta cannot introduce other record types')
        if h.admitted:
            raise ValueError('Delta checking performed recognition')
    finally:
        db.close()
    return dict(counts)


class CheckedReplay:
    """Only checked append merges may change the exclusively owned connection.

    External writers, direct same-connection writes, policy/schema changes,
    unfinished checking and failed operations invalidate this instance. Cached
    Python objects must remain immutable; guards do not hash in-memory objects
    or protect against raw-file edits or forged SQLite pragmas.
    """
    def __init__(self, path, options):
        self.h = BudgetedInventory(path, **options)
        self.h.set_admission_budget(0)
        self.valid = True
        self.config = self._config()
        self._snapshot()

    def _config(self):
        return encode([(name, view.config) for name, view in verifier_views(self.h)])

    def _snapshot(self):
        db = self.h.db
        self.version = db.execute('PRAGMA data_version').fetchone()[0]
        self.schema = db.execute('PRAGMA schema_version').fetchone()[0]
        self.changes = db.total_changes

    def _begin(self):
        if not self.valid or self.h is None:
            raise ValueError('Discard invalid or transferred replay state')
        h, db = self.h, self.h.db
        if db.in_transaction or h.admitted or any(v.active for _, v in verifier_views(h)):
            self.valid = False
            raise ValueError('Finish writes/checks before replay')
        db.execute('BEGIN IMMEDIATE')
        if (db.execute('PRAGMA data_version').fetchone()[0] != self.version or
                db.execute('PRAGMA schema_version').fetchone()[0] != self.schema or
                db.total_changes != self.changes or self._config() != self.config):
            db.rollback(); self.valid = False
            raise ValueError('Changed replay authority or policy')

    def merge(self, delta):
        """Check a suffix atomically; failed suffixes never leave reusable state."""
        self._begin()
        db = self.h.db
        source = None
        try:
            source = sqlite3.connect(Path(delta).resolve().as_uri()+'?mode=ro', uri=True)
            added = 0
            for table in DELTA_TABLES:
                for key, payload in source.execute(f'SELECT id,payload FROM {table} ORDER BY rowid'):
                    old = db.execute(f'SELECT payload FROM {table} WHERE id=?', (key,)).fetchone()
                    if old is not None:
                        if old != (payload,):
                            raise ValueError('Conflicting checkpoint row')
                    else:
                        db.execute(f'INSERT INTO {table} VALUES (?,?)', (key, payload))
                        added += 1
            result = check_delta_in_inventory(self.h, delta)
            if (db.total_changes-self.changes != added or self._config() != self.config or
                    db.execute('PRAGMA schema_version').fetchone()[0] != self.schema):
                raise ValueError('Unexpected writes while replaying')
            db.commit(); self.changes = db.total_changes
            return dict(result, appended_rows=added)
        except BaseException:
            db.rollback(); self.valid = False
            raise
        finally:
            if source is not None:
                source.close()

    def check(self, action):
        """Check fresh evidence while retaining already verified dependencies."""
        self._begin()
        try:
            result = action(self.h)
            if self.h.db.total_changes != self.changes or self.h.admitted or self._config() != self.config:
                raise ValueError('Verification changed replay state')
            return result
        except BaseException:
            self.valid = False
            raise
        finally:
            self.h.db.rollback()

    def handoff(self):
        """Transfer the live verifier; no complete frontier is implied."""
        self.check(lambda h: None)
        h = self.h
        self.h = None; self.valid = False
        return h

    def close(self):
        if self.h is not None:
            self.h.close(); self.h = None
        self.valid = False
