#!/usr/bin/env python3
"""Compare two bounded lookahead options with saved conditioning on one frontier.

This checkpoint follows a retained clear-result preflight. Ordinary and learned
negative evidence is persisted before ranking the expanded pool of saved pairs.
"""
from collections import Counter
import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

from experiments.continue_cnf_probe_split import restore_checkpoint as restore_base, routes_for
from experiments.continue_cnf_affine_clause import selected_frontiers
from experiments.cnf_target_probe import search
from experiments.cnf_learning_continuation import record_key as learning_key
from experiments.compare_cnf_split_batch import save_delta, closure
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key, digests, unpack, apply_delta, audit
from experiments.compare_cnf_trace_split import reference, matched_control
from experiments.cnf_split_frontier import frontier
from experiments.cnf_split_batch import run as split_run, children
from experiments.cnf_trace_split import candidates, record_key
from experiments.cnf_trace_reuse import source_attempts
from experiments.cnf_learning_batch import selection as learning_selection
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_pattern_inventory import encode

BASE=Path('experiments/results/cnf-probe-split/report.json')
FORMAT='original-frontier-option-comparison-v1'
POLICY=dict(candidate_pairs=64,state_limit=32,pair_limit=32,ordinary_steps=1,ordinary_sources=1,ordinary_states=0)
FILES=['experiments/continue_cnf_frontier_comparison.py','experiments/cnf_learning_continuation.py','experiments/cnf_target_probe.py','experiments/cnf_trace_split.py',
       'experiments/cnf_split_batch.py','experiments/cnf_split_frontier.py',
       'solver/test_cnf_original_splits.py']


def add_splits(evidence, records):
    if len(evidence)!=5: raise ValueError('Five evidence lists are required')
    saved={record_key(r):r for r in evidence[3]}
    for record in records:
        identity=record_key(record)
        if identity in saved and encode(saved[identity])!=encode(record):
            raise ValueError('Conflicting immutable split')
        saved[identity]=record
    return [*evidence[:3],list(saved.values()),evidence[4]]


def add_learning(evidence, records):
    if len(evidence)!=5: raise ValueError('Five evidence lists are required')
    saved={learning_key(r):r for r in evidence[2]}
    for record in records:
        identity=learning_key(record)
        if identity in saved and encode(saved[identity])!=encode(record):
            raise ValueError('Conflicting immutable learning continuation')
        saved[identity]=record
    return [*evidence[:2],list(saved.values()),*evidence[3:]]


def restore_checkpoint(report_path,path,tmp):
    current=Path(report_path);chain=[];seen=set()
    while current.resolve()!=BASE.resolve():
        if current.resolve() in seen: raise ValueError('Cyclic original-split lineage')
        seen.add(current.resolve());r=json.loads(current.read_text())
        if r['format']!=FORMAT or sha(r['parent']['path'])!=r['parent']['sha256']:
            raise ValueError('Changed original-split parent')
        for filename,digest in r['fingerprints'].items():
            if sha(filename)!=digest: raise ValueError('Changed original-split implementation')
        chain.append(r);current=Path(r['parent']['path'])
    inherited=tmp/'frontier-comparison-inherited';inherited.mkdir(exist_ok=True)
    parent,*evidence=restore_base(BASE,path,inherited)
    for i,r in enumerate(reversed(chain)):
        if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:
            raise ValueError('Incorrect original-split seed')
        d=r['delta'];delta=tmp/f'frontier-comparison-delta-{i}'
        if sha(d['path'])!=d['sha256']: raise ValueError('Changed original-split delta')
        unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
        if digests(path)!=r['logical_table_digests']: raise ValueError('Incorrect original-split reconstruction')
        evidence=add_learning(add_splits(evidence,read_archive(r['splits'])),read_archive(r['learning_additions']));parent=r
    return parent,*evidence


def select(h,routes,evidence,roots,closed,counts):
    before=frontier(h,routes,evidence[3],counts)
    navigation,original_leaves=selected_frontiers(h,roots,routes,closed)
    by_id={record_key(r):r for r in evidence[3]}
    if before['pending']:
        pending=before['pending'][0]
        if 'split' not in pending: raise ValueError('Pending internal state needs its original acquisition route')
        return dict(mode='resume_pending',before=before,navigation=navigation,
            record=by_id[pending['split']],pending=pending)
    if before['leaves']:
        mode='split_descendant';pool=[row['source'] for row in before['leaves']]
    else:
        mode='original_leaf';pool=list(original_leaves)
    def rank(source):
        cnf=h._load(source)['cnf'];return [len({abs(l) for c in cnf for l in c}),sum(map(len,cnf)),source]
    skipped=[]
    for source in sorted(pool,key=rank):
        ranked=candidates(h,source,routes,counts,candidate_limit=POLICY['candidate_pairs'])
        if not ranked: skipped.append(dict(source=source,reason='no_saved_clear_pairs'));continue
        attempts,_=source_attempts(h,source,counts);node=h._load(source)
        leaf=dict(source=source,variables=rank(source)[0],clauses=len(node['cnf']),literals=rank(source)[1],
            selected_original_cases=original_leaves.get(source,[]))
        return dict(mode=mode,before=before,navigation=navigation,leaf=leaf,skipped=skipped,ranked=ranked,
            record=ranked[0]['record'],saved_pairs=len(attempts)//2,all_saved_pairs_ranked=len(ranked)*2==len(attempts))
    raise ValueError('No saved pair on the selected open frontier; choose a different inference')


def diagnostics(h,routes,evidence,roots,closed):
    navigation,_=selected_frontiers(h,roots,routes,closed)
    return dict(frontier=frontier(h,routes,evidence[3],Counter()),
        children=children(h,routes,evidence[3]),open_originals=navigation,
        learning=learning_selection(h,routes,Counter()))


def run(out,parent_path=BASE,preview_path=None,comparison_path=None):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'seed';path=tmp/'history';started=time.perf_counter()
        parent,*evidence=restore_checkpoint(parent_path,seed,tmp)
        r=dict(format=FORMAT,parent=dict(path=str(parent_path),sha256=sha(parent_path)),
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={p:sha(p) for p in FILES},options=parent['options'],cases=parent['cases'],policy=POLICY,
            baseline_closed=parent['final_closed'],seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,
            restore_seconds=time.perf_counter()-started,limitations=[
                'One adaptively selected leaf of 83 reused development cases, not an independent holdout.',
                'Smallest support/literal frontier and then ranked retained pairs are heuristics, not globally minimum expansion.',
                'Both branches share 32 new recognition states; this does not bound CPU, bytes, peak RAM or repeated expansion.',
                'Original frontiers follow selected internal/ordinary routes; retained external split frontiers are recorded separately.',
                'Matched control compares only saved versus freshly acquired unit closures on the same selected pair, not complete solver runtime.',
                'All five evidence lists and earlier sidecars remain required for later checkpoints.',
                'The two bounded lookahead blocks are required to be clear as observed in the preserved preflight; this is not inference exhaustion.',
                'Preflight reconstruction is additional charged work; acquisition compares options on one representation, not full competing solvers.'])
        started=time.perf_counter();shutil.copyfile(seed,path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']
        r['preparation_seconds']=time.perf_counter()-started
        started=time.perf_counter();counts=Counter();before=select(h,routes,evidence,roots,r['baseline_closed'],counts)
        r['initial_selection_seconds']=time.perf_counter()-started;r['initial_selection_counts']=dict(counts)
        source=before['leaf']['source']
        assert before['mode']=='original_leaf'
        counts=Counter();started=time.perf_counter()
        ordinary=search(h,source,routes,counts,step_limit=POLICY['ordinary_steps'],source_limit=POLICY['ordinary_sources'],state_limit=0)
        r['ordinary_seconds']=time.perf_counter()-started;r['ordinary_counts']=dict(counts)
        assert len(ordinary['visits'])==1 and ordinary['visits'][0]['status']=='clear' and not h.admitted
        started=time.perf_counter();counts=Counter()
        queue=[row for row in learning_selection(h,routes,counts) if row['source']==source and row['reason']=='ready']
        assert len(queue)==1
        record,target=routes.learned_blocks.advance(h,queue[0]['base_sha256'],counts)
        r['learning_seconds']=time.perf_counter()-started;r['learning_counts']=dict(counts)
        assert record is not None and record['probing']['status']=='clear' and record['edge'] is None
        evidence=add_learning(evidence,[record]);r['learning_additions']=archive_json(out/'learning-additions.json.gz',[record])
        r['options_comparison']=archive_json(out/'options-comparison.json.gz',dict(before=before,ordinary=ordinary,learning_selection=queue[0]))
        if preview_path is not None:
            preview=json.loads(preview_path.read_text());assert preview['source']==source
            assert preview['parent_validation_sha256']==sha(parent_path.parent/'validation.json')
            r['ordinary_preflight']=archive_json(out/'ordinary-preflight.json.gz',preview)
        if comparison_path is not None:
            preview_comparison=json.loads(comparison_path.read_text())
            assert preview_comparison['selection']==before and preview_comparison['learning_record']==record
            r['comparison_preflight']=archive_json(out/'comparison-preflight.json.gz',preview_comparison)
        started=time.perf_counter();counts=Counter();selected=select(h,routes,evidence,roots,r['baseline_closed'],counts)
        assert selected['leaf']['source']==source
        r['selection_seconds']=time.perf_counter()-started;r['selection_counts']=dict(counts)
        records=[selected['record']];r['selection']=archive_json(out/'selection.json.gz',selected)
        r['splits']=archive_json(out/'splits.json.gz',records)
        r['matched_control']=archive_json(out/'matched-control.json.gz',matched_control(h,records[0]))
        print(json.dumps(dict(mode=selected['mode'],leaf=selected.get('leaf'),chosen_rank=selected.get('ranked',[{}])[0].get('rank'))),flush=True)
        h.counts=Counter();h.prepared.counts=Counter();started=time.perf_counter()
        result=split_run(h,routes,records,state_limit=POLICY['state_limit'],pair_limit=POLICY['pair_limit'])
        r['acquisition']=dict(seconds=time.perf_counter()-started,inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
            admission_counts=dict(h.admission_counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
        assert len(h.admitted)<=POLICY['state_limit'];evidence=add_splits(evidence,records)
        started=time.perf_counter();summary,plan=closure(h,roots,routes,r['baseline_closed']);r.update(summary)
        d=diagnostics(h,routes,evidence,roots,r['final_closed']);d['acquisition']=result
        r['composition_diagnosis_seconds']=time.perf_counter()-started
        r['diagnostics']=archive_json(out/'diagnostics.json.gz',d);r['certificate']=archive_json(out/'coverage.json.gz',plan)
        h.close();r['expanded_database_bytes']=path.stat().st_size
        r['delta']=save_delta(seed,path,tmp/'delta',out/'proof-delta.sqlite3.gz');r['logical_table_digests']=digests(path)
        db=sqlite3.connect(tmp/'delta');r['new_node_kinds']=dict(Counter(json.loads(p)['kind'] for p, in db.execute('SELECT payload FROM cnf_patterns_v1')));db.close()
        print(json.dumps(dict(admitted=len(h.admitted),kinds=r['new_node_kinds'],closed=sum(r['final_closed']),gains=r['gains'],
            remaining=[[x['variables'],x['clauses']] for x in d['frontier']['leaves']],pending=len(d['frontier']['pending']))),flush=True)
        rebuilt=tmp/'rebuilt';shutil.copyfile(seed,rebuilt);apply_delta(rebuilt,tmp/'delta')
        assert digests(rebuilt)==r['logical_table_digests'];before=sha(rebuilt);apply_delta(rebuilt,tmp/'delta');assert sha(rebuilt)==before
        print('full cold inventory audit',flush=True);r['audit']=audit(rebuilt,AnchoredAdditiveInventory,r['options'])
        print('cold routes and retained reference proofs',flush=True);started=time.perf_counter()
        h=BudgetedInventory(rebuilt,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        cold,_=closure(h,roots,routes,r['baseline_closed']);assert all(cold[k]==r[k] for k in cold)
        assert diagnostics(h,routes,evidence,roots,r['final_closed'])=={k:v for k,v in d.items() if k!='acquisition'}
        assert not h.admitted;r['cold_routes_seconds']=time.perf_counter()-started
        ep=parent['reference'];assert sha(ep['path'])==ep['sha256'];unpack(ep['path'],tmp/'reference',ep['database_sha256'])
        shutil.copyfile(tmp/'reference',tmp/'reference-seed');r['reference']=reference(h,records,r,out,tmp)
        h.close();assert sha(rebuilt)==before
    r['pipeline_seconds']=time.perf_counter()-pipeline
    r['pipeline_plus_preflight_seconds']=r['pipeline_seconds']+(preview['seconds'] if preview_path is not None else 0)+(preview_comparison['total_seconds'] if comparison_path is not None else 0)
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path,default=BASE)
    p.add_argument('--preview',type=Path);p.add_argument('--comparison',type=Path)
    a=p.parse_args();run(a.output,a.parent,a.preview,a.comparison)
