#!/usr/bin/env python3
"""Propagate the saved growth escape through finite, checked alternative routes."""
from collections import Counter
import gzip
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_additive_elimination import lift_additive_elimination
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_growth_escape import TABLE
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_route_composition import CheckedRoutes, compose, verify_plan
from experiments.compare_cnf_growth_escape import restore_latest, apply_delta, digests, sha, unpack
from experiments.compare_cnf_pivot_alternatives import compressed


def main(out):
    out.mkdir(exist_ok=False)
    source_path = Path('experiments/results/cnf-growth-escape/report.json')
    source = json.loads(source_path.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); history = tmp / 'history'; started = time.perf_counter()
        prior, _ = restore_latest(history, tmp)
        d = source['delta']; assert sha(d['path']) == d['sha256']
        delta = tmp / 'growth'; unpack(d['path'], delta, d['database_sha256']); apply_delta(history, delta)
        assert digests(history) == source['logical_table_digests']
        r = dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            source_report_sha256=sha(source_path), restore_seconds=time.perf_counter()-started,
            fingerprints={p:sha(p) for p in ('experiments/cnf_route_composition.py',
                'experiments/compose_cnf_growth_routes.py', 'solver/test_cnf_route_composition.py')},
            options=source['options'], cases=source['cases'], limitations=[
                'Finite structural-coverage witness, not a SAT answer or proof of an efficient complete partition.',
                'All retained alternatives are checked before reuse; their preparation and history costs remain.',
                'Independent reference solver results do not refine the Python recognizer into Lean or certify a runtime bound.'])
        before = sha(history); h = BudgetedInventory(history, **source['options']); h.set_admission_budget(0)
        started = time.perf_counter(); roots = [h.inspect(c['source'])['root']['key'] for c in source['cases']]
        routes = CheckedRoutes(h)
        r['preparation_seconds'] = time.perf_counter()-started; r['route_checks'] = dict(routes.counts)
        counts = Counter(); started = time.perf_counter(); closed, plan = compose(h, roots, routes, counts)
        r['composition_seconds'] = time.perf_counter()-started; r['composition_counts'] = dict(counts)
        r['baseline_closed'] = source['baseline_closed']; r['final_closed'] = closed
        assert all(b or not a for a,b in zip(r['baseline_closed'],closed,strict=True))
        r['gains'] = [i for i,(a,b) in enumerate(zip(r['baseline_closed'],closed,strict=True)) if b and not a]
        counts = Counter(); started = time.perf_counter(); verify_plan(h, plan, [k for k,c in zip(roots,closed,strict=True) if c], routes, counts)
        r['resident_replay'] = dict(seconds=time.perf_counter()-started, counts=dict(counts))
        started = time.perf_counter(); payload = (encode(plan)+'\n').encode()
        certificate = out / 'coverage.json.gz'; certificate.write_bytes(gzip.compress(payload, mtime=0))
        r['certificate'] = dict(path=str(certificate), sha256=sha(certificate), bytes=len(payload),
            compressed_bytes=certificate.stat().st_size, serialization_seconds=time.perf_counter()-started,
            selected_rules=dict(Counter(x['rule']['kind'] for x in plan['steps'])))
        assert not h.admitted; h.close(); assert sha(history) == before
        print('composed', sum(closed), 'gains', r['gains'], flush=True)
        # Fresh verifier caches: recheck records and replay serialized finite
        # premises without invoking any recognition discovery or graph search.
        started = time.perf_counter(); h = BudgetedInventory(history, **source['options']); h.set_admission_budget(0)
        cold_routes = CheckedRoutes(h); counts = Counter()
        verify_plan(h, json.loads(gzip.decompress(certificate.read_bytes())), plan['roots'], cold_routes, counts)
        assert not h.admitted; h.close(); assert sha(history) == before
        r['cold_replay'] = dict(seconds=time.perf_counter()-started, route_checks=dict(cold_routes.counts),
            witness_checks=dict(counts), bytes_unchanged=True)
        # Reference solving is separate from discovery and plan-composition time.
        h = BudgetedInventory(history, **source['options']); h.set_admission_budget(0)
        endpoints = tmp / 'endpoints'; solver = AccountedResidualSolver(endpoints)
        started = time.perf_counter(); reference = []
        for _, payload in h.db.execute(f'SELECT id,payload FROM {TABLE}'):
            record = json.loads(payload); node = h._load(record['source']); child = h._load(record['edge']['key'])
            a, b = solver.solve(node['cnf']), solver.solve(child['cnf']); assert a['answer'] == b['answer']
            if b['answer']:
                model = {v:b['model'][i] for i,v in enumerate(record['edge']['names'],1)}
                lifted = lift_additive_elimination(node['cnf'],dict(variable=record['variable']),model,Counter(),
                    pair_limit=h.config['elimination_pair_limit'],clause_growth_limit=record['growth_limit'])
                assert holds(node['cnf'],lifted)
            reference.append(dict(kind='escape', source=a, target=b))
        for i in r['gains']:
            result = solver.solve(r['cases'][i]['source'])
            if result['answer']: assert holds(r['cases'][i]['source'],result['model'])
            reference.append(dict(kind='original', case=i, result=result))
        solver.close(); h.close(); assert sha(history) == before
        elapsed = time.perf_counter()-started; before_ep = sha(endpoints); started = time.perf_counter()
        solver = ResidualSolver(endpoints); verified = 0
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
            assert solver._read(key) is not None; verified += 1
        assert not solver.counts.get('expanded_nodes',0); solver.close(); assert sha(endpoints) == before_ep
        cold = time.perf_counter()-started; archive = out / 'endpoints.sqlite3.gz'; compressed(endpoints,archive)
        r['reference'] = dict(records=reference, seconds=elapsed, cold_seconds=cold, verified_nodes=verified,
            path=str(archive), sha256=sha(archive), database_sha256=before_ep, database_bytes=endpoints.stat().st_size)
        r['history_unchanged'] = True; r['logical_table_digests'] = digests(history)
    (out/'report.json').write_text(encode(r)+'\n'); print(json.dumps(dict(closed=sum(closed),gains=r['gains'])),flush=True)


if __name__ == '__main__': main(Path(sys.argv[1]))
