#!/usr/bin/env python3
"""Persist a forced frontier reduction through the exact source-local store.

Both matched arms perform the same single ordinary advance. Global composition,
independent positive replay and reference solving are charged separately. All
historical records and the five complete sidecar lists remain available.
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
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from experiments.continue_cnf_source_local import restore_checkpoint as restore_base
from experiments.continue_cnf_reused_branch import routes_for
from experiments.cnf_source_local import check_delta
from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_expanded_coverage import expand,checked_inventory
from experiments.cnf_positive_primitives import verify_positive
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_probe_window import choices
from experiments.cnf_trace_split import candidates
from experiments.cnf_split_frontier import frontier
from experiments.cnf_trace_reuse import source_attempts
from experiments.cnf_learning_batch import selection as learning_selection
from experiments.compare_cnf_split_batch import closure,new_probes
from experiments.compare_cnf_target_probe import reference
from experiments.continue_cnf_learning import preserved_reference
from experiments.compare_cnf_trace_reuse import archive_json,read_archive
from experiments.compare_cnf_probe_continuation import sha,sha_key,digests,apply_delta,unpack,compressed

BASE=Path('experiments/results/cnf-source-local-checked/report.json')
FORMAT='source-local-forced-frontier-v1'
FILES=['experiments/continue_cnf_local_forcing.py','solver/test_cnf_local_forcing.py',
       'experiments/cnf_source_local.py','experiments/continue_cnf_source_local.py']


def restore_checkpoint(report_path,path,tmp):
    current=Path(report_path);chain=[];seen=set()
    while current.resolve()!=BASE.resolve():
        if current.resolve() in seen: raise ValueError('Cyclic local forcing lineage')
        seen.add(current.resolve());r=json.loads(current.read_text())
        if r['format']!=FORMAT or sha(r['parent']['path'])!=r['parent']['sha256']:
            raise ValueError('Changed local forcing parent')
        for name,digest in r['fingerprints'].items():
            if sha(name)!=digest: raise ValueError('Changed local forcing implementation')
        chain.append(r);current=Path(r['parent']['path'])
    inherited=tmp/'inherited';inherited.mkdir(exist_ok=True)
    parent,*evidence=restore_base(BASE,path,inherited)
    for i,r in enumerate(reversed(chain)):
        if (digests(path)!=r['seed_table_digests'] or parent['final_closed']!=r['baseline_closed'] or
                parent['options']!=r['options'] or parent['cases']!=r['cases']):
            raise ValueError('Incorrect local forcing seed')
        d=r['delta'];delta=tmp/f'local-forcing-delta-{i}'
        if sha(d['path'])!=d['sha256']: raise ValueError('Changed forcing delta')
        unpack(d['path'],delta,d['database_sha256']);apply_delta(path,delta)
        check_delta(path,delta,r['options'])
        if digests(path)!=r['logical_table_digests']: raise ValueError('Incorrect forcing reconstruction')
        h=BudgetedInventory(path,**r['options']);h.set_admission_budget(0)
        try:
            claimed=[h._canonical(c['source'],h.config['max_depth'])[2]
                     for c,closed in zip(r['cases'],r['final_closed'],strict=True) if closed]
            verify_positive(h,read_archive(r['expanded_certificate']),claimed,evidence,Counter())
        finally:h.close()
        if any(a and not b for a,b in zip(r['baseline_closed'],r['final_closed'],strict=True)):
            raise ValueError('Lost previous positive coverage')
        parent=r
    return parent,*evidence


def profile(h,routes,row):
    source=row['source'];node=h._load(source);counts=Counter()
    _,ranked=choices(h,source,64,counts)
    attempted,refs=source_attempts(h,source,counts)
    used={a['variable'] for a in attempted}
    return dict(source=source,source_sha256=sha_key(source),variables=row['variables'],
        clauses=len(node['cnf']),literals=sum(map(len,node['cnf'])),
        next_ordinary_variables=[v for v in ranked if v not in used][:4],
        candidates=candidates(h,source,routes,counts,candidate_limit=64),counts=dict(counts))


def run(out,parent_path=BASE):
    pipeline=time.perf_counter();out.mkdir(exist_ok=False)
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);seed=tmp/'authority';tick=time.perf_counter()
        parent,*evidence=restore_checkpoint(parent_path,seed,tmp)
        r=dict(format=FORMAT,parent=dict(path=str(parent_path),sha256=sha(parent_path)),
            source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
            fingerprints={name:sha(name) for name in FILES},options=parent['options'],cases=parent['cases'],
            baseline_closed=parent['final_closed'],restore_seconds=time.perf_counter()-tick,
            seed_table_digests=digests(seed),seed_database_bytes=seed.stat().st_size,
            evidence_counts=list(map(len,evidence)),limitations=[
                'One preselected 23-variable frontier on adaptively reused development inputs, not an independent holdout.',
                'Unmeasured exploratory propagation identified a forced candidate before this pipeline; selection is adaptive, not a minimum-cost split comparison.',
                'Both arms advance one ordinary block with 32 state admissions; full authority is required and first restoration is charged separately.',
                'Two reversed fresh-process repetitions share OS caches; no confidence interval, peak-RAM or unrestricted complexity claim.',
                'Global recomposition, diagnostics, positive replay and reference solving remain separate costs.',
                'Only new delta records and their dependencies are cold-checked; this does not repeat a full historical archive audit.'])
        original_sha=sha(seed)
        if parent_path.resolve()==BASE.resolve():
            claim=json.loads(Path(parent['claim']['path']).read_text())
            if sha(parent['claim']['path'])!=parent['claim']['sha256']:raise ValueError('Changed source claim')
        else:
            prior=read_archive(parent['frontier_profiles'])
            if not prior:raise ValueError('No acquired open leaf in this checkpoint')
            claim=dict(source=prior[0]['source'],source_sha256=prior[0]['source_sha256'],options=r['options'],state_limit=32)
        claim_path=out/'claim.json';claim_path.write_text(encode(claim)+'\n')
        r['claim']=dict(path=str(claim_path),sha256=sha(claim_path))
        samples=[];deltas=[]
        for repeat,order in enumerate((('eager','local'),('local','eager'))):
            for mode in order:
                delta=tmp/f'{mode}-{repeat}';deltas.append(delta)
                print(json.dumps(dict(phase='one forced advance',mode=mode,repeat=repeat)),flush=True)
                tick=time.perf_counter()
                process=subprocess.run([sys.executable,str(ROOT/'experiments/continue_cnf_source_local.py'),
                    '--worker',mode,'--authority',str(seed),'--claim',str(claim_path.resolve()),
                    '--delta',str(delta)],cwd=tmp,text=True,capture_output=True)
                elapsed=time.perf_counter()-tick
                if process.returncode:
                    (out/f'failed-{mode}-{repeat}.txt').write_text(process.stdout+process.stderr)
                    raise RuntimeError('Matched worker failed; output preserved')
                sample=json.loads(process.stdout);sample.update(mode=mode,repeat=repeat,process_seconds=elapsed)
                samples.append(sample)
                print(json.dumps(dict(mode=mode,seconds=elapsed,admitted=len(sample['admitted']),
                    rows=sample['delta_rows'],pending=sample['result']['admission_stopped'])),flush=True)
        first=samples[0]
        for sample in samples:
            for key in ('result','admitted','counts','delta_rows','delta_sha256'):
                if sample[key]!=first[key]:raise ValueError('Matched operation differs: '+key)
        if first['result']['record']['probing']['status']!='forced':
            raise ValueError('Expected forced source; preserve and evaluate a different policy separately')
        r['samples']=samples
        r['summary']={mode:{key:sum(s[key] for s in samples if s['mode']==mode)/2 for key in
            ('preparation_seconds','advance_seconds','export_seconds','operation_seconds','process_seconds','working_database_bytes')}
            for mode in ('eager','local')}
        archive=out/'proof-delta.sqlite3.gz';compressed(deltas[0],archive)
        r['delta']=dict(path=str(archive),sha256=sha(archive),database_sha256=sha(deltas[0]),
            database_bytes=deltas[0].stat().st_size,compressed_bytes=archive.stat().st_size,added_rows=first['delta_rows'])
        r['operation']=archive_json(out/'operation.json.gz',first['result'])
        tick=time.perf_counter();merged=tmp/'merged';shutil.copyfile(seed,merged);apply_delta(merged,deltas[0])
        r['merge_seconds']=time.perf_counter()-tick
        tick=time.perf_counter();r['cold_delta_check']=check_delta(merged,deltas[0],r['options'])
        r['cold_delta_check_seconds']=time.perf_counter()-tick
        r['logical_table_digests']=digests(merged);r['expanded_database_bytes']=merged.stat().st_size
        db=sqlite3.connect(deltas[0]);r['new_node_kinds']=dict(Counter(json.loads(p)['kind'] for p, in
            db.execute('SELECT payload FROM cnf_patterns_v1')));db.close()
        before=sha(merged);apply_delta(merged,deltas[0]);assert sha(merged)==before
        assert sha(seed)==original_sha and digests(seed)==r['seed_table_digests']
        r['history_unchanged']=True;r['idempotent_merge']=True
        print('global route composition and frontier diagnostics',flush=True)
        tick=time.perf_counter();h=BudgetedInventory(merged,**r['options']);h.set_admission_budget(0)
        routes=routes_for(h,evidence)
        roots=[h._canonical(c['source'],h.config['max_depth'])[2] for c in r['cases']]
        r['global_preparation_seconds']=time.perf_counter()-tick
        tick=time.perf_counter();summary,plan=closure(h,roots,routes,r['baseline_closed']);r.update(summary)
        r['composition_seconds']=time.perf_counter()-tick
        r['certificate']=archive_json(out/'coverage.json.gz',plan)
        tick=time.perf_counter();state=frontier(h,routes,evidence[3],Counter())
        profiles=[profile(h,routes,row) for row in state['leaves']]
        r['frontier']=archive_json(out/'frontier.json.gz',state)
        r['frontier_profiles']=archive_json(out/'frontier-profiles.json.gz',profiles)
        r['learning']=archive_json(out/'learning.json.gz',learning_selection(h,routes,Counter()))
        r['diagnostics_seconds']=time.perf_counter()-tick
        r['global_historical_cache']=checked_inventory(h)[1]
        tick=time.perf_counter();expanded=expand(h,plan,plan['roots'],routes,Counter())
        r['expanded_certificate']=archive_json(out/'expanded-coverage.json.gz',expanded)
        r['proof_expansion_seconds']=time.perf_counter()-tick
        print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],kinds=r['new_node_kinds'],
            remaining=[[x['variables'],x['clauses']] for x in profiles],pending=len(state['pending']))),flush=True)
        ep=parent['reference'];assert sha(ep['path'])==ep['sha256']
        unpack(ep['path'],tmp/'reference',ep['database_sha256']);shutil.copyfile(tmp/'reference',tmp/'reference-seed')
        probes=[dict(kind=item['kind'],id=item['id']) for item in new_probes(deltas[0])]
        r['reference']=reference(h,routes,probes,r,out,tmp)
        r['reference']['preserved_nodes']=preserved_reference(tmp/'reference-seed',tmp/'reference')
        h.close()
        tick=time.perf_counter();h=BudgetedInventory(merged,**r['options']);h.set_admission_budget(0)
        replay_counts=Counter();verify_positive(h,expanded,plan['roots'],evidence,replay_counts)
        r['cold_positive_seconds']=time.perf_counter()-tick;r['cold_positive_counts']=dict(replay_counts)
        r['cold_positive_historical_cache']=checked_inventory(h)[1];assert not h.admitted;h.close()
        assert sha(merged)==before
    r['pipeline_seconds']=time.perf_counter()-pipeline
    (out/'report.json').write_text(encode(r)+'\n')
    print(json.dumps(dict(closed=sum(r['final_closed']),gains=r['gains'],seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path);p.add_argument('--parent',type=Path,default=BASE)
    a=p.parse_args();run(a.output,a.parent)
