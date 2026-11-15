#!/usr/bin/env python3
"""Cold replay every consecutive batch without using the retained-session helper."""
from collections import Counter, deque
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_case1196_discovery import (
    BASE, POLICY, restore_checkpoint, restore_base, routes_for, add_splits,
    select, BudgetedInventory, full, verify_split, verify_positive, read_archive,
    sha, sha_key, unpack, digests, split_key, remaining, frontier)
from experiments.compare_cnf_pending_maintenance import focus_selection
from experiments.validate_cnf_pattern_activation import prefix_replay
from experiments.validate_cnf_split_cost import load_report, merge_checked, novel_patterns, split_findings
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.continue_cnf_local_forcing import profile
from experiments.validate_cnf_warm_transfer import shape


def checked_lineage(h, routes, cases, target, indices):
    """Check an actual dependency path from a selected or retained original scope.

    These paths do not transfer SAT truth; all other coverage premises remain.
    A retained selection with no original indices keeps its empty selector label.
    """
    from experiments.cnf_route_composition import options
    assert indices and len(set(indices))==len(indices)
    assert all(type(i) is int and 0<=i<len(cases) for i in indices)
    roots={h._canonical(cases[i]['source'],h.config['max_depth'])[2]:i for i in indices}
    todo=deque(roots);parents={root:None for root in roots}
    while todo:
        source=todo.popleft()
        if source==target:break
        for rule,children in options(h,source,routes):
            for index,child in enumerate(children):
                if child not in parents:
                    parents[child]=(source,rule['kind'],index);todo.append(child)
    assert target in parents, 'Detached retained focus'
    path=[];child=target
    while parents[child] is not None:
        source,kind,index=parents[child]
        path.append(dict(source_sha256=sha_key(source),child_sha256=sha_key(child),kind=kind,child_index=index))
        child=source
    original=roots[child]
    return dict(original_index=original,original_case=cases[original]['original_case'],
                scope_indices=indices,target_sha256=sha_key(target),
                path=list(reversed(path)),visited=len(parents))


def validate(out):
    start = time.perf_counter(); r = json.loads((out/'report.json').read_text())
    parent = load_report(r['parent']); assert Path(r['parent']['path']) == BASE
    assert r['policy'] == POLICY
    initial = read_archive(r['initial_selection'])
    assert initial == read_archive(parent['next_selection']) and r['source']==initial['source']
    assert r['source_original_indices']==initial['selected_original_cases']==[36]
    assert r['initial_scope_indices']==[36] and r['cases'][36]['original_case']==1196 and initial['pending_split'] is None
    expected_order=[(0,'canonical'),(1,'canonical')]
    assert [(a['repeat'],a['startup_mode']) for a in r['session_runs']]==expected_order
    expected=[(a['repeat'],a['startup_mode'],b) for a in r['session_runs'] for b in range(a['batches'])]
    assert [(a['repeat'],a['startup_mode'],a['batch']) for a in r['arms']]==expected
    assert all(a['digest_mode']=='live' and 1<=a['batches']<=r['batch_limit']==6 for a in r['session_runs'])
    assert all(a['mode']=='activation' and a['scenario']=='resume' for a in r['arms'])
    previous_bound = max((a for a in parent['arms'] if a['repeat']==0 and a['startup_mode']=='canonical'), key=lambda a:a['batch'])
    assert r['previous_worker']==previous_bound
    previous = load_report(previous_bound)
    initial_lost = set(previous['entered_but_unstored_sha256'])
    assert sorted(initial_lost)==r['previously_unstored_sha256'] and not initial_lost
    lost = initial_lost
    result = dict(report_sha256=sha(out/'report.json'), parent_restore_mode='authoritative_without_materialized_cache', arms=[], handoffs=[])
    findings = dict(arms=[], initial_source_sha256=sha_key(initial['source']),
        previously_unstored_sha256=sorted(lost))
    with tempfile.TemporaryDirectory() as td, patch.object(BudgetedInventory, '_discover', side_effect=AssertionError('fresh recognition')):
        tmp = Path(td); tick = time.perf_counter()
        restored, *evidence = restore_checkpoint(out/'report.json', tmp/'final', tmp, materialized=False)
        assert restored == r; result['restore_seconds'] = time.perf_counter()-tick
        ct = tmp/'seed-restore'; ct.mkdir()
        original, *base_evidence = restore_base(BASE, ct/'seed', ct, materialized=False); assert original == parent
        seed_hash = sha(ct/'seed'); assert digests(ct/'seed') == r['seed_table_digests']
        bridges = read_archive(parent['bridges']); assert bridges == read_archive(r['bridges'])
        d = r['reference']; assert sha(d['path']) == d['sha256']
        unpack(d['path'], tmp/'reference', d['database_sha256']); solver = ResidualSolver(tmp/'reference')
        # Independently recompute the common initial global query once, then
        # compare every arm's saved output to that exact checked result.
        q=BudgetedInventory(ct/'seed',**r['options']);q.set_admission_budget(0)
        try:
            qr=routes_for(q,base_evidence,bridges)
            qrts=[q._canonical(c['source'],q.config['max_depth'])[2] for c in r['cases']]
            initial_flags,initial_plans,_=full(q,qrts,qr)
            initial_chosen=select(q,qr,base_evidence,qrts,initial_flags[0],Counter())
            assert initial_chosen==initial and initial_flags==[parent['final_closed'],parent['without_growth_closed']]
            findings['initial_lineage'] = checked_lineage(q,qr,r['cases'],initial['source'],r['initial_scope_indices'])
            assert not q.admitted
        finally:q.close()
        signatures = {}; touched = {}; workers = []; sequences = {}; global_queries={}
        try:
            with patch.object(solver, '_expand', side_effect=AssertionError('fresh reference search')):
                for bound in r['arms']:
                    ar = load_report(bound); workers.append((bound,ar))
                    key=(bound['repeat'],bound['startup_mode']); batch=bound['batch']
                    prior_batch=sequences.get(key)
                    if batch==0:
                        assert prior_batch is None
                        batch_seed=ct/'seed';batch_evidence=base_evidence;lost=set(initial_lost);expected_selection=initial
                        run=next(run for run in r['session_runs'] if (run['repeat'],run['startup_mode'])==key)
                        warm=load_report(run['handoff'])
                        assert warm['closed']==initial_flags
                        assert read_archive(warm['selection'])==initial_chosen
                        assert read_archive(warm['certificate'])==initial_plans[0]
                        result['handoffs'].append(dict(repeat=bound['repeat'],startup_mode=bound['startup_mode'],
                            checked=True,covered=sum(initial_flags[0]),next_original=1196))
                    else:
                        assert prior_batch['batch']==batch-1
                        batch_seed=prior_batch['history'];batch_evidence=prior_batch['evidence']
                        lost=prior_batch['unfinished'];expected_selection=prior_batch['selected']
                    assert ar['policy']==POLICY and ar['seed_table_digests']==digests(batch_seed) and ar['focus']==expected_selection['source']
                    assert bound['source_sha256']==sha_key(ar['focus'])
                    assert bound['original_indices']==expected_selection['selected_original_cases']
                    anchor_indices=bound['original_indices'] or (prior_batch['anchor_indices'] if prior_batch is not None else r['initial_scope_indices'])
                    assert ar['seed_mode']=='copy'
                    assert (ar['seed_copy_bytes']>0)==(ar['seed_mode']=='copy')
                    if ar['seed_mode']=='copy':assert ar['seed_copy_bytes']==(r['seed_database_bytes'] if batch==0 else prior_batch['original_history_bytes'])
                    assert ar['session_reused'] is True
                    dc=ar['digest_cost']; mode=bound['digest_mode']
                    assert ar['digest_mode']==mode
                    tables=set(ar['seed_table_digests'])
                    assert set(dc['scanned_tables']).isdisjoint(dc['reused_tables'])
                    assert set(dc['scanned_tables'])|set(dc['reused_tables'])==tables
                    assert set(dc['scan_seconds'])==set(dc['scanned_tables'])
                    assert dc['scanned_rows']==sum(ar['seed_table_digests'][t]['rows'] for t in dc['scanned_tables'])
                    assert dc['reused_rows']==sum(ar['seed_table_digests'][t]['rows'] for t in dc['reused_tables'])
                    if mode=='guarded' and batch:
                        previous_digests=prior_batch['seed_digests']
                        changed={t for t in tables if previous_digests[t]!=ar['seed_table_digests'][t]}
                        assert set(dc['scanned_tables'])==changed
                        assert dc['added_rows']=={t:ar['seed_table_digests'][t]['rows']-previous_digests[t]['rows'] for t in tables}
                    else:
                        assert set(dc['scanned_tables'])==tables and not dc['reused_tables']
                    name=f"repeat-{bound['repeat']}-{bound['startup_mode']}-batch-{batch}";history=tmp/name;delta=tmp/(name+'-delta')
                    shutil.copyfile(batch_seed,history);merge_checked(ar['delta'],history,delta,r['options'])
                    splits=read_archive(ar['splits']);ev=add_splits(batch_evidence,splits)
                    assert read_archive(ar['bridges']) == bridges
                    h = BudgetedInventory(history, **r['options']); h.set_admission_budget(0)
                    try:
                        routes = routes_for(h, ev, bridges); closed, _, _ = full(h, [ar['focus']], routes)
                        assert closed == [ar['target_flags'], ar['without_growth_flags']]
                        verify_positive(h, read_archive(ar['expanded_certificate']), [ar['focus']] if closed[0][0] else [], ev, bridges, Counter())
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
                        assert ops[0]['source']==expected_selection['source']
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
                        selected = focus_selection(h, routes, ev, ev[3], ar['focus'], closed[0][0])
                        assert selected == read_archive(ar['next_selection'])
                        run=next(run for run in r['session_runs'] if (run['repeat'],run['startup_mode'])==key)
                        saved_query=load_report(run['queries'][batch])
                        assert saved_query['mode']=='maintained'
                        if batch not in global_queries:
                            all_roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
                            flags,proofs,_=full(h,all_roots,routes)
                            chosen=select(h,routes,ev,all_roots,flags[0],Counter())
                            global_queries[batch]=(flags,proofs[0],chosen)
                        assert (saved_query['closed'],read_archive(saved_query['certificate']),read_archive(saved_query['selection']))==global_queries[batch]

                        record = dict(repeat=bound['repeat'], startup_mode=bound['startup_mode'], digest_mode=bound['digest_mode'], batch=batch, closed=closed[0][0], admitted=len(entered),
                            completed=len(completed), unfinished=len(entered-completed), cold_selection_matches=True, idempotent=True)
                        result['arms'].append(record)
                        detail = dict(**record, focus_lineage=checked_lineage(h,routes,r['cases'],ar['focus'],anchor_indices),
                            splits=[split_findings(h, routes, solver, s) for s in records.values()],
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
                        sequences[key]=dict(anchor_indices=anchor_indices,seed_digests=ar['seed_table_digests'],batch=batch,history=history,evidence=ev,unfinished=entered-completed,selected=global_queries[batch][2],original_history_bytes=ar['history_bytes'])
                        assert not h.admitted; print(json.dumps(record), flush=True)
                    finally:
                        h.close()
                for batch,group in signatures.items():
                    assert len(group)==2 and all(group[0]==item for item in group[1:])
                    assert len({a['delta']['database_sha256'] for b,a in workers if b['batch']==batch})==1
                    assert len({a['delta']['sha256'] for b,a in workers if b['batch']==batch})==1
                for run in r['session_runs']:
                    chosen=[a for b,a in workers if (b['repeat'],b['startup_mode'])==(run['repeat'],run['startup_mode'])]
                    assert len(chosen)==run['batches']
                    assert run['batches']==r['batch_limit'] or global_queries[run['batches']-1][2]['source'] is None
                    assert sum(len(a['admitted_state_sha256']) for a in chosen)==run['admitted']<=6*POLICY['state_limit']
                    assert sum(len(a['completed_new_state_sha256']) for a in chosen)==run['completed']
                    assert run['worker_seconds']==sum(a['worker_seconds'] for a in chosen)
                    assert run['seed_copy_bytes']==sum(a['seed_copy_bytes'] for a in chosen)
                    assert run['seed_copy_seconds']==sum(a['seed_copy_seconds'] for a in chosen)
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
                    with sqlite3.connect(tmp/'case1196-discovery-delta') as db:
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
    result.update(checked_global_queries=2+sum(len(s['queries']) for s in r['session_runs']), passed=True, seconds=time.perf_counter()-start, identical_operations_and_logical_results=True, seed_unchanged=True)
    # Independent repetitions test reproducibility; timings are descriptive, not a comparison.
    summary=dict(batches=[],sequences=[],limitations=r['limitations'])
    for run in r['session_runs']:
        row={k:v for k,v in run.items() if k!='final_digests'}
        warm=load_report(run['handoff'])
        row['handoff_costs']={k:warm[k] for k in ('seconds','session_construction_seconds','query_seconds','composition_seconds','selection_seconds','checked_nodes','prepared_checked_nodes')}
        row['global_queries']=[load_report(q) for q in run['queries']]
        summary['sequences'].append(row)
    for bound,a in workers:
        summary['batches'].append(dict(repeat=bound['repeat'],startup_mode=bound['startup_mode'],digest_mode=bound['digest_mode'],digest_cost=a['digest_cost'],batch=bound['batch'],
            seed_copy_bytes=a['seed_copy_bytes'],seed_copy_seconds=a['seed_copy_seconds'],steps=len(a['steps']),target_closed=a['target_closed'],admitted=len(a['admitted_state_sha256']),
            completed=len(a['completed_new_state_sha256']),unfinished=len(a['entered_but_unstored_sha256']),
            **{k:a[k] for k in ('preparation_seconds','session_startup_seconds','expansion_seconds','worker_seconds')},
            export_seconds=a['delta']['seconds'],history_bytes=a['history_bytes'],
            costs_seconds={k:sum(row[k] for row in a['steps']) for k in
                ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')}))
    for name, data in [('reconstruction.json', result), ('structural-findings.json', findings), ('cost-summary.json', summary)]:
        (out/name).write_text(json.dumps(data, indent=2, sort_keys=True)+'\n')
    print(json.dumps({k: result[k] for k in ('passed', 'covered', 'gains', 'seconds')}), flush=True)


if __name__ == '__main__':
    validate(Path(sys.argv[1]))
