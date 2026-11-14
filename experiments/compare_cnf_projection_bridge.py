#!/usr/bin/env python3
"""Compare completion of two retained leaves with a checked projection bridge.

All arms own independent seeds and one shared admission budget. The union keeps
both successful and unsuccessful work; repeated comparison budgets are separate.
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
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_split_cost import restore_checkpoint as restore_base
from experiments.continue_cnf_local_forcing import profile
from experiments.continue_cnf_reused_branch import routes_for as base_routes
from experiments.continue_cnf_original_splits import add_splits
from experiments.cnf_original_frontier import select
from experiments.cnf_early_closed import EarlyClosedExpansion
from experiments.cnf_source_local import SourceProbeRoutes, advance_one
from experiments.cnf_trace_split import candidates
from experiments.cnf_split_batch import acquire_pair
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_trace_split import record_key, verify as verify_split
from experiments.cnf_split_frontier import frontier
from experiments.cnf_route_composition import compose, verify_plan
from experiments.cnf_source_local import check_delta
from experiments.cnf_expanded_coverage import expand, checked_inventory
from experiments.cnf_projection_bridge import discover as discover_bridge, attach as attach_bridge, verify as verify_bridge, verify_positive
from experiments.cnf_learning_batch import selection as learning_selection
from experiments.compare_cnf_incremental_coverage import full, check_plans
from experiments.compare_cnf_split_batch import save_delta, new_probes
from experiments.compare_cnf_target_probe import reference as probe_reference
from experiments.compare_cnf_trace_split import reference as split_reference
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key, digests, unpack, apply_delta, WithoutGrowth
from experiments.cnf_pattern_inventory import encode

BASE=Path('experiments/results/cnf-split-cost-1299/report.json')
FORMAT='projection-bridge-comparison-v1'
POLICY=dict(step_limit=12,state_limit=32,pair_limit=32,candidate_limit=64)
FILES=['experiments/compare_cnf_projection_bridge.py','experiments/cnf_projection_bridge.py',
       'solver/test_cnf_projection_bridge.py','experiments/cnf_early_closed.py',
       'experiments/cnf_original_frontier.py','experiments/cnf_warm_expansion.py',
       'experiments/cnf_source_local.py','experiments/cnf_split_batch.py']


def routes_for(h,evidence,bridges=()):
    routes=base_routes(h,evidence)
    for record in bridges:attach_bridge(h,routes,record,Counter())
    return routes


def restore_checkpoint(report_path,path,tmp):
    r=json.loads(Path(report_path).read_text())
    if r['format']!=FORMAT or Path(r['parent']['path'])!=BASE or sha(BASE)!=r['parent']['sha256']:
        raise ValueError('Changed bridge checkpoint parent')
    for name,digest in r['fingerprints'].items():
        if sha(name)!=digest:raise ValueError('Changed bridge implementation')
    parent,*evidence=restore_base(BASE,path,tmp)
    if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:
        raise ValueError('Incorrect bridge checkpoint seed')
    d=r['delta'];delta=tmp/'bridge-delta'
    if sha(d['path'])!=d['sha256']:raise ValueError('Changed bridge delta')
    unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta);check_delta(path,delta,r['options'])
    if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect bridge reconstruction')
    evidence=add_splits(evidence,read_archive(r['splits']));bridges=read_archive(r['bridges'])
    h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
    try:
        for record in bridges:verify_bridge(h,record,Counter())
        roots=[h._canonical(c['source'],h.config['max_depth'])[2]
            for c,b in zip(r['cases'],r['final_closed'],strict=True) if b]
        verify_positive(h,read_archive(r['expanded_certificate']),roots,evidence,bridges,Counter())
        assert not h.admitted
    finally:h.close()
    return r,*evidence


def shape(h,key):
    cnf=h._load(key)['cnf']
    return [len({abs(l) for c in cnf for l in c}),len(cnf),sum(map(len,cnf))]


def worker(out,tmp,seed,parent,evidence,targets,bridge,mode):
    out.mkdir();tmp.mkdir();started=time.perf_counter();history=tmp/'history'
    shutil.copyfile(seed,history);r=dict(mode=mode,policy=POLICY,root_sha256=list(map(sha_key,targets)),steps=[],seed_table_digests=digests(seed))
    h=BudgetedInventory(history,**parent['options']);h.set_admission_budget(0)
    saved=[];evidence=copy.deepcopy(evidence)
    try:
        routes=routes_for(h,evidence,[bridge] if mode=="bridge" else []);closed,plans,_=full(h,targets,routes)
        if closed[0]!=[False,False]:raise ValueError('Comparison target must initially be open')
        r['root_shape']=[shape(h,target) for target in targets];r['preparation_seconds']=time.perf_counter()-started
        engine=EarlyClosedExpansion(h,**{k:v for k,v in POLICY.items() if k!='step_limit'})
        h.set_admission_budget(POLICY['state_limit']);stop='step_limit'
        for step in range(POLICY['step_limit']):
            if all(closed[0]):stop='target_closed';break
            row=dict(step=step);tick=time.perf_counter();counts=Counter()
            # Only splits generated below this target seed the scheduling view.
            # The semantic route catalog still contains ALL inherited evidence.
            scheduling=[*evidence[:3],saved,evidence[4]]
            chosen=select(h,routes,scheduling,targets,closed[0],counts)
            source=chosen['source'];assert source is not None
            row.update(selection_seconds=time.perf_counter()-tick,selection_counts=dict(counts),
                source_sha256=sha_key(source),source_shape=shape(h,source))
            counts=Counter();tick=time.perf_counter()
            result=engine.advance(source,routes,counts,pending_split=chosen['pending_split'])
            row.update(acquisition_seconds=time.perf_counter()-tick,acquisition_counts=dict(counts),
                mode=result['mode'],admitted_total=len(h.admitted),admitted_now=len(result['added']),pending=result['pending'])
            row['operation']=archive_json(out/f'step-{step:02d}.json.gz',result)
            if result['mode'] in ('preselected_split','early_closed_split','split_after_ordinary_exhaustion'):
                saved=add_splits([[],[],[],saved,[]],[result['record']])[3]
                evidence=add_splits(evidence,[result['record']])
            tick=time.perf_counter();routes=routes_for(h,evidence,[bridge] if mode=="bridge" else [])
            row['route_refresh_seconds']=time.perf_counter()-tick
            tick=time.perf_counter();closed,plans,cc=full(h,targets,routes)
            row.update(coverage_seconds=time.perf_counter()-tick,coverage_counts=cc,target_closed=all(closed[0]))
            r['steps'].append(row)
            print(json.dumps(dict(arm=out.name,step=step,shape=row['source_shape'],mode=result['mode'],
                admitted=len(h.admitted),closed=all(closed[0]),pending=result['pending'])),flush=True)
            if result['pending']:stop='admission_limit';break
            if result['mode']=='no_saved_pair':stop='no_saved_pair';break
        if all(closed[0]):stop='target_closed'
        r.update(stop=stop,target_closed=all(closed[0]),target_flags=closed[0],without_growth_closed=all(closed[1]),without_growth_flags=closed[1],
            admitted_state_sha256=sorted(map(sha_key,h.admitted)),admission_counts=dict(h.admission_counts))
        assert len(h.admitted)<=POLICY['state_limit']
        r['splits']=archive_json(out/'splits.json.gz',saved)
        r['certificate']=archive_json(out/'coverage.json.gz',plans[0])
        r['expanded_certificate']=archive_json(out/'expanded-coverage.json.gz',expand(h,plans[0],plans[0]['roots'],routes,Counter()))
        r['next_selection']=archive_json(out/'next-selection.json.gz',
            None if all(closed[0]) else select(h,routes,[*evidence[:3],saved,evidence[4]],targets,closed[0],Counter()))
        r['delta']=save_delta(seed,history,tmp/'delta',out/'proof-delta.sqlite3.gz')
        tick=time.perf_counter();r['cold_delta_counts']=check_delta(history,tmp/'delta',parent['options'])
        r['cold_delta_seconds']=time.perf_counter()-tick
        db=sqlite3.connect(tmp/'delta')
        stored={sha_key(k) for k, in db.execute('SELECT id FROM cnf_patterns_v1')};db.close()
        entered=set(r['admitted_state_sha256'])
        if not stored<=entered:raise ValueError('Stored novel pattern lacks admission')
        r['completed_new_state_sha256']=sorted(stored)
        r['entered_but_unstored_sha256']=sorted(entered-stored)
        r['history_bytes']=history.stat().st_size
    except BaseException:
        r['splits']=archive_json(out/'failed-splits.json.gz',saved)
        r['failed_delta']=save_delta(seed,history,tmp/'failed-delta',out/'failed-proof-delta.sqlite3.gz')
        (out/'failed-report.json').write_text(encode(r)+'\n');raise
    finally:h.close()
    r['worker_seconds']=time.perf_counter()-started
    r['expansion_seconds']=sum(sum(row[k] for k in ('selection_seconds','acquisition_seconds','route_refresh_seconds','coverage_seconds')) for row in r['steps'])
    r['external_assumption_attempts']=sum(row['acquisition_counts'].get('probe_attempts',0) for row in r['steps'])
    (out/'report.json').write_text(encode(r)+'\n')
    return r


def run(out):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    r=dict(format=FORMAT,parent=dict(path=str(BASE),sha256=sha(BASE)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={name:sha(name) for name in FILES},policy=POLICY,arms=[],limitations=[
            'One pair of adaptively selected development leaves; two serial repetitions per mode with reversed order.',
            'Both modes must structurally close the same two roots. A checked projection bridge can reuse the smaller root.',
            'Each worker owns an independent seed, twelve advances and a single 32-state allowance; the union is not one allowance.',
            'Discovery, exact projection/subsumption checking, preparation, refresh, persistence and cold replay are charged.',
            'The bridge is order-preserving and one-variable, with at most 64 opposing pairs and two final extra clauses. A miss proves no hardness.',
            'Reference answers do not supply structural closure. Disk bytes are not peak RAM; no unrestricted expansion bound follows.'])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';tick=time.perf_counter()
        parent,*base_evidence=restore_base(BASE,seed,tmp)
        r.update(restore_seconds=time.perf_counter()-tick,options=parent['options'],cases=parent['cases'],
            baseline_closed=parent['final_closed'],seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,
            evidence_counts_before=list(map(len,base_evidence)))
        parent_hash=sha(seed)
        h=BudgetedInventory(seed,**r['options']);h.set_admission_budget(0)
        try:
            leaves=read_archive(parent['frontier_profiles']);targets=[row['source'] for row in leaves]
            assert len(targets)==2
            small,large=[h._load(key)['cnf'] for key in targets]
            tick=time.perf_counter();counts=Counter();proof=discover_bridge(large,small,counts)
            assert proof is not None
            bridge=dict(source=targets[1],target=targets[0],proof=proof)
            verify_bridge(h,bridge,counts)
            r['bridge_discovery']=dict(seconds=time.perf_counter()-tick,counts=dict(counts),
                source_shape=shape(h,targets[1]),target_shape=shape(h,targets[0]))
            r['bridges']=archive_json(out/'bridges.json.gz',[bridge])
            r['target_keys']=archive_json(out/'targets.json.gz',targets)
            assert not h.admitted
        finally:h.close()
        history=tmp/'history';shutil.copyfile(seed,history);evidence=copy.deepcopy(base_evidence)
        for repeat,order in enumerate((('independent','bridge'),('bridge','independent'))):
            for mode in order:
                name=f'{repeat}-{mode}'
                arm=worker(out/name,tmp/name,seed,parent,base_evidence,targets,bridge,mode)
                r['arms'].append(dict(mode=mode,repeat=repeat,path=str(out/name/'report.json'),sha256=sha(out/name/'report.json')))
                try:
                    apply_delta(history,tmp/name/'delta');check_delta(history,tmp/name/'delta',r['options'])
                    evidence=add_splits(evidence,read_archive(arm['splits']))
                except BaseException:
                    r['failed_delta']=save_delta(seed,history,tmp/'failed-delta',out/'failed-proof-delta.sqlite3.gz')
                    r['failed_evidence']=archive_json(out/'failed-evidence.json.gz',evidence)
                    (out/'failed-report.json').write_text(encode(r)+'\n');raise
        assert sha(seed)==parent_hash;r['parent_unchanged']=True
        previous={record_key(x) for x in base_evidence[3]}
        new_splits=[x for x in evidence[3] if record_key(x) not in previous]
        r['splits']=archive_json(out/'splits.json.gz',new_splits);r['evidence_counts_after']=list(map(len,evidence))
        print('Check complete original coverage after merging all arms',flush=True)
        tick=time.perf_counter();h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
        try:
            routes=routes_for(h,evidence,[bridge]);roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
            r['global_route_preparation_seconds']=time.perf_counter()-tick;tick=time.perf_counter()
            closed,plans,cc=full(h,roots,routes);r['global_coverage_seconds']=time.perf_counter()-tick;r['global_counts']=cc
            r['final_closed'],r['without_growth_closed']=closed
            if any(a and not b for a,b in zip(r['baseline_closed'],r['final_closed'],strict=True)):raise ValueError('Lost coverage')
            r['gains']=[i for i,(a,b) in enumerate(zip(r['baseline_closed'],r['final_closed'],strict=True)) if b and not a]
            r['certificate']=archive_json(out/'coverage.json.gz',plans[0])
            r['expanded_certificate']=archive_json(out/'expanded-coverage.json.gz',expand(h,plans[0],plans[0]['roots'],routes,Counter()))
            state=frontier(h,routes,evidence[3],Counter());r['frontier']=archive_json(out/'frontier.json.gz',state)
            r['frontier_profiles']=archive_json(out/'frontier-profiles.json.gz',[profile(h,routes,row) for row in state['leaves']])
            r['learning']=archive_json(out/'learning.json.gz',learning_selection(h,routes,Counter()))
            r['next_selection']=archive_json(out/'next-selection.json.gz',select(h,routes,evidence,roots,closed[0],Counter()))
            r['historical_cache']=checked_inventory(h)[1]
            r['delta']=save_delta(seed,history,tmp/'delta',out/'proof-delta.sqlite3.gz')
            d=parent['reference'];assert sha(d['path'])==d['sha256'];unpack(d['path'],tmp/'reference',d['database_sha256'])
            shutil.copyfile(tmp/'reference',tmp/'reference-seed')
            pr=probe_reference(h,routes,[dict(kind=x['kind'],id=x['id']) for x in new_probes(tmp/'delta')],r,out,tmp)
            r['probe_reference']={k:pr[k] for k in ('rows','originals','seconds','cold_seconds','verified_nodes')}
            r['reference']=split_reference(h,new_splits,r,out,tmp)
        finally:h.close()
        r['logical_table_digests']=digests(history);r['expanded_database_bytes']=history.stat().st_size
        tick=time.perf_counter();r['cold_delta_counts']=check_delta(history,tmp/'delta',r['options']);r['cold_delta_seconds']=time.perf_counter()-tick
        rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,tmp/'delta')
        assert digests(rebuilt)==r['logical_table_digests'];before=sha(rebuilt);apply_delta(rebuilt,tmp/'delta');assert sha(rebuilt)==before
        r['idempotent_merge']=True;tick=time.perf_counter();h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0)
        try:
            for record in new_splits:verify_split(h,record,Counter())
            claimed=[h._canonical(c['source'],h.config['max_depth'])[2] for c,b in zip(r['cases'],r['final_closed'],strict=True) if b]
            verify_positive(h,read_archive(r['expanded_certificate']),claimed,evidence,[bridge],Counter());assert not h.admitted
        finally:h.close()
        r['cold_positive_seconds']=time.perf_counter()-tick
        db=sqlite3.connect(tmp/'delta');r['new_node_kinds']=dict(Counter(json.loads(p)['kind'] for p, in db.execute('SELECT payload FROM cnf_patterns_v1')));db.close()
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],new_kinds=r['new_node_kinds'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
