#!/usr/bin/env python3
"""Resume the exact retained cofactor with a fresh, shared admission allowance.

Two independent copies check reproducibility; this is a coverage experiment,
not a speed comparison against a different scheduler or a fresh SAT solver.
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

from experiments.compare_cnf_pending_maintenance import (
    restore_checkpoint as restore_base, worker, POLICY, FILES as INHERITED_FILES,
    routes_for, add_splits, select, BudgetedInventory, full, expand,
    archive_json, read_archive, sha, sha_key, digests, unpack, apply_delta,
    check_delta, save_delta, new_probes, probe_reference, split_reference,
    frontier, profile, learning_selection, checked_inventory, verify_split,
    verify_positive, verify_bridge, remaining, split_key)
from experiments.cnf_pattern_inventory import encode

BASE = Path('experiments/results/cnf-pending-maintenance/report.json')
FORMAT = 'retained-pending-pair-resumption-v1'
FILES = ['experiments/continue_cnf_pending_pair.py', *INHERITED_FILES]


def restore_checkpoint(report_path, path, tmp):
    r = json.loads(Path(report_path).read_text())
    if r['format'] != FORMAT or Path(r['parent']['path']) != BASE or sha(BASE) != r['parent']['sha256']:
        raise ValueError('Changed pending-pair parent')
    for name, digest in r['fingerprints'].items():
        if sha(name) != digest:
            raise ValueError('Changed pending-pair implementation')
    parent, *evidence = restore_base(BASE, path, tmp)
    if digests(path) != r['seed_table_digests'] or parent['final_closed'] != r['baseline_closed']:
        raise ValueError('Incorrect pending-pair seed')
    d = r['delta']; delta = tmp/'pending-pair-delta'
    if sha(d['path']) != d['sha256']:
        raise ValueError('Changed pending-pair delta')
    unpack(d['path'], delta, d['database_sha256'])
    apply_delta(path, delta); check_delta(path, delta, r['options'])
    if digests(path) != r['logical_table_digests']:
        raise ValueError('Incorrect pending-pair reconstruction')
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
        fingerprints={name: sha(name) for name in FILES}, policy=POLICY, arms=[], limitations=[
        'Two independent seed copies with identical scheduling; reproducibility, not a comparative speedup.',
        'Resume the exact retained pair before selecting new work. Both polarities remain obligations regardless of a SAT witness.',
        'Each worker has twelve advances and one fresh shared 32-state allowance. Previously unstored admissions are charged again.',
        'Preparation, acquisition, route updates, coverage, persistence, reconstruction and reference checks are separate costs.',
        'Development cases, shared OS caches, no holdout or confidence intervals. Stored bytes are not peak RAM.',
        'No globally minimal expansion, polynomial unrestricted-SAT algorithm or P-versus-NP conclusion.'])
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); seed = tmp/'seed'; tick = time.perf_counter()
        parent, *base_evidence = restore_base(BASE, seed, tmp)
        r.update(restore_seconds=time.perf_counter()-tick, options=parent['options'],
            cases=parent['cases'], baseline_closed=parent['final_closed'],
            seed_table_digests=digests(seed), seed_database_bytes=seed.stat().st_size,
            evidence_counts_before=list(map(len, base_evidence)), source=parent['source'])
        seed_hash = sha(seed); root = r['source']; bridges = read_archive(parent['bridges'])
        before = read_archive(parent['next_selection'])
        assert before['pending_split'] is not None
        r['initial_selection'] = archive_json(out/'initial-selection.json.gz', before)
        history = tmp/'history'; shutil.copyfile(seed, history); evidence = copy.deepcopy(base_evidence)
        touched = {}
        for repeat in range(2):
            name = f'resume-{repeat}-pending'
            arm = worker(out/name, tmp/name, seed, parent, base_evidence, bridges, root, 'pending', 'resume')
            first = read_archive(arm['steps'][0]['operation'])
            assert first['mode'] == 'resume_split' and first['record'] == before['pending_split']
            r['arms'].append(dict(case=1154, scenario='resume', repeat=repeat, mode='pending',
                path=str(out/name/'report.json'), sha256=sha(out/name/'report.json')))
            apply_delta(history, tmp/name/'delta'); check_delta(history, tmp/name/'delta', r['options'])
            evidence = add_splits(evidence, read_archive(arm['splits']))
            for row in arm['steps']:
                op = read_archive(row['operation'])
                if op.get('record') is not None:
                    touched[split_key(op['record'])] = op['record']
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
