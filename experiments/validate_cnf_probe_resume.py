#!/usr/bin/env python3
"""Independently rebuild a resumed probe pass and replay its complete evidence."""
from collections import Counter
import argparse
import gzip
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_probes import restore_report, opportunity
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_probe_continuation import TABLE, ContinuationRoutes
from experiments.cnf_route_composition import compose, verify_plan
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_probe_continuation import TABLES, apply_delta, digests, sha, sha_key, unpack, WithoutGrowth


def validate(out, test_log):
    r = json.loads((out/'report.json').read_text())
    for p,digest in r['fingerprints'].items(): assert sha(p) == digest,p
    assert sha(r['parent']['path']) == r['parent']['sha256']
    assert r['policy'] == dict(source_limit=4,state_limit=32) and r['width'] == 4
    assert r['gains'] == [i for i,(a,b) in enumerate(zip(r['baseline_closed'],r['final_closed'],strict=True)) if b and not a]
    admitted = set()
    for row in r['records']:
        keys = row['admitted_state_sha256']; assert len(keys) == len(set(keys)) <= 32
        assert len(keys) == row['admission_counts'].get('entered_states',0)
        assert row['inventory_counts'].get('inserted_nodes',0) <= len(keys)
        visits = row['search']['visits']; assert len(visits) == len({v['source'] for v in visits}) <= 4
        if row['search']['budget_stop'] is not None: assert len(keys) == 32
        admitted.update(keys)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp); seed = tmp/'seed'; prior = restore_report(r['parent']['path'],seed,tmp)
        assert prior['final_closed'] == r['baseline_closed']
        assert prior['options'] == r['options'] and prior['cases'] == r['cases']
        assert digests(seed) == r['seed_table_digests'] and sha(seed) == r['seed_database_sha256']
        d = r['delta']; assert sha(d['path']) == d['sha256']; delta = tmp/'delta'
        unpack(d['path'],delta,d['database_sha256']); assert delta.stat().st_size == d['database_bytes']
        history = tmp/'history'; shutil.copyfile(seed,history); apply_delta(history,delta)
        assert digests(history) == r['logical_table_digests']; before = sha(history)
        apply_delta(history,delta); assert sha(history) == before
        db = sqlite3.connect(delta)
        for t in TABLES:
            added = db.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
            assert added == r['delta_rows'][t] and r['preserved_rows'][t] == r['seed_table_digests'][t]['rows']
            assert r['logical_table_digests'][t]['rows'] == added + r['preserved_rows'][t]
            if t not in ('cnf_patterns_v1','cnf_probe_windows_v1',TABLE): assert added == 0
        assert all(sha_key(k) in admitted for k, in db.execute('SELECT id FROM cnf_patterns_v1'))
        assert r['delta_rows']['cnf_patterns_v1'] == sum(row['inventory_counts'].get('inserted_nodes',0) for row in r['records'])
        for t,counter,field in [(TABLE,'new_probe_continuations','new_continuation_kinds'),
                               ('cnf_probe_windows_v1','new_probe_windows','new_window_kinds')]:
            assert r['delta_rows'][t] == sum(row['counts'].get(counter,0) for row in r['records'])
            statuses = Counter(json.loads(p)['probing']['status'] for p, in db.execute(f'SELECT payload FROM {t}'))
            assert dict(statuses) == r[field]
        db.close(); h = BudgetedInventory(history,**r['options']); h.set_admission_budget(0)
        with patch('experiments.cnf_probe_continuation.discover_probes',side_effect=AssertionError('rediscovery')):
            with patch('experiments.cnf_probe_window.discover_probes',side_effect=AssertionError('rediscovery')):
                routes = ContinuationRoutes(h)
                roots = [h.inspect(c['source'])['root']['key'] for c in r['cases']]
                final,_ = compose(h,roots,routes,Counter()); assert final == r['final_closed']
                c = r['certificate']; assert sha(c['path']) == c['sha256']
                saved = json.loads(gzip.decompress(Path(c['path']).read_bytes()))
                verify_plan(h,saved,[k for k,b in zip(roots,final,strict=True) if b],routes,Counter())
                ablated,_ = compose(h,roots,WithoutGrowth(routes),Counter()); assert ablated == r['without_growth_closed']
        pending = sum(rec['edge'] is not None and h._load(rec['edge']['key']) is None for rec in routes.continuations.values())
        assert pending == r['pending_continuations'] and not h.admitted
        assert sha(out/'continuation-opportunity.json') == r['opportunity_sha256']
        assert opportunity(h,routes,roots) == json.loads((out/'continuation-opportunity.json').read_text())
        assert h.db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        ep = r['reference']; assert sha(ep['path']) == ep['sha256']; path = tmp/'endpoints'
        unpack(ep['path'],path,ep['database_sha256']); before_ep = sha(path); solver = ResidualSolver(path)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'): assert solver._read(key) is not None
        assert len(solver.checked) == ep['verified_nodes']
        assert {row['case'] for row in ep['originals']} == set(r['gains'])
        for row in ep['originals']:
            source = r['cases'][row['case']]['source']; _,_,key = solver._canonical(source)
            assert key == row['result']['root']; answer = solver.solve(source)
            assert answer['answer'] == row['result']['answer']
            if answer['answer']: assert holds(source,answer['model'])
        expected_local = {sha_key(k):rec for k,rec in routes.continuations.items()
            if rec['edge'] is not None and h._load(rec['edge']['key']) is not None
            and h._load(rec['edge']['key'])['summary']['closed']}
        assert {row['continuation_sha256'] for row in ep['local']} == set(expected_local)
        for row in ep['local']:
            rec = expected_local[row['continuation_sha256']]
            for name,cnf in [('source',h._load(rec['source'])['cnf']),('target',routes.verify(h,rec,Counter()))]:
                _,_,key = solver._canonical(cnf); assert key == row[name]['root']
                answer = solver.solve(cnf); assert answer['answer'] == row[name]['answer']
                if answer['answer']: assert holds(cnf,answer['model'])
            assert row['source']['answer'] == row['target']['answer']
        assert not solver.counts.get('expanded_nodes',0); solver.close(); assert sha(path) == before_ep
        h.close(); assert sha(history) == before
    log = test_log.read_text(); match = re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log)
    assert match and int(match[1]) >= 551
    (out/'full-validation.txt').write_text(log)
    evidence = dict(script_sha256=sha(Path(__file__)),report_sha256=sha(out/'report.json'),
        coverage=sum(final),gains=r['gains'],without_growth=sum(ablated),pending_continuations=pending,
        original_answers={str(row['case']):row['result']['answer'] for row in ep['originals']},
        reference_nodes=ep['verified_nodes'],python_tests=int(match[1]),test_log_sha256=sha(out/'full-validation.txt'),
        logical_table_digests=r['logical_table_digests'],cold_probe_discovery_disabled=True)
    (out/'validation.json').write_text(json.dumps(evidence,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],without_growth=sum(ablated))),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output',type=Path)
    parser.add_argument('--test-log',type=Path,default=Path('/tmp/oraclemachines-probe-resume-tests.log'))
    args = parser.parse_args(); validate(args.output,args.test_log)
