#!/usr/bin/env python3
"""Resume bounded probe passes below acquired learned-clause targets."""
from collections import Counter
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_trace_learning import restore_checkpoint as restore_base
from experiments.compare_cnf_trace_reuse import read_archive,archive_json
from experiments.compare_cnf_probe_continuation import (sha,sha_key,digests,export_delta,apply_delta,
    compressed,unpack,audit,WithoutGrowth)
from experiments.cnf_target_probe import search,targets,remaining
from experiments.cnf_trace_learning import LearnedTraceRoutes
from experiments.cnf_probe_window import verify_window
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_residual_dag import ResidualSolver,holds,restrict
from experiments.cnf_simplification import check_simplification
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_pattern_inventory import encode

BASE=Path('experiments/results/cnf-trace-learning/report.json')
FORMAT='learned-target-probe-v1'
POLICY=dict(step_limit=8,source_limit=4,state_limit=32)


def restore_checkpoint(report_path,path,tmp):
    """Replay an immutable base and any number of additive target-probe passes."""
    current=Path(report_path);chain=[];seen=set()
    while current.resolve()!=BASE.resolve():
        if current.resolve() in seen:raise ValueError('Cyclic checkpoint lineage')
        seen.add(current.resolve());r=json.loads(current.read_text())
        if r.get('format')!=FORMAT:raise ValueError('Unexpected target-probe checkpoint')
        for p,digest in r['fingerprints'].items():
            if sha(p)!=digest:raise ValueError('Changed target-probe implementation')
        if sha(r['parent']['path'])!=r['parent']['sha256']:raise ValueError('Changed parent')
        chain.append(r);current=Path(r['parent']['path'])
    parent,rewrites,learning=restore_base(BASE,path,tmp)
    for i,r in enumerate(reversed(chain)):
        if digests(path)!=r['seed_table_digests']:raise ValueError('Incorrect target-probe seed')
        if r['baseline_closed']!=parent['final_closed']:raise ValueError('Incorrect baseline coverage')
        d=r['delta'];delta=tmp/f'target-pass-{i}'
        if sha(d['path'])!=d['sha256']:raise ValueError('Changed target-probe delta')
        unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
        if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect target-probe reconstruction')
        parent=r
    return parent,rewrites,learning


def checked_target(h,routes,kind,record):
    if kind=='probe_window':return verify_window(h,record,Counter())
    if kind=='probe_continuation':return routes.verify(h,record,Counter())
    raise ValueError('Unexpected probe kind')


def lift_forced(source,record,model):
    last=record['probing']['attempts'][-1];fixed={last['variable']:not last['value']}
    _,closure=check_simplification(restrict(source,fixed,Counter()),record['probing']['closure'],Counter(),pure=False)
    fixed.update(closure);result={abs(l):False for c in source for l in c}
    result.update(model);result.update(fixed)
    if not holds(source,result):raise ValueError('Invalid lifted probe model')
    return result


def reference(h,routes,new_records,r,out,tmp):
    path=tmp/'reference';solver=AccountedResidualSolver(path);started=time.perf_counter();rows=[];originals=[]
    for item in new_records:
        kind,identity=item['kind'],item['id']
        record=(routes.windows if kind=='probe_window' else routes.continuations)[identity]
        if record['edge'] is None:continue
        source=h._load(record['source'])['cnf'];target=checked_target(h,routes,kind,record)
        a=solver.solve(source);b=solver.solve(target);assert a['answer']==b['answer']
        if b['answer']:lift_forced(source,record,b['model'])
        rows.append(dict(kind=kind,id_sha256=sha_key(identity),source=a,target=b))
    for case in r['gains']:
        answer=solver.solve(r['cases'][case]['source'])
        if answer['answer']:assert holds(r['cases'][case]['source'],answer['model'])
        originals.append(dict(case=case,result=answer))
    solver.close();elapsed=time.perf_counter()-started;before=sha(path);started=time.perf_counter();solver=ResidualSolver(path)
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
    nodes=len(solver.checked);assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(path)==before
    cold=time.perf_counter()-started;archive=out/'reference.sqlite3.gz';compressed(path,archive)
    return dict(rows=rows,originals=originals,seconds=elapsed,cold_seconds=cold,verified_nodes=nodes,path=str(archive),
        sha256=sha(archive),database_sha256=before,database_bytes=path.stat().st_size,compressed_bytes=archive.stat().st_size)


def run(out,parent_path):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';history=tmp/'history';started=time.perf_counter()
        parent,rewrites,learning=restore_checkpoint(parent_path,seed,tmp);restore_seconds=time.perf_counter()-started
        r=dict(format=FORMAT,parent=dict(path=str(parent_path),sha256=sha(parent_path)),
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/cnf_target_probe.py','experiments/compare_cnf_target_probe.py',
                'solver/test_cnf_target_probe.py')},options=parent['options'],cases=parent['cases'],policy=POLICY,
            seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,restore_seconds=restore_seconds,
            limitations=['Same reused 83 development originals. Only selected frontiers below the three retained learned targets are explored.',
                'Eight advances, four distinct sources and 32 state admissions per target; reused advances and exhaustion consume steps.',
                'Probe pool capped at 64 ranked variables; clear probing is inconclusive, and all preprocessing/checking is charged.',
                'Reference answers are separate from structural coverage. Peak RAM, competitive end-to-end timing and unrestricted guarantees remain open.'])
        shutil.copyfile(seed,history);h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
        started=time.perf_counter();roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        routes=LearnedTraceRoutes(h,rewrites,learning);baseline,_=compose(h,roots,routes,Counter());assert baseline==parent['final_closed']
        selected=targets(h,learning,Counter());before_remaining=remaining(h,selected,routes,Counter())
        r['preparation_seconds']=time.perf_counter()-started;r['baseline_closed']=baseline
        previous_windows=set(routes.windows);previous_continuations=set(routes.continuations);passes=[];r['acquisitions']=[]
        for row in selected:
            h.counts=Counter();h.prepared.counts=Counter();counts=Counter();started=time.perf_counter()
            result=search(h,row['target'],routes,counts,**POLICY)
            elapsed=time.perf_counter()-started
            passes.append(dict(target=row['target'],result=result))
            r['acquisitions'].append(dict(target_sha256=sha_key(row['target']),seconds=elapsed,counts=dict(counts),
                inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),admission_counts=dict(h.admission_counts),
                admitted_state_sha256=sorted(map(sha_key,h.admitted)),stop=result['stop']))
            print(json.dumps(dict(rank=row['rank'],steps=len(result['visits']),stop=result['stop'],admitted=len(h.admitted),seconds=elapsed)),flush=True)
        started=time.perf_counter();final,plan=compose(h,roots,routes,Counter());verify_plan(h,plan,plan['roots'],routes,Counter())
        assert all(b or not a for a,b in zip(baseline,final));r['final_closed']=final
        r['gains']=[i for i,(a,b) in enumerate(zip(baseline,final)) if b and not a]
        r['without_growth_closed'],without=compose(h,roots,WithoutGrowth(routes),Counter());verify_plan(h,without,without['roots'],WithoutGrowth(routes),Counter())
        after_remaining=remaining(h,selected,routes,Counter());r['composition_diagnosis_seconds']=time.perf_counter()-started
        new_records=[dict(kind=kind,id=k) for kind,records,previous in (
            ('probe_window',routes.windows,previous_windows),('probe_continuation',routes.continuations,previous_continuations)) for k in sorted(set(records)-previous)]
        r['new_probe_summary']=dict(Counter((routes.windows if x['kind']=='probe_window' else routes.continuations)[x['id']]['probing']['status'] for x in new_records))
        r['diagnostics']=archive_json(out/'diagnostics.json.gz',dict(selected=selected,before=before_remaining,passes=passes,after=after_remaining,new_records=new_records))
        r['certificate']=archive_json(out/'coverage.json.gz',plan)
        h.close();r['expanded_database_bytes']=history.stat().st_size;delta=tmp/'delta';started=time.perf_counter()
        r['preserved_rows'],r['delta_rows']=export_delta(seed,history,delta);compressed(delta,out/'proof-delta.sqlite3.gz')
        r['delta']=dict(path=str(out/'proof-delta.sqlite3.gz'),sha256=sha(out/'proof-delta.sqlite3.gz'),database_sha256=sha(delta),
            database_bytes=delta.stat().st_size,compressed_bytes=(out/'proof-delta.sqlite3.gz').stat().st_size,export_seconds=time.perf_counter()-started)
        r['logical_table_digests']=digests(history);rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,delta)
        assert digests(rebuilt)==r['logical_table_digests'];before=sha(rebuilt);apply_delta(rebuilt,delta);assert sha(rebuilt)==before
        print('cold inventory audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        print('cold routes and reference proofs',flush=True);started=time.perf_counter();h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0)
        routes=LearnedTraceRoutes(h,rewrites,learning);verify_plan(h,read_archive(r['certificate']),plan['roots'],routes,Counter())
        assert compose(h,roots,routes,Counter())[0]==final and not h.admitted
        assert remaining(h,selected,routes,Counter())==after_remaining
        r['cold_routes']=dict(seconds=time.perf_counter()-started,counts=dict(routes.counts))
        r['reference']=reference(h,routes,new_records,r,out,tmp);h.close();assert sha(rebuilt)==before
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],probes=r['new_probe_summary'],added=r['delta_rows'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path,default=BASE)
    a=p.parse_args();run(a.output,a.parent)
