#!/usr/bin/env python3
"""Frozen synthetic transfer stream with exact, subsumption and empty controls."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import random
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.cnf_coverage_union import inventory
from experiments.cnf_coupled_pivots import BudgetedInventory, AdmissionExhausted
from experiments.cnf_expanded_coverage import owner
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_positive_bundle import TABLES, capture_reads
from experiments.cnf_projection_bridge import verify_positive
from experiments.cnf_residual_dag import normalize
from experiments.cnf_subsumption_transfer import CoreIndex, minimal, check_transfer
from experiments.compare_cnf_coverage_union import no_acquisition

PARENT = Path('experiments/results/cnf-coverage-union/report.json')
PARENT_SHA = 'd2bbb9591401978393da509cb2309312aa71b0927699cc221a3cec4c5340df30'
TEMPLATE = 'a9e2ae2f969428ac5ad0f7d71f8860d398c056b212b85826fc16014be83fa3cc'
OPTIONS = dict(max_depth=2, probe_limit=4, learn_limit=4, clause_growth_limit=2)
MODES = ('empty', 'exact', 'subsumption')
STATE_LIMIT = 32
SEED = 20261115184918
TABLE = 'cnf_transfer_queries_v1'
FILES = ['experiments/cnf_subsumption_transfer.py',
         'experiments/compare_cnf_subsumption_transfer.py',
         'solver/test_cnf_subsumption_transfer.py']


def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def key_sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def source_id(source):
    return key_sha(encode(normalize(source)[0]))


def load(path):
    return json.loads(Path(path).read_text())


def archived(path, value):
    raw = encode(value).encode(); Path(path).write_bytes(gzip.compress(raw, mtime=0))
    return dict(path=str(path), sha256=sha(path), bytes=len(raw), compressed_bytes=Path(path).stat().st_size)


def unpack(entry):
    assert sha(entry['path']) == entry['sha256']
    return json.loads(gzip.decompress(Path(entry['path']).read_bytes()))


def install_rows(path, rows):
    with sqlite3.connect(path) as db:
        for table in TABLES:
            db.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
            db.executemany(f'INSERT INTO {table} VALUES (?,?)', rows[table])


def verify_bank(bank, path):
    """Cold positive verification; never turn a partial bundle into a planner."""
    started = time.perf_counter(); install_rows(path, bank['rows'])
    h = inventory(path, bank['policy'])
    try:
        h.db.execute('PRAGMA query_only=ON')
        view = owner(h, bank['root'])
        assert view._canonical(bank['source'], bank['depth'])[2] == bank['root']
        assert key_sha(bank['root']) == bank['id'] == TEMPLATE
        with no_acquisition(), capture_reads(h) as capture:
            counts = Counter()
            result = verify_positive(h, bank['proof'], [bank['root']], [[], [], [], [], []], [], counts)
        assert not capture.counts['missing_lookups'] and capture.export() == bank['rows']
        return dict(seconds=time.perf_counter()-started, steps=len(result.justified),
                    counts=dict(counts), database_bytes=path.stat().st_size)
    finally:
        h.close()


def make_bank(parent_bundle, tmp):
    tick = time.perf_counter()
    key = next(k for k, _ in parent_bundle['rows']['cnf_patterns_v1'] if key_sha(k) == TEMPLATE)
    identity = json.loads(key); source = identity[-1]
    all_steps = parent_bundle['parts']['retained']['proof']['steps']
    by_key = {s['source']: s for s in all_steps}; needed = set(); todo = [key]
    while todo:
        current = todo.pop()
        if current in needed:
            continue
        needed.add(current); todo.extend(by_key[current]['children'])
    proof = dict(format=parent_bundle['parts']['retained']['proof']['format'], roots=[key],
                 steps=[step for step in all_steps if step['source'] in needed])
    path = tmp/'capture'; install_rows(path, parent_bundle['rows'])
    policy = parent_bundle['claim']['policies']['retained']; h = inventory(path, policy)
    try:
        h.db.execute('PRAGMA query_only=ON'); counts = Counter()
        with no_acquisition(), capture_reads(h) as capture:
            verify_positive(h, proof, [key], [[], [], [], [], []], [], counts)
        assert not capture.counts['missing_lookups']
        bank = dict(id=TEMPLATE, root=key, source=source, depth=identity[2], policy=policy,
                    proof=proof, rows=capture.export())
    finally:
        h.close()
    return bank, dict(seconds=time.perf_counter()-tick, steps=len(proof['steps']),
                      rows={t:len(rows) for t, rows in bank['rows'].items()})


def new_cases(template):
    rng = random.Random(SEED); source = [list(c) for c in template]
    _, certificate, _ = minimal(source, Counter())
    normalized, _ = normalize(source)
    assert encode(normalized) == encode(source)
    # Reduction compacts names: added/removed clauses need the original source
    # coordinates, not the smaller core's compacted variable identifiers.
    core = [source[i] for i in certificate['kept']]
    n = max(abs(l) for c in source for l in c)
    cases = []

    def redundant(count):
        added = [list(core[i % len(core)]) + [(n+i+1)*rng.choice((-1, 1))]
                 for i in range(count)]
        assert all(any(set(old) <= set(clause) for old in source) for clause in added)
        return source + added

    def rename(cnf, shuffled):
        names = sorted({abs(l) for c in cnf for l in c}); targets = [101+17*v for v in names]
        if shuffled:
            rng.shuffle(targets)
        mapping = dict(zip(names, targets))
        return [[mapping[abs(l)]*(1 if l > 0 else -1) for l in reversed(c)] for c in reversed(cnf)]

    for i, size in enumerate((2, 4, 8, 16, 32, 64)):
        cases.append(dict(group='redundant_extension', size=size, source=redundant(size)))
    for shuffled, group in ((False, 'ordered_rename'), (True, 'permuted_rename')):
        for size in (3, 6, 9, 12, 24, 48):
            cases.append(dict(group=group, size=size, source=rename(redundant(size), shuffled)))
    for i in range(6):
        a = n+100+3*i
        cases.append(dict(group='disconnected_mixture', size=i,
            source=redundant(i+1)+[[a, a+1], [-a-1, a+2], [-a-2, a]]))
        cases.append(dict(group='connected_mixture', size=i,
            source=redundant(i+7)+[[i+1, a], [-a, (i+9)]]))
        changed = redundant(i+11)
        if i < 3:
            changed += [[-(i+1)]]
        else:
            changed.remove(list(core[i]))
        cases.append(dict(group='invalidating_edit', size=i, source=changed))
    for size in (12, 18, 24, 30, 36, 48):
        cnf = [[v*rng.choice((-1, 1)) for v in rng.sample(range(1, size+1), 3)]
               for _ in range(round(4.25*size))]
        cases.append(dict(group='novel_random', size=size, source=cnf))
    assert len(cases) == 42 and len({source_id(c['source']) for c in cases}) == 42
    return cases


def ordinary(h, source):
    try:
        edge = h._edge(source, h.config['max_depth'])
    except AdmissionExhausted:
        return None, False, True
    return edge['key'], h._load(edge['key'])['summary']['closed'], False


def cold_replay(path, protocol, bank, mode, records):
    started = time.perf_counter(); h = BudgetedInventory(path, **protocol['options'])
    h.set_admission_budget(0)
    try:
        h.db.execute('PRAGMA query_only=ON')
        with no_acquisition():
            nodes = 0
            for key, _ in h.db.execute('SELECT id,payload FROM cnf_patterns_v1'):
                assert owner(h, key)._load(key) is not None; nodes += 1
            for i, row in enumerate(records):
                source = protocol['cases'][i]['source']
                saved = json.loads(h.db.execute(f'SELECT payload FROM {TABLE} WHERE id=?', (str(i),)).fetchone()[0])
                assert saved == row and row['source_sha256'] == source_id(source)
                if row['route'] == 'subsumption':
                    check_transfer(source, bank['source'], bank['id'], row['certificate'])
                    assert row['closed']
                elif row['route'] == 'exact':
                    assert normalize(source)[0] == normalize(bank['source'])[0] and row['closed']
                elif row['root'] is not None:
                    assert h._canonical(source, h.config['max_depth'])[2] == row['root']
                    assert h._load(row['root'])['summary']['closed'] == row['closed']
                else:
                    assert row['capped'] and not row['closed']
                assert row['entered_states'] <= protocol['state_limit']
        return dict(seconds=time.perf_counter()-started, nodes=nodes, queries=len(records),
                    no_acquisition=True, capped_outcomes_remain_unknown=True)
    finally:
        h.close()


def worker(out, protocol, bank, mode):
    out.mkdir(exist_ok=False); began = time.perf_counter(); preparation = {}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); index = None
        if mode != 'empty':
            preparation['bank'] = verify_bank(bank, tmp/'bank')
            tick = time.perf_counter(); index = CoreIndex({bank['id']: bank['source']}) if mode=='subsumption' else None
            preparation['index_seconds'] = time.perf_counter()-tick
            preparation['index_counts'] = dict(index.counts) if index else {}
        ready = time.perf_counter(); path = tmp/'history'; h = BudgetedInventory(path, **protocol['options'])
        h.db.execute(f'CREATE TABLE {TABLE} (id TEXT PRIMARY KEY, payload TEXT NOT NULL)'); h.db.commit()
        records = []
        try:
            initial_bytes = path.stat().st_size
            for i, case in enumerate(protocol['cases']):
                source = case['source']; tick = time.perf_counter(); counts = Counter()
                h.counts = Counter(); h.prepared.counts = Counter(); h.set_admission_budget(protocol['state_limit'])
                certificate = None; route = 'ordinary'; root = None; closed = False; capped = False
                before = h.db.execute('SELECT count(*) FROM cnf_patterns_v1').fetchone()[0]
                if mode == 'exact':
                    if normalize(source, counts)[0] == normalize(bank['source'], counts)[0]:
                        route = 'exact'; closed = True
                elif mode == 'subsumption':
                    certificate = index.lookup(source, counts)
                    if certificate is not None:
                        check_transfer(source, bank['source'], bank['id'], certificate, counts)
                        route = 'subsumption'; closed = True
                if not closed:
                    root, closed, capped = ordinary(h, source)
                after = h.db.execute('SELECT count(*) FROM cnf_patterns_v1').fetchone()[0]
                row = dict(case=i, group=case['group'], source_sha256=source_id(source), route=route,
                    root=root, closed=closed, capped=capped, certificate=certificate,
                    entered_states=len(h.admitted), stored_states=after-before,
                    lookup_counts=dict(counts), recognition_counts=dict(h.counts),
                    probe_attempts=h.counts.get('probe_attempts', 0))
                with h.db:
                    h.db.execute(f'INSERT INTO {TABLE} VALUES (?,?)', (str(i), encode(row)))
                # Persist the measured total separately: a timestamp cannot
                # include writing itself. The operation timer includes the
                # first complete semantic journal insertion above.
                row['operation_seconds'] = time.perf_counter()-tick
                with h.db:
                    h.db.execute(f'UPDATE {TABLE} SET payload=? WHERE id=?', (encode(row), str(i)))
                records.append(row)
            query_seconds = time.perf_counter()-ready
            dbbytes = path.stat().st_size
        finally:
            h.close()
        before_hash = sha(path); replay = cold_replay(path, protocol, bank, mode, records)
        assert sha(path) == before_hash
        tick = time.perf_counter()
        archive_path = out/'history.sqlite3.gz'; archive_path.write_bytes(gzip.compress(path.read_bytes(), mtime=0))
        archive_seconds = time.perf_counter()-tick
        result = dict(mode=mode, preparation=preparation, preparation_seconds=ready-began,
            query_seconds=query_seconds, records=records, cold=replay,
            database_bytes=dbbytes, database_growth=dbbytes-initial_bytes,
            archive=dict(path=str(archive_path), sha256=sha(archive_path), database_sha256=before_hash,
                         compressed_bytes=archive_path.stat().st_size), archive_seconds=archive_seconds,
            total_seconds=time.perf_counter()-began)
        result['groups'] = {group: dict(cases=sum(c['group']==group for c in protocol['cases']),
            covered=sum(x['closed'] for x in records if x['group']==group),
            reuse_hits=sum(x['route']!='ordinary' for x in records if x['group']==group),
            entered=sum(x['entered_states'] for x in records if x['group']==group),
            stored=sum(x['stored_states'] for x in records if x['group']==group),
            probes=sum(x['probe_attempts'] for x in records if x['group']==group),
            operation_seconds=sum(x['operation_seconds'] for x in records if x['group']==group))
            for group in sorted({c['group'] for c in protocol['cases']})}
        (out/'report.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
        return {k:result[k] for k in ('mode','preparation_seconds','query_seconds','database_growth','groups')}


def run(out):
    started = time.perf_counter(); out.mkdir(exist_ok=False)
    assert sha(PARENT) == PARENT_SHA; parent = load(PARENT); bundle = unpack(parent['bundle'])
    with tempfile.TemporaryDirectory() as td:
        bank, extraction = make_bank(bundle, Path(td))
    cases = new_cases(bank['source'])
    old_inputs = {source_id(c) for c in bundle['claim']['sources']}
    old_nodes = {source_id(json.loads(k)[-1]) for k, _ in bundle['rows']['cnf_patterns_v1']}
    assert all(source_id(c['source']) not in old_inputs | old_nodes for c in cases)
    protocol = dict(seed=SEED, options=OPTIONS, state_limit=STATE_LIMIT, cases=cases,
        template_id=TEMPLATE, modes=list(MODES), repetitions=2,
        history_policy='Each arm starts empty and persists fallback states across its fixed 42-input stream; prepared arms additionally receive one checked positive template.',
        novelty_scope=dict(historical_inputs=len(old_inputs), selected_history_cnf_nodes=len(old_nodes),
                           absent_from_both=True),
        limitations=['Constructed motif-transfer probes plus six random inputs, not an unbiased or industrial holdout.',
            'Sorted-name normalization is incomplete for arbitrary permutations; no semantic equivalence oracle is used.',
            'Only whole-formula matching is attempted before the unchanged bounded planner. Connected/disconnected mixtures may miss.',
            'A miss, cap or unclosed plan is unknown coverage, never UNSAT. No SAT solver is invoked.',
            'Results persist across queries within an arm, with a fresh 32-state allowance per query. Earlier fallbacks may help later queries.',
            'Positive template verification is charged once per prepared arm; original acquisition remains a prerequisite.',
            'Peak RAM and generalization beyond these generated inputs are unmeasured.'])
    protocol_path = out/'protocol.json'; protocol_path.write_text(json.dumps(protocol, indent=2, sort_keys=True)+'\n')
    bank_entry = archived(out/'template-proof.json.gz', bank)
    preservation = load('experiments/results/cnf-coverage-union/validation.json')
    files = dict(preservation['source_fingerprints']); files.update({p:sha(p) for p in FILES})
    for p, digest in files.items():
        assert sha(p) == digest
    frozen = dict(parent=dict(path=str(PARENT), sha256=PARENT_SHA), bank=bank_entry,
        protocol=dict(path=str(protocol_path), sha256=sha(protocol_path)), fingerprints=files,
        template_extraction=extraction, source_commit=subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip())
    (out/'frozen.json').write_text(json.dumps(frozen, indent=2, sort_keys=True)+'\n')
    print(json.dumps(dict(phase='frozen before acquisition', cases=len(cases), protocol_sha256=sha(protocol_path),
                         bank_bytes=bank_entry['compressed_bytes'], template_steps=extraction['steps'])), flush=True)
    samples = []
    for repeat, order in enumerate((MODES, tuple(reversed(MODES)))):
        for mode in order:
            destination = out/f'{mode}-{repeat}'
            command = [sys.executable, str(Path(__file__).resolve()), '--worker', mode,
                       '--protocol', str(protocol_path.resolve()), '--bank', str(Path(bank_entry['path']).resolve()),
                       str(destination.resolve())]
            tick = time.perf_counter(); process = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
            (out/f'{mode}-{repeat}.txt').write_text(process.stdout+process.stderr)
            if process.returncode:
                raise RuntimeError('Transfer worker failed; output preserved')
            row = load(destination/'report.json')
            samples.append(dict(mode=mode, repeat=repeat, path=str(destination/'report.json'),
                                sha256=sha(destination/'report.json'), process_seconds=time.perf_counter()-tick))
            print(json.dumps(dict(mode=mode, repeat=repeat, covered=sum(x['closed'] for x in row['records']),
                hits=sum(x['route']!='ordinary' for x in row['records']), entered=sum(x['entered_states'] for x in row['records']),
                probes=sum(x['probe_attempts'] for x in row['records']), query_seconds=row['query_seconds'])), flush=True)
    assert sha(protocol_path) == frozen['protocol']['sha256']
    for p, digest in files.items():
        assert sha(p) == digest
    for mode in MODES:
        a, b = [load(s['path']) for s in samples if s['mode']==mode]
        for x, y in zip(a['records'], b['records'], strict=True):
            assert {k:v for k,v in x.items() if k!='operation_seconds'} == {k:v for k,v in y.items() if k!='operation_seconds'}
    result = dict(**frozen, samples=samples, pipeline_seconds=time.perf_counter()-started,
                  format='subsumption-core-transfer-study-v1')
    (out/'report.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output', type=Path)
    parser.add_argument('--worker', choices=MODES); parser.add_argument('--protocol', type=Path)
    parser.add_argument('--bank', type=Path); args = parser.parse_args()
    if args.worker:
        bank = json.loads(gzip.decompress(args.bank.read_bytes()))
        print(json.dumps(worker(args.output, load(args.protocol), bank, args.worker)))
    else:
        run(args.output)
