"""Matched expansion workers differing only in digest source and guarded reuse.

The baseline copies the history and scans that copy as the frozen worker did.
The live mode scans every table on the owned inventory connection. Guarded mode
reuses unchanged-table hashes. All modes retain the batch copy, discovery budget,
scheduler, certificate checks and append exporter. The exclusive-ownership and
ordinary SQLite file-copy assumptions are inherited from the baseline worker.
"""
from collections import Counter
import copy
from pathlib import Path
import json
import shutil
import sqlite3
import time
from experiments.compare_cnf_expansion_session import (
    POLICY, BudgetedInventory, sha_key, split_key, AppendDelta, ExpansionSession,
    full, shape, EarlySavedExpansion, focus_selection, archive_json, add_splits,
    routes_for, expand, check_delta, save_delta, encode)
from experiments.compare_cnf_probe_continuation import TABLES
from experiments.compare_cnf_clause_mask import table_digest
from experiments.cnf_guarded_digests import GuardedDigests


def full_snapshot(db):
    started=time.perf_counter()
    if db.in_transaction:raise ValueError('Commit before hashing')
    db.execute('BEGIN IMMEDIATE')
    try:
        results={}; scans={}
        for table in TABLES:
            tick=time.perf_counter();results[table]=table_digest(db,table)
            scans[table]=time.perf_counter()-tick
    finally:db.rollback()
    return results,dict(seconds=time.perf_counter()-started,scan_seconds=scans,
        scanned_tables=list(TABLES),reused_tables=[],scanned_rows=sum(x['rows'] for x in results.values()),reused_rows=0)


def worker(out,tmp,history,parent,evidence,old_bridges,root,session=None,digest_mode='copy'):
    out.mkdir();tmp.mkdir();started=time.perf_counter();seed=tmp/'batch-seed';shutil.copyfile(history,seed)
    h=session.h if session is not None else BudgetedInventory(history,**parent['options'])
    if session is None:h.set_admission_budget(0)
    cache=getattr(session,'digest_cache',None) if session is not None else None
    try:
        if digest_mode=='copy':
            with sqlite3.connect(seed) as db: seed_digests,digest_cost=full_snapshot(db)
        elif digest_mode=='live':
            seed_digests,digest_cost=full_snapshot(h.db)
        elif digest_mode=='guarded':
            if cache is None:cache=GuardedDigests(h.db)
            seed_digests,digest_cost=cache.snapshot()
        else:raise ValueError('Unknown digest mode')
    except BaseException:
        h.close();raise
    r=dict(mode='activation',scenario='resume',export_mode='append',session_reused=session is not None,
        policy=POLICY,source_sha256=sha_key(root),steps=[],seed_table_digests=seed_digests,
        digest_mode=digest_mode,digest_cost=digest_cost)
    inherited={split_key(x) for x in evidence[3]}
    saved=copy.deepcopy(evidence[3])
    bridges=copy.deepcopy(old_bridges);evidence=copy.deepcopy(evidence);focus=root
    try:
        tick=time.perf_counter();boundary=AppendDelta(h.db)
        r['export_boundary_seconds']=time.perf_counter()-tick;tick=time.perf_counter()
        if session is None:session=ExpansionSession(h,evidence,bridges)
        session.digest_cache=cache
        maintained=session.begin(POLICY['state_limit'],evidence,bridges)
        r['session_startup_seconds']=time.perf_counter()-tick
        routes=maintained.routes
        r['initial_activation_index']=maintained.statistics()
        closed,plans,_=full(h,[root],routes)
        assert closed[0]==[False];r['source_shape']=shape(h,root);r['preparation_seconds']=time.perf_counter()-started
        settings={k:v for k,v in POLICY.items() if k!='step_limit'}
        engine=EarlySavedExpansion(h,**settings)
        stop='step_limit'
        for step in range(POLICY['step_limit']):
            if closed[0][0]:stop='target_closed';break
            tick=time.perf_counter();counts=Counter()
            chosen=focus_selection(h,routes,evidence,saved,focus,False);source=chosen['source'];assert source is not None
            row=dict(step=step,selection_seconds=time.perf_counter()-tick,source_sha256=sha_key(source),source_shape=shape(h,source))
            tick=time.perf_counter()
            result=engine.advance(source,routes,counts,pending_split=chosen['pending_split'])
            row.update(acquisition_seconds=time.perf_counter()-tick,acquisition_counts=dict(counts),
                mode=result['mode'],admitted_total=len(h.admitted),admitted_now=len(result['added']),pending=result['pending'])
            row['operation']=archive_json(out/f'step-{step:02d}.json.gz',result)
            if result['mode'] in ('early_saved_split','early_closed_split','split_after_ordinary_exhaustion','resume_split'):
                saved=add_splits([[],[],[],saved,[]],[result['record']])[3];evidence=add_splits(evidence,[result['record']])
            tick=time.perf_counter()
            if maintained:
                row['maintenance']=maintained.refresh(result,evidence,bridges);routes=maintained.routes
            else:
                routes=routes_for(h,evidence,bridges);row['maintenance']=dict(mode='full_rebuild')
            row['route_refresh_seconds']=time.perf_counter()-tick
            row['database_changes']=h.db.total_changes
            tick=time.perf_counter();closed,plans,cc=full(h,[root],routes)
            row.update(coverage_seconds=time.perf_counter()-tick,coverage_counts=cc,target_closed=closed[0][0]);r['steps'].append(row)
            print(json.dumps(dict(arm=out.name,step=step,shape=row['source_shape'],mode=result['mode'],
                admitted=len(h.admitted),closed=closed[0][0],pending=result['pending'])),flush=True)
            if result['pending']:stop='admission_limit';break
            if result['mode']=='no_saved_pair':stop='no_saved_pair';break
        if closed[0][0]:stop='target_closed'
        r['final_activation_index']=maintained.statistics()
        r.update(stop=stop,target_closed=closed[0][0],target_flags=closed[0],without_growth_flags=closed[1],focus=focus,
            admitted_state_sha256=sorted(map(sha_key,h.admitted)),admission_counts=dict(h.admission_counts))
        r['bridges']=archive_json(out/'bridges.json.gz',bridges);r['splits']=archive_json(out/'splits.json.gz',[x for x in saved if split_key(x) not in inherited])
        r['certificate']=archive_json(out/'coverage.json.gz',plans[0])
        r['expanded_certificate']=archive_json(out/'expanded-coverage.json.gz',expand(h,plans[0],plans[0]['roots'],routes,Counter()))
        next_selection=focus_selection(h,routes,evidence,saved,focus,closed[0][0])
        r['next_selection']=archive_json(out/'next-selection.json.gz',next_selection)
        r['delta']=(boundary.save(tmp/'delta',out/'proof-delta.sqlite3.gz') if boundary is not None
            else save_delta(seed,history,tmp/'delta',out/'proof-delta.sqlite3.gz'))
        tick=time.perf_counter();r['cold_delta_counts']=check_delta(history,tmp/'delta',parent['options']);r['cold_delta_seconds']=time.perf_counter()-tick
        with sqlite3.connect(tmp/'delta') as db:stored={sha_key(k) for k, in db.execute('SELECT id FROM cnf_patterns_v1')}
        entered=set(r['admitted_state_sha256']);assert stored<=entered and len(entered)<=POLICY['state_limit']
        r.update(completed_new_state_sha256=sorted(stored),entered_but_unstored_sha256=sorted(entered-stored),history_bytes=history.stat().st_size)
    except BaseException:
        r['splits']=archive_json(out/'failed-splits.json.gz',saved);r['bridges']=archive_json(out/'failed-bridges.json.gz',bridges)
        r['failed_delta']=save_delta(seed,history,tmp/'failed-delta',out/'failed-proof-delta.sqlite3.gz')
        (out/'failed-report.json').write_text(encode(r)+'\n');h.close();raise
    r['worker_seconds']=time.perf_counter()-started
    r['expansion_seconds']=sum(sum(row[k] for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')) for row in r['steps'])
    r['external_assumption_attempts']=sum(row['acquisition_counts'].get('probe_attempts',0) for row in r['steps'])
    (out/'report.json').write_text(encode(r)+'\n');return r,session

