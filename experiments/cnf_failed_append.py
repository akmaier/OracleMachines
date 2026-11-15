"""Preserve committed evidence after a worker failure without trusting it.

An available copied seed permits full comparison; otherwise the ordinary-write
append guard exports the suffix. Rejected boundaries fall back to a complete
SQLite backup for inspection. None of these failure artifacts is a checkpoint.
"""
from pathlib import Path
import sqlite3

from experiments.compare_cnf_split_batch import save_delta
from experiments.compare_cnf_probe_continuation import compressed, sha


def preserve_failure(out, tmp, h, history, seed, boundary):
    out, tmp, seed = Path(out), Path(tmp), Path(seed)
    rolled_back = h.db.in_transaction
    if rolled_back:
        h.db.rollback()
    result = dict(verified_checkpoint=False, rolled_back_uncommitted=rolled_back)
    try:
        if seed.exists():
            delta = save_delta(seed, history, tmp/'failed-delta', out/'failed-proof-delta.sqlite3.gz')
        elif boundary is not None:
            delta = boundary.save(tmp/'failed-delta', out/'failed-proof-delta.sqlite3.gz')
        else:
            raise ValueError('No established append boundary')
        result.update(kind='unchecked_delta', delta=delta)
    except Exception as exc:
        # Raw backup is evidence for inspection, not authority for automatic replay.
        path = tmp/'failed-history'; archive = out/'failed-history.sqlite3.gz'
        with sqlite3.connect(path) as db:
            h.db.backup(db)
        compressed(path, archive)
        result.update(kind='unchecked_snapshot', rejection=type(exc).__name__+': '+str(exc)[:500],
                      snapshot=dict(path=str(archive), sha256=sha(archive),
                                    database_sha256=sha(path), database_bytes=path.stat().st_size,
                                    compressed_bytes=archive.stat().st_size))
    return result
