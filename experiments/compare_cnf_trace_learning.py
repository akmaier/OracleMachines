#!/usr/bin/env python3
"""Matched retained-implication graph and bounded augmented-CNF experiment."""
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.compare_cnf_trace_reuse import restore_checkpoint as restore_parent,read_archive,archive_json
from experiments.compare_cnf_probe_continuation import (sha,sha_key,digests,export_delta,apply_delta,
    compressed,unpack,audit,WithoutGrowth)
from experiments.cnf_trace_reuse import source_attempts
from experiments.cnf_trace_learning import (implication_graph,discover_graph,check_graph,acquire_learning,
    verify_learning,checked_augmentation,lift_learning,LearnedTraceRoutes,PROBE_LIMIT)
from experiments.cnf_coupled_pivots import BudgetedInventory,AdmissionExhausted
from experiments.cnf_failed_literal import probe_choices
from experiments.cnf_probe_equivalence import discover_equivalence_probes,check_equivalence_probes
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_residual_dag import ResidualSolver,holds
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_pattern_inventory import encode

PARENT=Path('experiments/results/cnf-trace-reuse/report.json')


def restore_checkpoint(report_path,path,tmp):
    r=json.loads(Path(report_path).read_text())
    if sha(r['parent']['path'])!=r['parent']['sha256']:raise ValueError('Changed parent')
    for p,digest in r['fingerprints'].items():
        if sha(p)!=digest:raise ValueError('Changed implementation')
    _,rewrites=restore_parent(Path(r['parent']['path']),path,tmp)
    if digests(path)!=r['seed_table_digests']:raise ValueError('Incorrect parent history')
    d=r['delta']
    if sha(d['path'])!=d['sha256']:raise ValueError('Changed learning delta')
    unpack(d['path'],tmp/'learning-delta',d['database_sha256']);apply_delta(path,tmp/'learning-delta')
    if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect learning reconstruction')
    return r,rewrites,read_archive(r['learning'])


def reference(h,records,r,out,tmp):
    path=tmp/'reference';solver=AccountedResidualSolver(path);started=time.perf_counter();rows=[];originals=[]
    for record in records:
        if record['edge'] is None:continue
        source=h._load(record['source'])['cnf'];target,_=verify_learning(h,record,Counter())
        a=solver.solve(source);b=solver.solve(target);assert a['answer']==b['answer']
        child=h._load(record['edge']['key'])
        if child is not None:
            c=solver.solve(child['cnf']);assert c['answer']==a['answer']
            if c['answer']:assert holds(source,lift_learning(h,record,c['model'],Counter()))
        rows.append(dict(source_sha256=sha_key(record['source']),source=a,target=b))
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


def run(out):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';history=tmp/'history';started=time.perf_counter()
        parent,rewrites=restore_parent(PARENT,seed,tmp);restore_seconds=time.perf_counter()-started
        r=dict(parent=dict(path=str(PARENT),sha256=sha(PARENT)),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/cnf_trace_learning.py','experiments/compare_cnf_trace_learning.py',
                'solver/test_cnf_trace_learning.py','solver/fixtures/trace-learning.json')},options=parent['options'],cases=parent['cases'],
            seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,restore_seconds=restore_seconds,
            policy='Same 41 retained sources as the parent scan, including its existing equivalence. All saved original-source implications in the graph; at most 16 learned clauses, four ranked probe variables, 32 target states per source.',
            limitations=['Reused development frontier, not an independent holdout or coverage of every new alternative leaf.',
                'Graph conclusions describe only the binary theory; every nonbinary clause remains in augmented-CNF lookahead.',
                'Learning selection is capped and order-dependent; no fixed-point saturation or unrestricted complexity guarantee.',
                'Matched controls fix the augmented variable order on the original source; their new computations and certificates are retained.',
                'Independent reference solves are not structural coverage. Peak RAM, competitive end-to-end timing and Lean verification remain open.'])
        shutil.copyfile(seed,history);h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
        input_rows=read_archive(parent['opportunities']);rows=[];records=[];counts=Counter();controls=Counter()
        r['graph_scan_seconds']=r['learning_seconds']=r['control_seconds']=0.0
        for index,row in enumerate(input_rows):
            started=time.perf_counter();source=row['source'];node=h._load(source)
            attempts,refs=source_attempts(h,source,counts);graph=implication_graph(node['cnf'],attempts,counts)
            certificate=discover_graph(graph,counts);check_graph(graph,certificate,counts)
            r['graph_scan_seconds']+=time.perf_counter()-started;started=time.perf_counter()
            record=acquire_learning(h,source,attempts,refs,counts)
            r['learning_seconds']+=time.perf_counter()-started
            result=dict(input_row=index,source_sha256=sha_key(source),cases=row['cases'],graph=certificate,learning_index=None,control=None)
            if record is not None:
                result['learning_index']=len(records);records.append(record)
                started=time.perf_counter();_,expanded=checked_augmentation(h,record,controls)
                choices=probe_choices(expanded,PROBE_LIMIT,controls)
                control=discover_equivalence_probes(node['cnf'],PROBE_LIMIT,controls,_choices=choices)
                check_equivalence_probes(node['cnf'],control,PROBE_LIMIT,controls,_choices=choices)
                r['control_seconds']+=time.perf_counter()-started
                result['control']=dict(choices=choices,probing=control)
            rows.append(result)
        r['discovery_counts']=dict(counts);r['control_counts']=dict(controls)
        r['discovery_inventory_counts']=dict(h.counts);r['discovery_prepared_counts']=dict(h.prepared.counts)
        r['diagnostics']=archive_json(out/'diagnostics.json.gz',rows)
        r['learning']=archive_json(out/'learning.json.gz',records) # Retain clear trials and pending rewrites before recognition.
        r['graph_summary']=dict(sources=len(rows),forced_sources=sum(bool(x['graph']['conclusions']['forced_literals']) for x in rows),
            equivalence_sources=sum(bool(x['graph']['conclusions']['equivalences']) for x in rows),
            contradictory_sources=sum(bool(x['graph']['conclusions']['contradictory_variables']) for x in rows))
        r['learning_kinds']=dict(Counter(x['probing']['status'] for x in records))
        r['control_kinds']=dict(Counter(x['control']['probing']['status'] for x in rows if x['control'] is not None))
        started=time.perf_counter();roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        routes=LearnedTraceRoutes(h,rewrites);baseline,_=compose(h,roots,routes,Counter());assert baseline==parent['final_closed']
        r['preparation_seconds']=time.perf_counter()-started;r['baseline_closed']=baseline;r['acquisitions']=[]
        for record in records:
            if record['edge'] is None:routes.add_learning(h,record);continue
            h.set_admission_budget(32);h.counts=Counter();counts=Counter();started=time.perf_counter()
            target,_=verify_learning(h,record,counts);node=h._load(record['source']);pending=False
            try:assert h._edge(target,node['depth'])==record['edge']
            except AdmissionExhausted:pending=True
            routes.add_learning(h,record)
            r['acquisitions'].append(dict(source_sha256=sha_key(record['source']),seconds=time.perf_counter()-started,pending=pending,
                counts=dict(counts),inventory_counts=dict(h.counts),admission_counts=dict(h.admission_counts),
                admitted_state_sha256=sorted(map(sha_key,h.admitted))))
        final,plan=compose(h,roots,routes,Counter());verify_plan(h,plan,plan['roots'],routes,Counter())
        assert all(b or not a for a,b in zip(baseline,final));r['final_closed']=final
        r['gains']=[i for i,(a,b) in enumerate(zip(baseline,final)) if b and not a]
        r['without_growth_closed'],without=compose(h,roots,WithoutGrowth(routes),Counter());verify_plan(h,without,without['roots'],WithoutGrowth(routes),Counter())
        r['certificate']=archive_json(out/'coverage.json.gz',plan)
        h.close();r['expanded_database_bytes']=history.stat().st_size;delta=tmp/'delta';started=time.perf_counter()
        r['preserved_rows'],r['delta_rows']=export_delta(seed,history,delta);compressed(delta,out/'proof-delta.sqlite3.gz')
        r['delta']=dict(path=str(out/'proof-delta.sqlite3.gz'),sha256=sha(out/'proof-delta.sqlite3.gz'),database_sha256=sha(delta),
            database_bytes=delta.stat().st_size,compressed_bytes=(out/'proof-delta.sqlite3.gz').stat().st_size,export_seconds=time.perf_counter()-started)
        r['logical_table_digests']=digests(history);rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,delta)
        assert digests(rebuilt)==r['logical_table_digests'];before=sha(rebuilt);apply_delta(rebuilt,delta);assert sha(rebuilt)==before
        print('cold inventory audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        started=time.perf_counter();h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0)
        routes=LearnedTraceRoutes(h,rewrites,read_archive(r['learning']));verify_plan(h,read_archive(r['certificate']),plan['roots'],routes,Counter())
        assert compose(h,roots,routes,Counter())[0]==final and not h.admitted
        r['cold_routes']=dict(seconds=time.perf_counter()-started,counts=dict(routes.counts))
        r['reference']=reference(h,records,r,out,tmp);h.close();assert sha(rebuilt)==before
    r['pipeline_seconds']=time.perf_counter()-pipeline
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],graph=r['graph_summary'],learning=r['learning_kinds'],controls=r['control_kinds'],added=r['delta_rows'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
