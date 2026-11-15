#!/usr/bin/env python3
"""Expand the new-stream frontier using an existing checked cofactor pair.

All inference comes from the frozen trace-split, inventory and coverage checkers.
The complete admission layer gates acquisition; pending polarities and completed
children survive each bounded batch. This is an adaptive development experiment.
"""
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_complete_admission import CompleteAdmissionInventory
from experiments.cnf_coupled_pivots import AdmissionExhausted, FrontierIndex
from experiments.cnf_expanded_coverage import expand, owner
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_projection_bridge import verify_positive
from experiments.cnf_route_composition import compose, verify_plan
from experiments.cnf_trace_split import candidates, verify, attach
from experiments.cnf_trace_reuse import read_attempt
from experiments.compare_cnf_trace_split import matched_control
from experiments.compare_cnf_subsumption_transfer import load, sha, key_sha, source_id, no_acquisition
from experiments.compare_cnf_complete_admission import rows, write, archive

PARENT = Path('experiments/results/cnf-complete-admission')
MODES = ('history', 'source_only')
POLICY = dict(candidate_pairs=4, batch_state_limit=32, max_batches=4)
FILES = ['experiments/continue_cnf_transfer_split.py', 'solver/test_cnf_transfer_split.py']


def restore_archive(entry, path):
    if sha(entry['path']) != entry['sha256']:
        raise ValueError('Changed history archive')
    raw = gzip.decompress(Path(entry['path']).read_bytes())
    with Path(path).open('xb') as f:
        f.write(raw)
    if sha(path) != entry['database_sha256']:
        raise ValueError('Changed history database')


def new_routes(h, record):
    routes = SimpleNamespace(by_source=defaultdict(list))
    attach(h, routes, record, Counter())
    return routes


def advance(h, record, limit):
    """One shared allowance, never treating an absent child as closed."""
    targets, _ = verify(h, record, Counter())
    h.set_admission_budget(limit); h.counts = Counter(); h.prepared.counts = Counter()
    before = rows(h); tick = time.perf_counter(); branches = []
    for target, expected in zip(targets, record['edges'], strict=True):
        try:
            edge = h._edge(target, h._load(record['source'])['depth'])
        except AdmissionExhausted:
            pending = True
        else:
            if encode(edge) != encode(expected):
                raise ValueError('Changed split cofactor')
            pending = False
        branches.append(dict(pending=pending, key=expected['key']))
    after = rows(h)
    if not before.items() <= after.items():
        raise ValueError('Prior pattern was changed')
    fresh = set(after)-set(before)
    if not fresh <= h.admitted or len(h.admitted) > limit:
        raise ValueError('Incomplete admission accounting')
    routes = new_routes(h, record)
    closed, plan = compose(h, [record['source']], routes, Counter())
    verify_plan(h, plan, plan['roots'], routes, Counter())
    return dict(branches=branches, entered=len(h.admitted), stored=len(fresh),
        admitted_ids=sorted(map(key_sha, h.admitted)), stored_ids=sorted(map(key_sha, fresh)),
        admission_counts=dict(h.admission_counts), recognition_counts=dict(h.counts),
        probes=h.counts['probe_attempts'], split_closed=closed[0], seconds=time.perf_counter()-tick)


def replay(path, options, record, roots, expected):
    before = sha(path); tick = time.perf_counter()
    h = CompleteAdmissionInventory(path, **options); h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with no_acquisition(), patch.object(h, '_admit', side_effect=AssertionError('Acquisition forbidden')):
            for key in rows(h):
                assert owner(h, key)._load(key) is not None
            routes = new_routes(h, record)
            closed, plan = compose(h, roots, routes, Counter())
            assert closed == expected
            verify_plan(h, plan, plan['roots'], routes, Counter())
            positive = expand(h, plan, plan['roots'], routes, Counter())
            checked = verify_positive(h, positive, plan['roots'], [[],[],[],[record],[]], [], Counter())
            assert len(checked.justified) == len(positive['steps'])
            nodes = len(rows(h))
    finally:
        h.close()
    assert sha(path) == before
    return dict(seconds=time.perf_counter()-tick, nodes=nodes, no_acquisition=True,
                closed=closed, positive=positive)


def frontier(h, record):
    result = []
    for value, edge in zip((False, True), record['edges'], strict=True):
        node = h._load(edge['key'])
        if node is None:
            result.append(dict(value=value, pending=True, key=edge['key']))
            continue
        leaves = FrontierIndex(h).frontier(edge['key'])
        result.append(dict(value=value, pending=False, key=edge['key'], closed=node['summary']['closed'],
            leaves=[dict(key=k, multiplicity=n, source=h._load(k)['cnf'],
                shape=h._load(k)['profile']['shape'], depth=h._load(k)['depth']) for k,n in leaves.items()]))
    return result


def worker(out, frozen, selection, mode):
    out.mkdir(); total = time.perf_counter(); options = frozen['options']; record = selection['record']
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'history'; tick = time.perf_counter()
        if mode == 'history':
            restore_archive(frozen['parent_archive'], path)
        else:
            h = CompleteAdmissionInventory(path, **options)
            try:
                with h.db:
                    h.db.execute('INSERT INTO cnf_patterns_v1 VALUES (?,?)',
                                 (record['source'], selection['source_payload']))
            finally:
                h.close()
        preparation = time.perf_counter()-tick
        initial = None; steps = []; closed = None
        roots = [record['source'], frozen['original_root']] if mode == 'history' else [record['source']]
        for batch in range(POLICY['max_batches']):
            tick = time.perf_counter(); h = CompleteAdmissionInventory(path, **options); h.set_admission_budget(0)
            try:
                old = rows(h)
                if initial is None:
                    initial = old
                with no_acquisition(), patch.object(h, '_admit', side_effect=AssertionError('Acquisition forbidden')):
                    for key in old:
                        assert owner(h, key)._load(key) is not None
                    verify(h, record, Counter())
                startup = time.perf_counter()-tick
                row = advance(h, record, POLICY['batch_state_limit'])
                assert initial.items() <= rows(h).items()
                routes = new_routes(h, record); closed, _ = compose(h, roots, routes, Counter())
                row.update(batch=batch, startup_seconds=startup, closed=closed, frontier=frontier(h,record))
            finally:
                h.close()
            dest = out/f'batch-{batch}'; dest.mkdir()
            row['archive'] = archive(path, dest)
            row['cold'] = replay(path, options, record, roots, closed)
            write(dest/'report.json',row); steps.append(row)
            if not any(b['pending'] for b in row['branches']):
                break
        last = steps[-1]
        result = dict(mode=mode, initial_patterns=len(initial), steps=steps, roots=roots, closed=closed,
            entered=sum(s['entered'] for s in steps), stored=sum(s['stored'] for s in steps),
            probes=sum(s['probes'] for s in steps), distinct_admitted=len(set().union(*(s['admitted_ids'] for s in steps))),
            preparation_seconds=preparation, startup_seconds=sum(s['startup_seconds'] for s in steps),
            expansion_seconds=sum(s['seconds'] for s in steps),
            initial_row_digest=key_sha(encode(sorted(initial.items()))),
            final_archive=last['archive'], total_seconds=time.perf_counter()-total)
        write(out/'report.json',result)
        return {k:result[k] for k in ('mode','closed','entered','stored','probes','startup_seconds','expansion_seconds')}


def restore_checkpoint(report_path, path):
    """Restore a history-mode sample, retaining all prior rows and split evidence."""
    report_path = Path(report_path); report = load(report_path)
    frozen = load(report_path.parent.parent/'frozen.json')
    master = load(report_path.parent.parent/'report.json')
    bound = next((s for s in master['samples'] if Path(s['path']).resolve()==report_path.resolve()), None)
    if (bound is None or sha(report_path)!=bound['sha256'] or report['mode']!='history'
            or sha(report_path.parent.parent/'frozen.json')!=master['frozen_sha256']):
        raise ValueError('Not a bound full-history checkpoint')
    for p, digest in frozen['source_fingerprints'].items():
        if sha(p) != digest:
            raise ValueError('Changed checkpoint implementation')
    selection_path = report_path.parent.parent/'selection.json'
    if sha(selection_path) != master['selection_sha256']:
        raise ValueError('Changed selected split')
    selection = load(selection_path); restore_archive(report['final_archive'], path)
    checked = replay(path, frozen['options'], selection['record'], report['roots'], report['closed'])
    return frozen, selection['record'], report, checked


def run(out):
    out.mkdir(exist_ok=False); parent_validation = load(PARENT/'validation.json')
    sources = dict(parent_validation['source_fingerprints'])
    for p,digest in sources.items():
        assert sha(p)==digest
    sources.update({p:sha(p) for p in FILES})
    prior = load(PARENT/'complete4096-0/report.json'); original = load(PARENT/'selected-frontier.json')
    protocol = load('experiments/results/cnf-subsumption-transfer/protocol.json')
    assert prior['records'][41]['root'] == original['root']
    frozen = dict(parent_validation_sha256=sha(PARENT/'validation.json'),parent_archive=prior['archive'],
        frontier_sha256=sha(PARENT/'selected-frontier.json'), original_root=original['root'],
        original_source=protocol['cases'][41]['source'], source_fingerprints=sources, options=protocol['options'],
        policy=POLICY, repetitions=2, orders=[list(MODES),list(reversed(MODES))],
        limitations=['Adaptive single-residual study, not an independent holdout.',
            'Only the four already saved top-level clear pairs are ranked, not every variable or a minimum-cost split.',
            'Both polarities are required for structural coverage; unknown never means UNSAT.',
            'Source-only control inherits the selected checked trace row. It is not wholly unprepared solving.',
            'Opening, full cold verification, recognition, row audits and proof persistence are charged separately; peak RAM is unmeasured.'])
    write(out/'frozen.json',frozen)
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'history';tick=time.perf_counter();restore_archive(prior['archive'],path)
        h=CompleteAdmissionInventory(path,**frozen['options']);h.set_admission_budget(0)
        try:
            for table in ('cnf_probe_windows_v1','cnf_probe_continuations_v1'):
                h.db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            h.db.commit()
            source=original['leaves'][0]['key'];routes=SimpleNamespace(by_source=defaultdict(list));counts=Counter()
            with no_acquisition(), patch.object(h,'_admit',side_effect=AssertionError('Acquisition forbidden')):
                assert h._canonical(frozen['original_source'],h.config['max_depth'])[2]==frozen['original_root']
                assert compose(h,[frozen['original_root']],routes,Counter())[0]==[False]
                ranked=candidates(h,source,routes,counts,candidate_limit=POLICY['candidate_pairs'])
            assert ranked
            record=ranked[0]['record'];targets,_=verify(h,record,Counter())
            selection=dict(record=record,ranked=ranked,counts=dict(counts),seconds=time.perf_counter()-tick,
                source_payload=h.db.execute('SELECT payload FROM cnf_patterns_v1 WHERE id=?',(source,)).fetchone()[0],
                variable=read_attempt(h,source,record['references'][0],Counter())['variable'],
                cofactor_shapes=[dict(variables=len({abs(l) for c in t for l in c}),clauses=len(t),literals=sum(map(len,t))) for t in targets],
                closure_control=matched_control(h,record))
            write(out/'selection.json',selection)
        finally:
            h.close()
    samples=[]
    print(json.dumps(dict(variable=selection['variable'],rank=ranked[0]['rank'],cofactors=selection['cofactor_shapes'])),flush=True)
    for repeat,order in enumerate(frozen['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';summary=worker(dest,frozen,selection,mode)
            samples.append(dict(mode=mode,repeat=repeat,path=str(dest/'report.json'),sha256=sha(dest/'report.json')))
            print(json.dumps(summary),flush=True)
    report=dict(frozen_sha256=sha(out/'frozen.json'),selection_sha256=sha(out/'selection.json'),samples=samples)
    write(out/'report.json',report)


if __name__=='__main__':
    run(Path(sys.argv[1]))
