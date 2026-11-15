#!/usr/bin/env python3
"""Continue bounded structural discovery across globally selected SAT sources in one session.
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

from experiments.continue_cnf_case1121_discovery import (
    restore_checkpoint as restore_base, POLICY, FILES as INHERITED_FILES,
    routes_for, add_splits, select, BudgetedInventory, full, expand,
    archive_json, read_archive, sha, sha_key, digests, unpack, apply_delta,
    check_delta, save_delta, new_probes, probe_reference, split_reference,
    frontier, profile, learning_selection, checked_inventory, verify_split,
    verify_positive, verify_bridge, remaining, split_key)
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_copyless_worker import worker
from experiments.cnf_expansion_session import ExpansionSession
from experiments.cnf_session_query import query, query_boundary
BASE = Path('experiments/results/cnf-case1121-discovery/report.json')
FORMAT = 'case1063-discovery-v1'
from experiments.cnf_canonical_source import CanonicalSourceInventory
ACCELERATOR = Path('experiments/results/cnf-materialized-checkpoint/report.json')
ACCELERATOR_SHA = 'bb0fd50de78cbe6c7a203ba28eb256f68f61dd15ff8236bb1940e623d84b7a93'
PRESERVATION = Path('experiments/results/cnf-case1121-discovery/validation.json')
if sha(PRESERVATION) != '5d0f193ed44b2e898fb67bca99799b4042885f7001d06b25f9113cf752b16d7a':
    raise ValueError('Changed complete source ledger')
FILES = ['experiments/continue_cnf_case1063_discovery.py', 'experiments/validate_cnf_case1063_discovery.py',
         'experiments/analyze_cnf_case1063_discovery.py', 'experiments/analyze_cnf_case1063_reuse.py', *json.loads(PRESERVATION.read_text())['source_fingerprints']]


def restore_seed(path, tmp, *, materialized=True, metrics=None):
    if sha(BASE) != '0282e3d40a20a20701c24503b7cd7608655806dace6e937e47082b1e30702790':
        raise ValueError('Changed acquisition parent')
    if sha(ACCELERATOR) != ACCELERATOR_SHA:
        raise ValueError('Changed materialized checkpoint report')
    started = time.perf_counter()
    result = restore_base(BASE, path, tmp, materialized=materialized)
    if result[0] != json.loads(BASE.read_text()):
        raise ValueError('Incorrect acquisition parent')
    if metrics is not None:
        metrics.update(materialization_allowed=materialized,
                       seconds=time.perf_counter()-started,
                       note='Parent restorer may use its verified snapshot plus delta; missing cache objects fall back to authoritative reconstruction.')
    return result
BATCHES = 4


def normalization_counts(h):
    return {name: {k: v for k, v in view.counts.items()
        if k.startswith(('canonical_', 'normalization_', 'key_serialized_', 'verified_pattern_'))}
        for name, view in [('current', h), ('prepared', h.prepared)]}



def restore_checkpoint(report_path, path, tmp, *, materialized=True):
    r = json.loads(Path(report_path).read_text())
    if r['format'] != FORMAT or Path(r['parent']['path']) != BASE or sha(BASE) != r['parent']['sha256']:
        raise ValueError('Changed case1063-discovery parent')
    for name, digest in r['fingerprints'].items():
        if sha(name) != digest:
            raise ValueError('Changed case1063-discovery implementation')
    if r['accelerator'] != dict(path=str(ACCELERATOR), sha256=ACCELERATOR_SHA):
        raise ValueError('Changed accelerator binding')
    parent, *evidence = restore_seed(path, tmp, materialized=materialized)
    if digests(path) != r['seed_table_digests'] or parent['final_closed'] != r['baseline_closed']:
        raise ValueError('Incorrect case1063-discovery seed')
    d = r['delta']; delta = tmp/'case1063-discovery-delta'
    if sha(d['path']) != d['sha256']:
        raise ValueError('Changed case1063-discovery delta')
    unpack(d['path'], delta, d['database_sha256'])
    apply_delta(path, delta); check_delta(path, delta, r['options'])
    if digests(path) != r['logical_table_digests']:
        raise ValueError('Incorrect case1063-discovery reconstruction')
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


def saved_query(out, session, evidence, bridges, roots, mode):
    out.mkdir()
    r, chosen, plans = query(session, evidence, bridges, roots, mode)
    tick=time.perf_counter()
    r['selection']=archive_json(out/'selection.json.gz',chosen)
    r['certificate']=archive_json(out/'coverage.json.gz',plans[0])
    r['serialization_seconds']=time.perf_counter()-tick
    (out/'report.json').write_text(encode(r)+'\n')
    return r, chosen


def prepare_handoff(out, history, parent, evidence, bridges, selection, mode):
    started=time.perf_counter()
    cls = BudgetedInventory if mode=='baseline' else CanonicalSourceInventory
    h=cls(history,**parent['options']);h.set_admission_budget(0)
    try:
        session=ExpansionSession(h,evidence,bridges)
        construction=time.perf_counter()-started
        roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in parent['cases']]
        result,chosen=saved_query(out,session,evidence,bridges,roots,'maintained')
        assert chosen==selection and result['closed']==[parent['final_closed'],parent['without_growth_closed']]
        result.update(session_construction_seconds=construction,seconds=time.perf_counter()-started,normalization_counts=normalization_counts(h))
        (out/'report.json').write_text(encode(result)+'\n')
        return result,session
    except BaseException:
        h.close();raise


def run(out):
    pipeline = time.perf_counter(); out.mkdir(exist_ok=False)
    r = dict(format=FORMAT, parent=dict(path=str(BASE), sha256=sha(BASE)), accelerator=dict(path=str(ACCELERATOR), sha256=ACCELERATOR_SHA),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
        fingerprints={name: sha(name) for name in FILES}, policy=POLICY, batch_limit=BATCHES, arms=[], session_runs=[], limitations=[
        'Two independent repetitions of up to four bounded expansion batches, resuming the pending 22-variable split in case 1063; this is a reproducibility and discovery study, not a speed comparison.',
        'The unchanged scheduler retains both cofactors, known-forcing priority and pending split resumption. Every batch has at most 32 admitted states and twelve advances, with interrupted re-entry charged again.',
        'Each repetition starts from the same checked parent, constructs a fresh canonical-source inventory and complete maintained catalog, and queries all originals after each batch. After each batch, follow the complete global selection, including handoff to a different original. Stop only when no source is selected or the four-batch allowance is exhausted.',
        'Existing copying, full live digests, append checks, positive certificates and reference validation remain enabled. The complete catalog is audited outside the timed sequence.',
        'Preparation, discovery, verification, serialization, retained bytes, reconstruction and reference checks are separate costs. Repeated family shapes are not proof transport or identity reuse.',
        'These are development cases with shared OS caches; no held-out claim, peak RAM bound, globally minimal expansion or unrestricted polynomial-SAT bound follows.'])
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); seed = tmp/'seed'; tick = time.perf_counter()
        r['seed_restore_metrics'] = {}
        parent, *base_evidence = restore_seed(seed, tmp, metrics=r['seed_restore_metrics'])
        r.update(restore_seconds=time.perf_counter()-tick, options=parent['options'],
            cases=parent['cases'], baseline_closed=parent['final_closed'],
            seed_table_digests=digests(seed), seed_database_bytes=seed.stat().st_size,
            evidence_counts_before=list(map(len, base_evidence)))
        seed_hash = sha(seed); bridges = read_archive(parent['bridges'])
        before = read_archive(parent['next_selection'])
        root = before['source']; assert root is not None and before['pending_split'] is not None
        r['source'] = root; r['source_original_indices'] = before['selected_original_cases']
        assert r['source_original_indices']==[] and parent['cases'][15]['original_case']==1063
        r['initial_scope_indices'] = [15]  # Checked independently through dependency edges.
        previous_bound = max((a for a in parent['arms'] if a['repeat']==0 and a['startup_mode']=='canonical'), key=lambda a:a['batch'])
        assert sha(previous_bound['path']) == previous_bound['sha256']
        previous = json.loads(Path(previous_bound['path']).read_text())
        r['previous_worker'] = previous_bound
        r['previously_unstored_sha256'] = previous['entered_but_unstored_sha256']
        assert not r['previously_unstored_sha256']
        r['initial_selection'] = archive_json(out/'initial-selection.json.gz', before)
        history = tmp/'history'; shutil.copyfile(seed, history); evidence = copy.deepcopy(base_evidence)
        touched = {}
        for repeat in range(2):
            for startup_mode in ('canonical',):
                name=f'session-{repeat}-{startup_mode}'; arm_history=tmp/(name+'-history')
                started=time.perf_counter();shutil.copyfile(seed,arm_history)
                arm_evidence=copy.deepcopy(base_evidence);session=None;batch_rows=[];queries=[];current=copy.deepcopy(before)
                warmup,session=prepare_handoff(out/(name+'-handoff'),arm_history,parent,arm_evidence,bridges,before,startup_mode)
                roots=[session.h._canonical(c['source'],session.h.config['max_depth'])[2] for c in r['cases']]
                try:
                    for batch in range(BATCHES):
                        if current['source'] is None:break
                        root=current['source']
                        batch_name=f'{name}-batch-{batch}'
                        arm,session=worker(out/batch_name,tmp/batch_name,arm_history,parent,arm_evidence,bridges,root,session,'live','copy')
                        first=read_archive(arm['steps'][0]['operation'])
                        assert first['source']==current['source']
                        r['arms'].append(dict(original_indices=current['selected_original_cases'],source_sha256=sha_key(root),scenario='resume',repeat=repeat,batch=batch,
                            mode='activation',export_mode='append',startup_mode=startup_mode,digest_mode='live',
                            path=str(out/batch_name/'report.json'),sha256=sha(out/batch_name/'report.json')))
                        batch_rows.append(arm)
                        apply_delta(history,tmp/batch_name/'delta');check_delta(history,tmp/batch_name/'delta',r['options'])
                        additions=read_archive(arm['splits']);evidence=add_splits(evidence,additions)
                        arm_evidence=add_splits(arm_evidence,additions)
                        for row in arm['steps']:
                            op=read_archive(row['operation'])
                            if op.get('record') is not None:touched[split_key(op['record'])]=op['record']
                        qr,chosen=saved_query(out/(batch_name+'-global'),session,arm_evidence,bridges,roots,'maintained')
                        queries.append(dict(path=str(out/(batch_name+'-global')/'report.json'),sha256=sha(out/(batch_name+'-global')/'report.json')))
                        current=chosen
                        print(json.dumps(dict(repeat=repeat,batch=batch,covered=sum(qr['closed'][0]),admitted=len(arm['admitted_state_sha256']),stored=len(arm['completed_new_state_sha256']),unfinished=len(arm['entered_but_unstored_sha256']))),flush=True)
                    final_cache=dict(checked_nodes=len(session.h.checked),prepared_checked_nodes=len(session.h.prepared.checked))
                    final_normalization=normalization_counts(session.h)
                    sequence_seconds=time.perf_counter()-started
                    tick=time.perf_counter()
                    with query_boundary(session,arm_evidence,bridges) as maintained:
                        fresh=routes_for(session.h,arm_evidence,bridges)
                        assert dict(maintained.by_source)==dict(fresh.by_source)
                        assert full(session.h,roots,maintained)==full(session.h,roots,fresh)
                    audit=dict(seconds=time.perf_counter()-tick,complete_catalog_equal=True)

                finally:
                    if session is not None:session.h.close()
                r['session_runs'].append(dict(repeat=repeat,startup_mode=startup_mode,digest_mode='live',handoff=dict(path=str(out/(name+'-handoff')/'report.json'),sha256=sha(out/(name+'-handoff')/'report.json')),batches=len(batch_rows),
                    seconds=sequence_seconds,queries=queries,catalog_audit=audit,final_cache=final_cache,worker_seconds=sum(a['worker_seconds'] for a in batch_rows),
                    admitted=sum(len(a['admitted_state_sha256']) for a in batch_rows),
                    completed=sum(len(a['completed_new_state_sha256']) for a in batch_rows),
                    seed_copy_bytes=sum(a['seed_copy_bytes'] for a in batch_rows),seed_copy_seconds=sum(a['seed_copy_seconds'] for a in batch_rows),
                    normalization_counts=final_normalization,final_digests=digests(arm_history)))
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
