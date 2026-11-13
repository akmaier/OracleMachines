#!/usr/bin/env python3
"""Learn from the two exhausted target frontiers and continue exact augmented probes."""
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_target_probe import restore_checkpoint as restore_parent
from experiments.compare_cnf_trace_reuse import read_archive,archive_json
from experiments.compare_cnf_probe_continuation import (sha,sha_key,digests,export_delta,apply_delta,
    compressed,unpack,audit,WithoutGrowth)
from experiments.cnf_trace_reuse import source_attempts,pair_witness
from experiments.cnf_trace_learning import (implication_graph,discover_graph,check_graph,acquire_learning,
    checked_augmentation,PROBE_LIMIT)
from experiments.cnf_learning_continuation import LearningBlocks,ContinuedLearningRoutes,base_id
from experiments.cnf_probe_exhaustion import certify_exhaustion
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_probe_equivalence import discover_equivalence_probes,check_equivalence_probes
from experiments.cnf_coupled_pivots import BudgetedInventory,AdmissionExhausted
from experiments.cnf_target_probe import remaining
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_pattern_inventory import encode

PARENT=Path('experiments/results/cnf-target-probe/report.json')
STEPS=8


def restore_checkpoint(report_path,path,tmp):
    r=json.loads(Path(report_path).read_text())
    if sha(r['parent']['path'])!=r['parent']['sha256']:raise ValueError('Changed frontier-learning parent')
    for p,digest in r['fingerprints'].items():
        if sha(p)!=digest:raise ValueError('Changed frontier-learning implementation')
    _,rewrites,learning=restore_parent(Path(r['parent']['path']),path,tmp)
    if digests(path)!=r['seed_table_digests']:raise ValueError('Incorrect frontier-learning seed')
    d=r['delta'];delta=tmp/'frontier-learning-delta'
    if sha(d['path'])!=d['sha256']:raise ValueError('Changed frontier-learning delta')
    unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
    if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect frontier-learning reconstruction')
    return r,rewrites,learning+read_archive(r['learning_bases']),read_archive(r['continuations'])


def reference(h,routes,r,out,tmp):
    path=tmp/'reference';solver=AccountedResidualSolver(path);started=time.perf_counter();rows=[];originals=[]
    blocks=routes.learned_blocks
    for identity,record in blocks.records.items():
        if record['edge'] is None:continue
        base=blocks.bases[record['base_sha256']];source=h._load(base['source'])['cnf']
        target,_=blocks.verify(h,record,Counter());a=solver.solve(source);b=solver.solve(target);assert a['answer']==b['answer']
        child=h._load(record['edge']['key'])
        if child is not None:
            c=solver.solve(child['cnf']);assert c['answer']==a['answer']
            if c['answer']:assert holds(source,blocks.lift(h,record,c['model']))
        rows.append(dict(id=identity,source=a,target=b))
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


def control(cnf,expanded,offset,counts):
    choices=probe_choices(expanded,64,counts)[offset:offset+PROBE_LIMIT]
    result=discover_equivalence_probes(cnf,PROBE_LIMIT,counts,_choices=choices)
    check_equivalence_probes(cnf,result,PROBE_LIMIT,counts,_choices=choices)
    return dict(offset=offset,choices=choices,probing=result)


def run(out):
    pipeline=time.perf_counter();out.mkdir(exist_ok=True)
    if (out/'report.json').exists():raise ValueError('Output already has a checkpoint')
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';history=tmp/'history';started=time.perf_counter()
        parent,rewrites,old_learning=restore_parent(PARENT,seed,tmp);restore_seconds=time.perf_counter()-started
        inputs=sorted([dict(source=leaf['source'],parent_target=row['target'],variables=leaf['variables'])
            for row in read_archive(parent['diagnostics'])['after'] for leaf in row['leaves']],key=lambda row:(row['variables'],row['source']))
        r=dict(parent=dict(path=str(PARENT),sha256=sha(PARENT)),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/cnf_learning_continuation.py','experiments/compare_cnf_frontier_learning.py',
                'solver/test_cnf_learning_continuation.py','solver/fixtures/learning-continuation.json')},options=parent['options'],cases=parent['cases'],
            seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,restore_seconds=restore_seconds,
            policy=dict(learned_clauses=16,base_probe_variables=4,later_block_variables=4,later_steps=STEPS,state_admissions_per_source=32),
            limitations=['Two reused development residuals, chosen after earlier evidence and a retained pilot; not independent holdouts.',
                'Original-source pair/graph scans and one capped batch precede later augmented probes; all original clauses remain.',
                'Same-variable controls isolate propagation, not end-to-end performance against equal-cost conditioning or a competitive solver.',
                'Probe pool capped at 64 variables. State admissions do not bound state bytes or reference work. Peak RAM and unrestricted bounds remain open.'])
        shutil.copyfile(seed,history);h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0);started=time.perf_counter()
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']];routes=ContinuedLearningRoutes(h,rewrites,old_learning)
        baseline,_=compose(h,roots,routes,Counter());assert baseline==parent['final_closed']
        r['preparation_seconds']=time.perf_counter()-started;r['baseline_closed']=baseline;rows=[];bases=[]
        counts=Counter();controls=Counter();r['source_scan_seconds']=r['learning_seconds']=r['continuation_seconds']=r['control_seconds']=0.0
        for item in inputs:
            started=time.perf_counter();source=item['source'];node=h._load(source);attempts,refs=source_attempts(h,source,counts)
            binary,outside=certify_exhaustion(node['cnf'],attempts,counts)
            pairs=[dict(index=i,result=pair_witness(attempts[i:i+2],counts)) for i in range(0,len(attempts),2)]
            graph=implication_graph(node['cnf'],attempts,counts);certificate=discover_graph(graph,counts);check_graph(graph,certificate,counts)
            r['source_scan_seconds']+=time.perf_counter()-started;started=time.perf_counter()
            base=acquire_learning(h,source,attempts,refs,counts);r['learning_seconds']+=time.perf_counter()-started
            row=dict(**item,pairs=pairs,graph=certificate,exhaustion=dict(binary=binary,outside=outside,attempts=len(attempts)),base_sha256=None,controls=[])
            if base is not None:
                row['base_sha256']=base_id(base);bases.append(base);_,expanded=checked_augmentation(h,base,controls)
                started=time.perf_counter();row['controls'].append(control(node['cnf'],expanded,0,controls));r['control_seconds']+=time.perf_counter()-started
            rows.append(row)
        r['learning_bases']=archive_json(out/'learning-bases.json.gz',bases)
        # This study follows clear bases only; successful base records must be acquired by a different policy.
        assert all(base['probing']['status']=='clear' for base in bases)
        blocks=LearningBlocks(h,old_learning+bases);routes.learned_blocks=blocks
        for base in bases:routes.add_learning(h,base)
        r['acquisitions']=[];selected=[];r['continuation_persistence_seconds']=0.0;r['continuation_diagnosis_seconds']=0.0
        for row in rows:
            if row['base_sha256'] is None:continue
            identity=row['base_sha256'];source=row['source'];h.set_admission_budget(32);h.counts=Counter();h.prepared.counts=Counter()
            local=Counter();visits=[];pending=False;target_key=source;recognition_seconds=0.0
            for _ in range(STEPS):
                started=time.perf_counter();record,target=blocks.advance(h,identity,local);r['continuation_seconds']+=time.perf_counter()-started
                if record is None:visits.append(None);break
                visits.append(record['offset']);node,expanded,_=blocks.context(h,identity,local)
                started=time.perf_counter();row['controls'].append(control(node['cnf'],expanded,record['offset'],controls));r['control_seconds']+=time.perf_counter()-started
                # Persist the complete prefix before attempting target recognition.
                started=time.perf_counter();r['continuations']=archive_json(out/'continuations.json.gz',list(blocks.records.values()))
                r['continuation_persistence_seconds']+=time.perf_counter()-started
                if record['edge'] is None:continue
                started=time.perf_counter()
                try:
                    assert h._edge(target,node['depth'])==record['edge'];target_key=record['edge']['key']
                except AdmissionExhausted:pending=True
                recognition_seconds+=time.perf_counter()-started;break
            routes.refresh_learning(h);row['visits']=visits;row['augmented_exhaustion']=None
            if visits and visits[-1] is None:
                started=time.perf_counter();_,expanded,_=blocks.context(h,identity,local)
                attempts=list(blocks.bases[identity]['probing']['attempts'])
                for rec in sorted((rec for rec in blocks.records.values() if rec['base_sha256']==identity),key=lambda x:x['offset']):
                    attempts.extend(rec['probing']['attempts'])
                binary,outside=certify_exhaustion(expanded,attempts,local)
                row['augmented_exhaustion']=dict(binary=binary,outside=outside,attempts=len(attempts))
                r['continuation_diagnosis_seconds']+=time.perf_counter()-started
            selected.append(dict(source=source,target=target_key))
            r['acquisitions'].append(dict(base_sha256=identity,seconds=recognition_seconds,pending=pending,counts=dict(local),
                inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),admission_counts=dict(h.admission_counts),
                admitted_state_sha256=sorted(map(sha_key,h.admitted))))
            print(json.dumps(dict(variables=row['variables'],visits=visits,pending=pending,admitted=len(h.admitted))),flush=True)
        r['continuations']=archive_json(out/'continuations.json.gz',list(blocks.records.values()))
        r['discovery_counts']=dict(counts);r['control_counts']=dict(controls)
        started=time.perf_counter();final,plan=compose(h,roots,routes,Counter());verify_plan(h,plan,plan['roots'],routes,Counter())
        assert all(b or not a for a,b in zip(baseline,final));r['final_closed']=final;r['gains']=[i for i,(a,b) in enumerate(zip(baseline,final)) if b and not a]
        r['without_growth_closed'],without=compose(h,roots,WithoutGrowth(routes),Counter());verify_plan(h,without,without['roots'],WithoutGrowth(routes),Counter())
        after=remaining(h,selected,routes,Counter());r['composition_seconds']=time.perf_counter()-started
        r['diagnostics']=archive_json(out/'diagnostics.json.gz',dict(rows=rows,selected=selected,after=after))
        r['certificate']=archive_json(out/'coverage.json.gz',plan);h.close();r['expanded_database_bytes']=history.stat().st_size
        delta=tmp/'delta';started=time.perf_counter();r['preserved_rows'],r['delta_rows']=export_delta(seed,history,delta);compressed(delta,out/'proof-delta.sqlite3.gz')
        r['delta']=dict(path=str(out/'proof-delta.sqlite3.gz'),sha256=sha(out/'proof-delta.sqlite3.gz'),database_sha256=sha(delta),
            database_bytes=delta.stat().st_size,compressed_bytes=(out/'proof-delta.sqlite3.gz').stat().st_size,export_seconds=time.perf_counter()-started)
        r['logical_table_digests']=digests(history);rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,delta)
        assert digests(rebuilt)==r['logical_table_digests'];before=sha(rebuilt);apply_delta(rebuilt,delta);assert sha(rebuilt)==before
        print('cold inventory audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        print('cold routes and reference proofs',flush=True);started=time.perf_counter();h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0)
        routes=ContinuedLearningRoutes(h,rewrites,old_learning+bases,read_archive(r['continuations']))
        verify_plan(h,read_archive(r['certificate']),plan['roots'],routes,Counter());assert compose(h,roots,routes,Counter())[0]==final
        assert remaining(h,selected,routes,Counter())==after and not h.admitted
        r['cold_routes']=dict(seconds=time.perf_counter()-started,counts=dict(routes.counts),block_counts=dict(routes.learned_blocks.counts))
        r['reference']=reference(h,routes,r,out,tmp);h.close();assert sha(rebuilt)==before
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],added=r['delta_rows'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
