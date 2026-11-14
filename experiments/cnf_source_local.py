"""Exact source-local probe continuation over an authoritative archive snapshot.

The working database is an initially empty read-through cache plus append-only
delta. An absent local row always consults the read-only authority. This is not
a disconnected bundle, complete route catalog, or negative coverage oracle.
"""
from collections import Counter, defaultdict
from collections.abc import MutableMapping
from contextlib import contextmanager
import json
from pathlib import Path
import re
import sqlite3

from experiments.cnf_coupled_pivots import BudgetedInventory, AdmissionExhausted
from experiments.cnf_expanded_coverage import verifier_views
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_positive_bundle import TABLES, LOOKUP
from experiments.cnf_probe_window import verify_window, record_key as window_key
from experiments.cnf_probe_continuation import ContinuationRoutes, record_key as continuation_key

INSERT = re.compile(r'INSERT INTO ([a-z0-9_]+) VALUES \(\?,\?\)')


class ReadThrough:
    """Restricted SQL adapter; never infer global absence from the local cache."""
    def __init__(self, local, authority):
        self.local, self.authority = local, authority
        self.counts = Counter()
        for table in TABLES:
            local.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            if local.execute(f'SELECT count(*) FROM {table}').fetchone()[0]:
                raise ValueError('Source-local working store must start empty')
        local.execute('CREATE TABLE local_new_rows (table_name TEXT,id TEXT,PRIMARY KEY(table_name,id))')
        local.commit()

    def execute(self, sql, parameters=()):
        read = LOOKUP.fullmatch(sql) if type(sql) is str else None
        write = INSERT.fullmatch(sql) if type(sql) is str else None
        match = read or write
        if (match is None or match[1] not in TABLES or
                type(parameters) not in (tuple,list) or len(parameters)!=(1 if read else 2) or
                any(type(x) is not str for x in parameters)):
            raise ValueError('Source-local access requires an allowed exact lookup or insert')
        table, key = match[1], parameters[0]
        lookup = f'SELECT payload FROM {table} WHERE id=?'
        if read:
            row = self.local.execute(lookup,(key,)).fetchone()
            self.counts['local_lookups'] += 1
            if row is None:
                row = self.authority.execute(lookup,(key,)).fetchone()
                self.counts['authority_lookups'] += 1
                if row is not None:
                    self.local.execute(f'INSERT INTO {table} VALUES (?,?)',(key,row[0]))
                    self.counts['imported_rows'] += 1
                    self.counts['imported_key_payload_bytes'] += len(key.encode())+len(row[0].encode())
                else:
                    self.counts['authoritative_absences'] += 1
            else:
                self.counts['local_hits'] += 1
            # Return a real cursor; no database-wide iteration API is exposed.
            return self.local.execute(lookup,(key,))
        # Independent authoritative membership check on every proposed insert.
        # New nodes cannot overwrite either omitted history or local work.
        self.counts['write_membership_checks'] += 1
        if self.authority.execute(lookup,(key,)).fetchone() is not None:
            raise ValueError('Proposed new row already exists in authoritative history')
        cursor = self.local.execute(sql,parameters)
        self.local.execute('INSERT INTO local_new_rows VALUES (?,?)',(table,key))
        self.counts['inserted_rows'] += 1
        return cursor

    def __enter__(self):
        self.local.__enter__()
        return self

    def __exit__(self,*args): return self.local.__exit__(*args)

    def close(self): self.local.close()

    def export_delta(self, path):
        """Export committed novel rows only, with the historical delta schema."""
        from experiments.compare_cnf_probe_continuation import TABLES as DELTA_TABLES
        if self.local.in_transaction:
            self.local.commit()
        if Path(path).exists(): raise ValueError('Delta output already exists')
        out = sqlite3.connect(path)
        counts = {}
        try:
            with out:
                for table in DELTA_TABLES:
                    out.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                    rows = [] if table not in TABLES else self.local.execute(
                        f'SELECT p.id,p.payload FROM {table} p JOIN local_new_rows n ON '
                        'n.table_name=? AND n.id=p.id ORDER BY p.rowid',(table,)).fetchall()
                    out.executemany(f'INSERT INTO {table} VALUES (?,?)',rows)
                    counts[table] = len(rows)
            return counts
        finally: out.close()


@contextmanager
def local_inventory(authority_path, working_path, options):
    """Caller supplies the fully reconstructed, identity-checked parent archive.

    The read transaction pins a snapshot. Do not reuse an old working cache with
    a different archive: this API requires an empty store and fresh check caches.
    """
    authority = sqlite3.connect(Path(authority_path).resolve().as_uri()+'?mode=ro',uri=True)
    h = None
    try:
        authority.execute('BEGIN')
        # Establish the snapshot now, before any discovery can occur.
        authority.execute('SELECT count(*) FROM sqlite_master').fetchone()
        h = BudgetedInventory(working_path,**options)
        adapter = ReadThrough(h.db,authority)
        for _,view in verifier_views(h): view.db = adapter
        yield h,adapter
    finally:
        if h is not None: h.close()
        authority.close()


class ExactSavedRows(MutableMapping):
    """Nullable exact membership, backed by authority rather than a partial map."""
    def __init__(self,h,table,identity,counts,check=None):
        self.h,self.table,self.identity,self.counts,self.check = h,table,identity,counts,check
        self.cache = {}

    def __getitem__(self,key):
        if key in self.cache: return self.cache[key]
        row = self.h.db.execute(f'SELECT payload FROM {self.table} WHERE id=?',(key,)).fetchone()
        self.counts['source_local_route_lookups'] += 1
        if row is None: raise KeyError(key)
        record = json.loads(row[0])
        if self.identity(record)!=key: raise ValueError('Incorrect source-local route identity')
        if self.check is not None: self.check(self.h,record,self.counts)
        self.cache[key] = record
        return record

    def __setitem__(self,key,record):
        if self.identity(record)!=key: raise ValueError('Incorrect new route identity')
        row = self.h.db.execute(f'SELECT payload FROM {self.table} WHERE id=?',(key,)).fetchone()
        if row is None or row[0]!=encode(record): raise ValueError('Route must first be persisted exactly')
        if self.check is not None: self.check(self.h,record,self.counts)
        self.cache[key] = record

    def __delitem__(self,key): raise ValueError('Immutable route cache')
    def __iter__(self): raise ValueError('Exact source-local map is not a complete route catalog')
    def __len__(self): raise ValueError('Exact source-local map is not a complete route catalog')


class SourceProbeRoutes(ContinuationRoutes):
    """Use the unchanged probe/prefix checker and scheduler for one exact source."""
    def __init__(self,h,source):
        self.source,self.h = source,h
        self.counts = Counter(); self.by_source = defaultdict(list); self.verified = set()
        self.windows = ExactSavedRows(h,'cnf_probe_windows_v1',window_key,self.counts,verify_window)
        self.continuations = ExactSavedRows(h,'cnf_probe_continuations_v1',continuation_key,self.counts)

    def advance(self,h,source,counts):
        if h is not self.h or source!=self.source: raise ValueError('Changed source-local scope')
        return super().advance(h,source,counts)


def advance_one(h,routes,source,counts):
    """One ordinary block; caller owns the single shared admission allowance."""
    kind,record,target = routes.advance(h,source,counts)
    stopped = False
    if record is not None and record['edge'] is not None:
        try:
            edge = h._edge(target,h._load(source)['depth'])
            if edge!=record['edge']: raise ValueError('Changed acquired residual')
        except AdmissionExhausted: stopped = True
    return dict(kind=kind,record=record,admission_stopped=stopped)


def check_delta(history, delta, options):
    """Cold-check all new records after conflict-checked merge into full history.

    Historical rows outside the dependency closure are not reaudited. The caller
    must bind and preserve the parent; this is not an initial archive validator.
    """
    from experiments.compare_cnf_probe_continuation import TABLES as DELTA_TABLES
    h = BudgetedInventory(history,**options); h.set_admission_budget(0)
    db = sqlite3.connect(Path(delta).resolve().as_uri()+'?mode=ro',uri=True)
    counts = Counter()
    try:
        for table in TABLES:
            for key,payload in db.execute(f'SELECT id,payload FROM {table} ORDER BY id'):
                actual = h.db.execute(f'SELECT payload FROM {table} WHERE id=?',(key,)).fetchone()
                if actual!=(payload,): raise ValueError('Delta differs from merged row')
                record = json.loads(payload)
                if table=='cnf_patterns_v1':
                    if h._load(key) is None: raise ValueError('Missing new node')
                elif table=='cnf_probe_windows_v1':
                    if window_key(record)!=key: raise ValueError('Invalid window identity')
                    verify_window(h,record,counts)
                elif table=='cnf_probe_continuations_v1':
                    if continuation_key(record)!=key: raise ValueError('Invalid continuation identity')
                    SourceProbeRoutes(h,record['source'])._verify_saved(h,key,counts)
                else: raise ValueError('Unsupported new source-local record kind')
                counts['checked_delta_rows'] += 1
        for table in set(DELTA_TABLES)-set(TABLES):
            if db.execute(f'SELECT count(*) FROM {table}').fetchone()[0]:
                raise ValueError('Source-local delta cannot introduce other record types')
        if h.admitted: raise ValueError('Delta checking performed recognition')
        return dict(counts)
    finally: h.close(); db.close()
