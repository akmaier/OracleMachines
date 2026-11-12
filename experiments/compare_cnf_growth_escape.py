#!/usr/bin/env python3
"""One matched growth-two/three escape from the preserved coupled core."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_additive_elimination import check_additive_elimination
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_coupled_pivots import BudgetedInventory, FrontierIndex
from experiments.cnf_growth_escape import TABLE, search, trial_key, verify_escape
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_pivot_alternatives import alternatives, covered
from experiments.compare_cnf_clause_mask import table_digest
from experiments.compare_cnf_coupled_pivots import (
    TABLES as OLD_TABLES, restore_seed, apply_coupled_delta, digests as old_digests,
    replay, replay_coupled)
from experiments.compare_cnf_frontier_pivots import unpack
from experiments.compare_cnf_pivot_alternatives import compressed
from experiments.compare_cnf_retained_plans import sha, audit

TABLES = OLD_TABLES + (TABLE,)
PRIOR = Path('experiments/results/cnf-coupled-pivots-originals/report.json')
CORE = PRIOR.parent / 'core-admission-audit.json'


def restore_latest(path, tmp):
    prior, inputs = restore_seed('originals', path, tmp)
    r = json.loads(PRIOR.read_text())
    assert r['inputs'] == inputs and r['options'] == prior['options']
    assert r['cases'] == prior['cases']
    delta = r['delta']; assert sha(delta['path']) == delta['sha256']
    unpack(delta['path'], tmp / 'coupled', delta['database_sha256'])
    apply_coupled_delta(path, tmp / 'coupled')
    assert old_digests(path) == r['logical_table_digests']
    validation_path = PRIOR.parent.parent / 'cnf-coupled-pivots-validation/validation.json'
    validation = json.loads(validation_path.read_text())
    evidence = next(x for x in validation['evidence'] if x['suite'] == 'originals')
    assert evidence['report_sha256'] == sha(PRIOR)
    assert evidence['reconstructed_table_digests'] == old_digests(path)
    with sqlite3.connect(path) as db:
        db.execute(f'CREATE TABLE {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
    db.close()
    return r, [dict(path=str(p), sha256=sha(p)) for p in (PRIOR, CORE, validation_path)]


def digests(path):
    db = sqlite3.connect(path)
    try: return {t: table_digest(db, t) for t in TABLES}
    finally: db.close()


def export_delta(seed, history, path):
    db = sqlite3.connect(history); out = sqlite3.connect(path)
    db.execute('ATTACH DATABASE ? AS old', (str(seed),)); added = {}; preserved = {}
    try:
        for t in TABLES:
            assert db.execute(f'SELECT count(*) FROM old.{t} o LEFT JOIN main.{t} n ON o.id=n.id WHERE n.id IS NULL OR n.payload!=o.payload').fetchone()[0] == 0
            preserved[t] = db.execute(f'SELECT count(*) FROM old.{t}').fetchone()[0]
            out.execute(f'CREATE TABLE {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            rows = db.execute(f'SELECT n.id,n.payload FROM main.{t} n WHERE NOT EXISTS (SELECT 1 FROM old.{t} o WHERE o.id=n.id) ORDER BY n.rowid')
            out.executemany(f'INSERT INTO {t} VALUES (?,?)', rows)
            added[t] = out.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
        out.commit(); return preserved, added
    finally: out.close(); db.close()


def apply_delta(history, path):
    db = sqlite3.connect(history); delta = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    try:
        with db:
            for t in TABLES:
                db.execute(f'CREATE TABLE IF NOT EXISTS {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                for key, payload in delta.execute(f'SELECT id,payload FROM {t} ORDER BY rowid'):
                    old = db.execute(f'SELECT payload FROM {t} WHERE id=?', (key,)).fetchone()
                    if old is not None and old != (payload,):
                        raise ValueError('Conflicting growth delta payload')
                    db.execute(f'INSERT OR IGNORE INTO {t} VALUES (?,?)', (key, payload))
    finally: delta.close(); db.close()


def replay_all(h):
    successes, counts = replay(h)
    first = {k: json.loads(p) for k, p in h.db.execute('SELECT id,payload FROM cnf_pivot_trials_v1')}
    paired, pc = replay_coupled(h, first); successes.update(paired); counts.update(pc)
    records = {}
    for key, payload in h.db.execute(f'SELECT id,payload FROM {TABLE}'):
        record = json.loads(payload)
        if key != trial_key(record): raise ValueError('Incorrect growth trial identity')
        if verify_escape(h, record, counts): successes.add(record['source'])
        records[key] = record
    return successes, records, counts


def admission_diagnostic(h, key):
    node = h._load(key); counts = Counter(); started = time.perf_counter()
    # With <=64 opposing pairs, at most 64 new clauses can be constructed.
    # Thus allowance 64 loses no pivot solely to a growth rejection here.
    choices = alternatives(node['cnf'], None, counts, pair_limit=64, candidate_limit=64, clause_growth_limit=64)
    rows = []
    for row in choices:
        target = check_additive_elimination(node['cnf'], dict(variable=row['variable']), counts,
            pair_limit=64, clause_growth_limit=64)
        assert target == row['target']
        rows.append(dict(variable=row['variable'], pairs=row['pairs'], growth=len(target)-len(node['cnf'])))
    return dict(key_sha256=sha_key(key), source=node['cnf'], shape=node['profile']['shape'],
        first_pivots=rows, minimum_first_growth=min((r['growth'] for r in rows), default=None),
        counts=dict(counts), seconds=time.perf_counter()-started)


def sha_key(key): return hashlib.sha256(key.encode()).hexdigest()


def main(out):
    out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); seed = tmp / 'seed'; history = tmp / 'history'
        started = time.perf_counter(); prior, inputs = restore_latest(seed, tmp)
        restore_seconds = time.perf_counter()-started
        core = json.loads(CORE.read_text())
        assert core['report_sha256'] == sha(PRIOR) and len(core['cores']) == 1
        core = core['cores'][0]
        files = set(prior['fingerprints']) | {'experiments/cnf_growth_escape.py',
            'experiments/compare_cnf_growth_escape.py', 'solver/test_cnf_growth_escape.py'}
        r = dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip(),
            inputs=inputs, fingerprints={p: sha(p) for p in sorted(files)}, options=prior['options'],
            cases=prior['cases'], core_sha256=core['key_sha256'], policy=dict(growth_limit=3,state_limit=32),
            restore_seconds=restore_seconds, seed_table_digests=digests(seed),
            seed_database_bytes=seed.stat().st_size, seed_database_sha256=sha(seed), limitations=[
            'One deliberately selected preserved core; no independent holdout or general SAT speedup.',
            'Only the first projection gets allowance three. Descendants retain growth two and original recognition policy.',
            'Minimum among enumerated pair/candidate-capped pivots, not globally minimum computational cost.',
            'State cap bounds newly entered recognition states, not prior history, preparation, per-state work or process RAM.',
            'Whole-source gains require finite composition through open saved alternatives; no gain is claimed by this experiment.'])
        started = time.perf_counter(); shutil.copyfile(seed, history); r['clone_seconds'] = time.perf_counter()-started
        h = BudgetedInventory(history, **r['options']); h.set_admission_budget(0)
        started = time.perf_counter(); roots = [h.inspect(c['source'])['root']['key'] for c in r['cases']]
        successes, known, counts = replay_all(h)
        _, _, source = h._canonical(core['source'], 0)
        assert sha_key(source) == core['key_sha256'] and h._load(source)['kind'] == 'unresolved'
        assert not h.admitted
        r['seed_verification_seconds'] = time.perf_counter()-started
        r['seed_trial_replay_counts'] = dict(counts)
        baseline = [covered(h, k, successes, Counter()) for k in roots]
        assert baseline == prior['final_closed']; print('seed verified', flush=True)
        # Matched resident control: the same source and prepared history, growth two.
        counts = Counter(); started = time.perf_counter()
        control, stop = search(h, source, {}, counts, growth_limit=2)
        r['control'] = dict(seconds=time.perf_counter()-started, counts=dict(counts), records=control, budget_stop=stop)
        assert not control and stop is None and not h.admitted
        h.counts = Counter(); h.prepared.counts = Counter(); counts = Counter(); started = time.perf_counter()
        records, stop = search(h, source, known, counts, **r['policy'])
        for record in records:
            with h.db: h.db.execute(f'INSERT INTO {TABLE} VALUES (?,?)', (trial_key(record), encode(record)))
            known[trial_key(record)] = record
        r['expansion'] = dict(seconds=time.perf_counter()-started, counts=dict(counts),
            inventory_counts=dict(h.counts), prepared_counts=dict(h.prepared.counts),
            admission_counts=dict(h.admission_counts), admitted_state_sha256=sorted(map(sha_key,h.admitted)),
            records=records, budget_stop=stop)
        assert len(h.admitted) <= 32 and h.counts.get('inserted_nodes',0) <= len(h.admitted)
        # Local closure is distinct from closure through every saved open route.
        local_successes = {x['source'] for x in records if x['summary']['closed']}
        r['baseline_closed'] = baseline
        r['local_closed'] = len(local_successes)
        r['old_graph_with_closed_replacements'] = [covered(h, k, successes | local_successes, Counter()) for k in roots]
        before = h.storage(); counts = Counter(); started = time.perf_counter()
        repeated, stop = search(h, source, known, counts, growth_limit=3, state_limit=0)
        r['warm_reuse'] = dict(seconds=time.perf_counter()-started, counts=dict(counts))
        assert not repeated and stop is None and not h.admitted and h.storage() == before
        started = time.perf_counter(); index = FrontierIndex(h); leaves = set()
        for record in records: leaves.update(index.frontier(record['edge']['key']))
        r['next_cores'] = [admission_diagnostic(h, key) for key in sorted(leaves)]
        r['frontier_analysis_seconds'] = time.perf_counter()-started
        r['frontier_index_counts'] = dict(index.counts)
        r['storage'] = h.storage(); h.close()
        r['expanded_database_bytes'] = history.stat().st_size
        (out / 'checkpoint.json').write_text(encode(r)+'\n')
        print('escape', json.dumps(dict(trials=len(records), states=r['expansion']['admission_counts'],
            next_minima=[x['minimum_first_growth'] for x in r['next_cores']])), flush=True)
        started = time.perf_counter(); delta = tmp / 'delta'
        r['preserved_rows'], r['delta_rows'] = export_delta(seed, history, delta)
        archive = out / 'proof-delta.sqlite3.gz'; compressed(delta, archive)
        r['delta'] = dict(path=str(archive), sha256=sha(archive), database_sha256=sha(delta),
            database_bytes=delta.stat().st_size, compressed_bytes=archive.stat().st_size,
            export_seconds=time.perf_counter()-started)
        delta.unlink(); unpack(archive, delta, r['delta']['database_sha256'])
        rebuilt = tmp / 'rebuilt'; started = time.perf_counter(); shutil.copyfile(seed, rebuilt)
        apply_delta(rebuilt, delta); r['logical_table_digests'] = digests(history)
        assert digests(rebuilt) == r['logical_table_digests']
        before = sha(rebuilt); apply_delta(rebuilt, delta); assert sha(rebuilt) == before
        r['rebuild_seconds'] = time.perf_counter()-started
        print('complete cold audit', flush=True)
        r['audit'] = audit(rebuilt, AnchoredAdditiveInventory, r['options'])
        before = sha(rebuilt); started = time.perf_counter()
        h = BudgetedInventory(rebuilt, **r['options']); h.set_admission_budget(0)
        checked, saved, counts = replay_all(h)
        assert saved == known and checked == successes | local_successes
        assert [covered(h, k, checked, Counter()) for k in roots] == r['old_graph_with_closed_replacements']
        assert not h.admitted; h.close(); assert sha(rebuilt) == before
        r['trial_replay'] = dict(seconds=time.perf_counter()-started, counts=dict(counts), bytes_unchanged=True)
        # Verify new nodes really fall within this admission scope.
        db = sqlite3.connect(delta)
        admitted = set(r['expansion']['admitted_state_sha256'])
        assert all(sha_key(k) in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1'))
        db.close()
    (out / 'report.json').write_text(encode(r)+'\n'); (out / 'checkpoint.json').unlink()
    print(json.dumps(dict(closed=sum(baseline), new_rows=r['delta_rows'], expansion_seconds=r['expansion']['seconds'])), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('output', type=Path)
    main(p.parse_args().output)
