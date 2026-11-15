"""Optional byte-bound snapshots of an independently checked acquisition history.

The descriptor hash is supplied by the caller's trusted experiment report, not
by the cache. A hash authenticates bytes only relative to that trust anchor.
Publication requires a closed, exclusively owned database reconstructed by the
authoritative restorer. This module does not certify arbitrary input databases.
No Python verifier objects or negative-frontier answers are persisted.
"""
from collections import Counter
import gzip
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from experiments.continue_cnf_retained_discovery import (
    BudgetedInventory, digests, read_archive, verify_bridge, verify_positive)
from experiments.cnf_pattern_inventory import encode

FORMAT = 'materialized-cnf-checkpoint-v1'
BLOCK = 1024 * 1024


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(BLOCK), b''): h.update(block)
    return h.hexdigest()


def bound_parent(path, expected):
    if sha(path) != expected: raise ValueError('Changed checkpoint parent')
    parent = json.loads(Path(path).read_text())
    for name, digest in parent['fingerprints'].items():
        if sha(name) != digest: raise ValueError('Changed checkpoint implementation')
    return parent


def verify_checkpoint(path, parent, evidence, bridges):
    if len(evidence) != 5 or list(map(len, evidence)) != parent['evidence_counts_after']:
        raise ValueError('Incorrect checkpoint evidence groups')
    if bridges != read_archive(parent['bridges']):
        raise ValueError('Incorrect checkpoint bridges')
    h = BudgetedInventory(path, **parent['options']); h.set_admission_budget(0)
    try:
        counts = Counter()
        for record in bridges: verify_bridge(h, record, counts)
        roots = [h._canonical(c['source'], h.config['max_depth'])[2]
                 for c, b in zip(parent['cases'], parent['final_closed'], strict=True) if b]
        verify_positive(h, read_archive(parent['expanded_certificate']), roots,
                        evidence, bridges, counts)
        if h.admitted: raise ValueError('Checkpoint verification acquired new states')
        return dict(counts)
    finally: h.close()


def _publish(source, cache):
    """Stream gzip to a content-addressed file; never replace existing bytes."""
    raw_hash = hashlib.sha256(); size = 0
    with tempfile.TemporaryDirectory(dir=cache) as td:
        packed = Path(td)/'object'
        with open(source, 'rb') as inp, open(packed, 'wb') as out:
            with gzip.GzipFile(filename='', mode='wb', fileobj=out, compresslevel=1, mtime=0) as z:
                for block in iter(lambda: inp.read(BLOCK), b''):
                    raw_hash.update(block); size += len(block); z.write(block)
        digest = sha(packed); target = cache/(digest+'.gz')
        try: os.link(packed, target)
        except FileExistsError:
            if sha(target) != digest: raise ValueError('Corrupt existing cache object')
        return dict(name=target.name, sha256=digest, compressed_bytes=packed.stat().st_size,
                    bytes=size, raw_sha256=raw_hash.hexdigest())


def materialize(history, evidence, bridges, parent_path, parent_sha256, cache_dir):
    """Caller first runs the frozen restorer; charge that work separately."""
    started = time.perf_counter(); cache = Path(cache_dir); cache.mkdir(parents=True, exist_ok=True)
    parent = bound_parent(parent_path, parent_sha256)
    for suffix in ('-wal', '-journal'):
        side = Path(str(history)+suffix)
        if side.exists() and side.stat().st_size:
            raise ValueError('Close and checkpoint database before materialization')
    before = sha(history)
    if digests(history) != parent['logical_table_digests']:
        raise ValueError('Incorrect materialized history')
    checks = verify_checkpoint(history, parent, evidence, bridges)
    descriptor = dict(format=FORMAT, parent=dict(path=str(parent_path), sha256=parent_sha256),
                      options=parent['options'], table_digests=parent['logical_table_digests'])
    descriptor['database'] = _publish(history, cache)
    with tempfile.TemporaryDirectory() as td:
        side = Path(td)/'evidence.json'
        side.write_text(encode(dict(evidence=evidence, bridges=bridges))+'\n')
        descriptor['evidence'] = _publish(side, cache)
    if sha(history) != before or descriptor['database']['raw_sha256'] != before:
        raise ValueError('History changed during materialization')
    return descriptor, dict(seconds=time.perf_counter()-started, positive_checks=checks,
                            cached_bytes=sum(descriptor[k]['compressed_bytes'] for k in ('database','evidence')))


def _descriptor(path, expected, parent_path, parent_sha256):
    if sha(path) != expected: raise ValueError('Changed trusted snapshot descriptor')
    d = json.loads(Path(path).read_text())
    parent = bound_parent(parent_path, parent_sha256)
    if (d['format'] != FORMAT or d['parent'] != dict(path=str(parent_path), sha256=parent_sha256)
            or d['options'] != parent['options'] or d['table_digests'] != parent['logical_table_digests']):
        raise ValueError('Snapshot parent, policy or table binding mismatch')
    for kind in ('database', 'evidence'):
        obj = d[kind]
        if obj['name'] != obj['sha256']+'.gz' or len(obj['sha256']) != 64 or any(
                c not in '0123456789abcdef' for c in obj['sha256']):
            raise ValueError('Invalid content-addressed cache name')
    return d, parent


def _unpack(obj, cache, dest):
    source = cache/obj['name']
    if source.stat().st_size != obj['compressed_bytes'] or sha(source) != obj['sha256']:
        raise ValueError('Corrupt materialized archive')
    digest = hashlib.sha256(); size = 0
    with gzip.open(source, 'rb') as inp, open(dest, 'xb') as out:
        for block in iter(lambda: inp.read(BLOCK), b''):
            size += len(block)
            if size > obj['bytes']: raise ValueError('Oversized materialized object')
            digest.update(block); out.write(block)
    if size != obj['bytes'] or digest.hexdigest() != obj['raw_sha256']:
        raise ValueError('Incorrect full materialized byte identity')


def restore_cached(descriptor_path, descriptor_sha256, parent_path, parent_sha256,
                   cache_dir, destination, tmp, fallback, metrics=None):
    """Restore checked bytes, or use the authoritative restorer on cache absence.

    Corruption is an error, not a cache miss. The destination must not exist.
    Positive verification is repeated; complete catalog/frontier querying is a
    separate caller obligation. Exclusive ownership excludes concurrent writers.
    """
    started = time.perf_counter(); m = metrics if metrics is not None else {}
    destination = Path(destination); cache = Path(cache_dir)
    if destination.exists(): raise ValueError('Checkpoint destination already exists')
    d, parent = _descriptor(descriptor_path, descriptor_sha256, parent_path, parent_sha256)
    m['binding_seconds'] = time.perf_counter()-started
    if any(not (cache/d[k]['name']).exists() for k in ('database','evidence')):
        m['mode'] = 'authoritative-fallback'
        result = fallback(parent_path, destination, tmp)
        m['seconds'] = time.perf_counter()-started
        return result
    m['mode'] = 'materialized'
    # Database bytes, including schema/triggers, are checked before SQLite opens.
    with tempfile.TemporaryDirectory(dir=destination.parent) as td:
        work = Path(td); db = work/'history'; side = work/'evidence'
        tick = time.perf_counter()
        _unpack(d['database'], cache, db); _unpack(d['evidence'], cache, side)
        m['unpack_seconds'] = time.perf_counter()-tick
        payload = json.loads(side.read_text()); evidence = payload['evidence']; bridges = payload['bridges']
        tick = time.perf_counter()
        if digests(db) != parent['logical_table_digests']:
            raise ValueError('Incorrect materialized tables')
        m['table_check_seconds'] = time.perf_counter()-tick
        tick = time.perf_counter()
        m['positive_checks'] = verify_checkpoint(db, parent, evidence, bridges)
        m['positive_seconds'] = time.perf_counter()-tick
        # The checker is read-only on a complete checkpoint. Detect own writes.
        tick = time.perf_counter()
        if sha(db) != d['database']['raw_sha256']:
            raise ValueError('Verification changed materialized database')
        os.link(db, destination)
        m['final_identity_seconds'] = time.perf_counter()-tick
    m['seconds'] = time.perf_counter()-started
    return parent, *evidence
