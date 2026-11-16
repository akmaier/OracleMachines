"""Diagnostic and isolated history control; no inference-default change."""
from collections import Counter
import sqlite3
from experiments import compare_cnf_bootstrap as base


def candidates(session, source):
    """Compare existing ranking with distinct, currently uncovered obligations.

    Both ranks inspect checked stored structure only. Neither certifies closure
    nor predicts acquisition cost. The alternate rank is diagnostic, not applied.
    """
    closed = {session.coverage.keys[i] for i in session.coverage.justified}
    rows = []
    for identity in session.by_source.get(source, ()):
        record = session.records[identity]; remaining = set(); missing = 0
        children = [b['edge']['key'] for b in record['branches']]
        for key in children:
            if session.h._load(key) is None:
                missing += 1
            elif key not in closed:
                remaining.update(session.internal.frontier(key))
        remaining -= closed
        rows.append(dict(variable=record['variable'], identity_sha256=base.key_sha(identity),
            old_rank=list(session._rank(identity)),
            open_distinct_rank=[missing, session.internal.literals(Counter({k: 1 for k in remaining})), record['variable']],
            closed_children=[k in closed for k in children], distinct_open_leaves=len(remaining)))
    return rows


def restore_variant(checkpoint, path, source, *, ablate=False):
    """Restore a NEW experimental copy, optionally omitting this source's splits.

    restore_archive refuses an existing destination. The authority archive is
    never modified. No verifier or append-only session exists during omission;
    once opened, each variant follows the ordinary immutable-prefix contract.
    All pattern rows and all other split rows remain byte-identical.
    """
    if type(ablate) is not bool:
        raise ValueError('Boolean control flag required')
    base.restore_archive(checkpoint['archive'], path)
    db = sqlite3.connect(path)
    try:
        rows = list(db.execute(f'SELECT id,payload FROM {base.split.TABLE} ORDER BY rowid'))
        removed = []
        for identity, payload in rows:
            record = base.load_json(payload)
            if base.split.record_key(record) != identity:
                raise ValueError('Unbound control split record')
            if ablate and record['source'] == source:
                removed.append(identity)
        with db:
            db.executemany(f'DELETE FROM {base.split.TABLE} WHERE id=?', [(k,) for k in removed])
        return dict(omitted_pairs=len(removed), omitted_pair_ids=sorted(map(base.key_sha, removed)))
    finally:
        db.close()
