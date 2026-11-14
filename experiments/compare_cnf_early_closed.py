#!/usr/bin/env python3
"""Compare early closed-cofactor reuse against probing, and preserve both arms.

Each arm starts from an independent copy of the same case-specific checkpoint.
The latest authoritative checkpoint receives the conflict-checked union of all
arms; its admission count is NOT a single arm's 32-state allowance.
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

from experiments.continue_cnf_original_warm import restore_checkpoint as restore_base
from experiments.continue_cnf_local_forcing import restore_checkpoint as restore_control, profile
from experiments.continue_cnf_reused_branch import routes_for
from experiments.continue_cnf_original_splits import add_splits
from experiments.cnf_original_frontier import select
from experiments.cnf_early_closed import EarlyClosedExpansion
from experiments.cnf_warm_expansion import WarmExpansion
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_trace_split import record_key, verify as verify_split
from experiments.cnf_split_frontier import frontier
from experiments.cnf_route_composition import compose, verify_plan
from experiments.cnf_source_local import check_delta
from experiments.cnf_expanded_coverage import expand, checked_inventory
from experiments.cnf_positive_primitives import verify_positive
from experiments.cnf_learning_batch import selection as learning_selection
from experiments.compare_cnf_incremental_coverage import full, check_plans
from experiments.compare_cnf_split_batch import save_delta, new_probes
from experiments.compare_cnf_target_probe import reference as probe_reference
from experiments.compare_cnf_trace_split import reference as split_reference
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key, digests, unpack, apply_delta, WithoutGrowth
from experiments.cnf_pattern_inventory import encode

BASE=Path('experiments/results/cnf-original-warm/report.json')
CONTROL=Path('experiments/results/cnf-local-forcing/report.json')
FORMAT='early-closed-expansion-comparison-v1'
POLICY=dict(step_limit=12,state_limit=32,pair_limit=32,candidate_limit=64)
FILES=['experiments/cnf_early_closed.py','experiments/compare_cnf_early_closed.py',
       'solver/test_cnf_early_closed.py','experiments/cnf_original_frontier.py',
       'experiments/cnf_warm_expansion.py']


def shape(h,key):
    cnf=h._load(key)['cnf']
    return [len({abs(l) for c in cnf for l in c}),len(cnf),sum(map(len,cnf))]


def restore_checkpoint(report_path,path,tmp):
    current=Path(report_path);chain=[];seen=set()
    while current.resolve()!=BASE.resolve():
        if current.resolve() in seen:raise ValueError('Cyclic warm-batch lineage')
        seen.add(current.resolve());r=json.loads(current.read_text())
        if r['format']!=FORMAT or sha(r['parent']['path'])!=r['parent']['sha256']:
            raise ValueError('Changed warm-batch parent')
        for name,digest in r['fingerprints'].items():
            if sha(name)!=digest:raise ValueError('Changed warm-batch implementation')
        chain.append(r);current=Path(r['parent']['path'])
    inherited=tmp/'early-closed-inherited';inherited.mkdir(exist_ok=True)
    parent,*evidence=restore_base(BASE,path,inherited)
    for i,r in enumerate(reversed(chain)):
        if (digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed'] or
                parent['options']!=r['options'] or parent['cases']!=r['cases']):
            raise ValueError('Incorrect warm-batch seed')
        d=r['delta'];delta=tmp/f'early-closed-delta-{i}'
        if sha(d['path'])!=d['sha256']:raise ValueError('Changed warm delta')
        unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
        check_delta(path,delta,r['options'])
        if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect warm reconstruction')
        splits=read_archive(r['splits']);evidence=add_splits(evidence,splits)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
        try:
            for record in splits:verify_split(h,record,Counter())
            roots=[h._canonical(c['source'],h.config['max_depth'])[2]
                   for c,closed in zip(r['cases'],r['final_closed'],strict=True) if closed]
            verify_positive(h,read_archive(r['expanded_certificate']),roots,evidence,Counter())
        finally:h.close()
        if any(a and not b for a,b in zip(r['baseline_closed'],r['final_closed'],strict=True)):
            raise ValueError('Lost previous positive coverage')
        parent=r
    return parent,*evidence


def worker(out,tmp,seed,parent,evidence,target,mode):
    out.mkdir();tmp.mkdir();started=time.perf_counter();history=tmp/'history'
    shutil.copyfile(seed,history);r=dict(mode=mode,policy=POLICY,root_sha256=sha_key(target),steps=[])
    h=BudgetedInventory(history,**parent['options']);h.set_admission_budget(0)
    saved=[];evidence=copy.deepcopy(evidence)
    try:
        routes=routes_for(h,evidence);closed,plans,_=full(h,[target],routes)
        if closed[0]!=[False]:raise ValueError('Comparison target must initially be open')
        r['root_shape']=shape(h,target);r['preparation_seconds']=time.perf_counter()-started
        engine_type=WarmExpansion if mode=='probe_first' else EarlyClosedExpansion
        engine=engine_type(h,**{k:v for k,v in POLICY.items() if k!='step_limit'})
        h.set_admission_budget(POLICY['state_limit']);stop='step_limit'
        for step in range(POLICY['step_limit']):
            if closed[0][0]:stop='target_closed';break
            row=dict(step=step);tick=time.perf_counter();counts=Counter()
            # Only splits generated below this target seed the scheduling view.
            # The semantic route catalog still contains ALL inherited evidence.
            scheduling=[*evidence[:3],saved,evidence[4]]
            chosen=select(h,routes,scheduling,[target],[False],counts)
            source=chosen['source'];assert source is not None
            row.update(selection_seconds=time.perf_counter()-tick,selection_counts=dict(counts),
                source_sha256=sha_key(source),source_shape=shape(h,source))
            counts=Counter();tick=time.perf_counter()
            result=engine.advance(source,routes,counts,pending_split=chosen['pending_split'])
            row.update(acquisition_seconds=time.perf_counter()-tick,acquisition_counts=dict(counts),
                mode=result['mode'],admitted_total=len(h.admitted),admitted_now=len(result['added']),pending=result['pending'])
            row['operation']=archive_json(out/f'step-{step:02d}.json.gz',result)
            if result['mode'] in ('early_closed_split','split_after_ordinary_exhaustion'):
                saved=add_splits([[],[],[],saved,[]],[result['record']])[3]
                evidence=add_splits(evidence,[result['record']])
            tick=time.perf_counter();routes=routes_for(h,evidence)
            row['route_refresh_seconds']=time.perf_counter()-tick
            tick=time.perf_counter();closed,plans,cc=full(h,[target],routes)
            row.update(coverage_seconds=time.perf_counter()-tick,coverage_counts=cc,target_closed=closed[0][0])
            r['steps'].append(row)
            print(json.dumps(dict(arm=out.name,step=step,shape=row['source_shape'],mode=result['mode'],
                admitted=len(h.admitted),closed=closed[0][0],pending=result['pending'])),flush=True)
            if result['pending']:stop='admission_limit';break
            if result['mode']=='no_saved_pair':stop='no_saved_pair';break
        if closed[0][0]:stop='target_closed'
        r.update(stop=stop,target_closed=closed[0][0],without_growth_closed=closed[1][0],
            admitted_state_sha256=sorted(map(sha_key,h.admitted)),admission_counts=dict(h.admission_counts))
        assert len(h.admitted)<=POLICY['state_limit']
        r['splits']=archive_json(out/'splits.json.gz',saved)
        r['certificate']=archive_json(out/'coverage.json.gz',plans[0])
        r['expanded_certificate']=archive_json(out/'expanded-coverage.json.gz',expand(h,plans[0],plans[0]['roots'],routes,Counter()))
        r['next_selection']=archive_json(out/'next-selection.json.gz',
            None if closed[0][0] else select(h,routes,[*evidence[:3],saved,evidence[4]],[target],[False],Counter()))
        r['delta']=save_delta(seed,history,tmp/'delta',out/'proof-delta.sqlite3.gz')
        tick=time.perf_counter();r['cold_delta_counts']=check_delta(history,tmp/'delta',parent['options'])
        r['cold_delta_seconds']=time.perf_counter()-tick
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
            'Two adaptively selected development residuals, one earlier forcing control and one current frontier; not independent holdouts.',
            'One serial run per policy and case, with reversed policy order across cases; no timing confidence intervals or general speedup claim.',
            'Each arm has twelve advances and its own shared 32-state allowance. The persisted union is NOT bounded by one such allowance.',
            'Worker comparisons include preparation, checking and delta persistence; authority reconstruction and final global coverage are separately charged.',
            'Selection follows one target and newly created split descendants. Full semantic catalogs retain all inherited routes.',
            'Closed children mean checked structural closure, not necessarily SAT. Both branches remain required; memory figures are serialized storage, not peak RAM.',
            'All arm deltas and split evidence are merged into the latest parent, including regressions. Old historical-control rows may already exist in that parent.'])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';tick=time.perf_counter()
        parent,*base_evidence=restore_base(BASE,seed,tmp)
        r.update(restore_seconds=time.perf_counter()-tick,options=parent['options'],cases=parent['cases'],
            baseline_closed=parent['final_closed'],seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,
            evidence_counts_before=list(map(len,base_evidence)))
        parent_hash=sha(seed);history=tmp/'history';shutil.copyfile(seed,history);evidence=copy.deepcopy(base_evidence)
        print('Restored current authority; compare current case 1445',flush=True)
        for case in (1445,1189):
            if case==1445:
                case_seed,case_parent,case_evidence=seed,parent,base_evidence
                order=('probe_first','early_closed')
            else:
                control_tmp=tmp/'control';control_tmp.mkdir();case_seed=control_tmp/'seed';tick=time.perf_counter()
                case_parent,*case_evidence=restore_control(CONTROL,case_seed,control_tmp)
                r['control']=dict(path=str(CONTROL),sha256=sha(CONTROL),restore_seconds=time.perf_counter()-tick,
                    seed_table_digests=digests(case_seed));order=('early_closed','probe_first')
                if case_parent['options']!=r['options']:raise ValueError('Control policy differs')
                print('Restored historical authority; compare forcing control 1189',flush=True)
            state=read_archive(case_parent['frontier'])
            if state['pending'] or len(state['leaves'])!=1:raise ValueError('Expected one selected case frontier')
            target=state['leaves'][0]['source'];initial_sha=sha(case_seed)
            for mode in order:
                name=f'{case}-{mode}';arm=worker(out/name,tmp/name,case_seed,case_parent,case_evidence,target,mode)
                r['arms'].append(dict(case=case,mode=mode,path=str(out/name/'report.json'),sha256=sha(out/name/'report.json')))
                apply_delta(history,tmp/name/'delta');check_delta(history,tmp/name/'delta',r['options'])
                evidence=add_splits(evidence,read_archive(arm['splits']))
            assert sha(case_seed)==initial_sha
        assert sha(seed)==parent_hash;r['parent_unchanged']=True
        previous={record_key(x) for x in base_evidence[3]}
        new_splits=[x for x in evidence[3] if record_key(x) not in previous]
        r['splits']=archive_json(out/'splits.json.gz',new_splits);r['evidence_counts_after']=list(map(len,evidence))
        print('Check complete original coverage after merging all arms',flush=True)
        tick=time.perf_counter();h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
        try:
            routes=routes_for(h,evidence);roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
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
            verify_positive(h,read_archive(r['expanded_certificate']),claimed,evidence,Counter());assert not h.admitted
        finally:h.close()
        r['cold_positive_seconds']=time.perf_counter()-tick
        db=sqlite3.connect(tmp/'delta');r['new_node_kinds']=dict(Counter(json.loads(p)['kind'] for p, in db.execute('SELECT payload FROM cnf_patterns_v1')));db.close()
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],new_kinds=r['new_node_kinds'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))

