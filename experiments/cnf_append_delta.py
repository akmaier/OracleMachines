"""Export a guarded append suffix of one exclusively owned SQLite connection.

The caller starts from a verified parent snapshot and owns ordinary SQL writes
on this connection. This is not a persistent trust marker or protection against
raw file tampering. Cold conflict checks and certificate verification remain.
"""
from pathlib import Path
import sqlite3
import time

from experiments.compare_cnf_probe_continuation import TABLES, compressed, sha


class AppendDelta:
    def __init__(self, db):
        self.db = db
        if db.in_transaction:
            raise ValueError('Commit acquisition before taking an export boundary')
        db.execute('BEGIN IMMEDIATE')
        try:
            tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if not set(TABLES) <= tables:
                raise ValueError('Missing export tables')
            # Historical solver tables are outside the delta format. Any
            # ordinary write to them increases total_changes without adding
            # an exported suffix row and therefore fails the export guard.
            self.legacy_tables = sorted(tables-set(TABLES))
            for t in TABLES:
                info = list(db.execute(f'PRAGMA table_info({t})'))
                if info != [(0, 'id', 'TEXT', 0, None, 1), (1, 'payload', 'TEXT', 1, None, 0)]:
                    raise ValueError('Unsupported export columns')
            self.version = db.execute('PRAGMA data_version').fetchone()[0]
            self.schema = db.execute('PRAGMA schema_version').fetchone()[0]
            self.changes = db.total_changes
            self.preserved = {t: db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES}
            self.boundaries = {t: db.execute(f'SELECT coalesce(max(rowid),0) FROM {t}').fetchone()[0] for t in TABLES}
        finally:
            db.rollback()

    def save(self, delta, archive):
        """Keep the boundary reusable; include every committed append since it."""
        started = time.perf_counter(); db = self.db
        delta, archive = Path(delta), Path(archive)
        if delta.exists() or archive.exists():
            raise ValueError('Delta output already exists')
        if db.in_transaction:
            raise ValueError('Commit acquisition before exporting')
        db.execute('BEGIN IMMEDIATE')
        try:
            if (db.execute('PRAGMA data_version').fetchone()[0] != self.version or
                    db.execute('PRAGMA schema_version').fetchone()[0] != self.schema):
                raise ValueError('Changed external writer or schema; use full comparison')
            added = {t: db.execute(f'SELECT count(*) FROM {t} WHERE rowid>?', (self.boundaries[t],)).fetchone()[0]
                     for t in TABLES}
            totals = {t: db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES}
            if (db.total_changes-self.changes != sum(added.values()) or
                    any(totals[t] != self.preserved[t]+added[t] for t in TABLES)):
                raise ValueError('Non-append writes; use full comparison')
            # The counts also reject REPLACE moving an old key past the boundary:
            # such a row does not increase its table's total cardinality.
            out = sqlite3.connect(delta)
            try:
                with out:
                    for t in TABLES:
                        out.execute(f'CREATE TABLE {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                        out.executemany(f'INSERT INTO {t} VALUES (?,?)', db.execute(
                            f'SELECT id,payload FROM {t} WHERE rowid>? ORDER BY rowid', (self.boundaries[t],)))
            finally:
                out.close()
        finally:
            db.rollback()
        compressed(delta, archive)
        return dict(path=str(archive), sha256=sha(archive), database_sha256=sha(delta),
            database_bytes=delta.stat().st_size, compressed_bytes=archive.stat().st_size,
            seconds=time.perf_counter()-started, preserved_rows=dict(self.preserved), added_rows=added,
            export_mode='append_suffix', boundary_rowids=dict(self.boundaries),
            unchanged_legacy_tables=list(self.legacy_tables),
            rows_exported=sum(added.values()), writer_changes=db.total_changes-self.changes)
