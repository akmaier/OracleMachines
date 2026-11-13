#!/usr/bin/env python3
"""Cold checked replay: all selected leaves, positive routes and reference DAG."""
from collections import Counter
from contextlib import ExitStack
import argparse
import json
from pathlib import Path
import re
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_affine_clause import restore_checkpoint, selected_frontiers, routes_for
from experiments.compare_cnf_split_batch import routes_for as old_routes
from experiments.compare_cnf_trace_reuse import read_archive
from experiments.compare_cnf_probe_continuation import sha, unpack
from experiments.validate_cnf_split_batch import check_coverage
from experiments.cnf_affine_clause import check_certificate, record_key
from experiments.cnf_affine_patterns import check_affine
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_route_composition import compose
from experiments.continue_cnf_learning import preserved_reference
from experiments.cnf_pattern_inventory import encode

TESTS = ['solver.test_cnf_affine_clause', 'solver.test_cnf_affine_patterns', 'solver.test_cnf_route_composition']


def validate(out, test_log):
    started = time.perf_counter()
    with tempfile.TemporaryDirectory() as td, ExitStack() as stack:
        tmp = Path(td); path = tmp/'history'
        stack.enter_context(patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('new recognition')))
        stack.enter_context(patch('experiments.cnf_affine_clause.extract_affine', side_effect=AssertionError('new extraction')))
        stack.enter_context(patch('experiments.cnf_affine_clause.discover', side_effect=AssertionError('new family discovery')))
        r, *evidence = restore_checkpoint(out/'report.json', path, tmp); before = sha(path)
        parent = json.loads(Path(r['parent']['path']).read_text())
        assert r['cases'] == parent['cases'] and r['options'] == parent['options']
        h = BudgetedInventory(path, **r['options']); h.set_admission_budget(0)
        old = old_routes(h, evidence[:4]); roots = [h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h, roots, old, Counter())[0] == r['baseline_closed'] == parent['final_closed']
        navigation, leaves = selected_frontiers(h, roots, old, r['baseline_closed'])
        selection = read_archive(r['selection']); assert selection['navigation'] == navigation
        assert len(selection['diagnostics']) == len(leaves) == r['acquisition']['tested']
        assert {row['source'] for row in selection['diagnostics']} == set(leaves)
        records = evidence[4]; by_source = {record['source']:record for record in records}
        assert len(by_source) == len(records) == r['acquisition']['accepted']
        accepted = set()
        for row in selection['diagnostics']:
            source = row['source']; node = h._load(source); cnf = node['cnf']
            summary = check_affine(cnf, node['profile']['evidence']['explicit_affine'], Counter())
            assert summary == row['affine'] and row['original_cases'] == leaves[source]
            assert row['variables'] == len({abs(l) for c in cnf for l in c}) and row['clauses'] == len(cnf)
            assert row['accepted'] == (summary['leftover_clauses'] <= 1)
            if row['accepted']:
                accepted.add(source)
                # JSON keys are strings; compare decoded objects, not sort order
                # (numeric 2 sorts before 10, but string "10" before "2").
                assert json.loads(encode(check_certificate(by_source[source]['proof'], expected_cnf=cnf))) == row['result']
            else: assert row['result'] is None
        assert accepted == set(by_source)
        print('selection and independent family proofs checked; replaying coverage', flush=True)
        routes = routes_for(h, evidence); check_coverage(h, routes, roots, r, r['baseline_closed'])
        after, after_leaves = selected_frontiers(h, roots, routes, r['final_closed'])
        assert after == read_archive(r['open_originals'])
        assert len(after['cases']) == r['remaining_originals'] and len(after_leaves) == r['remaining_selected_leaves']
        assert not h.admitted and r['acquisition']['new_inventory_states'] == 0
        h.close(); assert sha(path) == before == r['inventory_sha256']
        ep = r['reference']; ref = tmp/'reference'; assert sha(ep['path']) == ep['sha256']
        unpack(ep['path'], ref, ep['database_sha256']); seed = tmp/'reference-seed'; oldref = parent['reference']
        assert sha(oldref['path']) == oldref['sha256']; unpack(oldref['path'], seed, oldref['database_sha256'])
        assert preserved_reference(seed, ref) == ep['preserved_nodes'] == oldref['verified_nodes']
        solver = ResidualSolver(ref); refbefore = sha(ref)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'): assert solver._read(key) is not None
        assert len(solver.checked) == ep['verified_nodes']
        def check_answer(cnf, saved):
            result = solver.solve(cnf)
            assert not solver.counts.get('expanded_nodes',0)
            assert result['root'] == saved['root'] and result['answer'] == saved['answer']
            if result['answer']: assert holds(cnf, result['model'])
        by_id = {record_key(record):record for record in records}
        assert {row['id'] for row in ep['rows']} == set(by_id)
        for row in ep['rows']:
            proof = by_id[row['id']]['proof']; check_answer(proof['cnf'], row['result'])
            assert check_certificate(proof)['sat'] == row['result']['answer']
        assert {row['case'] for row in ep['originals']} == set(r['gains'])
        for row in ep['originals']: check_answer(r['cases'][row['case']]['source'], row['result'])
        solver.close(); assert sha(ref) == refbefore
    log = test_log.read_text(); match = re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK',log)
    assert match and int(match[1]) == 21
    (out/'targeted-validation.txt').write_text(log.rstrip()+'\n')
    result = dict(report_sha256=sha(out/'report.json'), script_sha256=sha(__file__),
        test_command='python3 -m unittest '+' '.join(TESTS), tests=int(match[1]),
        test_source_sha256={p.replace('.','/')+'.py':sha(p.replace('.','/')+'.py') for p in TESTS},
        test_log_sha256=sha(out/'targeted-validation.txt'), coverage=sum(r['final_closed']), gains=r['gains'],
        without_growth=sum(r['without_growth_closed']), selected_leaves=len(leaves), accepted=len(records),
        remaining_selected_leaves=len(after_leaves), history_bytes_unchanged=True, cold_new_discovery=False,
        inventory_audit_scope='Checked reachable route dependencies; no full rescan of unchanged unrelated rows.',
        splits=len(evidence[3]), learning_bases=len(evidence[1]), augmented_blocks=len(evidence[2]),
        reference_nodes=ep['verified_nodes'], preserved_reference_nodes=ep['preserved_nodes'],
        seconds=time.perf_counter()-started)
    (out/'validation.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result),flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('output',type=Path); p.add_argument('--test-log',type=Path,required=True)
    a = p.parse_args(); validate(a.output,a.test_log)
