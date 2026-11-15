#!/usr/bin/env python3
"""Compare copied, live-full and guarded table digests during matched expansion.
"""
from collections import Counter
import copy
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_reduction_reuse import (
    restore_checkpoint as restore_base, POLICY, FILES as INHERITED_FILES,
    routes_for, add_splits, select, BudgetedInventory, full, expand,
    archive_json, read_archive, sha, sha_key, digests, unpack, apply_delta,
    check_delta, save_delta, new_probes, probe_reference, split_reference,
    frontier, profile, learning_selection, checked_inventory, verify_split,
    verify_positive, verify_bridge, remaining, split_key)
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_digest_worker import worker, full_snapshot
BASE = Path('experiments/results/cnf-reduction-reuse/report.json')
FORMAT = 'guarded-digest-expansion-v1'
FILES = ['experiments/compare_cnf_guarded_digests.py', 'experiments/cnf_digest_worker.py',
    'experiments/cnf_guarded_digests.py', 'solver/test_cnf_guarded_digests.py', *INHERITED_FILES]
BATCHES = 2


def restore_checkpoint(report_path, path, tmp):
    r = json.loads(Path(report_path).read_text())
    if r['format'] != FORMAT or Path(r['parent']['path']) != BASE or sha(BASE) != r['parent']['sha256']:
        raise ValueError('Changed guarded-digests parent')
    for name, digest in r['fingerprints'].items():
        if sha(name) != digest:
            raise ValueError('Changed guarded-digests implementation')
    parent, *evidence = restore_base(BASE, path, tmp)
    if digests(path) != r['seed_table_digests'] or parent['final_closed'] != r['baseline_closed']:
        raise ValueError('Incorrect guarded-digests seed')
    d = r['delta']; delta = tmp/'guarded-digests-delta'
    if sha(d['path']) != d['sha256']:
        raise ValueError('Changed guarded-digests delta')
    unpack(d['path'], delta, d['database_sha256'])
    apply_delta(path, delta); check_delta(path, delta, r['options'])
    if digests(path) != r['logical_table_digests']:
        raise ValueError('Incorrect guarded-digests reconstruction')
    evidence = add_splits(evidence, read_archive(r['splits']))
    bridges = read_archive(r['bridges'])
    h = BudgetedInventory(path, **r['options']); h.set_admission_budget(0)
    try:
        for record in bridges:
            verify_bridge(h, record, Counter())
        roots = [h._canonical(c['source'], h.config['max_depth'])[2]
                 for c, b in zip(r['cases'], r['final_closed'], strict=True) if b]
        verify_positive(h, read_archive(r['expanded_certificate']), roots, evidence, bridges, Counter())
        assert not h.admitted
    finally:
        h.close()
    return r, *evidence


def run(out):
    pipeline = time.perf_counter(); out.mkdir(exist_ok=False)
    r = dict(format=FORMAT, parent=dict(path=str(BASE), sha256=sha(BASE)),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        fingerprints={name: sha(name) for name in FILES}, policy=POLICY, batch_limit=BATCHES, arms=[], session_runs=[], limitations=[
        'Two reversed-order repetitions of copied full scans, live full scans and guarded live reuse; two bounded batches per independent seed.',
        'Resume the globally selected pending pair within the still-open original-bound focus. Preserve both polarities.',
        'Each batch has twelve advances and its own 32-state allowance; up to 64 entries per sequence, including repeated unfinished inputs. Stop once the focus closes.',
        'All modes retain the batch copy, scheduler and checks. Initial full hashing, changed-table rescans and live guards are charged. No cProfile instrumentation.',
        'Preparation, acquisition, route updates, coverage, persistence, reconstruction and reference checks are separate costs.',
        'Development cases and shared OS caches; two observations per mode do not establish general speedups or confidence intervals. Stored bytes are not peak RAM.',
        'No globally minimal expansion, polynomial unrestricted-SAT algorithm or P-versus-NP conclusion.'])
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); seed = tmp/'seed'; tick = time.perf_counter()
        parent, *base_evidence = restore_base(BASE, seed, tmp)
        r.update(restore_seconds=time.perf_counter()-tick, options=parent['options'],
            cases=parent['cases'], baseline_closed=parent['final_closed'],
            seed_table_digests=digests(seed), seed_database_bytes=seed.stat().st_size,
            evidence_counts_before=list(map(len, base_evidence)))
        with sqlite3.connect(seed) as db:
            measured,r['seed_table_profile']=full_snapshot(db)
        assert measured==r['seed_table_digests']
        seed_hash = sha(seed); bridges = read_archive(parent['bridges'])
        before = read_archive(parent['next_selection'])
        root = parent['source']; assert root is not None and before['pending_split'] is not None
        r['source'] = root; r['source_original_indices'] = parent['source_original_indices']
        assert r['source_original_indices']==[22] and parent['cases'][22]['original_case']==1120
        r['initial_selection'] = archive_json(out/'initial-selection.json.gz', before)
        history = tmp/'history'; shutil.copyfile(seed, history); evidence = copy.deepcopy(base_evidence)
        touched = {}
        for repeat in range(2):
            for digest_mode in (('copy','live','guarded') if repeat==0 else ('guarded','live','copy')):
                startup_mode='retained'
                name=f'session-{repeat}-{digest_mode}'; arm_history=tmp/(name+'-history')
                started=time.perf_counter();shutil.copyfile(seed,arm_history)
                arm_evidence=copy.deepcopy(base_evidence);session=None;batch_rows=[]
                try:
                    for batch in range(BATCHES):
                        batch_name=f'{name}-batch-{batch}'
                        arm,session=worker(out/batch_name,tmp/batch_name,arm_history,parent,arm_evidence,bridges,root,session,digest_mode)
                        first=read_archive(arm['steps'][0]['operation'])
                        if batch==0:
                            assert first['source']==before['source'] and first['mode']=='resume_split' and first['record']==before['pending_split']
                        r['arms'].append(dict(case=1120,scenario='resume',repeat=repeat,batch=batch,
                            mode='activation',export_mode='append',startup_mode=startup_mode,digest_mode=digest_mode,
                            path=str(out/batch_name/'report.json'),sha256=sha(out/batch_name/'report.json')))
                        batch_rows.append(arm)
                        apply_delta(history,tmp/batch_name/'delta');check_delta(history,tmp/batch_name/'delta',r['options'])
                        additions=read_archive(arm['splits']);evidence=add_splits(evidence,additions)
                        arm_evidence=add_splits(arm_evidence,additions)
                        for row in arm['steps']:
                            op=read_archive(row['operation'])
                            if op.get('record') is not None:touched[split_key(op['record'])]=op['record']
                        if arm['target_closed']:break
                finally:
                    if session is not None:session.h.close()
                r['session_runs'].append(dict(repeat=repeat,startup_mode=startup_mode,digest_mode=digest_mode,batches=len(batch_rows),
                    seconds=time.perf_counter()-started,worker_seconds=sum(a['worker_seconds'] for a in batch_rows),
                    admitted=sum(len(a['admitted_state_sha256']) for a in batch_rows),
                    completed=sum(len(a['completed_new_state_sha256']) for a in batch_rows),
                    final_digests=digests(arm_history)))
        assert sha(seed) == seed_hash; r['parent_unchanged'] = True
        previous = {split_key(x) for x in base_evidence[3]}
        new_splits = [x for x in evidence[3] if split_key(x) not in previous]
        r['splits'] = archive_json(out/'splits.json.gz', new_splits)
        r['touched_splits'] = archive_json(out/'touched-splits.json.gz', list(touched.values()))
        r['bridges'] = archive_json(out/'bridges.json.gz', bridges)
        r['evidence_counts_after'] = list(map(len, evidence))
        tick = time.perf_counter(); h = BudgetedInventory(history, **r['options']); h.set_admission_budget(0)
        try:
            routes = routes_for(h, evidence, bridges)
            roots = [h._canonical(c['source'], h.config['max_depth'])[2] for c in r['cases']]
            r['global_route_preparation_seconds'] = time.perf_counter()-tick; tick = time.perf_counter()
            closed, plans, counts = full(h, roots, routes)
            r.update(global_coverage_seconds=time.perf_counter()-tick, global_counts=counts,
                final_closed=closed[0], without_growth_closed=closed[1])
            assert not any(a and not b for a, b in zip(r['baseline_closed'], closed[0], strict=True))
            r['gains'] = [i for i, (a, b) in enumerate(zip(r['baseline_closed'], closed[0], strict=True)) if b and not a]
            r['certificate'] = archive_json(out/'coverage.json.gz', plans[0])
            r['expanded_certificate'] = archive_json(out/'expanded-coverage.json.gz', expand(h, plans[0], plans[0]['roots'], routes, Counter()))
            state = frontier(h, routes, evidence[3], Counter())
            r['frontier'] = archive_json(out/'frontier.json.gz', state)
            r['frontier_profiles'] = archive_json(out/'frontier-profiles.json.gz', [profile(h, routes, row) for row in state['leaves']])
            r['projection_frontier'] = archive_json(out/'projection-frontier.json.gz', remaining(h, [dict(source=x['source'], target=x['target']) for x in bridges], routes, Counter()))
            r['learning'] = archive_json(out/'learning.json.gz', learning_selection(h, routes, Counter()))
            r['next_selection'] = archive_json(out/'next-selection.json.gz', select(h, routes, evidence, roots, closed[0], Counter()))
            r['historical_cache'] = checked_inventory(h)[1]
            r['delta'] = save_delta(seed, history, tmp/'delta', out/'proof-delta.sqlite3.gz')
            d = parent['reference']; assert sha(d['path']) == d['sha256']
            unpack(d['path'], tmp/'reference', d['database_sha256']); shutil.copyfile(tmp/'reference', tmp/'reference-seed')
            pr = probe_reference(h, routes, [dict(kind=x['kind'], id=x['id']) for x in new_probes(tmp/'delta')], r, out, tmp)
            r['probe_reference'] = {k: pr[k] for k in ('rows', 'originals', 'seconds', 'cold_seconds', 'verified_nodes')}
            # Include resumed splits: newly available canonical children need reference evidence too.
            r['reference'] = split_reference(h, list(touched.values()), r, out, tmp)
        finally:
            h.close()
        r['logical_table_digests'] = digests(history); r['expanded_database_bytes'] = history.stat().st_size
        tick = time.perf_counter(); r['cold_delta_counts'] = check_delta(history, tmp/'delta', r['options'])
        r['cold_delta_seconds'] = time.perf_counter()-tick
        rebuilt = tmp/'rebuilt'; shutil.copyfile(seed, rebuilt); apply_delta(rebuilt, tmp/'delta')
        assert digests(rebuilt) == r['logical_table_digests']
        previous_hash = sha(rebuilt); apply_delta(rebuilt, tmp/'delta'); assert sha(rebuilt) == previous_hash
        r['idempotent_merge'] = True
        with sqlite3.connect(tmp/'delta') as db:
            r['new_node_kinds'] = dict(Counter(json.loads(p)['kind'] for p, in db.execute('SELECT payload FROM cnf_patterns_v1')))
    r['pipeline_seconds'] = time.perf_counter()-pipeline
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']), gains=r['gains'], new_kinds=r['new_node_kinds'], seconds=r['pipeline_seconds'])), flush=True)


if __name__ == '__main__':
    run(Path(sys.argv[1]))
