#!/usr/bin/env python3
"""Compare rebuilding and retaining checked state between different original cases.
"""
from collections import Counter
import copy
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_guarded_digests import (
    restore_checkpoint as restore_base, POLICY, FILES as INHERITED_FILES,
    routes_for, add_splits, select, BudgetedInventory, full, expand,
    archive_json, read_archive, sha, sha_key, digests, unpack, apply_delta,
    check_delta, save_delta, new_probes, probe_reference, split_reference,
    frontier, profile, learning_selection, checked_inventory, verify_split,
    verify_positive, verify_bridge, remaining, split_key)
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_digest_worker import worker
from experiments.cnf_expansion_session import ExpansionSession
from experiments.cnf_original_binding import bind_original_focus
BASE = Path('experiments/results/cnf-guarded-digests/report.json')
FORMAT = 'original-handoff-expansion-v1'
FILES = ['experiments/compare_cnf_original_handoff.py', 'experiments/cnf_original_binding.py',
    'solver/test_cnf_original_binding.py', *INHERITED_FILES]
BATCHES = 2


def restore_checkpoint(report_path, path, tmp):
    r = json.loads(Path(report_path).read_text())
    if r['format'] != FORMAT or Path(r['parent']['path']) != BASE or sha(BASE) != r['parent']['sha256']:
        raise ValueError('Changed original-handoff parent')
    for name, digest in r['fingerprints'].items():
        if sha(name) != digest:
            raise ValueError('Changed original-handoff implementation')
    parent, *evidence = restore_base(BASE, path, tmp)
    if digests(path) != r['seed_table_digests'] or parent['final_closed'] != r['baseline_closed']:
        raise ValueError('Incorrect original-handoff seed')
    d = r['delta']; delta = tmp/'original-handoff-delta'
    if sha(d['path']) != d['sha256']:
        raise ValueError('Changed original-handoff delta')
    unpack(d['path'], delta, d['database_sha256'])
    apply_delta(path, delta); check_delta(path, delta, r['options'])
    if digests(path) != r['logical_table_digests']:
        raise ValueError('Incorrect original-handoff reconstruction')
    evidence = add_splits(evidence, read_archive(r['splits']))
    bridges = read_archive(r['bridges'])
    h = BudgetedInventory(path, **r['options']); h.set_admission_budget(0)
    try:
        for record in bridges:
            verify_bridge(h, record, Counter())
        roots = [h._canonical(c['source'], h.config['max_depth'])[2]
                 for c, b in zip(r['cases'], r['final_closed'], strict=True) if b]
        verify_positive(h, read_archive(r['expanded_certificate']), roots, evidence, bridges, Counter())
        assert not h.admitted
    finally:
        h.close()
    return r, *evidence


def prepare_handoff(out, history, parent, evidence, bridges, selection):
    """Pay for the completed-original query and exact new-original binding."""
    out.mkdir();started=time.perf_counter()
    h=BudgetedInventory(history,**parent['options']);h.set_admission_budget(0)
    changes=h.db.total_changes
    try:
        session=ExpansionSession(h,evidence,bridges);session.begin(0,evidence,bridges)
        r=dict(session_construction_seconds=time.perf_counter()-started)
        old_index=parent['source_original_indices'][0]
        assert old_index==22 and parent['final_closed'][old_index]
        old_root=h._canonical(parent['cases'][old_index]['source'],h.config['max_depth'])[2]
        tick=time.perf_counter();closed,plans,counts=full(h,[old_root],session.maintenance.routes)
        assert closed[0]==[True]
        certificate=expand(h,plans[0],plans[0]['roots'],session.maintenance.routes,Counter())
        r.update(completed_query_seconds=time.perf_counter()-tick,completed_original_index=old_index,
            completed_original_case=parent['cases'][old_index]['original_case'],completed_root=old_root,
            completed_flags=closed,completed_counts=counts)
        r['completed_certificate']=archive_json(out/'completed-certificate.json.gz',certificate)
        tick=time.perf_counter()
        bound=bind_original_focus(h,session.maintenance.routes,parent['cases'],selection['source'],selection['selected_original_cases'])
        r['binding_seconds']=time.perf_counter()-tick
        r['binding']=archive_json(out/'binding.json.gz',bound)
        assert not h.admitted and h.db.total_changes==changes
        r.update(no_acquisition=True,rows_unchanged=True,checked_nodes=len(h.checked),
            prepared_checked_nodes=len(h.prepared.checked),seconds=time.perf_counter()-started)
        (out/'report.json').write_text(encode(r)+'\n')
        return r,session
    except BaseException:
        h.close();raise


def run(out):
    pipeline = time.perf_counter(); out.mkdir(exist_ok=False)
    r = dict(format=FORMAT, parent=dict(path=str(BASE), sha256=sha(BASE)),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        fingerprints={name: sha(name) for name in FILES}, policy=POLICY, batch_limit=BATCHES, arms=[], session_runs=[], limitations=[
        'Two reversed-order repetitions of restarting versus retaining the checked session after querying completed original case 1120 and binding the next case 1061.',
        'Both arms charge initial session construction, the completed-original query and selected-path original binding. This setup replays an already stored result, not fresh acquisition of case 1120.',
        'Each batch has twelve advances and its own 32-state allowance; up to 64 entries per sequence, including repeated unfinished inputs. Stop once the focus closes.',
        'Only the restart arm discards checked state at the original boundary. Both retain it between any subsequent batches of case 1061. All workers use live full digests and the same scheduler, budgets, checks and append exports.',
        'Preparation, acquisition, route updates, coverage, persistence, reconstruction and reference checks are separate costs.',
        'Development cases and shared OS caches; two observations per mode do not establish general speedups or confidence intervals. Stored bytes are not peak RAM.',
        'No globally minimal expansion, polynomial unrestricted-SAT algorithm or P-versus-NP conclusion.'])
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); seed = tmp/'seed'; tick = time.perf_counter()
        parent, *base_evidence = restore_base(BASE, seed, tmp)
        r.update(restore_seconds=time.perf_counter()-tick, options=parent['options'],
            cases=parent['cases'], baseline_closed=parent['final_closed'],
            seed_table_digests=digests(seed), seed_database_bytes=seed.stat().st_size,
            evidence_counts_before=list(map(len, base_evidence)))
        seed_hash = sha(seed); bridges = read_archive(parent['bridges'])
        before = read_archive(parent['next_selection'])
        root = before['source']; assert root is not None and before['pending_split'] is None
        r['source'] = root; r['source_original_indices'] = before['selected_original_cases']
        assert r['source_original_indices']==[13] and parent['cases'][13]['original_case']==1061
        r['initial_selection'] = archive_json(out/'initial-selection.json.gz', before)
        history = tmp/'history'; shutil.copyfile(seed, history); evidence = copy.deepcopy(base_evidence)
        touched = {}
        for repeat in range(2):
            for startup_mode in (('restart','retained') if repeat==0 else ('retained','restart')):
                name=f'session-{repeat}-{startup_mode}'; arm_history=tmp/(name+'-history')
                started=time.perf_counter();shutil.copyfile(seed,arm_history)
                arm_evidence=copy.deepcopy(base_evidence);session=None;batch_rows=[]
                warmup,session=prepare_handoff(out/(name+'-handoff'),arm_history,parent,arm_evidence,bridges,before)
                if startup_mode=='restart':session.h.close();session=None
                try:
                    for batch in range(BATCHES):
                        batch_name=f'{name}-batch-{batch}'
                        arm,session=worker(out/batch_name,tmp/batch_name,arm_history,parent,arm_evidence,bridges,root,session,'live')
                        first=read_archive(arm['steps'][0]['operation'])
                        if batch==0:
                            assert first['source']==before['source']
                        r['arms'].append(dict(case=1061,scenario='resume',repeat=repeat,batch=batch,
                            mode='activation',export_mode='append',startup_mode=startup_mode,digest_mode='live',
                            path=str(out/batch_name/'report.json'),sha256=sha(out/batch_name/'report.json')))
                        batch_rows.append(arm)
                        apply_delta(history,tmp/batch_name/'delta');check_delta(history,tmp/batch_name/'delta',r['options'])
                        additions=read_archive(arm['splits']);evidence=add_splits(evidence,additions)
                        arm_evidence=add_splits(arm_evidence,additions)
                        for row in arm['steps']:
                            op=read_archive(row['operation'])
                            if op.get('record') is not None:touched[split_key(op['record'])]=op['record']
                        if arm['target_closed']:break
                    final_cache=dict(checked_nodes=len(session.h.checked),prepared_checked_nodes=len(session.h.prepared.checked))
                finally:
                    if session is not None:session.h.close()
                r['session_runs'].append(dict(repeat=repeat,startup_mode=startup_mode,digest_mode='live',handoff=dict(path=str(out/(name+'-handoff')/'report.json'),sha256=sha(out/(name+'-handoff')/'report.json')),batches=len(batch_rows),
                    seconds=time.perf_counter()-started,final_cache=final_cache,worker_seconds=sum(a['worker_seconds'] for a in batch_rows),
                    admitted=sum(len(a['admitted_state_sha256']) for a in batch_rows),
                    completed=sum(len(a['completed_new_state_sha256']) for a in batch_rows),
                    final_digests=digests(arm_history)))
        assert sha(seed) == seed_hash; r['parent_unchanged'] = True
        previous = {split_key(x) for x in base_evidence[3]}
        new_splits = [x for x in evidence[3] if split_key(x) not in previous]
        r['splits'] = archive_json(out/'splits.json.gz', new_splits)
        r['touched_splits'] = archive_json(out/'touched-splits.json.gz', list(touched.values()))
        r['bridges'] = archive_json(out/'bridges.json.gz', bridges)
        r['evidence_counts_after'] = list(map(len, evidence))
        tick = time.perf_counter(); h = BudgetedInventory(history, **r['options']); h.set_admission_budget(0)
        try:
            routes = routes_for(h, evidence, bridges)
            roots = [h._canonical(c['source'], h.config['max_depth'])[2] for c in r['cases']]
            r['global_route_preparation_seconds'] = time.perf_counter()-tick; tick = time.perf_counter()
            closed, plans, counts = full(h, roots, routes)
            r.update(global_coverage_seconds=time.perf_counter()-tick, global_counts=counts,
                final_closed=closed[0], without_growth_closed=closed[1])
            assert not any(a and not b for a, b in zip(r['baseline_closed'], closed[0], strict=True))
            r['gains'] = [i for i, (a, b) in enumerate(zip(r['baseline_closed'], closed[0], strict=True)) if b and not a]
            r['certificate'] = archive_json(out/'coverage.json.gz', plans[0])
            r['expanded_certificate'] = archive_json(out/'expanded-coverage.json.gz', expand(h, plans[0], plans[0]['roots'], routes, Counter()))
            state = frontier(h, routes, evidence[3], Counter())
            r['frontier'] = archive_json(out/'frontier.json.gz', state)
            r['frontier_profiles'] = archive_json(out/'frontier-profiles.json.gz', [profile(h, routes, row) for row in state['leaves']])
            r['projection_frontier'] = archive_json(out/'projection-frontier.json.gz', remaining(h, [dict(source=x['source'], target=x['target']) for x in bridges], routes, Counter()))
            r['learning'] = archive_json(out/'learning.json.gz', learning_selection(h, routes, Counter()))
            r['next_selection'] = archive_json(out/'next-selection.json.gz', select(h, routes, evidence, roots, closed[0], Counter()))
            r['historical_cache'] = checked_inventory(h)[1]
            r['delta'] = save_delta(seed, history, tmp/'delta', out/'proof-delta.sqlite3.gz')
            d = parent['reference']; assert sha(d['path']) == d['sha256']
            unpack(d['path'], tmp/'reference', d['database_sha256']); shutil.copyfile(tmp/'reference', tmp/'reference-seed')
            pr = probe_reference(h, routes, [dict(kind=x['kind'], id=x['id']) for x in new_probes(tmp/'delta')], r, out, tmp)
            r['probe_reference'] = {k: pr[k] for k in ('rows', 'originals', 'seconds', 'cold_seconds', 'verified_nodes')}
            # Include resumed splits: newly available canonical children need reference evidence too.
            r['reference'] = split_reference(h, list(touched.values()), r, out, tmp)
        finally:
            h.close()
        r['logical_table_digests'] = digests(history); r['expanded_database_bytes'] = history.stat().st_size
        tick = time.perf_counter(); r['cold_delta_counts'] = check_delta(history, tmp/'delta', r['options'])
        r['cold_delta_seconds'] = time.perf_counter()-tick
        rebuilt = tmp/'rebuilt'; shutil.copyfile(seed, rebuilt); apply_delta(rebuilt, tmp/'delta')
        assert digests(rebuilt) == r['logical_table_digests']
        previous_hash = sha(rebuilt); apply_delta(rebuilt, tmp/'delta'); assert sha(rebuilt) == previous_hash
        r['idempotent_merge'] = True
        with sqlite3.connect(tmp/'delta') as db:
            r['new_node_kinds'] = dict(Counter(json.loads(p)['kind'] for p, in db.execute('SELECT payload FROM cnf_patterns_v1')))
    r['pipeline_seconds'] = time.perf_counter()-pipeline
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']), gains=r['gains'], new_kinds=r['new_node_kinds'], seconds=r['pipeline_seconds'])), flush=True)


if __name__ == '__main__':
    run(Path(sys.argv[1]))
