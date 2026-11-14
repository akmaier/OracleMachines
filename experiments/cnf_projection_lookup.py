"""Find retained projection targets by minimal-clause signatures.

The SQLite index is a proposal cache, never a proof or a closed-world oracle.
Every accepted hit is replayed by the existing projection bridge checker.
"""
from collections import Counter
import hashlib
import json
import sqlite3
import zlib

from experiments.cnf_anchored_subsets import anchored_certificate
from experiments.cnf_pattern_inventory import FORMAT as PATTERN, encode
from experiments.cnf_projection_bridge import (FORMAT as BRIDGE, canonical,
    projection, verify, record_key)
from experiments.cnf_variable_elimination import _limit

FORMAT = 'projection-kernel-index-v1'


def kernel(cnf, counts):
    certificate = anchored_certificate(cnf, counts)
    return tuple(tuple(cnf[i]) for i in certificate['kept'])


def signature(depth, support, core, counts):
    payload = encode([depth, support, core]).encode()
    counts['signature_bytes'] += len(payload)
    return hashlib.sha256(payload).digest()


class KernelIndex:
    def __init__(self, path, config):
        self.config = json.loads(encode(config))
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS metadata (id INTEGER PRIMARY KEY, value TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS targets (id BLOB PRIMARY KEY, kernel BLOB NOT NULL, clauses INTEGER NOT NULL, payload BLOB NOT NULL)')
        self.db.execute('CREATE INDEX IF NOT EXISTS target_kernels ON targets(kernel, id)')
        expected = encode([FORMAT, config])
        saved = self.db.execute('SELECT value FROM metadata WHERE id=1').fetchone()
        if saved is not None and saved[0] != expected:
            self.db.close()
            raise ValueError('Projection index policy mismatch')
        self.db.execute('INSERT OR IGNORE INTO metadata VALUES(1, ?)', (expected,))
        self.db.commit()

    def close(self):
        self.db.close()

    def add(self, key, counts):
        """Append one acquired key; old records are immutable and deduplicated."""
        fmt, config, depth, cnf = json.loads(key)
        if fmt != PATTERN or config != self.config:
            counts['index_policy_skips'] += 1
            return False
        if type(depth) is not int or depth < 0:
            raise ValueError('Invalid index depth')
        ident = hashlib.sha256(key.encode()).digest()
        previous = self.db.execute('SELECT payload FROM targets WHERE id=?', (ident,)).fetchone()
        if previous:
            if zlib.decompress(previous[0]).decode() != key:
                raise ValueError('Projection index key digest collision')
            counts['index_duplicate_keys'] += 1
            return False
        support = canonical(cnf, counts)
        core = kernel(cnf, counts)
        sig = signature(depth, support, core, counts)
        payload = zlib.compress(key.encode())
        self.db.execute('INSERT INTO targets VALUES(?,?,?,?)', (ident, sig, len(cnf), payload))
        counts['index_added_keys'] += 1
        counts['index_key_bytes'] += len(key.encode())
        counts['index_compressed_key_bytes'] += len(payload)
        counts['index_kernel_clauses'] += len(core)
        return True

    def candidates(self, sig, max_clauses, limit, counts, *, mode='indexed'):
        _limit(limit)
        counts['target_lookups'] += 1
        if mode == 'indexed':
            rows = self.db.execute('SELECT id,payload FROM targets WHERE kernel=? AND clauses<=? ORDER BY id LIMIT ?',
                                   (sig, max_clauses, limit))
        elif mode == 'scan':
            # Same prepared signatures, deterministic order and proof checker.
            # Only candidate selection changes; no repeated kernel construction.
            def scan():
                emitted = 0
                for ident, stored, clauses in self.db.execute('SELECT id,kernel,clauses FROM targets ORDER BY id'):
                    counts['scan_entries'] += 1
                    if stored == sig and clauses <= max_clauses:
                        if emitted >= limit: break
                        payload = self.db.execute('SELECT payload FROM targets WHERE id=?', (ident,)).fetchone()[0]
                        emitted += 1
                        yield ident, payload
            rows = scan()
        else:
            raise ValueError('Unknown projection lookup mode')
        for ident, payload in rows:
            counts['target_candidate_entries'] += 1
            key = zlib.decompress(payload).decode()
            counts['candidate_decompressed_bytes'] += len(key.encode())
            if hashlib.sha256(key.encode()).digest() != ident:
                raise ValueError('Changed projection index key')
            yield key


def search(h, source_key, index, counts=None, *, mode='indexed', pair_limit=64,
           variable_limit=64, target_limit=64):
    """Return checked bridges; an empty result is only a bounded search miss."""
    counts = Counter() if counts is None else counts
    for value in (pair_limit, variable_limit, target_limit): _limit(value)
    if index.config != h.config: raise ValueError('Foreign index policy')
    source = h._load(source_key)
    if source is None: raise ValueError('Missing acquired projection source')
    cnf = source['cnf']; n = canonical(cnf, counts); records = []; seen = set(); tried = 0
    for variable in range(1, min(n, variable_limit)+1):
        if tried >= target_limit:
            counts['target_budget_exhausted'] += 1
            break
        counts['projection_variables'] += 1
        try:
            projected, names = projection(cnf, variable, counts, pair_limit)
        except ValueError:
            counts['projection_pair_misses'] += 1
            continue
        core = kernel(projected, counts)
        # Any target admitted by the old bridge rule contains every minimal
        # projected clause. A larger minimal set cannot satisfy the final cap.
        if len(core) > len(cnf)+2:
            counts['projection_final_growth_misses'] += 1
            continue
        sig = signature(source['depth'], len(names), core, counts)
        for key in index.candidates(sig, len(cnf)+2, target_limit-tried, counts, mode=mode):
            tried += 1
            target = h._load(key)
            if target is None:
                counts['missing_target_misses'] += 1
                continue
            wanted = {tuple(c) for c in target['cnf']}
            if not wanted <= set(projected):
                counts['target_subset_misses'] += 1
                continue
            subsumers = []; sets = list(map(set, target['cnf']))
            for i, clause in enumerate(projected):
                if clause in wanted: continue
                match = None
                for j, subset in enumerate(sets):
                    counts['target_subsumption_tests'] += 1
                    if subset < set(clause): match = j; break
                if match is None: break
                subsumers.append([i, match])
            else:
                record = dict(source=source_key, target=key, proof=dict(format=BRIDGE,
                    variable=variable, names=list(names), subsumers=subsumers))
                # Reconstruct from authoritative endpoints, independently of
                # signatures, cached minima and proposed deletion witnesses.
                verify(h, record, counts)
                ident = record_key(record)
                if ident not in seen: records.append(record); seen.add(ident)
                continue
            counts['target_subsumption_misses'] += 1
    counts['accepted_bridges'] += len(records)
    return records
