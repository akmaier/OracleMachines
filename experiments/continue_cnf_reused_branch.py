#!/usr/bin/env python3
"""Acquire a saved split while reusing an already checked cofactor.

Keep all five evidence lists, including affine family routes. Pending pairs and
open retained split descendants take precedence over selecting a new original.
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

from experiments.continue_cnf_frontier_batch import restore_checkpoint as restore_base, routes_for
from experiments.continue_cnf_original_splits import add_splits, select, diagnostics
from experiments.compare_cnf_split_batch import save_delta, closure
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key, digests, unpack, apply_delta, audit
from experiments.compare_cnf_trace_split import reference, matched_control
from experiments.cnf_split_batch import run as split_run
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_pattern_inventory import encode

BASE=Path('experiments/results/cnf-frontier-batch/report.json')
FORMAT='reused-branch-frontier-split-v1'
POLICY=dict(candidate_pairs=64,state_limit=32,pair_limit=32)
FILES=['experiments/continue_cnf_reused_branch.py','experiments/continue_cnf_original_splits.py','experiments/cnf_trace_split.py',
       'experiments/cnf_split_batch.py','experiments/cnf_split_frontier.py',
       'solver/test_cnf_original_splits.py']


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
    inherited=tmp/'reused-branch-inherited';inherited.mkdir(exist_ok=True)
    parent,*evidence=restore_base(BASE,path,inherited)
    for i,r in enumerate(reversed(chain)):
        if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:
            raise ValueError('Incorrect original-split seed')
        d=r['delta'];delta=tmp/f'reused-branch-delta-{i}'
        if sha(d['path'])!=d['sha256']: raise ValueError('Changed original-split delta')
        unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
        if digests(path)!=r['logical_table_digests']: raise ValueError('Incorrect original-split reconstruction')
        evidence=add_splits(evidence,read_archive(r['splits']));parent=r
    return parent,*evidence


def run(out,parent_path=BASE):
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
                'All five evidence lists and earlier sidecars remain required for later checkpoints.'])
        started=time.perf_counter();shutil.copyfile(seed,path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']
        r['preparation_seconds']=time.perf_counter()-started
        started=time.perf_counter();counts=Counter();selected=select(h,routes,evidence,roots,r['baseline_closed'],counts)
        r['selection_seconds']=time.perf_counter()-started;r['selection_counts']=dict(counts)
        r['evidence_counts_before']=[len(items) for items in evidence]
        records=[selected['record']];r['selection']=archive_json(out/'selection.json.gz',selected)
        r['splits']=archive_json(out/'splits.json.gz',records)
        r['branch_before']=[dict(value=value,key_sha256=sha_key(edge['key']),variables=len(edge['names']),
            present=h._load(edge['key']) is not None,
            closed=h._load(edge['key']) is not None and compose(h,[edge['key']],routes,Counter())[0][0])
            for value,edge in zip((False,True),records[0]['edges'],strict=True)]
        r['matched_control']=archive_json(out/'matched-control.json.gz',matched_control(h,records[0]))
        print(json.dumps(dict(mode=selected['mode'],variables=selected.get('leaf',{}).get('variables'),
            chosen_rank=selected.get('ranked',[{}])[0].get('rank'),branches=r['branch_before'])),flush=True)
        h.counts=Counter();h.prepared.counts=Counter();started=time.perf_counter()
        result=split_run(h,routes,records,state_limit=POLICY['state_limit'],pair_limit=POLICY['pair_limit'])
        r['acquisition']=dict(seconds=time.perf_counter()-started,inventory_counts=dict(h.counts),prepared_counts=dict(h.prepared.counts),
            admission_counts=dict(h.admission_counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
        assert len(h.admitted)<=POLICY['state_limit'];evidence=add_splits(evidence,records)
        r['evidence_counts_after']=[len(items) for items in evidence]
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
    r['pipeline_seconds']=time.perf_counter()-pipeline;(out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path,default=BASE)
    a=p.parse_args();run(a.output,a.parent)
