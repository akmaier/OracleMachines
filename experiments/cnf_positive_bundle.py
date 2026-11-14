"""Self-contained data for one positive proof, not a discovery checkpoint.

Capture exact successful SQL reads from a fresh replay. Every consumer builds a
new temporary database and runs the semantic checker again. File hashes are
integrity metadata only; neither a hash nor the producer's result licenses reuse.
"""
from collections import Counter
from contextlib import contextmanager
import json
from pathlib import Path
import re
import tempfile
import time

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_expanded_coverage import verifier_views, checked_inventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_positive_primitives import verify_positive

FORMAT = 'positive-coverage-bundle-v1'
SCOPE = 'positive-proof-only'
TABLES = ('cnf_patterns_v1', 'cnf_pivot_trials_v1', 'cnf_coupled_trials_v1',
          'cnf_growth_trials_v1', 'cnf_probe_windows_v1', 'cnf_probe_continuations_v1')
LOOKUP = re.compile(r'SELECT payload FROM ([a-z0-9_]+) WHERE id=\?')


class _OneRow:
    def __init__(self, row): self.row = row

    def fetchone(self):
        row, self.row = self.row, None
        return row


class ReadCapture:
    """Fail closed on any operation other than the known exact-key read API."""
    def __init__(self, connection):
        self.connection = connection
        self.rows = {table:{} for table in TABLES}
        self.counts = Counter()

    def execute(self, sql, parameters=()):
        match = LOOKUP.fullmatch(sql) if type(sql) is str else None
        if (match is None or match[1] not in TABLES or
                type(parameters) not in (tuple,list) or len(parameters)!=1 or
                type(parameters[0]) is not str):
            raise ValueError('Bundle capture requires an allowed exact-key read')
        table, key = match[1], parameters[0]
        row = self.connection.execute(sql, parameters).fetchone()
        self.counts['lookup_calls'] += 1
        if row is None:
            self.counts['missing_lookups'] += 1
        else:
            payload = row[0]
            if type(payload) is not str:
                raise ValueError('Invalid captured payload')
            if key in self.rows[table] and self.rows[table][key] != payload:
                raise ValueError('Changed row during positive capture')
            self.rows[table][key] = payload
            self.counts['read_payload_bytes'] += len(payload.encode())
        return _OneRow(row)

    def export(self):
        return {table:[[k,v] for k,v in sorted(rows.items())] for table,rows in self.rows.items()}


@contextmanager
def capture_reads(h):
    views = [view for _,view in verifier_views(h)]
    connection = h.db
    if any(view.db is not connection for view in views):
        raise ValueError('Expected one shared inventory connection')
    capture = ReadCapture(connection)
    for view in views: view.db = capture
    try:
        yield capture
    finally:
        for view in views: view.db = connection


def bound_roots(h, sources):
    if type(sources) is not list:
        raise ValueError('Expected explicit claimed source formulas')
    return [h._canonical(source,h.config['max_depth'])[2] for source in sources]


def collect_bundle(h, proof, sources, options, evidence, counts):
    """Read all consumed rows; prefilled historical caches would hide premises."""
    if any(view.checked for _,view in verifier_views(h)):
        raise ValueError('Bundle export requires fresh historical caches')
    claimed = bound_roots(h,sources)
    with capture_reads(h) as capture:
        verify_positive(h,proof,claimed,evidence,counts)
    if capture.counts['missing_lookups']:
        raise ValueError('Positive capture used an absent row')
    bundle = dict(format=FORMAT,scope=SCOPE,options=options,sources=sources,
                  proof=proof,evidence=evidence,rows=capture.export())
    # A value snapshot: later producer-side mutation cannot alter this bundle.
    return json.loads(encode(bundle)), dict(capture.counts)


def validate_envelope(bundle, expected_sources, expected_options):
    if (type(bundle) is not dict or
            set(bundle) != {'format','scope','options','sources','proof','evidence','rows'} or
            bundle['format'] != FORMAT or bundle['scope'] != SCOPE or
            encode(bundle['sources']) != encode(expected_sources) or
            encode(bundle['options']) != encode(expected_options) or
            type(bundle['options']) is not dict or type(bundle['sources']) is not list or
            type(bundle['evidence']) is not list or len(bundle['evidence']) != 5 or
            any(type(items) is not list for items in bundle['evidence']) or
            type(bundle['rows']) is not dict or set(bundle['rows']) != set(TABLES)):
        raise ValueError('Invalid positive bundle or changed requested claim')
    for table,rows in bundle['rows'].items():
        seen = set()
        if type(rows) is not list: raise ValueError('Invalid bundled rows')
        for row in rows:
            if type(row) is not list or len(row)!=2 or any(type(x) is not str for x in row):
                raise ValueError('Invalid bundled row')
            if row[0] in seen: raise ValueError('Duplicate bundled identity')
            seen.add(row[0])


def replay_bundle(bundle, expected_sources, expected_options):
    """Cold-check in a disposable DB. Return metrics, never a partial inventory.

The caller supplies the claim independently. This checks positive coverage only,
even though the old validators also inspect some historical-policy premises.
No source archive, lineage report or external sidecar path is consulted here.
"""
    started = time.perf_counter()
    validate_envelope(bundle,expected_sources,expected_options)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'positive-only.sqlite3'
        h = BudgetedInventory(path,**expected_options); h.set_admission_budget(0)
        try:
            with h.db:
                for table in TABLES:
                    h.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                    h.db.executemany(f'INSERT INTO {table} VALUES (?,?)',bundle['rows'][table])
            claimed = bound_roots(h,expected_sources)
            h.db.execute('PRAGMA query_only=ON')
            prepared = time.perf_counter(); counts = Counter()
            with capture_reads(h) as capture:
                result = verify_positive(h,bundle['proof'],claimed,bundle['evidence'],counts)
            replayed = time.perf_counter()
            # Exported records must all be exercised, and no missing premise is
            # supplied by another archive or interpreted as a negative claim.
            if capture.counts['missing_lookups'] or capture.export() != bundle['rows']:
                raise ValueError('Bundle has unused rows or lacks a checked dependency')
            _,accounting = checked_inventory(h)
            if h.admitted: raise ValueError('Bundle replay acquired new recognition states')
            return dict(preparation_seconds=prepared-started,replay_seconds=replayed-prepared,
                total_seconds=time.perf_counter()-started,temporary_database_bytes=path.stat().st_size,
                roots=len(claimed),steps=len(result.justified),counts=dict(counts),
                capture_counts=dict(capture.counts),historical=accounting,
                rows={t:len(rows) for t,rows in bundle['rows'].items()},
                current_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
                route_counts=dict(result.routes.counts))
        except (KeyError,TypeError,IndexError,AttributeError) as exc:
            raise ValueError('Malformed positive bundle evidence') from exc
        finally:
            h.close()
