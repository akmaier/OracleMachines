"""Reuse key-ordered table hashes on one exclusively owned SQLite connection.

Initial hashes are computed here, never accepted from a caller or disk. Between
snapshots only committed append writes are supported. Invalidated instances must
be discarded. This is live bookkeeping, not certificate verification or a
defence against raw-file modification or deliberately falsified SQLite pragmas.
"""
import copy
import time

from experiments.compare_cnf_probe_continuation import TABLES
from experiments.compare_cnf_clause_mask import table_digest


class GuardedDigests:
    def __init__(self, db):
        self.db = db
        self._digests = None
        self._valid = True

    def snapshot(self):
        """Return fresh-equivalent digests, plus charged scan/guard statistics.

        Count and rowid guards still read index pages. Changed tables are hashed
        in their entirety in key order; this is not a suffix-hash algorithm.
        """
        started = time.perf_counter()
        db = self.db
        if not self._valid:
            raise ValueError('Invalidated digest cache; reconstruct it')
        if db.in_transaction:
            raise ValueError('Commit acquisition before taking a digest snapshot')
        db.execute('BEGIN IMMEDIATE')
        try:
            version = db.execute('PRAGMA data_version').fetchone()[0]
            schema = db.execute('PRAGMA schema_version').fetchone()[0]
            if self._digests is None:
                tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if not set(TABLES) <= tables:
                    raise ValueError('Missing digest tables')
                for t in TABLES:
                    if list(db.execute(f'PRAGMA table_info({t})')) != [
                            (0, 'id', 'TEXT', 0, None, 1), (1, 'payload', 'TEXT', 1, None, 0)]:
                        raise ValueError('Unsupported digest columns')
                added = None
            else:
                if version != self._version or schema != self._schema:
                    raise ValueError('Changed external writer or schema; reconstruct digests')
                added = {t: db.execute(f'SELECT count(*) FROM {t} WHERE rowid>?',
                                     (self._boundaries[t],)).fetchone()[0] for t in TABLES}
            totals = {t: db.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in TABLES}
            boundaries = {t: db.execute(f'SELECT coalesce(max(rowid),0) FROM {t}').fetchone()[0] for t in TABLES}
            if added is not None and (db.total_changes-self._changes != sum(added.values()) or
                    any(totals[t] != self._totals[t]+added[t] for t in TABLES)):
                raise ValueError('Non-append writes; reconstruct digests')
            guard_seconds = time.perf_counter()-started
            scanned = [t for t in TABLES if added is None or added[t]]
            reused = [t for t in TABLES if t not in scanned]
            fresh = {} if self._digests is None else copy.deepcopy(self._digests)
            scans = {}
            for t in scanned:
                tick = time.perf_counter()
                fresh[t] = table_digest(db, t)
                scans[t] = time.perf_counter()-tick
                if fresh[t]['rows'] != totals[t]:
                    raise ValueError('Inconsistent digest snapshot')
            self._digests = fresh
            self._version, self._schema, self._changes = version, schema, db.total_changes
            self._totals, self._boundaries = totals, boundaries
            result = copy.deepcopy(fresh)
        except BaseException:
            self._valid = False
            raise
        finally:
            db.rollback()
        return result, dict(seconds=time.perf_counter()-started, guard_seconds=guard_seconds,
            scan_seconds=scans, scanned_tables=scanned, reused_tables=reused,
            added_rows=added, scanned_rows=sum(totals[t] for t in scanned),
            reused_rows=sum(totals[t] for t in reused))
