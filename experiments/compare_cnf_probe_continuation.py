#!/usr/bin/env python3
"""Advance one saved clear block per visited source in the retained history."""
from collections import Counter
import gzip
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_probe_window import choices
from experiments.cnf_probe_continuation import TABLE, ContinuationRoutes, search
from experiments.cnf_failed_literal import discover_probes, check_probes
from experiments.cnf_route_composition import compose, verify_plan
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_residual_dag import ResidualSolver, holds, restrict
from experiments.cnf_simplification import check_simplification
from experiments.compare_cnf_probe_window import (
    TABLES as OLD_TABLES, restore as restore_old, apply_delta as apply_old,
    digests as old_digests, sha, sha_key, unpack, compressed, audit,
    table_digest, WithoutGrowth)

TABLES = OLD_TABLES + (TABLE,)
PREVIOUS = Path('experiments/results/cnf-probe-window/report.json')


def digests(path):
    db = sqlite3.connect(path)
    try: return {t: table_digest(db,t) for t in TABLES}
    finally: db.close()


def restore(path, tmp):
    restore_old(path, tmp)
    r = json.loads(PREVIOUS.read_text())
    for item in r['inputs']: assert sha(item['path']) == item['sha256']
    for p, digest in r['fingerprints'].items(): assert sha(p) == digest, p
    d = r['delta']; assert sha(d['path']) == d['sha256']
    unpack(d['path'], tmp/'window', d['database_sha256']); apply_old(path, tmp/'window')
    assert old_digests(path) == r['logical_table_digests']
    db = sqlite3.connect(path)
    db.execute(f'CREATE TABLE {TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
    db.commit(); db.close()
    return r


def export_delta(seed, history, path):
    db = sqlite3.connect(history); out = sqlite3.connect(path)
    db.execute('ATTACH DATABASE ? AS old', (str(seed),)); preserved = {}; added = {}
    try:
        for t in TABLES:
            assert db.execute(f'SELECT count(*) FROM old.{t} o LEFT JOIN main.{t} n ON o.id=n.id WHERE n.id IS NULL OR n.payload!=o.payload').fetchone()[0] == 0
            preserved[t] = db.execute(f'SELECT count(*) FROM old.{t}').fetchone()[0]
            out.execute(f'CREATE TABLE {t} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
            out.executemany(f'INSERT INTO {t} VALUES (?,?)', db.execute(f'SELECT n.id,n.payload FROM main.{t} n WHERE NOT EXISTS (SELECT 1 FROM old.{t} o WHERE o.id=n.id) ORDER BY n.rowid'))
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
                    if old is not None and old != (payload,): raise ValueError('Conflicting continuation delta payload')
                    db.execute(f'INSERT OR IGNORE INTO {t} VALUES (?,?)', (key,payload))
    finally: delta.close(); db.close()


def matched_probes(h, routes, repeats=5):
    """Warm discovery+checking only: same next result, with/without rediscovery.

    Both modes rank the same source. Prior prefix validation is paid by the route
    loader, outside these warm measurements; full cold costs are reported too.
    Persistence and target recognition are excluded from BOTH microbenchmarks.
    """
    samples = []; records = list(routes.continuations.values())
    for repeat in range(repeats):
        for mode in (('shared','fresh') if repeat % 2 == 0 else ('fresh','shared')):
            counts = Counter(); started = time.perf_counter()
            for record in records:
                source, offset, width = record['source'], record['offset'], record['width']
                node, ranked = choices(h, source, 64, counts)
                selected = ranked[offset:offset+width] if mode == 'shared' else ranked[:offset+width]
                result = discover_probes(node['cnf'], 64, counts, _choices=selected)
                check_probes(node['cnf'], result, 64, counts, _choices=selected)
                if mode == 'shared':
                    expected = record['probing']
                else:
                    prefix = list(routes.windows[encode([source,width])]['probing']['attempts'])
                    for previous in range(width,offset,width):
                        prefix.extend(routes.continuations[encode([source,width,previous])]['probing']['attempts'])
                    expected = dict(record['probing'], attempts=prefix + record['probing']['attempts'])
                assert result == expected
            samples.append(dict(repeat=repeat, mode=mode, seconds=time.perf_counter()-started, counts=dict(counts)))
    return dict(records=len(records), samples=samples,
        scope='Matched warm ranking, probe discovery and checking only. Saved prefix already verified; persistence, target recognition and cold preparation excluded from both modes.')


def endpoints(h, routes, r, out, tmp):
    path = tmp/'endpoints'; solver = AccountedResidualSolver(path)
    started = time.perf_counter(); originals = []; local = []
    for i in r['gains']:
        answer = solver.solve(r['cases'][i]['source'])
        if answer['answer']: assert holds(r['cases'][i]['source'], answer['model'])
        originals.append(dict(case=i, result=answer))
    for identity, record in routes.continuations.items():
        if record['edge'] is None: continue
        child = h._load(record['edge']['key'])
        if child is None or not child['summary']['closed']: continue
        node = h._load(record['source']); target = routes.verify(h, record, Counter())
        a, b = solver.solve(node['cnf']), solver.solve(target); assert a['answer'] == b['answer']
        if b['answer']:
            last = record['probing']['attempts'][-1]; fixed = {last['variable']:not last['value']}
            _, closure = check_simplification(restrict(node['cnf'],fixed,Counter()), record['probing']['closure'],Counter(),pure=False)
            fixed.update(closure)
            model = {abs(l):False for c in node['cnf'] for l in c}; model.update(b['model']); model.update(fixed)
            assert holds(node['cnf'], model)
        local.append(dict(continuation_sha256=sha_key(identity), source=a, target=b))
    solver.close(); elapsed = time.perf_counter()-started
    before = sha(path); started = time.perf_counter(); solver = ResidualSolver(path); verified = 0
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
        assert solver._read(key) is not None; verified += 1
    assert not solver.counts.get('expanded_nodes',0); solver.close(); assert sha(path) == before
    cold = time.perf_counter()-started; archive = out/'endpoints.sqlite3.gz'; compressed(path,archive)
    return dict(originals=originals, local=local, seconds=elapsed, cold_seconds=cold, verified_nodes=verified,
        path=str(archive), sha256=sha(archive), database_sha256=before, database_bytes=path.stat().st_size)


def main(out):
    pipeline_started = time.perf_counter(); out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); seed = tmp/'seed'; history = tmp/'history'; started = time.perf_counter()
        prior = restore(seed,tmp); restore_seconds = time.perf_counter()-started
        r = dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            source_report_sha256=sha(PREVIOUS), options=prior['options'], cases=prior['cases'],
            fingerprints={p:sha(p) for p in ('experiments/cnf_probe_continuation.py',
                'experiments/compare_cnf_probe_continuation.py','solver/test_cnf_probe_continuation.py',
                'solver/fixtures/probe-continuation.json')},
            policy=dict(source_limit=4,state_limit=32), width=4, seed_table_digests=digests(seed),
            seed_database_bytes=seed.stat().st_size, seed_database_sha256=sha(seed),
            restore_seconds=restore_seconds, records=[], eligibility_seconds=0.0, limitations=[
                'At most one new four-candidate block per visited source, four distinct sources and 32 admitted states per original. Shared sources can advance again on a later original.',
                'Only the first 64 binary-frequency candidates are eligible. Exhausting them does not decide SAT or UNSAT.',
                'Reused development cases, no independent holdout, competitive solver speedup, peak RAM or unrestricted SAT complexity claim.',
                'Warm matched microbenchmark excludes paid prefix verification, persistence and target recognition in both modes; end-to-end phases are separate.'])
        started = time.perf_counter(); shutil.copyfile(seed,history); r['clone_seconds'] = time.perf_counter()-started
        h = BudgetedInventory(history,**r['options']); h.set_admission_budget(0); started = time.perf_counter()
        roots = [h.inspect(c['source'])['root']['key'] for c in r['cases']]; routes = ContinuationRoutes(h)
        baseline,_ = compose(h,roots,routes,Counter()); assert baseline == prior['final_closed']; assert not h.admitted
        r['baseline_closed'] = baseline; r['preparation_seconds'] = time.perf_counter()-started
        for i,root in enumerate(roots):
            started = time.perf_counter(); skip = compose(h,[root],routes,Counter())[0][0]
            r['eligibility_seconds'] += time.perf_counter()-started
            if skip: continue
            h.counts = Counter(); h.prepared.counts = Counter(); counts = Counter(); started = time.perf_counter()
            result = search(h,root,routes,counts,**r['policy'])
            covered,plan = compose(h,[root],routes,counts)
            if covered[0]: verify_plan(h,plan,[root],routes,counts)
            row = dict(case=i,seconds=time.perf_counter()-started,closed=covered[0],search=result,
                counts=dict(counts),inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
                admission_counts=dict(h.admission_counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
            assert len(h.admitted) <= 32 and h.counts.get('inserted_nodes',0) <= len(h.admitted)
            r['records'].append(row); (out/'checkpoint.json').write_text(encode(r)+'\n')
            print('case',i,'blocks',counts.get('new_probe_continuations',0),'states',len(h.admitted),'closed',covered[0],flush=True)
        started = time.perf_counter(); routes.refresh(h); final,plan = compose(h,roots,routes,Counter())
        r['recomposition_seconds'] = time.perf_counter()-started
        verify_plan(h,plan,[k for k,b in zip(roots,final,strict=True) if b],routes,Counter())
        r['final_closed'] = final; r['gains'] = [i for i,(a,b) in enumerate(zip(baseline,final,strict=True)) if b and not a]
        assert all(b or not a for a,b in zip(baseline,final,strict=True))
        r['without_growth_closed'],without = compose(h,roots,WithoutGrowth(routes),Counter())
        verify_plan(h,without,without['roots'],WithoutGrowth(routes),Counter())
        r['continuation_kinds'] = dict(Counter(rec['probing']['status'] for rec in routes.continuations.values()))
        r['pending_continuations'] = sum(rec['edge'] is not None and h._load(rec['edge']['key']) is None for rec in routes.continuations.values())
        r['matched_probes'] = matched_probes(h,routes)
        r['storage'] = h.storage(); h.close(); r['expanded_database_bytes'] = history.stat().st_size
        started = time.perf_counter(); certificate = out/'coverage.json.gz'; payload = (encode(plan)+'\n').encode()
        certificate.write_bytes(gzip.compress(payload,mtime=0))
        r['certificate'] = dict(path=str(certificate),sha256=sha(certificate),bytes=len(payload),
            compressed_bytes=certificate.stat().st_size,serialization_seconds=time.perf_counter()-started)
        delta = tmp/'delta'; started = time.perf_counter(); r['preserved_rows'],r['delta_rows'] = export_delta(seed,history,delta)
        archive = out/'proof-delta.sqlite3.gz'; compressed(delta,archive)
        r['delta'] = dict(path=str(archive),sha256=sha(archive),database_sha256=sha(delta),database_bytes=delta.stat().st_size,
            compressed_bytes=archive.stat().st_size,export_seconds=time.perf_counter()-started)
        started = time.perf_counter(); rebuilt = tmp/'rebuilt'; shutil.copyfile(seed,rebuilt); apply_delta(rebuilt,delta)
        r['logical_table_digests'] = digests(history); assert digests(rebuilt) == r['logical_table_digests']
        before = sha(rebuilt); apply_delta(rebuilt,delta); assert sha(rebuilt) == before
        r['rebuild_seconds'] = time.perf_counter()-started
        print('cold audit',flush=True); r['audit'] = audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        started = time.perf_counter(); h = BudgetedInventory(rebuilt,**r['options']); h.set_admission_budget(0)
        cold_routes = ContinuationRoutes(h); counts = Counter()
        verify_plan(h,json.loads(gzip.decompress(certificate.read_bytes())),plan['roots'],cold_routes,counts)
        assert compose(h,roots,cold_routes,Counter())[0] == final; assert not h.admitted
        r['cold_routes'] = dict(seconds=time.perf_counter()-started,counts=dict(cold_routes.counts),witness_counts=dict(counts))
        r['reference'] = endpoints(h,cold_routes,r,out,tmp)
        h.close(); assert sha(rebuilt) == before; r['cold_routes']['bytes_unchanged'] = True
        db = sqlite3.connect(delta); admitted = set().union(*(set(row['admitted_state_sha256']) for row in r['records']))
        assert all(sha_key(k) in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1')); db.close()
    r['pipeline_seconds'] = time.perf_counter()-pipeline_started
    (out/'report.json').write_text(encode(r)+'\n'); (out/'checkpoint.json').unlink()
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],new_rows=r['delta_rows'])),flush=True)


if __name__ == '__main__': main(Path(sys.argv[1]))
