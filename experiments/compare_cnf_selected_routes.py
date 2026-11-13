#!/usr/bin/env python3
"""Matched cold replay of one positive witness, with all or selected routes.

Both arms use fresh verifier caches and the unchanged inventory checker. Full
route reconstruction is the comparator, not a full archive audit. This study
does not change coverage, the archive, discovery policy or unresolved frontier.
"""
from collections import Counter
from contextlib import ExitStack
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_reused_branch import restore_checkpoint, routes_for
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key, digests
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_route_composition import verify_plan
from experiments.cnf_selected_routes import verify_selected_plan

PARENT = Path('experiments/results/cnf-reused-branch/report.json')
FILES = ['experiments/cnf_selected_routes.py', 'experiments/compare_cnf_selected_routes.py',
         'solver/test_cnf_selected_routes.py']


def dependencies(h, routes, plan):
    steps = {step['source'] for step in plan['steps']}
    keys = set(h.checked)
    return dict(pattern_nodes=len(keys), explicit_steps=len(steps),
        additional_pattern_nodes=len(keys-steps), pattern_kinds=dict(Counter(n['kind'] for n in h.checked.values())),
        pattern_key_bytes=sum(len(k.encode()) for k in keys),
        decoded_pattern_json_bytes=sum(len(encode(n).encode()) for n in h.checked.values()),
        pattern_key_sha256=sorted(map(sha_key, keys)),
        additional_pattern_key_sha256=sorted(map(sha_key, keys-steps)),
        external_routes_exposed=sum(len(rows) for rows in routes.by_source.values()),
        verified_ordinary_prefixes=len(routes.verified),
        verified_learning_prefixes=len(routes.learned_blocks.verified),
        checked_learning_bases=len(routes.learned_blocks.contexts),
        scope='Actual recursively checked inventory keys, not just witness steps. Byte counts are logical JSON payload, not Python heap or peak RAM.')


def run(out):
    started = time.perf_counter(); out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td, ExitStack() as stack:
        tmp = Path(td); path = tmp/'history'; restore_started = time.perf_counter()
        parent, *evidence = restore_checkpoint(PARENT, path, tmp)
        r = dict(format='selected-positive-routes-study-v1', parent=dict(path=str(PARENT), sha256=sha(PARENT)),
            source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            fingerprints={p:sha(p) for p in FILES}, restore_seconds=time.perf_counter()-restore_started,
            evidence_counts=[len(items) for items in evidence], inventory_bytes=path.stat().st_size,
            inventory_sha256=sha(path), logical_table_digests=digests(path),
            limitations=[
                'Positive replay of the same 58 covered roots in 83 reused development originals; no new structural coverage or fresh holdout.',
                'The comparator eagerly checks all external routes, not every unrelated inventory node and not the whole SAT solving pipeline.',
                'Original recursive inventory checks remain: internal losing alternatives and other inherited dependencies are not pruned.',
                'Omitted routes are not asserted invalid or absent; selected replay cannot certify completeness of a catalog or negative coverage.',
                'Two repetitions in opposite orders, fresh Python verifier caches but shared operating-system caches; no confidence interval.',
                'Logical payload counts are not peak RAM; indexing all five sidecar lists and parent restoration are still charged.',
                'All old archives are preserved. Discovery, active open-frontier replay and full history audit still need separate work.'])
        assert r['logical_table_digests'] == parent['logical_table_digests']
        plan = read_archive(parent['certificate'])
        r['certificate'] = parent['certificate']
        r['rule_kinds'] = dict(Counter(step['rule']['kind'] for step in plan['steps']))
        r['explicit_steps'] = len(plan['steps']); r['covered_originals'] = sum(parent['final_closed'])
        # Bind the certificate to actual original CNFs and this exact config,
        # without loading all 25 open originals merely to verify a positive list.
        h = BudgetedInventory(path, **parent['options']); h.set_admission_budget(0)
        bind_started = time.perf_counter()
        roots = [h._canonical(case['source'], h.config['max_depth'])[2] for case in parent['cases']]
        claimed = [root for root, closed in zip(roots, parent['final_closed'], strict=True) if closed]
        assert plan['roots'] == claimed
        r['root_binding_seconds'] = time.perf_counter()-bind_started; h.close()
        stack.enter_context(patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('new recognition')))
        for name in ('experiments.cnf_probe_window.discover_probes', 'experiments.cnf_probe_continuation.discover_probes',
                     'experiments.cnf_trace_learning.discover_equivalence_probes',
                     'experiments.cnf_learning_continuation.discover_equivalence_probes',
                     'experiments.cnf_affine_clause.discover'):
            stack.enter_context(patch(name, side_effect=AssertionError('new discovery')))
        r['samples'] = []; profiles = {}
        for repeat, order in enumerate((('selected', 'full'), ('full', 'selected'))):
            for mode in order:
                print(json.dumps(dict(repeat=repeat, mode=mode, phase='cold replay')), flush=True)
                sample_started = time.perf_counter()
                h = BudgetedInventory(path, **parent['options']); h.set_admission_budget(0)
                h.db.execute('PRAGMA query_only=ON')
                counts = Counter()
                if mode == 'selected':
                    routes = verify_selected_plan(h, plan, claimed, evidence, counts)
                else:
                    routes = routes_for(h, evidence)
                    verify_plan(h, plan, claimed, routes, counts)
                elapsed = time.perf_counter()-sample_started
                assert counts['verified_steps'] == len(plan['steps']) and not h.admitted
                sample = dict(mode=mode, repeat=repeat, cold_seconds=elapsed,
                    plan_counts=dict(counts), inventory_counts=dict(h.counts),
                    prepared_counts=dict(h.prepared.counts), route_counts=dict(routes.counts))
                profile = dependencies(h, routes, plan)
                if mode in profiles:
                    assert profile == profiles[mode]
                else:
                    profiles[mode] = profile
                    r[mode+'_dependencies'] = archive_json(out/f'{mode}-dependencies.json.gz', profile)
                # Warm verification reuses the same checked subset in both arms.
                warm_started = time.perf_counter(); warm_counts = Counter()
                verify_plan(h, plan, claimed, routes, warm_counts)
                sample['warm_plan_seconds'] = time.perf_counter()-warm_started
                assert warm_counts['verified_steps'] == len(plan['steps'])
                sample['pattern_nodes_checked'] = len(h.checked)
                h.close(); r['samples'].append(sample)
                print(json.dumps(dict(mode=mode, seconds=elapsed, nodes=sample['pattern_nodes_checked'])), flush=True)
        assert set(profiles['selected']['pattern_key_sha256']) <= set(profiles['full']['pattern_key_sha256'])
        assert sha(path) == r['inventory_sha256'] and digests(path) == r['logical_table_digests']
        r['inventory_bytes_unchanged'] = True
        r['no_fresh_discovery'] = True
        r['summary'] = {mode:dict(cold_seconds=[s['cold_seconds'] for s in r['samples'] if s['mode']==mode],
            pattern_nodes=profiles[mode]['pattern_nodes'], additional_pattern_nodes=profiles[mode]['additional_pattern_nodes'],
            decoded_pattern_json_bytes=profiles[mode]['decoded_pattern_json_bytes']) for mode in profiles}
    r['pipeline_seconds'] = time.perf_counter()-started
    (out/'report.json').write_text(json.dumps(r, sort_keys=True, indent=2)+'\n')
    print(json.dumps(r['summary']), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('output', type=Path)
    run(p.parse_args().output)
