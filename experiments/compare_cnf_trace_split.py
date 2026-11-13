#!/usr/bin/env python3
"""Condition the smallest retained target using already checked unit traces."""
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_learning import restore_checkpoint as restore_parent,target_state,preserved_reference
from experiments.compare_cnf_trace_reuse import read_archive,archive_json
from experiments.compare_cnf_probe_continuation import sha,sha_key,digests,export_delta,apply_delta,compressed,unpack,audit,WithoutGrowth
from experiments.cnf_learning_continuation import ContinuedLearningRoutes
from experiments.cnf_trace_split import candidates,verify,attach,lift,record_key
from experiments.cnf_trace_reuse import source_attempts,read_attempt,check_pair
from experiments.cnf_probe_exhaustion import certify_exhaustion
from experiments.cnf_target_probe import search
from experiments.cnf_coupled_pivots import BudgetedInventory,AdmissionExhausted
from experiments.cnf_route_composition import compose,verify_plan
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_residual_dag import ResidualSolver,holds,restrict
from experiments.cnf_simplification import discover_simplification,check_simplification
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_pattern_inventory import encode

PARENT=Path('experiments/results/cnf-learning-batch/report.json')
FORMAT='saved-trace-split-v1'
POLICY=dict(ordinary_steps=8,ordinary_sources=1,ordinary_states=32,candidate_pairs=8,split_states=32,selected_sources=1)


def restore_checkpoint(report_path,path,tmp):
    r=json.loads(Path(report_path).read_text())
    if r['format']!=FORMAT or sha(r['parent']['path'])!=r['parent']['sha256']:raise ValueError('Changed split parent')
    for p,digest in r['fingerprints'].items():
        if sha(p)!=digest:raise ValueError('Changed split implementation')
    parent,rewrites,learning,continuations=restore_parent(Path(r['parent']['path']),path,tmp)
    if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:raise ValueError('Incorrect split seed')
    d=r['delta'];delta=tmp/'trace-split-delta'
    if sha(d['path'])!=d['sha256']:raise ValueError('Changed split delta')
    unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
    if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect split reconstruction')
    return r,rewrites,learning,continuations,read_archive(r['splits'])


def select_leaf(h,routes):
    state=target_state(h,routes)
    leaves={leaf['source']:leaf for row in state['remaining'] for leaf in row['leaves'] if not leaf['pending']}
    if not leaves:raise ValueError('No acquired unresolved target leaf')
    return min(leaves.values(),key=lambda leaf:(leaf['variables'],sum(map(len,h._load(leaf['source'])['cnf'])),leaf['source'])),state


def reference(h,records,r,out,tmp):
    path=tmp/'reference';solver=AccountedResidualSolver(path);started=time.perf_counter();rows=[];originals=[]
    for record in records:
        source=h._load(record['source'])['cnf'];targets,_=verify(h,record,Counter());a=solver.solve(source);children=[]
        for value,target,edge in zip((False,True),targets,record['edges'],strict=True):
            answer=solver.solve(target);child=h._load(edge['key'])
            if child is not None:
                result=solver.solve(child['cnf']);assert result['answer']==answer['answer']
                if result['answer']:assert holds(source,lift(h,record,value,result['model']))
            children.append(answer)
        assert a['answer']==any(c['answer'] for c in children)
        rows.append(dict(id=record_key(record),source=a,children=children))
    for case in r['gains']:
        answer=solver.solve(r['cases'][case]['source'])
        if answer['answer']:assert holds(r['cases'][case]['source'],answer['model'])
        originals.append(dict(case=case,result=answer))
    acquisition_counts=dict(solver.counts);solver.close();elapsed=time.perf_counter()-started;before=sha(path)
    started=time.perf_counter();solver=ResidualSolver(path)
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):assert solver._read(key) is not None
    nodes=len(solver.checked);assert not solver.counts.get('expanded_nodes',0);solver.close();assert sha(path)==before
    cold=time.perf_counter()-started;archive=out/'reference.sqlite3.gz';compressed(path,archive)
    return dict(rows=rows,originals=originals,seconds=elapsed,cold_seconds=cold,verified_nodes=nodes,counts=acquisition_counts,
        preserved_nodes=preserved_reference(tmp/'reference-seed',path),path=str(archive),sha256=sha(archive),database_sha256=before,
        database_bytes=path.stat().st_size,compressed_bytes=archive.stat().st_size)


def matched_control(h,record):
    """Compare saved-proof replay with fresh propagation for the same two cofactors.

    Both arms replay unit reasons twice and check canonical child bindings. The
    reference arm reacquires the reasons; this is not a whole-solver benchmark.
    """
    counts=Counter();started=time.perf_counter();verify(h,record,counts)
    result=dict(reuse_seconds=time.perf_counter()-started,reuse_counts=dict(counts))
    source=h._load(record['source'])['cnf'];variable=read_attempt(h,record['source'],record['references'][0],Counter())['variable']
    counts=Counter();started=time.perf_counter();attempts=[]
    for value in (False,True):
        certificate=discover_simplification(restrict(source,{variable:value},counts),counts,pure=False)
        attempts.append(dict(variable=variable,value=value,certificate=certificate));counts['fresh_assumption_traces']+=1
    check_pair(source,attempts,counts)
    for attempt,edge in zip(attempts,record['edges'],strict=True):
        target,_=check_simplification(restrict(source,{variable:attempt['value']},counts),attempt['certificate'],counts,pure=False)
        _,names,key=h._canonical(target,h._load(record['source'])['depth']);assert edge==dict(key=key,names=names)
    result.update(fresh_seconds=time.perf_counter()-started,fresh_counts=dict(counts),attempts=attempts)
    return result


def run(out):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';history=tmp/'history';started=time.perf_counter()
        parent,rewrites,learning,continuations=restore_parent(PARENT,seed,tmp)
        r=dict(format=FORMAT,parent=dict(path=str(PARENT),sha256=sha(PARENT)),
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/cnf_trace_split.py','experiments/compare_cnf_trace_split.py',
                'solver/test_cnf_trace_split.py','solver/fixtures/trace-split.json')},options=parent['options'],cases=parent['cases'],policy=POLICY,
            seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,restore_seconds=time.perf_counter()-started,
            limitations=['One adaptively selected development residual, after the retained pilot; no independent holdout.',
                'Standard conditioning with exact saved unit closures, not a new tractability theorem or a globally minimum-cost split.',
                'Rank at most eight retained pairs by uncovered/missing distinct children, then cofactor support and literal counts.',
                'State counts do not bound bytes, CPU or reference solving. Repeated splitting may grow exponentially; peak RAM is unmeasured.'])
        shutil.copyfile(seed,history);started=time.perf_counter();h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']];routes=ContinuedLearningRoutes(h,rewrites,learning,continuations)
        baseline,_=compose(h,roots,routes,Counter());assert baseline==parent['final_closed'];r['baseline_closed']=baseline
        leaf,before_targets=select_leaf(h,routes);r['preparation_seconds']=time.perf_counter()-started
        counts=Counter();h.counts=Counter();h.prepared.counts=Counter();started=time.perf_counter()
        ordinary=search(h,leaf['source'],routes,counts,step_limit=POLICY['ordinary_steps'],source_limit=POLICY['ordinary_sources'],state_limit=POLICY['ordinary_states'])
        r['ordinary']=dict(seconds=time.perf_counter()-started,counts=dict(counts),inventory_counts=dict(h.counts),
            prepared_counts=dict(h.prepared.counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
        # The retained pilot predicts exhaustion; a changed outcome must be reviewed
        # as a different experiment rather than silently changing the split policy.
        assert all(v['status'] in ('clear',None) for v in ordinary['visits']) and not h.admitted
        started=time.perf_counter();counts=Counter();attempts,_=source_attempts(h,leaf['source'],counts)
        binary,outside=certify_exhaustion(h._load(leaf['source'])['cnf'],attempts,counts)
        exhaustion=dict(binary=binary,outside=outside,attempts=len(attempts));ranked=candidates(h,leaf['source'],routes,counts,candidate_limit=POLICY['candidate_pairs'])
        r['selection_seconds']=time.perf_counter()-started;r['selection_counts']=dict(counts);assert ranked
        records=[ranked[0]['record']];control=matched_control(h,records[0]);started=time.perf_counter();r['splits']=archive_json(out/'splits.json.gz',records)
        r['split_persistence_seconds']=time.perf_counter()-started
        h.set_admission_budget(POLICY['split_states']);h.counts=Counter();h.prepared.counts=Counter();started=time.perf_counter();pending=False
        targets,_=verify(h,records[0],Counter())
        try:
            for target,edge in zip(targets,records[0]['edges'],strict=True):assert h._edge(target,h._load(leaf['source'])['depth'])==edge
        except AdmissionExhausted:pending=True
        r['acquisition']=dict(seconds=time.perf_counter()-started,pending=pending,inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
            admission_counts=dict(h.admission_counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
        attach(h,routes,records[0],Counter());started=time.perf_counter();final,plan=compose(h,roots,routes,Counter())
        verify_plan(h,plan,plan['roots'],routes,Counter());assert all(b or not a for a,b in zip(baseline,final,strict=True))
        r['final_closed']=final;r['gains']=[i for i,(a,b) in enumerate(zip(baseline,final)) if b and not a]
        r['without_growth_closed'],without=compose(h,roots,WithoutGrowth(routes),Counter());verify_plan(h,without,without['roots'],WithoutGrowth(routes),Counter())
        after_targets=target_state(h,routes);r['composition_seconds']=time.perf_counter()-started
        r['diagnostics']=archive_json(out/'diagnostics.json.gz',dict(leaf=leaf,before=before_targets,ordinary=ordinary,exhaustion=exhaustion,candidates=ranked,control=control,after=after_targets))
        r['certificate']=archive_json(out/'coverage.json.gz',plan);h.close();r['expanded_database_bytes']=history.stat().st_size
        print(json.dumps(dict(leaf_variables=leaf['variables'],ordinary_visits=len(ordinary['visits']),candidates=len(ranked),
            variable=ranked[0]['rank'][-1],closed=sum(final),gains=r['gains'],admitted=len(r['acquisition']['admitted_state_sha256']))),flush=True)
        delta=tmp/'delta';started=time.perf_counter();r['preserved_rows'],r['delta_rows']=export_delta(seed,history,delta)
        compressed(delta,out/'proof-delta.sqlite3.gz');r['delta']=dict(path=str(out/'proof-delta.sqlite3.gz'),sha256=sha(out/'proof-delta.sqlite3.gz'),
            database_sha256=sha(delta),database_bytes=delta.stat().st_size,compressed_bytes=(out/'proof-delta.sqlite3.gz').stat().st_size,export_seconds=time.perf_counter()-started)
        r['logical_table_digests']=digests(history);rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,delta)
        assert digests(rebuilt)==r['logical_table_digests'];before=sha(rebuilt);apply_delta(rebuilt,delta);assert sha(rebuilt)==before
        print('cold inventory audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        print('cold routes and reference proofs',flush=True);started=time.perf_counter();h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0)
        routes=ContinuedLearningRoutes(h,rewrites,learning,continuations)
        for record in read_archive(r['splits']):attach(h,routes,record,Counter())
        verify_plan(h,read_archive(r['certificate']),plan['roots'],routes,Counter());assert compose(h,roots,routes,Counter())[0]==final
        assert target_state(h,routes)==after_targets and not h.admitted;r['cold_routes_seconds']=time.perf_counter()-started
        started=time.perf_counter();ep=parent['reference'];assert sha(ep['path'])==ep['sha256'];unpack(ep['path'],tmp/'reference',ep['database_sha256'])
        shutil.copyfile(tmp/'reference',tmp/'reference-seed');r['reference_seed_seconds']=time.perf_counter()-started
        r['reference']=reference(h,records,r,out,tmp);h.close();assert sha(rebuilt)==before
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(final),gains=r['gains'],added=r['delta_rows'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
