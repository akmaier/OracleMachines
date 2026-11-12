#!/usr/bin/env python3
"""Independently reconstruct and check the saved one-core growth experiment."""
from collections import Counter
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_coupled_pivots import BudgetedInventory, FrontierIndex
from experiments.cnf_growth_escape import TABLE, trial_key, verify_escape
from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.compare_cnf_growth_escape import (
    TABLES, CORE, PRIOR, restore_latest, apply_delta, digests, sha, sha_key, unpack)


def main(out):
    report_path = out / 'report.json'; r = json.loads(report_path.read_text())
    assert r['policy'] == dict(growth_limit=3, state_limit=32)
    assert r['options'] == json.loads(PRIOR.read_text())['options']
    for p, digest in r['fingerprints'].items(): assert sha(p) == digest, p
    for entry in r['inputs']: assert sha(entry['path']) == entry['sha256']
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); seed = tmp / 'seed'; prior, inputs = restore_latest(seed, tmp)
        assert inputs == r['inputs'] and r['cases'] == prior['cases']
        assert digests(seed) == r['seed_table_digests'] and sha(seed) == r['seed_database_sha256']
        assert seed.stat().st_size == r['seed_database_bytes']
        assert r['baseline_closed'] == prior['final_closed']
        d = r['delta']; assert sha(d['path']) == d['sha256']
        delta = tmp / 'delta'; unpack(d['path'], delta, d['database_sha256'])
        assert delta.stat().st_size == d['database_bytes']
        assert Path(d['path']).stat().st_size == d['compressed_bytes']
        rebuilt = tmp / 'rebuilt'; shutil.copyfile(seed, rebuilt); apply_delta(rebuilt, delta)
        assert digests(rebuilt) == r['logical_table_digests']
        before = sha(rebuilt); apply_delta(rebuilt, delta); assert sha(rebuilt) == before
        db = sqlite3.connect(delta)
        admitted = r['expansion']['admitted_state_sha256']
        assert len(admitted) == len(set(admitted)) <= 32
        assert len(admitted) == r['expansion']['admission_counts'].get('entered_states', 0)
        for t in TABLES:
            n = db.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
            assert n == r['delta_rows'][t]
            assert r['preserved_rows'][t] == r['seed_table_digests'][t]['rows']
            assert r['logical_table_digests'][t]['rows'] == n + r['preserved_rows'][t]
        for t in TABLES:
            if t not in ('cnf_patterns_v1', TABLE): assert r['delta_rows'][t] == 0
        assert all(sha_key(k) in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1'))
        assert r['delta_rows']['cnf_patterns_v1'] == r['expansion']['inventory_counts'].get('inserted_nodes', 0)
        records = {k: json.loads(p) for k, p in db.execute(f'SELECT id,payload FROM {TABLE}')}; db.close()
        assert records == {trial_key(x): x for x in r['expansion']['records']}
        assert len(records) == r['warm_reuse']['counts'].get('reused_growth_trials', 0)
        h = BudgetedInventory(rebuilt, **r['options']); h.set_admission_budget(0)
        assert h.db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        core = json.loads(CORE.read_text())['cores'][0]
        _, _, key = h._canonical(core['source'], 0)
        assert sha_key(key) == core['key_sha256'] == r['core_sha256']
        # Independent variable enumeration (no candidate-ranking routine): prove
        # that all and only the least-growth-three choices were attempted.
        choices = []; pairs_rejected = []
        for v in sorted({abs(l) for c in core['source'] for l in c}):
            pairs = sum(v in c for c in core['source']) * sum(-v in c for c in core['source'])
            if pairs > 64: pairs_rejected.append(v); continue
            target = check_additive_elimination(core['source'], dict(variable=v), Counter(), clause_growth_limit=64)
            choices.append((len(target)-len(core['source']), v))
        assert len(choices) + len(pairs_rejected) <= 64
        minimum = min(g for g, _ in choices)
        assert minimum == 3
        assert {v for g, v in choices if g == minimum} == {x['variable'] for x in records.values()}
        assert r['control']['records'] == [] and r['control']['budget_stop'] is None
        assert r['control']['counts'].get('admitted_candidates', 0) == 0
        index = FrontierIndex(h); leaves = set(); counts = Counter(); local_closed = 0
        for identity, record in records.items():
            assert identity == trial_key(record) and record['source'] == key
            local_closed += verify_escape(h, record, counts)
            leaves.update(index.frontier(record['edge']['key']))
        assert local_closed == r['local_closed']
        assert {sha_key(k) for k in leaves} == {c['key_sha256'] for c in r['next_cores']}
        for c in r['next_cores']:
            _, _, leaf = h._canonical(c['source'], 0)
            assert leaf in leaves and h._load(leaf)['profile']['shape'] == c['shape']
            actual = []
            variables = {abs(l) for clause in c['source'] for l in clause}
            assert len(variables) <= 64 and c['counts'].get('candidate_budget_skips', 0) == 0
            for v in sorted(variables):
                pairs = sum(v in clause for clause in c['source']) * sum(-v in clause for clause in c['source'])
                if pairs > 64: continue
                target = check_additive_elimination(c['source'], dict(variable=v), Counter(), clause_growth_limit=64)
                actual.append(dict(variable=v, pairs=pairs, growth=len(target)-len(c['source'])))
            assert sorted(actual, key=lambda x:x['variable']) == sorted(c['first_pivots'], key=lambda x:x['variable'])
            assert min((x['growth'] for x in actual), default=None) == c['minimum_first_growth']
        assert not h.admitted; h.close(); assert sha(rebuilt) == before
        for field, t in [('nodes','cnf_patterns_v1'), ('sources','cnf_pattern_sources_v1'), ('residuals','cnf_residual_v1')]:
            assert r['audit'][field] == r['logical_table_digests'][t]['rows']
        assert r['audit']['bytes_unchanged'] and r['trial_replay']['bytes_unchanged']
        for metric, t in [('verified_trials','cnf_pivot_trials_v1'), ('verified_coupled_trials','cnf_coupled_trials_v1'), ('verified_growth_trials',TABLE)]:
            assert r['trial_replay']['counts'][metric] == r['logical_table_digests'][t]['rows']
    tests = Path('/tmp/oraclemachines-growth-tests.log').read_text()
    assert re.search(r'Ran 538 tests in [0-9.]+s\s+OK', tests)
    (out / 'full-validation.txt').write_text(tests)
    result = dict(script_sha256=sha(Path(__file__)), report_sha256=sha(report_path), python_tests=538,
        tests_sha256=sha(out/'full-validation.txt'), test_resource_warnings=tests.count('ResourceWarning: unclosed database'),
        independent_first_pivot_minimum=minimum, local_closed=local_closed,
        reconstructed_table_digests=r['logical_table_digests'], checks=dict(
            six_table_roundtrip=True, idempotent_reapplication=True, source_and_target_binding=True,
            every_new_node_admitted=True, warm_reuse_without_new_states=True, independent_next_core_enumeration=True))
    (out / 'validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__': main(Path(sys.argv[1]))
