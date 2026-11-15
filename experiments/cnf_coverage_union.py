"""Exact finite-source coverage across explicitly named recognition policies.

The union is a positive proof, not a discovery catalog or SAT decision. A caller
supplies the source list, policy configurations and partition independently.
Every part is replayed under its own policy; identical family names, truth
labels and stored closure bits never substitute for a checked proof.
"""
from collections import Counter
import json
from pathlib import Path
import sqlite3
import tempfile
import time

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_expanded_coverage import checked_inventory, verifier_views
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_positive_bundle import TABLES, capture_reads
from experiments.cnf_projection_bridge import verify_positive
from experiments.cnf_retained_plans import RetainedPlanInventory

FORMAT = 'finite-policy-coverage-union-v1'
SCOPE = 'positive-coverage-only'
READERS = {'retained': RetainedPlanInventory, 'expanded': BudgetedInventory}


def validate_claim(claim):
    if (type(claim) is not dict or set(claim) != {'sources', 'policies', 'partition'}
            or type(claim['sources']) is not list or type(claim['policies']) is not dict
            or type(claim['partition']) is not dict
            or not claim['policies'] or set(claim['policies']) != set(claim['partition'])):
        raise ValueError('Invalid independently supplied union claim')
    for source in claim['sources']:
        if (type(source) is not list or any(type(c) is not list or
                any(type(l) is not int or l == 0 for l in c) for c in source)):
            raise ValueError('Invalid explicit CNF source')
    indices = []
    for name, policy in claim['policies'].items():
        if (type(name) is not str or type(policy) is not dict
                or set(policy) != {'reader', 'options'}
                or policy['reader'] not in READERS or type(policy['options']) is not dict):
            raise ValueError('Invalid explicit policy')
        part = claim['partition'][name]
        if (type(part) is not list or any(type(i) is not int for i in part)
                or part != sorted(set(part))):
            raise ValueError('Invalid ordered policy partition')
        indices.extend(part)
    if sorted(indices) != list(range(len(claim['sources']))):
        raise ValueError('Partition must cover every source exactly once')


def inventory(path, policy):
    h = READERS[policy['reader']](path, **policy['options'])
    if isinstance(h, BudgetedInventory):
        h.set_admission_budget(0)
    return h


def roots_for(h, claim, name):
    return [h._canonical(claim['sources'][i], h.config['max_depth'])[2]
            for i in claim['partition'][name]]


def empty_rows():
    return {table: {} for table in TABLES}


def merge_rows(target, rows):
    for table in TABLES:
        for key, payload in rows[table]:
            if key in target[table] and target[table][key] != payload:
                raise ValueError('Conflicting exact-key proof payload')
            target[table][key] = payload


def exported_rows(rows):
    return {table: [[k, v] for k, v in sorted(rows[table].items())] for table in TABLES}


def check_part(h, claim, name, part):
    if (type(part) is not dict or set(part) != {'proof', 'evidence', 'bridges'}
            or type(part['evidence']) is not list or len(part['evidence']) != 5
            or any(type(v) is not list for v in part['evidence'])
            or type(part['bridges']) is not list):
        raise ValueError('Invalid policy proof part')
    roots = roots_for(h, claim, name)
    counts = Counter()
    replay = verify_positive(h, part['proof'], roots, part['evidence'], part['bridges'], counts)
    if isinstance(h, BudgetedInventory) and h.admitted:
        raise ValueError('Coverage union must not acquire recognition states')
    return dict(roots=len(roots), unique_roots=len(set(roots)), steps=len(replay.justified),
                counts=dict(counts), historical=checked_inventory(h)[1])


def capture_part(h, claim, name, part):
    if any(view.checked for _, view in verifier_views(h)):
        raise ValueError('Capture requires empty historical checker caches')
    with capture_reads(h) as capture:
        metrics = check_part(h, claim, name, part)
    if capture.counts['missing_lookups']:
        raise ValueError('Missing captured proof dependency')
    metrics['capture_counts'] = dict(capture.counts)
    return capture.export(), metrics


def make_bundle(claim, parts, rows):
    validate_claim(claim)
    bundle = json.loads(encode(dict(format=FORMAT, scope=SCOPE, claim=claim,
                                    parts=parts, rows=exported_rows(rows))))
    validate_bundle(bundle, claim)
    return bundle


def validate_bundle(bundle, expected_claim):
    validate_claim(expected_claim)
    if (type(bundle) is not dict or
            set(bundle) != {'format', 'scope', 'claim', 'parts', 'rows'}
            or bundle['format'] != FORMAT or bundle['scope'] != SCOPE
            or encode(bundle['claim']) != encode(expected_claim)
            or type(bundle['parts']) is not dict
            or set(bundle['parts']) != set(expected_claim['policies'])
            or type(bundle['rows']) is not dict or set(bundle['rows']) != set(TABLES)):
        raise ValueError('Changed union claim or invalid bundle envelope')
    for table, rows in bundle['rows'].items():
        seen = set()
        if type(rows) is not list:
            raise ValueError('Invalid bundled table')
        for row in rows:
            if (type(row) is not list or len(row) != 2
                    or any(type(s) is not str for s in row) or row[0] in seen):
                raise ValueError('Invalid or duplicate bundled identity')
            seen.add(row[0])


def replay_union(bundle, expected_claim):
    """Reconstruct only consumed data, then recheck all claimed sources.

    The returned coverage is structural, not a SAT/UNSAT answer. No persistent
    trusted validation cache is created. Historical archives are not consulted.
    """
    started = time.perf_counter()
    validate_bundle(bundle, expected_claim)
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'coverage.sqlite3'
        with sqlite3.connect(path) as db:
            for table in TABLES:
                db.execute(f'CREATE TABLE {table} (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
                db.executemany(f'INSERT INTO {table} VALUES (?,?)', bundle['rows'][table])
        installed = time.perf_counter()
        used = empty_rows(); parts = {}
        for name, policy in expected_claim['policies'].items():
            tick = time.perf_counter(); h = inventory(path, policy)
            try:
                h.db.execute('PRAGMA query_only=ON')
                rows, result = capture_part(h, expected_claim, name, bundle['parts'][name])
                merge_rows(used, rows)
                result['seconds'] = time.perf_counter() - tick
                parts[name] = result
            finally:
                h.close()
        if exported_rows(used) != bundle['rows']:
            raise ValueError('Unused proof rows cannot be treated as checked history')
        result = dict(covered=len(expected_claim['sources']), parts=parts,
                      preparation_seconds=installed-started,
                      replay_seconds=time.perf_counter()-installed,
                      temporary_database_bytes=path.stat().st_size,
                      rows={t: len(v) for t, v in used.items()})
    result['total_seconds'] = time.perf_counter()-started
    return result
