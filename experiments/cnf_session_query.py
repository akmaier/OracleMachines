"""Read global coverage from an exclusively owned expansion session.

Reuse requires immutable historical rows, checked objects and route objects.
The guard detects database/policy/sidecar/admission changes; it is not a hash of
all in-memory objects. Restart requires complete reconstruction and checking.
"""
from collections import Counter
from contextlib import contextmanager
import time

from experiments.cnf_expanded_coverage import verifier_views
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_projection_bridge import routes_for
from experiments.compare_cnf_incremental_coverage import full
from experiments.cnf_original_frontier import select


@contextmanager
def query_boundary(session, evidence, bridges):
    """Hold the database boundary without resetting the acquisition ledger."""
    h, m = session.h, session.maintenance
    db = h.db
    if db.in_transaction or any(v.active for _, v in verifier_views(h)):
        raise ValueError('Finish acquisition before querying the session')

    def check():
        if (db.execute('PRAGMA data_version').fetchone()[0] != m.version or
                db.execute('PRAGMA schema_version').fetchone()[0] != m.schema):
            raise ValueError('Changed external writer or schema; reopen checked state')
        if (db.total_changes != m.changes or h.admitted != m.admitted or
                encode([evidence, bridges]) != m.sidecars or
                session._config() != session.config):
            raise ValueError('Unmaintained session state; cannot query retained routes')

    db.execute('BEGIN IMMEDIATE')
    try:
        check()
        yield m.routes
        check()
    finally:
        db.rollback()


def query(session, evidence, bridges, roots, mode='maintained'):
    """Both modes fully compose and check plans; only catalog construction differs."""
    if mode not in ('rebuild', 'maintained'):
        raise ValueError('Unknown catalog mode')
    start = time.perf_counter()
    with query_boundary(session, evidence, bridges) as maintained:
        guard_seconds = time.perf_counter()-start
        tick = time.perf_counter()
        routes = routes_for(session.h, evidence, bridges) if mode == 'rebuild' else maintained
        r = dict(mode=mode, entry_guard_seconds=guard_seconds,
                 route_seconds=time.perf_counter()-tick)
        tick = time.perf_counter()
        closed, plans, counts = full(session.h, roots, routes)
        r.update(closed=closed, composition_seconds=time.perf_counter()-tick,
                 composition_counts=counts)
        tick = time.perf_counter(); counts = Counter()
        selected = select(session.h, routes, evidence, roots, closed[0], counts)
        r.update(selection_seconds=time.perf_counter()-tick, selection_counts=dict(counts))
    r.update(query_seconds=time.perf_counter()-start,
             checked_nodes=len(session.h.checked),
             prepared_checked_nodes=len(session.h.prepared.checked))
    return r, selected, plans
