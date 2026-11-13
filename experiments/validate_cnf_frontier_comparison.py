#!/usr/bin/env python3
"""Cold original-frontier selection, both split obligations and five-list preservation."""
from collections import Counter
from contextlib import ExitStack
import argparse
import json
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_frontier_comparison import restore_checkpoint, select, diagnostics, POLICY, add_splits, add_learning, routes_for
from experiments.cnf_learning_batch import selection as learning_selection
from experiments.cnf_learning_continuation import record_key as learning_key
from experiments.cnf_probe_window import verify_window, record_key as window_key, TABLE as WINDOW_TABLE
from experiments.cnf_probe_continuation import record_key as continuation_key, TABLE as CONTINUATION_TABLE
from experiments.cnf_failed_literal import check_probes
from experiments.compare_cnf_split_batch import new_probes
from experiments.validate_cnf_split_batch import check_coverage, delta_file
from experiments.compare_cnf_trace_reuse import read_archive, archive_json
from experiments.compare_cnf_probe_continuation import sha, sha_key, unpack
from experiments.cnf_trace_split import verify, lift, record_key
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.continue_cnf_learning import preserved_reference
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_target_probe import remaining
from experiments.cnf_trace_reuse import check_pair, source_attempts
from experiments.cnf_residual_dag import restrict
from experiments.cnf_simplification import check_simplification

TEST_MODULES = ['solver.test_cnf_original_splits', 'solver.test_cnf_trace_split',
    'solver.test_cnf_split_batch', 'solver.test_cnf_split_frontier',
    'solver.test_cnf_route_composition', 'solver.test_cnf_affine_clause',
    'solver.test_cnf_probe_window', 'solver.test_cnf_target_probe',
    'solver.test_cnf_probe_continuation', 'solver.test_cnf_learning_continuation']
TEST_COMMAND = 'python3 -m unittest '+' '.join(TEST_MODULES)


def validate(out, test_log):
    started = time.perf_counter(); r = json.loads((out/'report.json').read_text())
    assert r['policy'] == POLICY
    with tempfile.TemporaryDirectory() as td, ExitStack() as stack:
        tmp = Path(td); seed = tmp/'seed'; path = tmp/'history'; delta = tmp/'new-delta'
        stack.enter_context(patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('new recognition')))
        for name in ('experiments.cnf_probe_window.discover_probes', 'experiments.cnf_probe_continuation.discover_probes',
                'experiments.cnf_trace_learning.discover_equivalence_probes',
                'experiments.cnf_learning_continuation.discover_equivalence_probes',
                'experiments.cnf_affine_clause.discover'):
            stack.enter_context(patch(name, side_effect=AssertionError('new discovery')))
        parent, *old_evidence = restore_checkpoint(Path(r['parent']['path']), seed, tmp)
        assert r['cases'] == parent['cases'] and r['options'] == parent['options']
        before = sha(seed); stage=tmp/'staged-clear-evidence';shutil.copyfile(seed,stage)
        h = BudgetedInventory(stage, **r['options']); h.set_admission_budget(0)
        routes = routes_for(h, old_evidence); roots = [h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h, roots, routes, Counter())[0] == r['baseline_closed'] == parent['final_closed']
        comparison=read_archive(r['options_comparison'])
        initial=select(h,routes,old_evidence,roots,r['baseline_closed'],Counter())
        assert comparison['before']==initial and initial['mode']=='original_leaf'
        source_key=initial['leaf']['source'];source=h._load(source_key)['cnf']
        delta_file(r['delta'],delta);probes=new_probes(delta);assert len(probes)==1
        item=probes[0];record=item['record'];identity=item['id']
        assert record['source']==source_key and record['probing']['status']=='clear' and record['edge'] is None
        if item['kind']=='probe_window':
            assert identity==window_key(record) and identity not in routes.windows
            assert encode(verify_window(h,record,Counter()))==encode(source)
            table=WINDOW_TABLE;routes.windows[identity]=record
        else:
            assert item['kind']=='probe_continuation' and identity==continuation_key(record) and identity not in routes.continuations
            assert encode(routes.verify(h,record,Counter()))==encode(source)
            table=CONTINUATION_TABLE;routes.continuations[identity]=record;routes.verified.add(identity)
        # Only add checked clear evidence before selecting a cofactor. Loading
        # the acquired children now would contaminate the historical ranking.
        with h.db:h.db.execute(f'INSERT INTO {table} VALUES (?,?)',(identity,encode(record)))
        stage_bytes=sha(stage)
        assert comparison['ordinary']==dict(visits=[dict(source=source_key,kind=item['kind'],offset=record.get('offset',0),status='clear')],stop='step_limit',distinct_sources=1,queued_sources=[source_key])
        preview=read_archive(r['ordinary_preflight'])
        assert preview['source']==source_key and preview['probing']==record['probing']
        assert preview['parent_validation_sha256']==sha(Path(r['parent']['path']).parent/'validation.json')
        target,fixed=check_probes(source,preview['probing'],4,Counter(),_choices=preview['choices'])
        assert encode(target)==encode(preview['target']) and encode(fixed)==encode(preview['fixed'])
        rows=[row for row in learning_selection(h,routes,Counter()) if row['source']==source_key and row['reason']=='ready']
        assert len(rows)==1 and comparison['learning_selection']==rows[0]
        additions=read_archive(r['learning_additions']);assert len(additions)==1
        learned=additions[0];identity=learning_key(learned)
        assert learned['base_sha256']==rows[0]['base_sha256'] and learned['offset']==rows[0]['next_offset']
        assert learned['probing']['status']=='clear' and learned['edge'] is None and identity not in routes.learned_blocks.records
        routes.learned_blocks.verify(h,learned,Counter())
        routes.learned_blocks.records[identity]=learned;routes.learned_blocks.verified.add(identity)
        staged_evidence=add_learning(old_evidence,additions)
        preflight=read_archive(r['comparison_preflight'])
        assert preflight['selection']==initial and preflight['learning_selection']==rows[0] and preflight['learning_record']==learned
        assert r['pipeline_plus_preflight_seconds']==r['pipeline_seconds']+preview['seconds']+preflight['total_seconds']
        assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']
        selected = select(h, routes, staged_evidence, roots, r['baseline_closed'], Counter())
        assert selected == read_archive(r['selection'])
        records = read_archive(r['splits']); assert records == [selected['record']]
        control = read_archive(r['matched_control']); source = h._load(records[0]['source'])['cnf']
        check_pair(source, control['attempts'], Counter())
        for attempt, edge in zip(control['attempts'], records[0]['edges'], strict=True):
            target, _ = check_simplification(restrict(source, {attempt['variable']: attempt['value']}, Counter()),
                attempt['certificate'], Counter(), pure=False)
            _, names, key = h._canonical(target, h._load(records[0]['source'])['depth'])
            assert edge == dict(key=key, names=names)
        assert not h.admitted; h.close(); assert sha(seed) == before and sha(stage)==stage_bytes
        print('cold expanded checkpoint and reference proofs', flush=True)
        restored, *evidence = restore_checkpoint(out/'report.json', path, tmp); assert restored == r
        assert evidence == add_learning(add_splits(old_evidence, records), additions)
        assert evidence[4] == old_evidence[4]  # preserve the affine closure
        before = sha(path); h = BudgetedInventory(path, **r['options']); h.set_admission_budget(0)
        routes = routes_for(h, evidence); check_coverage(h, routes, roots, r, r['baseline_closed'])
        d = read_archive(r['diagnostics'])
        assert diagnostics(h, routes, evidence, roots, r['final_closed']) == {k:v for k,v in d.items() if k != 'acquisition'}
        profiles = []
        for leaf in d['frontier']['leaves']:
            node = h._load(leaf['source']); attempts, _ = source_attempts(h, leaf['source'], Counter())
            cnf = node['cnf']
            profiles.append(dict(source=leaf['source'], source_sha256=sha_key(leaf['source']),
                variables=leaf['variables'], clauses=len(cnf), literals=sum(map(len,cnf)),
                clause_widths=dict(Counter(map(len,cnf))), outcomes=node['profile']['outcomes'],
                extracted_equations=len(node['profile']['evidence']['explicit_affine']['equations']),
                saved_pair_variables=[a['variable'] for a in attempts[::2]],
                untried_ordinary_variables=leaf['remaining_ranked_variables']))
        profiles_archive = archive_json(out/'frontier-profiles.json.gz', profiles)
        # Preserve both the selected original frontier and external split children.
        # This follows selected internal and ordinary routes, not all alternatives.
        navigation_started = time.perf_counter(); open_cases = [i for i,b in enumerate(r['final_closed']) if not b]
        open_rows = remaining(h, [dict(source=roots[i], target=roots[i]) for i in open_cases], routes, Counter())
        occurrences = {}
        for case, row in zip(open_cases, open_rows, strict=True):
            assert not row['closed']
            for leaf in row['leaves']:
                if not leaf['pending']: occurrences.setdefault(leaf['source'], set()).add(case)
        queue = [dict(row, selected_original_cases=sorted(occurrences.get(row['source'], set())))
            for row in d['learning'] if row['reason'] == 'ready']
        navigation = archive_json(out/'open-originals.json.gz', dict(cases=open_cases, frontiers=open_rows,
            ready_learning=queue, seconds=time.perf_counter()-navigation_started,
            scope='Selected internal/ordinary routes only; absence here does not prove an alternative source irrelevant.'))
        assert len(d['acquisition']) == 1 and not d['acquisition'][0]['skipped_covered']
        acquired = d['acquisition'][0]; assert acquired['source'] == records[0]['source']
        admitted = r['acquisition']['admitted_state_sha256']
        assert sorted(map(sha_key, acquired['admitted'])) == admitted and len(admitted) <= POLICY['state_limit']
        branch_admitted = set()
        for branch, edge in zip(acquired['branches'], records[0]['edges'], strict=True):
            assert branch['pending'] == (h._load(edge['key']) is None)
            assert not branch_admitted.intersection(branch['admitted']); branch_admitted.update(branch['admitted'])
        assert branch_admitted == set(acquired['admitted'])
        delta_file(r['delta'], delta); db = sqlite3.connect(delta); kinds = Counter()
        for key, payload in db.execute('SELECT id,payload FROM cnf_patterns_v1'):
            assert sha_key(key) in admitted and h._load(key) is not None
            kinds[json.loads(payload)['kind']] += 1
        db.close(); assert dict(kinds) == r['new_node_kinds']
        ep = r['reference']; ref = tmp/'reference'; assert sha(ep['path']) == ep['sha256']
        unpack(ep['path'], ref, ep['database_sha256']); old = parent['reference']
        assert sha(old['path']) == old['sha256']; unpack(old['path'], tmp/'reference-seed', old['database_sha256'])
        assert preserved_reference(tmp/'reference-seed', ref) == ep['preserved_nodes'] == old['verified_nodes']
        refbefore = sha(ref); solver = ResidualSolver(ref)
        for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'): assert solver._read(key) is not None
        assert len(solver.checked) == ep['verified_nodes']
        def answer(cnf, saved=None):
            _, _, key = solver._canonical(cnf)
            if saved is not None: assert key == saved['root']
            actual = solver.solve(cnf)
            assert not solver.counts.get('expanded_nodes', 0)
            if saved is not None: assert actual['answer'] == saved['answer']
            if actual['answer']: assert holds(cnf, actual['model'])
            return actual
        by_id = {record_key(record): record for record in records}
        assert {row['id'] for row in ep['rows']} == set(by_id)
        for row in ep['rows']:
            record = by_id[row['id']]; source = h._load(record['source'])['cnf']
            a = answer(source, row['source']); targets, _ = verify(h, record, Counter()); children = []
            for value, target, edge, saved in zip((False, True), targets, record['edges'], row['children'], strict=True):
                b = answer(target, saved); children.append(b['answer']); child = h._load(edge['key'])
                if child is not None:
                    canonical = answer(child['cnf']); assert canonical['answer'] == b['answer']
                    if canonical['answer']: assert holds(source, lift(h, record, value, canonical['model']))
            assert a['answer'] == any(children)
        assert {row['case'] for row in ep['originals']} == set(r['gains'])
        for row in ep['originals']: answer(r['cases'][row['case']]['source'], row['result'])
        solver.close(); assert sha(ref) == refbefore
        assert not h.admitted and h.db.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        h.close(); assert sha(path) == before
    log = test_log.read_text(); match = re.search(r'Ran (\d+) tests in [0-9.]+s\s+OK', log)
    assert match and int(match[1]) == 41
    (out/'targeted-validation.txt').write_text(log.rstrip()+'\n')
    result = dict(report_sha256=sha(out/'report.json'), script_sha256=sha(__file__), test_command=TEST_COMMAND,
        tests=int(match[1]), test_log_sha256=sha(out/'targeted-validation.txt'),
        test_source_sha256={m.replace('.', '/')+'.py':sha(m.replace('.', '/')+'.py') for m in TEST_MODULES},
        all_saved_pairs_ranked=selected.get('all_saved_pairs_ranked'), selection_mode=selected['mode'],
        staged_clear_evidence_only=True, ordinary_status=item['record']['probing']['status'],
        learned_status=learned['probing']['status'], initial_saved_pairs=initial['saved_pairs'], final_saved_pairs=selected['saved_pairs'],
        splits=len(evidence[3]), affine_family_records=len(evidence[4]),
        learning_bases=len(evidence[1]), augmented_blocks=len(evidence[2]), coverage=sum(r['final_closed']),
        gains=r['gains'], without_growth=sum(r['without_growth_closed']),
        remaining_leaves=[[leaf['variables'], leaf['clauses']] for leaf in d['frontier']['leaves']],
        pending=len(d['frontier']['pending']), new_pattern_nodes=sum(kinds.values()),
        open_originals=navigation, frontier_profiles=profiles_archive,
        reference_nodes=ep['verified_nodes'], preserved_reference_nodes=ep['preserved_nodes'],
        history_bytes_unchanged=True, cold_new_discovery=False, seconds=time.perf_counter()-started)
    (out/'validation.json').write_text(json.dumps(result, sort_keys=True, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('output', type=Path); p.add_argument('--test-log', type=Path, required=True)
    a = p.parse_args(); validate(a.output, a.test_log)
