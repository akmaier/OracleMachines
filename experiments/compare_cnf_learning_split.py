#!/usr/bin/env python3
"""Matched recognition allowances for learned clauses and saved cofactor splits."""
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.continue_cnf_split_frontier import restore_checkpoint as restore_parent
from experiments.compare_cnf_split_batch import routes_for,save_delta,closure
from experiments.compare_cnf_trace_reuse import read_archive,archive_json
from experiments.compare_cnf_probe_continuation import sha,sha_key,digests,apply_delta,unpack,audit
from experiments.compare_cnf_trace_split import reference as split_reference
from experiments.cnf_split_frontier import frontier
from experiments.cnf_split_batch import run as split_run,children
from experiments.cnf_trace_split import candidates
from experiments.cnf_trace_reuse import source_attempts
from experiments.cnf_trace_learning import (acquire_learning,verify_learning,checked_augmentation,lift_learning,
    implication_graph,discover_graph,check_graph,LEARN_LIMIT,PROBE_LIMIT)
from experiments.cnf_learning_continuation import LearningBlocks,base_id,record_key
from experiments.cnf_learning_batch import search as learning_search,selection,acquire
from experiments.cnf_target_probe import remaining
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_residual_dag import holds
from experiments.cnf_pattern_inventory import encode

PARENT=Path('experiments/results/cnf-split-frontier/report.json')
FORMAT='learned-versus-saved-split-v1'
POLICY=dict(candidate_pairs=8,learning_clauses=LEARN_LIMIT,learning_probe_width=PROBE_LIMIT,learning_steps=8,state_limit=32)


def additions(evidence,bases=(),blocks=(),splits=()):
    rewrites,learning,continuations,old_splits=evidence
    return [rewrites,learning+list(bases),continuations+list(blocks),old_splits+list(splits)]


def restore_checkpoint(report_path,path,tmp):
    r=json.loads(Path(report_path).read_text())
    if r['format']!=FORMAT or sha(r['parent']['path'])!=r['parent']['sha256']:raise ValueError('Changed comparison parent')
    for p,digest in r['fingerprints'].items():
        if sha(p)!=digest:raise ValueError('Changed comparison implementation')
    parent,*evidence=restore_parent(Path(r['parent']['path']),path,tmp)
    if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:raise ValueError('Incorrect comparison seed')
    d=r['delta'];delta=tmp/'learning-split-delta'
    if sha(d['path'])!=d['sha256']:raise ValueError('Changed comparison delta')
    unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
    if digests(path)!=r['logical_table_digests']:raise ValueError('Incorrect comparison reconstruction')
    return r,*additions(evidence,read_archive(r['learning']),read_archive(r['blocks']),read_archive(r['splits']))


def learning_targets(h,routes,bases,blocks):
    selected=[];pending=[];by_id={base_id(b):b for b in bases}
    for kind,record in [('base',b) for b in bases]+[('continuation',b) for b in blocks]:
        if record['edge'] is None:continue
        source=record['source'] if kind=='base' else by_id[record['base_sha256']]['source']
        row=dict(source=source,target=record['edge']['key'])
        (pending if h._load(row['target']) is None else selected).append(row)
    return dict(pending=pending,remaining=remaining(h,selected,routes,Counter()))


def learning_references(h,routes,bases,blocks,tmp):
    started=time.perf_counter();solver=AccountedResidualSolver(tmp/'reference');rows=[]
    for base in bases:
        node,expanded=checked_augmentation(h,base,Counter());a=solver.solve(node['cnf']);b=solver.solve(expanded)
        assert a['answer']==b['answer']
        if b['answer']:assert holds(node['cnf'],b['model'])
        targets=[]
        relevant=[('base',base)]+[('continuation',rec) for rec in blocks if rec['base_sha256']==base_id(base)]
        for kind,rec in relevant:
            if rec['edge'] is None:continue
            target,_=(verify_learning(h,rec,Counter()) if kind=='base' else routes.learned_blocks.verify(h,rec,Counter()))
            answer=solver.solve(target);assert answer['answer']==a['answer'];canonical=None
            child=h._load(rec['edge']['key'])
            if child is not None:
                canonical=solver.solve(child['cnf']);assert canonical['answer']==answer['answer']
                if canonical['answer']:
                    model=lift_learning(h,rec,canonical['model'],Counter()) if kind=='base' else routes.learned_blocks.lift(h,rec,canonical['model'])
                    assert holds(node['cnf'],model)
            targets.append(dict(kind=kind,identity=base_id(rec) if kind=='base' else record_key(rec),target=answer,canonical=canonical))
        rows.append(dict(base_sha256=base_id(base),source=a,expanded=b,targets=targets))
    counts=dict(solver.counts);solver.close();return dict(rows=rows,seconds=time.perf_counter()-started,counts=counts)


def run(out):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';started=time.perf_counter();parent,*evidence=restore_parent(PARENT,seed,tmp)
        r=dict(format=FORMAT,parent=dict(path=str(PARENT),sha256=sha(PARENT)),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in ('experiments/compare_cnf_learning_split.py',)},options=parent['options'],cases=parent['cases'],policy=POLICY,
            baseline_closed=parent['final_closed'],seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,restore_seconds=time.perf_counter()-started,arms={},
            limitations=['One adaptive residual among 83 reused development originals; no independent holdout or general coverage estimate.',
                'The same 32-state recognition allowance does not equalize propagation, checking, ranking, proof size or CPU work.',
                'One bounded learned batch and at most eight later advances are compared with one split chosen from at most eight saved pairs.',
                'Fresh verifier caches are used for each arm. Shared preparation and split ranking are charged separately; OS caches are not flushed.',
                'Source unit-refutation exhaustion does not exclude stronger learning. Splits require both child plans for structural closure.',
                'Selected frontiers omit some alternative learned routes. Peak RAM and a uniformly polynomial construction for arbitrary CNFs remain unproved.'])
        started=time.perf_counter();h=BudgetedInventory(seed,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']];assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']
        r['preparation_seconds']=time.perf_counter()-started;started=time.perf_counter();counts=Counter()
        before=frontier(h,routes,evidence[-1],counts);leaf=before['leaves'][0];source=leaf['source']
        assert all(base['source']!=source for base in evidence[1]),'Use retained learning continuation for an existing base'
        attempts,refs=source_attempts(h,source,counts);graph=implication_graph(h._load(source)['cnf'],attempts,counts)
        graph_proof=discover_graph(graph,counts);conclusions=check_graph(graph,graph_proof,counts)
        r['navigation_graph_seconds']=time.perf_counter()-started;r['navigation_graph_counts']=dict(counts)
        started=time.perf_counter();counts=Counter();ranked=candidates(h,source,routes,counts,candidate_limit=POLICY['candidate_pairs']);assert ranked
        records=[ranked[0]['record']];r['ranking_seconds']=time.perf_counter()-started;r['ranking_counts']=dict(counts);h.close()
        r['selection']=archive_json(out/'selection.json.gz',dict(before=before,leaf=leaf,ranked=ranked,graph=graph_proof,graph_conclusions=conclusions))
        r['splits']=archive_json(out/'splits.json.gz',records)
        print(json.dumps(dict(variables=leaf['variables'],split_rank=ranked[0]['rank'],graph_conclusions=conclusions)),flush=True)
        bases=[];blocks=[]
        for arm in ('learning','split'):
            path=tmp/arm;started=time.perf_counter();shutil.copyfile(seed,path);h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
            routes=routes_for(h,evidence);assert compose(h,roots,routes,Counter())[0]==r['baseline_closed'];prep=time.perf_counter()-started
            h.counts=Counter();h.prepared.counts=Counter();counts=Counter();started=time.perf_counter();result=None
            if arm=='learning':
                attempts,refs=source_attempts(h,source,counts);base=acquire_learning(h,source,attempts,refs,counts)
                bases=[] if base is None else [base];r['learning']=archive_json(out/'learning.json.gz',bases)
                if base is None:h.set_admission_budget(POLICY['state_limit']);result=dict(kind='no_batch')
                elif base['edge'] is not None:
                    h.set_admission_budget(POLICY['state_limit']);target,_=verify_learning(h,base,counts)
                    edge,pending,admitted=acquire(h,target,h._load(source)['depth'],total_limit=POLICY['state_limit'],target_limit=POLICY['state_limit'])
                    if not pending:assert edge==base['edge']
                    result=dict(kind='base_reduction',pending=pending,admitted=sorted(admitted))
                else:
                    local=LearningBlocks(h,bases);proxy=SimpleNamespace(by_source=routes.by_source,learned_blocks=local,refresh_learning=lambda reader:local.attach(reader,routes))
                    journal=out/'learning-blocks.jsonl'
                    def save(record):
                        with journal.open('a') as stream:stream.write(encode(record)+'\n')
                    result=dict(kind='continuation',search=learning_search(h,proxy,[dict(base_sha256=base_id(base),reason='ready')],counts,save,
                        step_limit=POLICY['learning_steps'],state_limit=POLICY['state_limit'],target_limit=POLICY['state_limit']))
                    blocks=list(local.records.values())
                r['blocks']=archive_json(out/'blocks.json.gz',blocks)
                journal=out/'learning-blocks.jsonl'
                if journal.exists():assert [json.loads(line) for line in journal.read_text().splitlines()]==blocks;journal.unlink()
            else:result=split_run(h,routes,records,state_limit=POLICY['state_limit'],pair_limit=POLICY['state_limit'])
            elapsed=time.perf_counter()-started
            a=dict(preparation_seconds=prep,acquisition_seconds=elapsed,counts=dict(counts),inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
                admission_counts=dict(h.admission_counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
            assert len(h.admitted)<=POLICY['state_limit'];started=time.perf_counter()
            arm_evidence=additions(evidence,bases,blocks) if arm=='learning' else additions(evidence,splits=records)
            routes=routes_for(h,arm_evidence);summary,plan=closure(h,roots,routes,r['baseline_closed']);a.update(summary)
            d=dict(result=result,frontier=frontier(h,routes,arm_evidence[-1],Counter()),
                learning_targets=learning_targets(h,routes,bases,blocks) if arm=='learning' else None)
            a['composition_diagnosis_seconds']=time.perf_counter()-started;a['diagnostics']=archive_json(out/f'{arm}-diagnostics.json.gz',d)
            a['certificate']=archive_json(out/f'{arm}-coverage.json.gz',plan);h.close();a['database_bytes']=path.stat().st_size
            a['delta']=save_delta(seed,path,tmp/f'{arm}-delta',out/f'{arm}-delta.sqlite3.gz');a['logical_table_digests']=digests(path);r['arms'][arm]=a
            print(json.dumps(dict(arm=arm,closed=sum(a['final_closed']),gains=a['gains'],admitted=len(a['admitted_state_sha256']),seconds=elapsed,
                base_status=None if not bases else bases[0]['probing']['status'],blocks=len(blocks))),flush=True)
        history=tmp/'union';started=time.perf_counter();shutil.copyfile(seed,history)
        for arm in ('learning','split'):apply_delta(history,tmp/f'{arm}-delta')
        r['merge_seconds']=time.perf_counter()-started;union_evidence=additions(evidence,bases,blocks,records)
        started=time.perf_counter();h=BudgetedInventory(history,**r['options']);h.set_admission_budget(0);routes=routes_for(h,union_evidence)
        summary,plan=closure(h,roots,routes,r['baseline_closed']);r.update(summary)
        for a in r['arms'].values():assert all(b or not a for a,b in zip(a['final_closed'],r['final_closed'],strict=True))
        r['union_composition_seconds']=time.perf_counter()-started
        r['diagnostics']=archive_json(out/'diagnostics.json.gz',dict(frontier=frontier(h,routes,union_evidence[-1],Counter()),
            learning_targets=learning_targets(h,routes,bases,blocks),learning_queue=selection(h,routes,Counter()),children=children(h,routes,records)))
        r['certificate']=archive_json(out/'coverage.json.gz',plan)
        ep=parent['reference'];assert sha(ep['path'])==ep['sha256'];unpack(ep['path'],tmp/'reference',ep['database_sha256']);shutil.copyfile(tmp/'reference',tmp/'reference-seed')
        learned_reference=learning_references(h,routes,bases,blocks,tmp);r['reference']=split_reference(h,records,r,out,tmp);r['reference']['learning']=learned_reference
        h.close();r['expanded_database_bytes']=history.stat().st_size
        r['delta']=save_delta(seed,history,tmp/'union-delta',out/'proof-delta.sqlite3.gz');r['logical_table_digests']=digests(history)
        rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,tmp/'union-delta');assert digests(rebuilt)==r['logical_table_digests']
        before_bytes=sha(rebuilt);apply_delta(rebuilt,tmp/'union-delta');assert sha(rebuilt)==before_bytes
        print('full cold inventory audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]))
