#!/usr/bin/env python3
"""Audit retention and provenance costs after the seven-priority implementation.

Uses temporary stores. Counts and storage deltas are diagnostics, not a timed
solver ranking. Existing experiment records and the user's archive are untouched.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from solver.persistent import DEFAULT_ENGINE, PersistentSolver
from solver.test_interfaces import neg, xor


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(service):
    kinds = {}
    for row in service.db.execute("""SELECT kind, count(*), sum(raw_bytes),
            sum(length(payload)) FROM knowledge_objects GROUP BY kind"""):
        kinds[row[0]] = dict(objects=row[1], raw_bytes=row[2], packed_bytes=row[3])
    tables = {name: service.db.execute(f'SELECT count(*) FROM {name}').fetchone()[0]
              for name in ('interface_nodes', 'interface_rows', 'expansion_states')}
    pages = service.db.execute('PRAGMA page_count').fetchone()[0]
    page_bytes = service.db.execute('PRAGMA page_size').fetchone()[0]
    return dict(kinds=kinds, table_rows=tables, logical_database_bytes=pages*page_bytes)


def storage_delta(before, after):
    kinds = {}
    for kind, values in after['kinds'].items():
        delta = {field: value-before['kinds'].get(kind, {}).get(field, 0)
                 for field, value in values.items()}
        if any(delta.values()):
            kinds[kind] = delta
    return dict(kinds=kinds,
                table_rows={k: v-before['table_rows'][k] for k, v in after['table_rows'].items()},
                logical_database_bytes=after['logical_database_bytes']-before['logical_database_bytes'])


def semantic_storage():
    rows = []
    for size in (16, 64, 320):
        with tempfile.TemporaryDirectory() as directory:
            with PersistentSolver(Path(directory)/'audit.db', interfaces=True) as service:
                initial = service.expand(add={f'e{i}': xor(i, i+1) for i in range(size)})
                before = snapshot(service)
                edit = service.expand(initial['state'], add={'e0': neg(xor(0, 1))})
                after = snapshot(service)
                assert initial['answer'] and edit['answer'] and edit['fallback_reason'] is None
                delta = storage_delta(before, after)
                # Durable result insertion happens after archive_new_objects is sampled.
                inserted = sum(v['objects'] for v in delta['kinds'].values())
                assert inserted >= edit['interfaces']['archive_new_objects']
                rows.append(dict(size=size, metrics=edit['interfaces'],
                                 before=before, after=after, delta=delta,
                                 answer=edit['answer'], wall_ns=edit['wall_ns']))
    return rows


def retention():
    rows = []
    for size in (256, 1024):
        rng = random.Random(1801+size)
        # Every edge allows (0,0), an independent SAT witness for all edits.
        edges = [rng.getrandbits(256) | 1 for _ in range(size)]
        replacements = [rng.getrandbits(256) | 1 for _ in range(6)]
        live = 2*size-1
        for multiplier in (1, 2):
            with tempfile.TemporaryDirectory() as directory:
                with PersistentSolver(Path(directory)/'audit.db',
                        native_layer_cells=multiplier*live*256) as service:
                    first = service.layered(4, append=edges, left=1, right=1)
                    assert first['answer']
                    state = first['state']
                    edits = []
                    for i, mask in enumerate(replacements):
                        result = service.layered(4, state,
                            replace={size//2+i: mask}, left=1, right=1)
                        assert result['answer']
                        edits.append(dict(metrics=result['layered'], wall_ns=result['wall_ns']))
                        state = result['state']
                    repeat = service.layered(4, state, left=1, right=1)
                    old = service.layered(4, first['state'], left=1, right=1)
                    assert repeat['answer'] and old['answer']
                    rows.append(dict(size=size, live_nodes=live, cap_nodes=multiplier*live,
                                     initial=first['layered'], edits=edits,
                                     unchanged=repeat['layered'], old_branch=old['layered']))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    output = parser.parse_args().output
    output.mkdir(parents=True, exist_ok=False)
    records = dict(retention=retention(), semantic_storage=semantic_storage())
    prior = ROOT/'experiments/results/priorities/diagnostics.json.gz'
    with gzip.open(prior, 'rt') as stream:
        previous = json.load(stream)
    records['previous_equal_edits'] = [dict(size=r['size'], repeat=r['repeat'],
        metrics=r['equal_edit']['interfaces'], wall_ns=r['equal_edit']['wall_ns'])
        for r in previous if r['kind'] == 'semantic_provenance']
    files = [Path(__file__), DEFAULT_ENGINE, ROOT/'formal/Solver.lean', prior,
             *sorted((ROOT/'solver').glob('*.py')),
             *sorted((ROOT/'formal/OracleMachines').glob('*.lean'))]
    metadata = dict(source_commit=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        purpose='Deterministic operation/storage diagnostics; elapsed times are not a benchmark',
        seed_rule='1801 + edge count; identical inputs at both retention caps',
        fingerprints={str(p.relative_to(ROOT)): digest(p) for p in files})
    for name, value in [('audit', records), ('metadata', metadata)]:
        (output/(name+'.json')).write_text(json.dumps(value, indent=2)+'\n')
    print(json.dumps(dict(retention_cases=len(records['retention']),
                          semantic_cases=len(records['semantic_storage']),
                          output=str(output))))


if __name__ == '__main__':
    main()
