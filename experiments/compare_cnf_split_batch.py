#!/usr/bin/env python3
"""Isolated saved-cofactor and ordinary-probe arms, retaining their exact union."""
from collections import Counter
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_trace_split import restore_checkpoint as restore_parent,reference as split_reference
from experiments.compare_cnf_trace_reuse import read_archive,archive_json
from experiments.compare_cnf_probe_continuation import sha,sha_key,digests,export_delta,apply_delta,compressed,unpack,audit,WithoutGrowth
from experiments.compare_cnf_target_probe import checked_target,lift_forced
from experiments.cnf_learning_continuation import ContinuedLearningRoutes
from experiments.cnf_trace_split import candidates,attach
from experiments.cnf_split_batch import leaves,run as split_run,children
from experiments.cnf_target_probe import search
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_pattern_inventory import encode
from experiments.continue_cnf_learning import target_state
from experiments.cnf_learning_batch import selection

PARENT=Path('experiments/results/cnf-trace-split/report.json')
FORMAT='saved-cofactor-batch-v1'
POLICY=dict(source_limit=4,candidate_pairs=8,pair_states=32,total_states=128,probe_steps=8,probe_sources=4)


def routes_for(h,evidence):
    rewrites,learning,continuations,splits=evidence
    routes=ContinuedLearningRoutes(h,rewrites,learning,continuations)
    for record in splits:attach(h,routes,record,Counter())
    return routes


def restore_checkpoint(report_path,path,tmp):
    r=json.loads(Path(report_path).read_text())
    if r['format']!=FORMAT or sha(r['parent']['path'])!=r['parent']['sha256']:raise ValueError('Changed batch parent')
    for p,digest in r['fingerprints'].items():
        if sha(p)!=digest:raise ValueError('Changed batch implementation')
    parent,*evidence=restore_parent(Path(r['parent']['path']),path,tmp)
    if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:raise ValueError('Incorrect batch seed')
    d=r['delta'];delta=tmp/'split-batch-delta'
    if sha(d['path'])!=d['sha256']:raise ValueError('Changed batch delta')
    unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
    if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect batch reconstruction')
    evidence[-1]=evidence[-1]+read_archive(r['splits'])
    return r,*evidence


def save_delta(seed,path,delta,archive):
    started=time.perf_counter();preserved,added=export_delta(seed,path,delta);compressed(delta,archive)
    return dict(path=str(archive),sha256=sha(archive),database_sha256=sha(delta),database_bytes=delta.stat().st_size,
        compressed_bytes=archive.stat().st_size,seconds=time.perf_counter()-started,preserved_rows=preserved,added_rows=added)


def closure(h,roots,routes,baseline):
    final,plan=compose(h,roots,routes,Counter());verify_plan(h,plan,plan['roots'],routes,Counter())
    assert all(b or not a for a,b in zip(baseline,final,strict=True))
    without,wplan=compose(h,roots,WithoutGrowth(routes),Counter());verify_plan(h,wplan,wplan['roots'],WithoutGrowth(routes),Counter())
    return dict(final_closed=final,gains=[i for i,(a,b) in enumerate(zip(baseline,final)) if b and not a],without_growth_closed=without),plan


def new_probes(delta):
    db=sqlite3.connect(delta);result=[]
    for table,kind in [('cnf_probe_windows_v1','probe_window'),('cnf_probe_continuations_v1','probe_continuation')]:
        result.extend(dict(kind=kind,id=k,record=json.loads(p)) for k,p in db.execute(f'SELECT id,payload FROM {table} ORDER BY id'))
    db.close();return result


def run(out):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';started=time.perf_counter();parent,*evidence=restore_parent(PARENT,seed,tmp)
        r=dict(format=FORMAT,parent=dict(path=str(PARENT),sha256=sha(PARENT)),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/cnf_split_batch.py','experiments/compare_cnf_split_batch.py','solver/test_cnf_split_batch.py')},
            options=parent['options'],cases=parent['cases'],policy=POLICY,baseline_closed=parent['final_closed'],seed_table_digests=digests(seed),
            seed_database_bytes=seed.stat().st_size,restore_seconds=time.perf_counter()-started,arms={},
            limitations=['Four adaptively selected leaves in 83 reused development cases; not an independent holdout or general coverage estimate.',
                'Same per-source state allowance, not equal CPU work: split and ordinary probe policies perform different recognition/checking operations.',
                'Each arm starts with fresh verifier caches from the same parent. Cold preparation, ranking and persistence are charged separately.',
                'A state cap does not bound bytes, CPU or reference solving; peak RAM is unmeasured. Repeated conditioning can be exponential.',
                'Both cofactors are required for structural closure. Open child diagnostics follow selected old plans, not every alternative route.'])
        # Freeze all source identities and candidate rankings before either arm.
        started=time.perf_counter();h=BudgetedInventory(seed,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']];assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']
        selected=leaves(h,routes)[:POLICY['source_limit']];r['preparation_seconds']=time.perf_counter()-started
        started=time.perf_counter();counts=Counter();ranked=[dict(source=row['source'],candidates=candidates(h,row['source'],routes,counts,candidate_limit=POLICY['candidate_pairs'])) for row in selected]
        records=[row['candidates'][0]['record'] for row in ranked if row['candidates']]
        r['ranking_seconds']=time.perf_counter()-started;r['ranking_counts']=dict(counts);h.close()
        r['selection']=archive_json(out/'selection.json.gz',dict(selected=selected,ranked=ranked));r['splits']=archive_json(out/'splits.json.gz',records)
        print(json.dumps(dict(selected=[row['variables'] for row in selected],pairs=len(records))),flush=True)
        for arm in ('split','probe'):
            path=tmp/arm;started=time.perf_counter();shutil.copyfile(seed,path);h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
            routes=routes_for(h,evidence);assert compose(h,roots,routes,Counter())[0]==r['baseline_closed'];prep=time.perf_counter()-started
            h.counts=Counter();h.prepared.counts=Counter();counts=Counter();started=time.perf_counter();passes=[];admitted=set();charged=0
            if arm=='split':
                passes=split_run(h,routes,records,state_limit=POLICY['total_states'],pair_limit=POLICY['pair_states'])
                admitted=set(h.admitted);charged=len(admitted)
            else:
                for row in selected:
                    result=search(h,row['source'],routes,counts,step_limit=POLICY['probe_steps'],source_limit=POLICY['probe_sources'],state_limit=POLICY['pair_states'])
                    passes.append(dict(source=row['source'],result=result,admitted=sorted(h.admitted),admission_counts=dict(h.admission_counts)))
                    routes.refresh_learning(h)
                    admitted.update(h.admitted);charged+=len(h.admitted)
            elapsed=time.perf_counter()-started;assert charged<=POLICY['total_states']
            a=dict(preparation_seconds=prep,acquisition_seconds=elapsed,counts=dict(counts),inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
                admitted_state_sha256=sorted(map(sha_key,admitted)),charged_admissions=charged,split_admission_counts=dict(h.admission_counts) if arm=='split' else {})
            started=time.perf_counter();summary,plan=closure(h,roots,routes,r['baseline_closed']);a.update(summary)
            diagnostics=dict(passes=passes,targets=target_state(h,routes),children=children(h,routes,records) if arm=='split' else [])
            a['composition_diagnosis_seconds']=time.perf_counter()-started;a['diagnostics']=archive_json(out/f'{arm}-diagnostics.json.gz',diagnostics)
            a['certificate']=archive_json(out/f'{arm}-coverage.json.gz',plan);h.close();a['database_bytes']=path.stat().st_size
            a['delta']=save_delta(seed,path,tmp/f'{arm}-delta',out/f'{arm}-delta.sqlite3.gz');a['logical_table_digests']=digests(path);r['arms'][arm]=a
            print(json.dumps(dict(arm=arm,closed=sum(a['final_closed']),gains=a['gains'],admitted=charged,seconds=elapsed)),flush=True)
        # Keep both arms. Conflicting immutable records fail in apply_delta.
        history=tmp/'union';started=time.perf_counter();shutil.copyfile(seed,history)
        for arm in ('split','probe'):apply_delta(history,tmp/f'{arm}-delta')
        r['merge_seconds']=time.perf_counter()-started;union_evidence=[*evidence[:-1],evidence[-1]+records]
        started=time.perf_counter();h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0);routes=routes_for(h,union_evidence)
        summary,plan=closure(h,roots,routes,r['baseline_closed']);r.update(summary)
        for a in r['arms'].values():assert all(b or not a for a,b in zip(a['final_closed'],r['final_closed'],strict=True))
        r['union_composition_seconds']=time.perf_counter()-started
        r['diagnostics']=archive_json(out/'diagnostics.json.gz',dict(children=children(h,routes,records),targets=target_state(h,routes),learning=selection(h,routes,Counter())))
        r['certificate']=archive_json(out/'coverage.json.gz',plan)
        # Independent SAT answers supplement, rather than define, structural closure.
        ep=parent['reference'];assert sha(ep['path'])==ep['sha256'];unpack(ep['path'],tmp/'reference',ep['database_sha256']);shutil.copyfile(tmp/'reference',tmp/'reference-seed')
        started=time.perf_counter();solver=AccountedResidualSolver(tmp/'reference');probes=[]
        for item in new_probes(tmp/'probe-delta'):
            record=item['record'];target=checked_target(h,routes,item['kind'],record)
            if record['edge'] is None:continue
            source=h._load(record['source'])['cnf'];a=solver.solve(source);b=solver.solve(target);assert a['answer']==b['answer']
            if b['answer']:lift_forced(source,record,b['model'])
            probes.append(dict(kind=item['kind'],id_sha256=sha_key(item['id']),source=a,target=b))
        probe_counts=dict(solver.counts);solver.close();probe_seconds=time.perf_counter()-started
        r['reference']=split_reference(h,records,r,out,tmp);r['reference'].update(probes=probes,probe_seconds=probe_seconds,probe_counts=probe_counts)
        h.close();r['expanded_database_bytes']=history.stat().st_size
        r['delta']=save_delta(seed,history,tmp/'union-delta',out/'proof-delta.sqlite3.gz');r['logical_table_digests']=digests(history)
        rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,tmp/'union-delta');assert digests(rebuilt)==r['logical_table_digests']
        before=sha(rebuilt);apply_delta(rebuilt,tmp/'union-delta');assert sha(rebuilt)==before
        print('full cold inventory audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
