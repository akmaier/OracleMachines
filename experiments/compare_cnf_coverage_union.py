#!/usr/bin/env python3
"""Bind and replay the entire historical corpus without acquiring new states.

Compare the same positive proof in fresh processes against restored histories
and a self-contained row bundle. The historical corpus is development data.
"""
import argparse
from collections import Counter
from contextlib import ExitStack, contextmanager
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.cnf_coverage_union import (capture_part, check_part, empty_rows,
    inventory, make_bundle, merge_rows, replay_union, roots_for, validate_claim)
from experiments.cnf_expanded_coverage import expand
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_selected_routes import SelectedRoutes
from experiments.compare_cnf_positive_bundle import no_discovery

LEGACY = Path('experiments/results/cnf-retained-plans-full/report.json')
LEGACY_SHA = '6b09f04a02286d4a9ca5ac692ea0bf4d7b481f90b2ce3c2fad9490aab42ddc32'
CURRENT = Path('experiments/results/cnf-case1196-discovery/report.json')
CURRENT_SHA = 'f8c8081bb0c345a3ed45c566e55b1641bb9ca436064c30ad7afd5a434cb1bb66'
PRESERVATION = Path('experiments/results/cnf-case1196-discovery/validation.json')
NEW_FILES = ['experiments/cnf_coverage_union.py', 'experiments/compare_cnf_coverage_union.py',
             'solver/test_cnf_coverage_union.py']


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def load(path):
    return json.loads(Path(path).read_text())


def archive(path, value):
    raw = encode(value).encode()
    with Path(path).open('wb') as f:
        with gzip.GzipFile(fileobj=f, mode='wb', mtime=0) as z:
            z.write(raw)
    return dict(path=str(path), sha256=sha(path), bytes=len(raw),
                compressed_bytes=Path(path).stat().st_size)


def read_archive(entry):
    assert sha(entry['path']) == entry['sha256']
    return json.loads(gzip.decompress(Path(entry['path']).read_bytes()))


@contextmanager
def no_acquisition():
    with ExitStack() as stack:
        stack.enter_context(no_discovery())
        for target in ('experiments.cnf_retained_plans.RetainedPlanInventory._discover',
                       'experiments.cnf_polarity_horn.PolarityHornInventory._discover',
                       'experiments.cnf_residual_dag.ResidualSolver._expand'):
            stack.enter_context(patch(target, side_effect=AssertionError('Fresh acquisition forbidden')))
        yield


def bind_claim():
    assert sha(LEGACY) == LEGACY_SHA and sha(CURRENT) == CURRENT_SHA
    old = load(LEGACY); current = load(CURRENT)
    records = [r for r in old['records'] if r['mode'] == 'retained']
    assert [r['case'] for r in records] == list(range(len(old['cases'])))
    closed = [r['case'] for r in records if r['discovery']['summary']['closed']]
    missed = [r['case'] for r in records if not r['discovery']['summary']['closed']]
    assert missed == [c['original_case'] for c in current['cases']]
    assert all(c['source'] == old['cases'][c['original_case']]['source'] for c in current['cases'])
    assert all(current['final_closed']) and len(closed) == 1414 and len(missed) == 83
    claim = dict(sources=[c['source'] for c in old['cases']],
        policies=dict(retained=dict(reader='retained', options=old['options']),
                      expanded=dict(reader='expanded', options=current['options'])),
        partition=dict(retained=closed, expanded=missed))
    validate_claim(claim)
    return old, current, claim


def restore_legacy(old, path):
    entry = next(a for a in old['archives'] if a['mode'] == 'retained')
    started = time.perf_counter()
    with gzip.open(entry['path'], 'rb') as src, path.open('wb') as dst:
        shutil.copyfileobj(src, dst)
    assert sha(path) == entry['database_sha256']
    return dict(seconds=time.perf_counter()-started, database_bytes=path.stat().st_size,
                compressed_bytes=Path(entry['path']).stat().st_size,
                database_sha256=entry['database_sha256'], archive_sha256=sha(entry['path']))


def historical_proof(path, claim):
    h = inventory(path, claim['policies']['retained'])
    try:
        h.db.execute('PRAGMA query_only=ON')
        roots = roots_for(h, claim, 'retained')
        # Closure bits select candidates only. expand invokes the full original
        # validators, including old policy choices, before exposing direct rules.
        base = dict(roots=roots, steps=[dict(source=k, rule=dict(kind='base'))
                                       for k in dict.fromkeys(roots)])
        evidence = [[], [], [], [], []]; counts = Counter()
        proof = expand(h, base, roots, SelectedRoutes(h, evidence), counts)
        return dict(proof=proof, evidence=evidence, bridges=[]), dict(counts)
    finally:
        h.close()


def full_worker(claim, parts):
    from experiments.continue_cnf_case1196_discovery import restore_checkpoint
    started = time.perf_counter(); old, current, bound = bind_claim()
    assert encode(bound) == encode(claim)
    results = {}; restored = {}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        for name in ('retained', 'expanded'):
            path = tmp / name
            if name == 'retained':
                restored[name] = restore_legacy(old, path)
            else:
                tick = time.perf_counter()
                parent, *_ = restore_checkpoint(CURRENT, path, tmp)
                assert parent == current
                restored[name] = dict(seconds=time.perf_counter()-tick,
                    database_bytes=path.stat().st_size, materialization_allowed=True)
            h = inventory(path, claim['policies'][name]); tick = time.perf_counter()
            try:
                h.db.execute('PRAGMA query_only=ON')
                results[name] = check_part(h, claim, name, parts[name])
                results[name]['seconds'] = time.perf_counter()-tick
            finally:
                h.close()
            path.unlink()
    return dict(covered=len(claim['sources']), parts=results, restorations=restored,
                operation_seconds=time.perf_counter()-started)


def run(out):
    started = time.perf_counter(); out.mkdir(exist_ok=False)
    old, current, claim = bind_claim()
    ledger = load(PRESERVATION)
    files = dict(ledger['source_fingerprints'])
    for path, digest in files.items():
        assert sha(path) == digest
    files.update({p: sha(p) for p in NEW_FILES})
    r = dict(format='finite-policy-coverage-union-study-v1',
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        legacy=dict(path=str(LEGACY), sha256=LEGACY_SHA),
        current=dict(path=str(CURRENT), sha256=CURRENT_SHA), fingerprints=files,
        preservation_parent=dict(path=str(PRESERVATION), sha256=sha(PRESERVATION)),
        limitations=[
            'All 1497 inputs are historical development cases, including the adaptively reused 83 misses; no new holdout is evaluated.',
            'The partition is a finite source-index dispatch certificate, not a structural classification of every CNF or a uniformly polynomial SAT algorithm.',
            'Structural coverage supplies a checked recognition plan, not a fresh SAT/UNSAT answer. No ordinary solver is run.',
            'Each policy retains its own exact configuration and depth; no implicit cross-policy proof transport is assumed.',
            'Both modes replay identical positive claims. Full mode also restores/checks historical lineage; the bundle does not certify a full discovery catalog.',
            'Historical acquisition remains a paid prerequisite. This experiment adds replay data and deletes no old archive.',
            'Two reversed-order repetitions run in fresh processes with shared operating-system caches; no significance estimate or peak-RAM measurement.',
            'Current restoration permits checked materialization but does not expose whether cache or fallback was used.',
            'All five sidecar lists and bridges are carried unchanged; unused sidecars may remain. Minimum-size encoding is not claimed.'])
    claims_path = out / 'claims.json'; claims_path.write_text(encode(claim)+'\n')
    r['claims'] = dict(path=str(claims_path), sha256=sha(claims_path), bytes=claims_path.stat().st_size)
    parts = {}; rows = empty_rows(); r['capture'] = {}; r['restoration'] = {}
    with tempfile.TemporaryDirectory() as td, no_acquisition():
        tmp = Path(td); path = tmp / 'legacy'
        r['restoration']['retained'] = restore_legacy(old, path)
        tick = time.perf_counter()
        parts['retained'], counts = historical_proof(path, claim)
        r['historical_expansion'] = dict(seconds=time.perf_counter()-tick, counts=counts)
        for name in ('retained', 'expanded'):
            if name == 'expanded':
                from experiments.continue_cnf_case1196_discovery import restore_checkpoint
                path = tmp / 'current'; tick = time.perf_counter()
                parent, *evidence = restore_checkpoint(CURRENT, path, tmp)
                assert parent == current
                r['restoration'][name] = dict(seconds=time.perf_counter()-tick,
                    database_bytes=path.stat().st_size, materialization_allowed=True)
                parts[name] = dict(proof=read_archive(current['expanded_certificate']),
                                   evidence=evidence, bridges=read_archive(current['bridges']))
            before = sha(path); h = inventory(path, claim['policies'][name])
            h.db.execute('PRAGMA query_only=ON'); tick = time.perf_counter()
            try:
                captured, metrics = capture_part(h, claim, name, parts[name])
                metrics['seconds'] = time.perf_counter()-tick
                metrics['rows'] = {t: len(v) for t, v in captured.items()}
                merge_rows(rows, captured); r['capture'][name] = metrics
            finally:
                h.close()
            assert sha(path) == before
            path.unlink()
            print(json.dumps(dict(phase='captured', policy=name, roots=metrics['roots'],
                                  steps=metrics['steps'], seconds=metrics['seconds'])), flush=True)
        tick = time.perf_counter(); bundle = make_bundle(claim, parts, rows)
        r['bundle'] = archive(out/'coverage-union.json.gz', bundle)
        r['parts'] = archive(out/'proof-parts.json.gz', parts)
        r['serialization_compression_seconds'] = time.perf_counter()-tick
        r['rows'] = {t: len(v) for t, v in rows.items()}
        r['logical_row_bytes'] = {t: dict(keys=sum(len(k.encode()) for k in v),
            payloads=sum(len(p.encode()) for p in v.values())) for t, v in rows.items()}
        r['deduplicated_row_occurrences'] = sum(sum(m['rows'].values()) for m in r['capture'].values())-sum(r['rows'].values())
        samples = []
        for repeat, order in enumerate((('full', 'bundle'), ('bundle', 'full'))):
            for mode in order:
                print(json.dumps(dict(phase='fresh replay', repeat=repeat, mode=mode)), flush=True)
                command = [sys.executable, str(Path(__file__).resolve()), '--worker', mode,
                           '--claim', str(claims_path.resolve()), '--input',
                           str(Path(r['parts' if mode=='full' else 'bundle']['path']).resolve())]
                tick = time.perf_counter()
                process = subprocess.run(command, cwd=ROOT if mode=='full' else tmp,
                                         capture_output=True, text=True)
                (out/f'{mode}-{repeat}.txt').write_text(process.stdout+process.stderr)
                if process.returncode:
                    raise RuntimeError('Replay failed; worker output retained')
                sample = json.loads(process.stdout)
                sample.update(repeat=repeat, mode=mode, process_seconds=time.perf_counter()-tick)
                assert sample['covered'] == 1497
                for name in claim['policies']:
                    assert sample['parts'][name]['roots'] == r['capture'][name]['roots']
                    assert sample['parts'][name]['steps'] == r['capture'][name]['steps']
                    assert sample['parts'][name]['counts'] == r['capture'][name]['counts']
                samples.append(sample)
                print(json.dumps({k:sample[k] for k in ('mode','repeat','covered','process_seconds')}), flush=True)
        r['samples'] = samples
    r['summary'] = {mode: dict(mean_process_seconds=sum(s['process_seconds'] for s in samples if s['mode']==mode)/2,
        mean_operation_seconds=sum(s['operation_seconds'] for s in samples if s['mode']==mode)/2)
        for mode in ('full','bundle')}
    r['coverage'] = dict(total=1497, covered=1497, non_tiny=985, non_tiny_covered=985,
                         retained=1414, expanded=83, new_acquisitions=0)
    r['no_fresh_discovery'] = True; r['history_bytes_unchanged'] = True
    r['pipeline_seconds'] = time.perf_counter()-started
    (out/'report.json').write_text(json.dumps(r, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(coverage=r['coverage'], summary=r['summary'],
                         compressed_bytes=r['bundle']['compressed_bytes'])), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output', type=Path, nargs='?')
    parser.add_argument('--worker', choices=('full', 'bundle'))
    parser.add_argument('--claim', type=Path); parser.add_argument('--input', type=Path)
    args = parser.parse_args()
    if args.worker:
        tick = time.perf_counter(); claim = load(args.claim)
        data = json.loads(gzip.decompress(args.input.read_bytes())); loaded = time.perf_counter()
        with no_acquisition():
            result = full_worker(claim, data) if args.worker=='full' else replay_union(data, claim)
        result['load_seconds'] = loaded-tick; result['operation_seconds'] = time.perf_counter()-tick
        print(json.dumps(result))
    else:
        run(args.output)
