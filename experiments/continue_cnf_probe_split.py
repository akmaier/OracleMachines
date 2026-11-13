#!/usr/bin/env python3
"""Finish one clear ordinary window, certify exhaustion, then reuse a cofactor pair.

This experiment requires the preflight-predicted clear result; it does not treat
clear probing as a SAT verdict. All split children share 32 new admissions.
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

from experiments.continue_cnf_original_probes import restore_checkpoint as restore_base, routes_for
from experiments.continue_cnf_original_splits import select, diagnostics, add_splits
from experiments.cnf_target_probe import search
from experiments.cnf_exhaustion_certificate import make_certificate, check_certificate
from experiments.cnf_probe_window import record_key as window_key
from experiments.compare_cnf_split_batch import save_delta, closure
from experiments.compare_cnf_trace_reuse import archive_json, read_archive
from experiments.compare_cnf_probe_continuation import sha, sha_key, digests, unpack, apply_delta, audit
from experiments.compare_cnf_trace_split import reference, matched_control
from experiments.cnf_split_frontier import frontier
from experiments.cnf_split_batch import run as split_run
from experiments.cnf_trace_reuse import source_attempts
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_route_composition import compose
from experiments.cnf_pattern_inventory import encode

BASE=Path('experiments/results/cnf-original-probe/report.json')
FORMAT='original-frontier-probe-then-split-v1'
POLICY=dict(ordinary_steps=1,ordinary_sources=1,ordinary_states=0,candidate_pairs=64,state_limit=32,pair_limit=32)
FILES=['experiments/continue_cnf_probe_split.py','experiments/cnf_exhaustion_certificate.py','experiments/cnf_target_probe.py','experiments/cnf_trace_split.py',
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
    inherited=tmp/'probe-split-inherited';inherited.mkdir(exist_ok=True)
    parent,*evidence=restore_base(BASE,path,inherited)
    for i,r in enumerate(reversed(chain)):
        if digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed']:
            raise ValueError('Incorrect original-split seed')
        d=r['delta'];delta=tmp/f'probe-split-delta-{i}'
        if sha(d['path'])!=d['sha256']: raise ValueError('Changed original-split delta')
        unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
        if digests(path)!=r['logical_table_digests']: raise ValueError('Incorrect original-split reconstruction')
        evidence=add_splits(evidence,read_archive(r['splits']));parent=r
    return parent,*evidence


def run(out,parent_path=BASE,preview_path=None):
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
                'One ordinary window must be clear and complete the actual binary-variable pool. A different outcome fails this experiment instead of authorizing a split.',
                'Certified single-variable UP exhaustion neither decides SAT nor excludes stronger inference.'])
        started=time.perf_counter();shutil.copyfile(seed,path)
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0);routes=routes_for(h,evidence)
        roots=[h.inspect(c['source'])['root']['key'] for c in r['cases']]
        assert compose(h,roots,routes,Counter())[0]==r['baseline_closed']
        r['preparation_seconds']=time.perf_counter()-started
        started=time.perf_counter();counts=Counter();before=frontier(h,routes,evidence[3],counts)
        if before['pending'] or not before['leaves']:raise ValueError('Expected acquired open split leaf')
        leaf=before['leaves'][0]
        r['navigation_seconds']=time.perf_counter()-started;r['navigation_counts']=dict(counts)
        if preview_path is not None:
            preview=json.loads(preview_path.read_text())
            assert preview['source']==leaf['source'] and preview['parent_validation_sha256']==sha(parent_path.parent/'validation.json')
            r['preflight']=archive_json(out/'preflight.json.gz',preview)
        counts=Counter();h.counts=Counter();h.prepared.counts=Counter();started=time.perf_counter()
        ordinary=search(h,leaf['source'],routes,counts,step_limit=POLICY['ordinary_steps'],
            source_limit=POLICY['ordinary_sources'],state_limit=POLICY['ordinary_states'])
        r['ordinary']=dict(seconds=time.perf_counter()-started,counts=dict(counts),inventory_counts=dict(h.counts),
            prepared_counts=dict(h.prepared.counts),admitted_state_sha256=sorted(map(sha_key,h.admitted)))
        assert len(ordinary['visits'])==1 and ordinary['visits'][0]['kind']=='probe_window'
        assert ordinary['visits'][0]['status']=='clear' and not h.admitted
        window=routes.windows[encode([leaf['source'],4])]
        if preview_path is not None:assert window['probing']==preview['probing']
        started=time.perf_counter();counts=Counter();attempts,_=source_attempts(h,leaf['source'],counts)
        certificate=make_certificate(h._load(leaf['source'])['cnf'],attempts)
        exhaustion=check_certificate(certificate,expected_cnf=h._load(leaf['source'])['cnf'],counts=counts)
        r['exhaustion_seconds']=time.perf_counter()-started;r['exhaustion_counts']=dict(counts)
        r['ordinary_evidence']=archive_json(out/'ordinary.json.gz',dict(before=before,leaf=leaf,result=ordinary,
            window=window,window_id=window_key(window),certificate=certificate,exhaustion=exhaustion))
        started=time.perf_counter();counts=Counter();selected=select(h,routes,evidence,roots,r['baseline_closed'],counts)
        assert selected['record']['source']==leaf['source'] and selected['all_saved_pairs_ranked']
        r['selection_seconds']=time.perf_counter()-started;r['selection_counts']=dict(counts)
        records=[selected['record']];r['selection']=archive_json(out/'selection.json.gz',selected)
        r['splits']=archive_json(out/'splits.json.gz',records)
        r['matched_control']=archive_json(out/'matched-control.json.gz',matched_control(h,records[0]))
        print(json.dumps(dict(mode=selected['mode'],variables=leaf['variables'],clauses=leaf['clauses'],saved_pairs=selected['saved_pairs'],chosen_rank=selected['ranked'][0]['rank'])),flush=True)
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
    if preview_path is not None:r['pipeline_plus_preflight_seconds']=r['pipeline_seconds']+preview['seconds']
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path,default=BASE)
    p.add_argument('--preview',type=Path)
    a=p.parse_args();run(a.output,a.parent,a.preview)
