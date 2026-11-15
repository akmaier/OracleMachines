#!/usr/bin/env python3
"""Complete admission audit and persistent resumption of the frozen transfer miss.

This is a supplemental, fixed-input experiment, not a new holdout. Each saved
archive is independently replayed with all acquisition entrances disabled.
"""
from collections import Counter
from contextlib import ExitStack
import gzip
import json
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.cnf_complete_admission import CompleteAdmissionInventory
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_early_subsumption import discover_family, check_family
from experiments.cnf_expanded_coverage import owner
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_subsumption_transfer import sha, load, source_id, key_sha, ordinary, no_acquisition

PARENT = Path('experiments/results/cnf-subsumption-transfer')
FILES = ['experiments/cnf_complete_admission.py', 'experiments/compare_cnf_complete_admission.py',
         'solver/test_cnf_complete_admission.py']
MODES = {'legacy32': (BudgetedInventory, 32), 'complete32': (CompleteAdmissionInventory, 32),
         'legacy4096': (BudgetedInventory, 4096), 'complete4096': (CompleteAdmissionInventory, 4096)}


def write(path, data):
    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')


def rows(h):
    return dict(h.db.execute('SELECT id,payload FROM cnf_patterns_v1'))


def cold(path, options, records, cases):
    tick = time.perf_counter(); before = sha(path)
    h = CompleteAdmissionInventory(path, **options); h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with no_acquisition(), patch.object(h, '_admit', side_effect=AssertionError('Acquisition forbidden')):
            for key in rows(h):
                assert owner(h, key)._load(key) is not None
            for row in records:
                source = cases[row['case']]['source']
                assert row['source_sha256'] == source_id(source)
                if row['certificate'] is not None:
                    check_family(source, row['certificate']); assert row['closed']
                elif row['root'] is not None:
                    assert h._canonical(source, h.config['max_depth'])[2] == row['root']
                    assert h._load(row['root'])['summary']['closed'] == row['closed']
                else:
                    assert row['capped'] and not row['closed']
            nodes = len(rows(h))
    finally:
        h.close()
    assert sha(path) == before
    return dict(seconds=time.perf_counter()-tick, nodes=nodes, queries=len(records), no_acquisition=True)


def query(h, case, index, limit, family=True):
    tick = time.perf_counter(); before = rows(h)
    h.counts = Counter(); h.prepared.counts = Counter(); h.set_admission_budget(limit)
    counts = Counter(); source = case['source']
    cert = discover_family(source, counts) if family else None
    if cert is not None:
        check_family(source, cert, counts); root, closed, capped = None, True, False
    else:
        root, closed, capped = ordinary(h, source)
    after = rows(h)
    assert before.items() <= after.items()
    fresh = set(after)-set(before)
    admitted = set(h.admitted)
    if isinstance(h, CompleteAdmissionInventory):
        assert fresh <= admitted and len(admitted) <= limit
    return dict(case=index, source_sha256=source_id(source), root=root, closed=closed, capped=capped,
        certificate=cert, stored=len(fresh), entered=len(admitted), off_ledger=len(fresh-admitted),
        admitted_unstored=len(admitted-fresh), admitted_ids=sorted(map(key_sha, admitted)),
        stored_ids=sorted(map(key_sha, fresh)), admission_counts=dict(h.admission_counts),
        recognition_counts=dict(h.counts), lookup_counts=dict(counts),
        probes=h.counts['probe_attempts'], seconds=time.perf_counter()-tick)


def archive(path, dest):
    tick = time.perf_counter(); target = dest/'history.sqlite3.gz'
    target.write_bytes(gzip.compress(path.read_bytes(), mtime=0))
    return dict(path=str(target), sha256=sha(target), database_sha256=sha(path),
                database_bytes=path.stat().st_size, compressed_bytes=target.stat().st_size,
                seconds=time.perf_counter()-tick)


def stream(out, protocol, mode):
    out.mkdir(); cls, limit = MODES[mode]; began = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'history'; h = cls(path, **protocol['options'])
        ready = time.perf_counter(); records = []
        try:
            for i, case in enumerate(protocol['cases']):
                records.append(query(h, case, i, limit))
            payloads = rows(h)
        finally:
            h.close()
        finished = time.perf_counter()
        check = cold(path, protocol['options'], records, protocol['cases'])
        saved = archive(path, out)
        result = dict(mode=mode, preparation_seconds=ready-began, operation_seconds=finished-ready,
            archive=saved, cold=check, records=records, covered=sum(r['closed'] for r in records),
            entered=sum(r['entered'] for r in records), stored=sum(r['stored'] for r in records),
            off_ledger=sum(r['off_ledger'] for r in records), probes=sum(r['probes'] for r in records),
            row_digest=key_sha(encode(sorted(payloads.items()))))
        write(out/'report.json', result)
        return result


def resume(out, protocol, prepared):
    out.mkdir(); steps = []; prior_rows = {}; initial = None
    if prepared:
        initial = load(PARENT/'family-control/family-0/report.json')['archive']
        assert sha(initial['path']) == initial['sha256']
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'history'
        if initial:
            path.write_bytes(gzip.decompress(Path(initial['path']).read_bytes()))
            assert sha(path) == initial['database_sha256']
        for batch in range(4):
            destination = out/f'batch-{batch}'; destination.mkdir()
            tick = time.perf_counter(); h = CompleteAdmissionInventory(path, **protocol['options'])
            if batch == 0:
                prior_rows = rows(h)
            # A new object makes every batch's prerequisite proof checks cold.
            ready = time.perf_counter()
            try:
                row = query(h, protocol['cases'][41], 41, 32, family=False)
                assert prior_rows.items() <= rows(h).items()
            finally:
                h.close()
            row['startup_seconds'] = ready-tick
            row['batch'] = batch
            row['cold'] = cold(path, protocol['options'], [row], protocol['cases'])
            row['archive'] = archive(path, destination)
            write(destination/'report.json', row); steps.append(row)
            if not row['capped']:
                break
        result = dict(prepared=prepared, initial=initial, initial_patterns=len(prior_rows), steps=steps,
            closed=steps[-1]['closed'], capped=steps[-1]['capped'],
            entered=sum(s['entered'] for s in steps), stored=sum(s['stored'] for s in steps),
            probes=sum(s['probes'] for s in steps), distinct_admitted=len(set().union(*(s['admitted_ids'] for s in steps))),
            total_seconds=sum(s['seconds']+s['startup_seconds'] for s in steps))
        write(out/'report.json', result); return result


def run(out):
    out.mkdir(exist_ok=False)
    parent_validation = load(PARENT/'validation.json')
    for p, digest in parent_validation['source_fingerprints'].items():
        assert sha(p) == digest
    protocol = load(PARENT/'protocol.json')
    assert source_id(protocol['cases'][41]['source']) == '511dd0f7c367b2af3e9f447f8411ef8ed10e0265dfcde5666b7d35f0b4aa1a22'
    frozen = dict(parent_validation_sha256=sha(PARENT/'validation.json'),
        protocol=dict(path=str(PARENT/'protocol.json'), sha256=sha(PARENT/'protocol.json')),
        source_fingerprints={**parent_validation['source_fingerprints'], **{p:sha(p) for p in FILES}},
        repetitions=2, orders=[list(MODES), list(reversed(MODES))],
        resume=dict(case=41, batches=4, complete_state_limit=32, modes=['prepared', 'empty'], reopen_each_batch=True),
        limitations=['Supplemental comparison on already inspected synthetic inputs.',
            'A distinct acquisition-state cap does not bound checking, normalization, I/O or repeated visits.',
            '4096-state runs check compatibility at a generous finite allowance, not an unbounded algorithm.',
            'No peak RAM or new SAT/UNSAT answers are measured; closure denotes checked structural coverage.'])
    write(out/'frozen.json', frozen)
    samples = []
    for repeat, order in enumerate(frozen['orders']):
        for mode in order:
            dest = out/f'{mode}-{repeat}'; result = stream(dest, protocol, mode)
            samples.append(dict(mode=mode, repeat=repeat, path=str(dest/'report.json'), sha256=sha(dest/'report.json')))
            print(json.dumps({k:result[k] for k in ('mode','covered','entered','stored','off_ledger','probes')}), flush=True)
    by_mode = {m:[load(s['path']) for s in samples if s['mode']==m] for m in MODES}
    # A large allowance must preserve the complete graph, not just its outcome.
    for a, b in zip(by_mode['legacy4096'], by_mode['complete4096']):
        assert a['row_digest'] == b['row_digest']
        assert [(r['root'],r['closed'],r['capped']) for r in a['records']] == [(r['root'],r['closed'],r['capped']) for r in b['records']]
    for arms in by_mode.values():
        assert arms[0]['row_digest'] == arms[1]['row_digest']
    resumptions = {m:resume(out/f'resume-{m}',protocol,m=='prepared') for m in ('prepared','empty')}
    summary = {m:{**{k:a[0][k] for k in ('covered','entered','stored','off_ledger','probes')},
        'mean_operation_seconds':sum(x['operation_seconds'] for x in a)/len(a),
        'mean_preparation_seconds':sum(x['preparation_seconds'] for x in a)/len(a),
        'database_bytes':a[0]['archive']['database_bytes'],
        'mean_compressed_bytes':sum(x['archive']['compressed_bytes'] for x in a)/len(a)} for m,a in by_mode.items()}
    report = dict(frozen_sha256=sha(out/'frozen.json'), samples=samples, summary=summary,
        resumptions={m:dict(path=str(out/f'resume-{m}/report.json'), sha256=sha(out/f'resume-{m}/report.json'),
            **{k:v for k,v in r.items() if k not in ('steps','initial')}) for m,r in resumptions.items()},
        generous_graphs_identical=True)
    write(out/'report.json', report); print(json.dumps(report['summary']), flush=True)
    print(json.dumps(report['resumptions']), flush=True)


if __name__ == '__main__':
    run(Path(sys.argv[1]))
