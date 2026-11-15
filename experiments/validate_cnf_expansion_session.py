#!/usr/bin/env python3
"""Cold replay every consecutive batch without using the retained-session helper."""
from collections import Counter
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

from experiments.compare_cnf_expansion_session import (
    BASE, POLICY, restore_checkpoint, restore_base, routes_for, add_splits,
    select, BudgetedInventory, full, verify_split, verify_positive, read_archive,
    sha, sha_key, unpack, digests, split_key, remaining, frontier)
from experiments.compare_cnf_pending_maintenance import focus_selection
from experiments.validate_cnf_pattern_activation import prefix_replay
from experiments.validate_cnf_split_cost import load_report, merge_checked, novel_patterns, split_findings
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.continue_cnf_local_forcing import profile
from experiments.validate_cnf_warm_transfer import shape


def validate(out):
    start = time.perf_counter(); r = json.loads((out/'report.json').read_text())
    parent = load_report(r['parent']); assert Path(r['parent']['path']) == BASE
    assert r['source'] == parent['source'] and r['policy'] == POLICY
    initial = read_archive(r['initial_selection'])
    assert initial == read_archive(parent['next_selection']) and initial['pending_split'] is not None
    expected_order=[(0,'restart'),(0,'retained'),(1,'retained'),(1,'restart')]
    assert [(a['repeat'],a['startup_mode']) for a in r['session_runs']]==expected_order
    expected=[(a['repeat'],a['startup_mode'],b) for a in r['session_runs'] for b in range(a['batches'])]
    assert [(a['repeat'],a['startup_mode'],a['batch']) for a in r['arms']]==expected
    assert all(1<=a['batches']<=r['batch_limit']==2 for a in r['session_runs'])
    assert all(a['mode']=='activation' and a['scenario']=='resume' for a in r['arms'])
    prior = load_report(next(a for a in parent['arms'] if a['scenario'] == 'resume' and a['repeat'] == 0 and a['mode'] == 'activation'))
    lost = set(prior['entered_but_unstored_sha256'])
    result = dict(report_sha256=sha(out/'report.json'), arms=[])
    findings = dict(arms=[], initial_pending_source_sha256=sha_key(initial['source']),
        previously_unstored_sha256=sorted(lost))
    with tempfile.TemporaryDirectory() as td, patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('fresh recognition')):
        tmp = Path(td); tick = time.perf_counter()
        restored, *evidence = restore_checkpoint(out/'report.json', tmp/'final', tmp)
        assert restored == r; result['restore_seconds'] = time.perf_counter()-tick
        ct = tmp/'seed-restore'; ct.mkdir()
        original, *base_evidence = restore_base(BASE, ct/'seed', ct); assert original == parent
        seed_hash = sha(ct/'seed'); assert digests(ct/'seed') == r['seed_table_digests']
        bridges = read_archive(parent['bridges']); assert bridges == read_archive(r['bridges'])
        d = r['reference']; assert sha(d['path']) == d['sha256']
        unpack(d['path'], tmp/'reference', d['database_sha256']); solver = ResidualSolver(tmp/'reference')
        signatures = {}; touched = {}; workers = []; sequences = {}
        try:
            with patch.object(solver, '_expand', side_effect=AssertionError('fresh reference search')):
                for bound in r['arms']:
                    ar = load_report(bound); workers.append((bound,ar))
                    key=(bound['repeat'],bound['startup_mode']); batch=bound['batch']
                    prior_batch=sequences.get(key)
                    if batch==0:
                        assert prior_batch is None
                        batch_seed=ct/'seed';batch_evidence=base_evidence;lost=set(prior['entered_but_unstored_sha256']);expected_selection=initial
                    else:
                        assert prior_batch['batch']==batch-1
                        batch_seed=prior_batch['history'];batch_evidence=prior_batch['evidence']
                        lost=prior_batch['unfinished'];expected_selection=prior_batch['selected']
                    assert ar['policy']==POLICY and ar['seed_table_digests']==digests(batch_seed) and ar['focus']==r['source']
                    assert ar['session_reused']==(bound['startup_mode']=='retained' and batch>0)
                    name=f"repeat-{bound['repeat']}-{bound['startup_mode']}-batch-{batch}";history=tmp/name;delta=tmp/(name+'-delta')
                    shutil.copyfile(batch_seed,history);merge_checked(ar['delta'],history,delta,r['options'])
                    splits=read_archive(ar['splits']);ev=add_splits(batch_evidence,splits)
                    assert read_archive(ar['bridges']) == bridges
                    h = BudgetedInventory(history, **r['options']); h.set_admission_budget(0)
                    try:
                        routes = routes_for(h, ev, bridges); closed, _, _ = full(h, [r['source']], routes)
                        assert closed == [ar['target_flags'], ar['without_growth_flags']]
                        verify_positive(h, read_archive(ar['expanded_certificate']), [r['source']] if closed[0][0] else [], ev, bridges, Counter())
                        entered = set(); records = {}; ops = []
                        for row in ar['steps']:
                            op = read_archive(row['operation']); ops.append(op)
                            assert sha_key(op['source']) == row['source_sha256']
                            ids = set(map(sha_key, op['added'])); assert not ids & entered; entered.update(ids)
                            assert len(ids) == row['admitted_now'] and len(entered) == row['admitted_total']
                            if op.get('record') is not None:
                                verify_split(h, op['record'], Counter()); assert len(op['acquisition']['branches']) == 2
                                assert op['pending'] == any(b['pending'] for b in op['acquisition']['branches'])
                                records[split_key(op['record'])] = op['record']
                            if op['mode'] == 'early_saved_split':
                                assert op['selected_rank'] == min(op['ranked_pairs'])
                        if expected_selection.get('pending_split') is not None:
                            assert ops[0]['mode']=='resume_split' and ops[0]['record']==expected_selection['pending_split']
                            assert not ops[0]['ranked_pairs']
                        assert len(ar['steps']) <= POLICY['step_limit'] and len(entered) <= POLICY['state_limit']
                        inherited = {split_key(s) for s in batch_evidence[3]}
                        assert set(records)-inherited == {split_key(s) for s in splits}
                        assert sorted(entered) == ar['admitted_state_sha256']
                        completed = novel_patterns(delta); assert completed <= entered
                        assert sorted(completed) == ar['completed_new_state_sha256']
                        assert sorted(entered-completed) == ar['entered_but_unstored_sha256']
                        selected = focus_selection(h, routes, ev, ev[3], r['source'], closed[0][0])
                        assert selected == read_archive(ar['next_selection'])
                        record = dict(repeat=bound['repeat'], startup_mode=bound['startup_mode'], batch=batch, closed=closed[0][0], admitted=len(entered),
                            completed=len(completed), unfinished=len(entered-completed), cold_selection_matches=True, idempotent=True)
                        result['arms'].append(record)
                        detail = dict(**record, splits=[split_findings(h, routes, solver, s) for s in records.values()],
                            previous_interrupted_reentered=sorted(lost & entered),
                            previous_interrupted_now_stored=sorted(lost & completed))
                        # These inputs were entered but have no stored pattern
                        # certificate. Their shapes do not certify reduction edges.
                        detail['interrupted_inputs'] = sorted([
                            dict(key_sha256=sha_key(key), shape=shape(json.loads(key)[-1]))
                            for op in ops for key in op['added']
                            if sha_key(key) in entered-completed], key=lambda x: x['key_sha256'])
                        # Distinguish actual reuse of stored nodes from recurrence
                        # of a reduction pattern or recognition of the same family.
                        for split in detail['splits']:
                            for branch in split['branches']:
                                prefix = branch['prefix']['nodes']
                                for node in prefix:
                                    node['acquisition'] = ('new' if node['key_sha256'] in completed else 'inherited')
                                branch['new_prefix_nodes'] = sum(n['acquisition'] == 'new' for n in prefix)
                                branch['reused_prefix_nodes'] = sum(n['acquisition'] == 'inherited' for n in prefix)
                                branch['reduction_kinds'] = [n['kind'] for n in prefix]
                        # Replay both repeats with only the rows available at each advance.
                        detail['prefix_replay'] = prefix_replay(batch_seed, delta, ar, batch_evidence, bridges, r['options'], tmp/(name+'-prefix'))
                        assert digests(tmp/(name+'-prefix')) == digests(history)
                        findings['arms'].append(detail); touched.update(records)
                        signatures.setdefault(batch,[]).append((digests(history),splits,sorted(entered),selected,closed,ops))
                        sequences[key]=dict(batch=batch,history=history,evidence=ev,unfinished=entered-completed,selected=selected)
                        assert not h.admitted; print(json.dumps(record), flush=True)
                    finally:
                        h.close()
                for batch,group in signatures.items():
                    assert len(group)==4 and all(group[0]==item for item in group[1:])
                    assert len({a['delta']['database_sha256'] for b,a in workers if b['batch']==batch})==1
                    assert len({a['delta']['sha256'] for b,a in workers if b['batch']==batch})==1
                for run in r['session_runs']:
                    chosen=[a for b,a in workers if (b['repeat'],b['startup_mode'])==(run['repeat'],run['startup_mode'])]
                    assert len(chosen)==run['batches']
                    assert sum(len(a['admitted_state_sha256']) for a in chosen)==run['admitted']<=2*POLICY['state_limit']
                    assert sum(len(a['completed_new_state_sha256']) for a in chosen)==run['completed']
                    assert run['worker_seconds']==sum(a['worker_seconds'] for a in chosen)
                    assert run['final_digests']==digests(sequences[(run['repeat'],run['startup_mode'])]['history'])
                assert list(touched.values()) == read_archive(r['touched_splits'])
                h = BudgetedInventory(tmp/'final', **r['options']); h.set_admission_budget(0)
                try:
                    tick = time.perf_counter(); routes = routes_for(h, evidence, bridges)
                    roots = [h._canonical(c['source'], h.config['max_depth'])[2] for c in r['cases']]
                    closed, _, counts = full(h, roots, routes)
                    assert closed == [r['final_closed'], r['without_growth_closed']]
                    assert not any(a and not b for a, b in zip(r['baseline_closed'], closed[0], strict=True))
                    gains = [i for i, (a, b) in enumerate(zip(r['baseline_closed'], closed[0], strict=True)) if b and not a]
                    assert gains == r['gains']
                    selected = select(h, routes, evidence, roots, closed[0], Counter())
                    assert selected == read_archive(r['next_selection'])
                    assert frontier(h, routes, evidence[3], Counter()) == read_archive(r['frontier'])
                    assert remaining(h, [dict(source=x['source'], target=x['target']) for x in bridges], routes, Counter()) == read_archive(r['projection_frontier'])
                    result.update(global_coverage_seconds=time.perf_counter()-tick, global_coverage_counts=counts,
                        covered=sum(closed[0]), gains=gains, cold_next_selection_matches=True, evidence_counts=list(map(len, evidence)))
                    findings['gained_originals'] = []
                    for i in gains:
                        answer = solver.solve(r['cases'][i]['source'])
                        if answer['answer']:
                            assert holds(r['cases'][i]['source'], answer['model'])
                        findings['gained_originals'].append(dict(index=i, case=r['cases'][i]['original_case'],
                            shape=shape(r['cases'][i]['source']), reference_answer=answer['answer']))
                    if selected['source'] is not None:
                        findings['next_source_sha256'] = sha_key(selected['source'])
                        findings['next_shape'] = shape(h._load(selected['source'])['cnf'])
                        findings['next_original_indices'] = selected['selected_original_cases']
                        if selected.get('pending') is None:
                            findings['next_profile'] = profile(h, routes, dict(source=selected['source'], variables=findings['next_shape'][0]))
                    with sqlite3.connect(tmp/'expansion-session-delta') as db:
                        nodes = [(k, json.loads(p)) for k, p in db.execute('SELECT id,payload FROM cnf_patterns_v1')]
                    findings['new_nodes'] = [dict(key_sha256=sha_key(k), kind=n['kind'], shape=shape(n['cnf']),
                        outcomes=n['profile']['outcomes'], edge_sha256=sha_key(n['edge']['key']) if 'edge' in n else None)
                        for k, n in nodes]
                    assert not h.admitted
                finally:
                    h.close()
                for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
                    assert solver._read(key) is not None
                result['verified_reference_nodes'] = len(solver.checked)
                assert not solver.counts.get('expanded_nodes', 0)
        finally:
            solver.close()
        assert sha(ct/'seed') == seed_hash and digests(tmp/'final') == r['logical_table_digests']
    result.update(passed=True, seconds=time.perf_counter()-start, identical_operations_and_logical_results=True, seed_unchanged=True)
    summary=dict(batches=[],sequences=[],limitations=r['limitations'])
    for mode in ('restart','retained'):
        runs=[a for a in r['session_runs'] if a['startup_mode']==mode]
        summary['sequences'].append(dict(startup_mode=mode,batches=runs[0]['batches'],
            worker_sum_mean_seconds=statistics.mean(a['worker_seconds'] for a in runs),
            sequence_mean_seconds=statistics.mean(a['seconds'] for a in runs),
            admitted=runs[0]['admitted'],completed=runs[0]['completed']))
        for batch in sorted(signatures):
            chosen=[a for b,a in workers if b['startup_mode']==mode and b['batch']==batch];first=chosen[0]
            summary['batches'].append(dict(startup_mode=mode,batch=batch,steps=len(first['steps']),
                target_closed=first['target_closed'],admitted=len(first['admitted_state_sha256']),
                completed=len(first['completed_new_state_sha256']),unfinished=len(first['entered_but_unstored_sha256']),
                preparation_mean_seconds=statistics.mean(a['preparation_seconds'] for a in chosen),
                session_startup_mean_seconds=statistics.mean(a['session_startup_seconds'] for a in chosen),
                boundary_mean_seconds=statistics.mean(a['export_boundary_seconds'] for a in chosen),
                expansion_mean_seconds=statistics.mean(a['expansion_seconds'] for a in chosen),
                export_mean_seconds=statistics.mean(a['delta']['seconds'] for a in chosen),
                worker_mean_seconds=statistics.mean(a['worker_seconds'] for a in chosen),
                costs_mean_seconds={k:statistics.mean(sum(row[k] for row in a['steps']) for a in chosen)
                    for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')},
                compressed_delta_bytes=first['delta']['compressed_bytes'],delta_database_bytes=first['delta']['database_bytes'],
                history_bytes=first['history_bytes'],initial_activation_index=first['initial_activation_index'],
                final_activation_index=first['final_activation_index']))
    for name, data in [('reconstruction.json', result), ('structural-findings.json', findings), ('cost-summary.json', summary)]:
        (out/name).write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: result[k] for k in ('passed', 'covered', 'gains', 'seconds')}), flush=True)


if __name__ == '__main__':
    validate(Path(sys.argv[1]))
