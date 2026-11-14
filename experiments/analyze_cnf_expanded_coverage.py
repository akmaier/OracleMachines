#!/usr/bin/env python3
"""Account for both verifier caches and expose implicit positive proof steps."""
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

from experiments.continue_cnf_reused_branch import restore_checkpoint
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key, digests
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_selected_routes import verify_selected_plan
from experiments.cnf_expanded_coverage import expand, verify_expanded, checked_inventory, owner

PARENT = Path('experiments/results/cnf-reused-branch/report.json')
PREVIOUS = Path('experiments/results/cnf-selected-routes/report.json')
FILES = ['experiments/cnf_expanded_coverage.py', 'experiments/analyze_cnf_expanded_coverage.py',
         'solver/test_cnf_expanded_coverage.py']


def run(out):
    started = time.perf_counter(); out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td, ExitStack() as stack:
        tmp = Path(td); path = tmp/'history'; restored = time.perf_counter()
        parent, *evidence = restore_checkpoint(PARENT, path, tmp)
        r = dict(format='expanded-positive-coverage-study-v1', parent=dict(path=str(PARENT), sha256=sha(PARENT)),
            previous_study=dict(path=str(PREVIOUS), sha256=sha(PREVIOUS)),
            source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
            fingerprints={p:sha(p) for p in FILES}, restore_seconds=time.perf_counter()-restored,
            evidence_counts=[len(items) for items in evidence], inventory_bytes=path.stat().st_size,
            inventory_sha256=sha(path), logical_table_digests=digests(path),
            limitations=[
                'This expands the existing positive proof, not structural coverage or a new SAT decision.',
                'Expanded replay still uses the original recursive inventory validators; it is not a standalone checker or a measured optimization.',
                'Nodes outside the explicit expanded graph include external evidence dependencies; they are not all proved dispensable.',
                'Logical JSON payload excludes Python-object overhead, other caches, RSS and peak memory.',
                'Current and prepared verifier caches share SQLite but not their checked node maps.',
                'Previous cold timings already included both verifier views; only the reported dependency/payload totals were incomplete.',
                'One adaptively reused 83-input development set; no unrestricted polynomial construction or bound.'])
        assert r['logical_table_digests'] == parent['logical_table_digests']
        old = read_archive(parent['certificate']); previous = json.loads(PREVIOUS.read_text())
        for name in ('experiments.cnf_probe_window.discover_probes', 'experiments.cnf_probe_continuation.discover_probes',
                     'experiments.cnf_trace_learning.discover_equivalence_probes',
                     'experiments.cnf_learning_continuation.discover_equivalence_probes',
                     'experiments.cnf_affine_clause.discover'):
            stack.enter_context(patch(name, side_effect=AssertionError('new discovery')))
        stack.enter_context(patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('new recognition')))
        h = BudgetedInventory(path, **parent['options']); h.set_admission_budget(0)
        h.db.execute('PRAGMA query_only=ON')
        roots = [h._canonical(c['source'], h.config['max_depth'])[2] for c in parent['cases']]
        claimed = [key for key, closed in zip(roots, parent['final_closed'], strict=True) if closed]
        assert claimed == old['roots']
        print('cold selected proof, including both verifier views', flush=True)
        cold_started = time.perf_counter(); counts = Counter()
        routes = verify_selected_plan(h, old, claimed, evidence, counts)
        r['selected_replay'] = dict(seconds=time.perf_counter()-cold_started, counts=dict(counts),
            current_counts=dict(h.counts), prepared_counts=dict(h.prepared.counts), route_counts=dict(routes.counts))
        rows, accounting = checked_inventory(h); before_keys = set(rows)
        assert set(h.checked).isdisjoint(h.prepared.checked)
        r['checking_closure'] = accounting
        previous_keys = read_archive(previous['selected_dependencies'])['pattern_key_sha256']
        assert sorted(map(sha_key, h.checked)) == previous_keys
        old_steps = {s['source'] for s in old['steps']}
        counts = Counter(); expansion_started = time.perf_counter()
        proof = expand(h, old, claimed, routes, counts)
        r['expansion'] = dict(seconds=time.perf_counter()-expansion_started, counts=dict(counts))
        after_rows, after_accounting = checked_inventory(h)
        assert set(after_rows) == before_keys and accounting == after_accounting
        proof_keys = {s['source'] for s in proof['steps']}
        assert old_steps <= proof_keys <= before_keys
        excluded = before_keys-proof_keys
        def profile(keys):
            return dict(nodes=len(keys), kinds=dict(Counter(rows[k]['kind'] for k in keys)),
                key_bytes=sum(len(k.encode()) for k in keys),
                node_json_bytes=sum(len(encode(rows[k]).encode()) for k in keys),
                current_policy_nodes=sum(owner(h,k) is h for k in keys),
                prepared_policy_nodes=sum(owner(h,k) is h.prepared for k in keys),
                key_sha256=sorted(map(sha_key, keys)))
        dependency = dict(checking_closure=profile(before_keys), expanded_plan=profile(proof_keys),
            outside_expanded_plan=profile(excluded),
            extra_beyond_old_steps=len(before_keys-old_steps),
            exposed_hidden_steps=len(proof_keys-old_steps),
            terminal_families=dict(Counter(rows[s['source']]['profile']['cell']
                for s in proof['steps'] if s['rule']['kind']=='family')),
            note='Outside means absent from this positive structural graph, not proved unnecessary for all primitive or external evidence checking.')
        r['dependencies'] = archive_json(out/'dependencies.json.gz', dependency)
        r['expanded_certificate'] = archive_json(out/'expanded-coverage.json.gz', proof)
        r['expanded_steps'] = len(proof['steps']); r['roots'] = len(claimed)
        r['expanded_rules'] = dict(Counter(s['rule']['kind'] for s in proof['steps']))
        # Correct old totals without rewriting fingerprinted historical reports.
        correction = []
        for sample in previous['samples']:
            a, b = sample['inventory_counts'], sample['prepared_counts']
            correction.append(dict(mode=sample['mode'], repeat=sample['repeat'],
                current_nodes=a['verified_pattern_nodes'], prepared_nodes=b['verified_pattern_nodes'],
                total_nodes=a['verified_pattern_nodes']+b['verified_pattern_nodes'],
                total_node_json_bytes=a['node_read_bytes']+b['node_read_bytes'],
                cold_seconds_unchanged=sample['cold_seconds']))
        r['previous_accounting_correction'] = correction
        assert all(s['prepared_nodes']==accounting['views']['current.prepared']['nodes'] for s in correction)
        assert not h.admitted; h.close()
        print(json.dumps(dict(old_steps=len(old['steps']), expanded_steps=len(proof['steps']),
            all_checked_nodes=len(before_keys), outside_expanded=len(excluded), rules=r['expanded_rules'])), flush=True)
        # Fresh independent replay of the serialized expanded witness. It does
        # not use the old certificate or any checked node/route objects.
        print('cold expanded-certificate replay', flush=True)
        h = BudgetedInventory(path, **parent['options']); h.set_admission_budget(0)
        h.db.execute('PRAGMA query_only=ON'); cold_started = time.perf_counter(); counts = Counter()
        verify_expanded(h, read_archive(r['expanded_certificate']), claimed, evidence, counts)
        r['expanded_replay'] = dict(seconds=time.perf_counter()-cold_started, counts=dict(counts),
            current_counts=dict(h.counts), prepared_counts=dict(h.prepared.counts))
        cold_rows, cold_accounting = checked_inventory(h)
        assert set(cold_rows) == before_keys and cold_accounting == accounting
        assert not h.admitted; h.close()
        assert sha(path) == r['inventory_sha256'] and digests(path) == r['logical_table_digests']
        r['history_bytes_unchanged'] = True; r['no_fresh_discovery'] = True
    r['pipeline_seconds'] = time.perf_counter()-started
    (out/'report.json').write_text(json.dumps(r, sort_keys=True, indent=2)+'\n')
    print(json.dumps(dict(pipeline_seconds=r['pipeline_seconds'], selected_seconds=r['selected_replay']['seconds'],
        expanded_seconds=r['expanded_replay']['seconds'], expanded_steps=r['expanded_steps'])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('output', type=Path)
    run(p.parse_args().output)
