#!/usr/bin/env python3
"""Cold replay matched first-split arms, their shared seed and retained union.

Fresh structural recognition and fresh reference solving are forbidden. Timing
is reported from the producer, not from this deliberately redundant audit.
"""
from collections import Counter
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import statistics
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_split_cost import (restore_checkpoint, restore_base,
    BASE, POLICY, routes_for, add_splits, select, BudgetedInventory, full,
    verify_split, verify_positive, read_archive, sha, sha_key, unpack, apply_delta,
    check_delta, digests, candidates)
from experiments.cnf_trace_reuse import read_attempt
from experiments.cnf_trace_split import lift, record_key
from experiments.cnf_route_composition import compose
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_source_local import SourceProbeRoutes, continuation_key
from experiments.validate_cnf_warm_transfer import path, shape
from experiments.continue_cnf_local_forcing import profile


def load_report(bound):
    assert sha(bound['path']) == bound['sha256']
    return json.loads(Path(bound['path']).read_text())


def merge_checked(bound, history, delta, options):
    assert sha(bound['path']) == bound['sha256']
    unpack(bound['path'], delta, bound['database_sha256'])
    apply_delta(history, delta)
    counts = check_delta(history, delta, options)
    before = sha(history)
    apply_delta(history, delta)
    assert sha(history) == before
    return counts


def novel_patterns(delta):
    with sqlite3.connect(delta) as db:
        return {sha_key(k) for k, in db.execute('SELECT id FROM cnf_patterns_v1')}


def split_findings(h, routes, solver, record):
    source = record['source']
    targets, _ = verify_split(h, record, Counter())
    branches = []
    for value, edge, target in zip((False, True), record['edges'], targets, strict=True):
        answer = solver.solve(target)
        child = h._load(edge['key'])
        item = dict(value=value, target_sha256=sha_key(edge['key']),
            target_shape=shape(target), reference_answer=answer['answer'],
            closed=bool(child) and compose(h, [edge['key']], routes, Counter())[0][0],
            prefix=path(h, edge['key']))
        if child is not None and answer['answer']:
            local = solver.solve(child['cnf'])
            assert local['answer']
            assert holds(h._load(source)['cnf'], lift(h, record, value, local['model']))
            item['lifted_source_model_checked'] = True
        branches.append(item)
    return dict(source_sha256=sha_key(source), source_shape=shape(h._load(source)['cnf']),
        variable=read_attempt(h, source, record['references'][0], Counter())['variable'],
        branches=branches)


def validate(out):
    started = time.perf_counter()
    r = json.loads((out/'report.json').read_text())
    for name, digest in r['fingerprints'].items():
        assert sha(name) == digest
    assert Path(r['parent']['path']) == BASE
    parent = load_report(r['parent'])
    common = load_report(r['common'])
    before = read_archive(parent['next_selection'])
    target = before['source']
    result = dict(report_sha256=sha(out/'report.json'), arms=[])
    findings = dict(arms=[], selected_originals=[dict(index=i,
        case=r['cases'][i]['original_case']) for i in before['selected_original_cases']])
    assert common['source_sha256'] == sha_key(target)
    assert common['selected_original_cases'] == before['selected_original_cases']
    # This experiment's contrast is valid only after clear, admission-free probes.
    assert common['status'] == 'clear' and not common['pending']
    assert not common['admitted_state_sha256']
    assert [(x['repeat'], x['variable']) for x in r['arms']] == [(0,17),(0,1),(1,1),(1,17)]
    assert r['policy'] == POLICY
    with tempfile.TemporaryDirectory() as td, patch.object(BudgetedInventory,
            '_discover', side_effect=AssertionError('new recognition during replay')):
        tmp = Path(td)
        tick = time.perf_counter()
        restored, *evidence = restore_checkpoint(out/'report.json', tmp/'final', tmp)
        assert restored == r
        result.update(restore_seconds=time.perf_counter()-tick,
            evidence_counts=list(map(len, evidence)))
        ct = tmp/'controls'; ct.mkdir()
        seed = ct/'seed'
        original, *base_evidence = restore_base(BASE, seed, ct)
        assert original == parent and digests(seed) == r['seed_table_digests']
        seed_sha = sha(seed)
        shared = ct/'shared'; shutil.copyfile(seed, shared)
        result['common_delta_counts'] = merge_checked(common['delta'], shared,
            ct/'common-delta', r['options'])
        assert digests(shared) == common['logical_table_digests']
        shared_sha = sha(shared)
        h = BudgetedInventory(shared, **r['options']); h.set_admission_budget(0)
        try:
            operation = read_archive(common['operation'])
            record = operation['record']
            assert operation['kind'] == 'probe_continuation' and record['source'] == target
            local = SourceProbeRoutes(h, target); key = continuation_key(record)
            assert local.continuations[key] == record
            local._verify_saved(h, key, Counter())
            assert record['probing']['status'] == 'clear' and record['edge'] is None
            findings['common'] = dict(offset=record['offset'], status='clear',
                attempts=[dict(variable=a['variable'], value=a['value'])
                    for a in record['probing']['attempts']])
            routes = routes_for(h, base_evidence)
            ranked = candidates(h, target, routes, Counter(), candidate_limit=POLICY['candidate_limit'])
            initial = {x['rank'][-1]:x for x in ranked}
            assert not h.admitted
        finally:
            h.close()
        ep = r['reference']; assert sha(ep['path']) == ep['sha256']
        unpack(ep['path'], tmp/'reference', ep['database_sha256'])
        solver = ResidualSolver(tmp/'reference')
        repeats = {}
        try:
            with patch.object(solver, '_expand', side_effect=AssertionError('fresh reference search')):
                for bound in r['arms']:
                    ar = load_report(bound); variable = bound['variable']
                    assert ar['variable'] == variable and ar['policy'] == POLICY
                    assert ar['root_sha256'] == sha_key(target)
                    assert ar['seed_table_digests'] == common['logical_table_digests']
                    name = f"{bound['repeat']}-{variable}"
                    history = ct/name; shutil.copyfile(shared, history)
                    delta = ct/(name+'-delta')
                    merge_checked(ar['delta'], history, delta, r['options'])
                    splits = read_archive(ar['splits']); ev = add_splits(base_evidence, splits)
                    h = BudgetedInventory(history, **r['options']); h.set_admission_budget(0)
                    try:
                        routes = routes_for(h, ev); closed, _, _ = full(h, [target], routes)
                        assert closed == [[ar['target_closed']], [ar['without_growth_closed']]]
                        verify_positive(h, read_archive(ar['expanded_certificate']),
                            [target] if closed[0][0] else [], ev, Counter())
                        selected = None if closed[0][0] else select(h, routes,
                            [*ev[:3], splits, ev[4]], [target], [False], Counter())
                        assert selected == read_archive(ar['next_selection'])
                        added = set(); saved = set()
                        for row in ar['steps']:
                            op = read_archive(row['operation'])
                            assert sha_key(op['source']) == row['source_sha256']
                            ids = set(map(sha_key, op['added']))
                            assert not ids & added; added.update(ids)
                            assert len(ids) == row['admitted_now'] and len(added) == row['admitted_total']
                            if row['step'] == 0:
                                assert op['mode'] == 'preselected_split' and op['source'] == target
                                assert op['record'] == initial[variable]['record']
                                assert op['selected_rank'] == initial[variable]['rank']
                                assert op['ranked_pairs'] == [x['rank'] for x in ranked]
                            if op.get('record') is not None:
                                verify_split(h, op['record'], Counter())
                                assert len(op['acquisition']['branches']) == 2
                                saved.add(record_key(op['record']))
                        assert saved == {record_key(x) for x in splits}
                        assert added == set(ar['admitted_state_sha256']) and len(added) <= POLICY['state_limit']
                        completed = novel_patterns(delta)
                        assert completed <= added
                        assert sorted(completed) == ar['completed_new_state_sha256']
                        assert sorted(added-completed) == ar['entered_but_unstored_sha256']
                        item = dict(variable=variable, repeat=bound['repeat'],
                            closed=closed[0][0], admitted=len(added), completed=len(completed),
                            cold_frontier_matches=True, idempotent=True)
                        result['arms'].append(item)
                        findings['arms'].append(dict(**item,
                            splits=[split_findings(h, routes, solver, s) for s in splits],
                            next_profile=None if selected is None else profile(h, routes,
                                dict(source=selected['source'], variables=shape(h._load(selected['source'])['cnf'])[0]))))
                        signature = (digests(history), splits, sorted(added), selected, closed)
                        if variable in repeats:
                            assert repeats[variable] == signature
                        else:
                            repeats[variable] = signature
                        assert not h.admitted
                        print(json.dumps(item), flush=True)
                    finally:
                        h.close()
                h = BudgetedInventory(tmp/'final', **r['options']); h.set_admission_budget(0)
                try:
                    tick = time.perf_counter(); routes = routes_for(h, evidence)
                    roots = [h._canonical(c['source'], h.config['max_depth'])[2] for c in r['cases']]
                    closed, _, counts = full(h, roots, routes)
                    assert closed == [r['final_closed'], r['without_growth_closed']]
                    selected = select(h, routes, evidence, roots, closed[0], Counter())
                    assert selected == read_archive(r['next_selection'])
                    result.update(full_cold_coverage_seconds=time.perf_counter()-tick,
                        full_cold_coverage_counts=counts, cold_next_selection_matches=True,
                        covered=sum(closed[0]), gains=r['gains'])
                    findings['next_profile'] = profile(h, routes, dict(source=selected['source'],
                        variables=shape(h._load(selected['source'])['cnf'])[0]))
                    assert not h.admitted
                finally:
                    h.close()
                for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
                    assert solver._read(key) is not None
                assert not solver.counts.get('expanded_nodes', 0)
                result['verified_reference_nodes'] = len(solver.checked)
        finally:
            solver.close()
        assert sha(seed) == seed_sha and sha(shared) == shared_sha
        assert digests(tmp/'final') == r['logical_table_digests']
    result.update(seconds=time.perf_counter()-started, passed=True,
        repeated_logical_results_identical=True, parent_and_common_seed_unchanged=True)
    summary = dict(arms=[], limitations=r['limitations'])
    for variable in (17,1):
        arms = [load_report(b) for b in r['arms'] if b['variable']==variable]
        costs = {k:statistics.mean(sum(row[k] for row in a['steps']) for a in arms)
            for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')}
        first = arms[0]
        summary['arms'].append(dict(variable=variable, repetitions=len(arms),
            closed=first['target_closed'], admitted=len(first['admitted_state_sha256']),
            completed=len(first['completed_new_state_sha256']),
            costs_mean_seconds=costs, expansion_mean_seconds=statistics.mean(a['expansion_seconds'] for a in arms),
            worker_mean_seconds=statistics.mean(a['worker_seconds'] for a in arms),
            preparation_mean_seconds=statistics.mean(a['preparation_seconds'] for a in arms),
            delta_export_mean_seconds=statistics.mean(a['delta']['seconds'] for a in arms),
            first_split_mean_seconds=statistics.mean(a['steps'][0]['acquisition_seconds'] for a in arms),
            history_bytes=first['history_bytes'], compressed_delta_bytes=first['delta']['compressed_bytes'],
            delta_database_bytes=first['delta']['database_bytes'],
            external_assumption_attempts=first['external_assumption_attempts']))
    for name, data in [('reconstruction.json', result), ('structural-findings.json', findings),
            ('comparison-summary.json', summary)]:
        (out/name).write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','covered','gains','seconds')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('output', type=Path)
    validate(parser.parse_args().output)
