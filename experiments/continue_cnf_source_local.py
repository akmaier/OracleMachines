#!/usr/bin/env python3
"""Advance one ordinary frontier block with exact lazy history access.

Compare the old eager route preparation/full copy against a source-local working
store. Both use the same already reconstructed authoritative parent and unchanged
recognizer. First restoration, delta merge and cold checking are charged outside
the matched worker timings, never claimed to disappear.
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

from experiments.cnf_coupled_pivots import BudgetedInventory
from experiments.cnf_expanded_coverage import checked_inventory
from experiments.cnf_source_local import local_inventory,SourceProbeRoutes,advance_one,check_delta
from experiments.cnf_probe_continuation import ContinuationRoutes
from experiments.cnf_probe_window import choices
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_trace_reuse import archive_json,read_archive
from experiments.compare_cnf_probe_continuation import (
    sha,sha_key,digests,apply_delta,unpack,export_delta,compressed)

PARENT=Path('experiments/results/cnf-reused-branch/report.json')
FORMAT='source-local-ordinary-frontier-v1'
FILES=['experiments/cnf_source_local.py','experiments/continue_cnf_source_local.py',
       'solver/test_cnf_source_local.py']


def worker(mode,authority,claim,delta):
    started=time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'work'
        def execute(h,routes):
            h.set_admission_budget(claim['state_limit']); counts=Counter()
            prepared=time.perf_counter()
            result=advance_one(h,routes,claim['source'],counts)
            acquired=time.perf_counter()
            return dict(result=result,preparation_seconds=prepared-started,
                advance_seconds=acquired-prepared,counts=dict(counts),route_counts=dict(routes.counts),
                admitted=sorted(h.admitted),admission_counts=dict(h.admission_counts),
                historical=checked_inventory(h)[1])
        if mode=='eager':
            shutil.copyfile(authority,path)
            h=BudgetedInventory(path,**claim['options'])
            try: result=execute(h,ContinuationRoutes(h))
            finally: h.close()
            tick=time.perf_counter(); _,added=export_delta(authority,path,delta)
        else:
            with local_inventory(authority,path,claim['options']) as (h,store):
                result=execute(h,SourceProbeRoutes(h,claim['source']))
                tick=time.perf_counter(); added=store.export_delta(delta)
                result['read_through_counts']=dict(store.counts)
        result['export_seconds']=time.perf_counter()-tick
        result['delta_rows']=added;result['working_database_bytes']=path.stat().st_size
        result['delta_sha256']=sha(delta);result['delta_database_bytes']=delta.stat().st_size
    result['operation_seconds']=time.perf_counter()-started
    return result


def restore_checkpoint(report_path,path,tmp):
    """Restore the complete parent and apply this checked ordinary-probe delta."""
    from experiments.continue_cnf_reused_branch import restore_checkpoint as restore_parent
    r=json.loads(Path(report_path).read_text())
    if r['format']!=FORMAT or sha(r['parent']['path'])!=r['parent']['sha256']:
        raise ValueError('Changed source-local checkpoint parent')
    for name,digest in r['fingerprints'].items():
        if sha(name)!=digest: raise ValueError('Changed source-local implementation')
    parent,*evidence=restore_parent(r['parent']['path'],path,tmp)
    if r['options']!=parent['options'] or r['cases']!=parent['cases']:
        raise ValueError('Changed source-local configuration or claims')
    if digests(path)!=r['seed_table_digests']: raise ValueError('Incorrect authoritative parent')
    d=r['delta']; delta=tmp/'source-local-delta'
    if sha(d['path'])!=d['sha256']: raise ValueError('Changed source-local delta')
    unpack(d['path'],delta,d['database_sha256'])
    from experiments.compare_cnf_probe_continuation import TABLES
    db=sqlite3.connect(delta)
    try:
        sizes={table:db.execute(f'SELECT count(*) FROM {table}').fetchone()[0] for table in TABLES}
        if sum(sizes.values())!=1 or sizes['cnf_probe_windows_v1']!=1:
            raise ValueError('Expected exactly one ordinary window in this checkpoint')
        record=json.loads(db.execute('SELECT payload FROM cnf_probe_windows_v1').fetchone()[0])
        if record['probing']['status']!='clear' or record['edge'] is not None:
            raise ValueError('Checkpoint adds a route and requires global recomposition')
    finally: db.close()
    apply_delta(path,delta)
    check_delta(path,delta,r['options'])
    if digests(path)!=r['logical_table_digests']: raise ValueError('Incorrect source-local reconstruction')
    # This checkpoint adds one clear block, hence adds no external closure edge.
    if r['final_closed']!=parent['final_closed']: raise ValueError('Unexpected coverage claim')
    return r,*evidence


def run(out):
    from experiments.continue_cnf_reused_branch import restore_checkpoint as restore_parent
    started=time.perf_counter();out.mkdir(exist_ok=False)
    r=dict(format=FORMAT,parent=dict(path=str(PARENT),sha256=sha(PARENT)),
        source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={name:sha(name) for name in FILES},limitations=[
            'One preselected open source from 83 reused development inputs; frontier selection is reused, not rediscovered.',
            'Only ordinary probe continuation is integrated; no complete route catalog, global scheduling, or independent holdout.',
            'The full authoritative archive remains required and read-only; local missing rows always consult it.',
            'First restoration and merge/cold checking remain charged separately; worker comparison starts with the same reconstructed authority.',
            'Eager control builds its historical route catalog and copies full SQLite; local mode checks only needed premises and exports only novel rows.',
            'Two reversed-order fresh-process samples share OS caches; no confidence interval or peak-RAM measurement.',
            'A state admission bound does not bound runtime, memory or cumulative work. No unrestricted SAT construction bound.',
            'The unchanged recognizer/checker is used, not the positive-only checker or its weaker validation caches.'])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);authority=tmp/'authority';tick=time.perf_counter()
        parent,*evidence=restore_parent(PARENT,authority,tmp)
        r['restore_seconds']=time.perf_counter()-tick
        r['seed_table_digests']=digests(authority);before=sha(authority)
        r.update(options=parent['options'],cases=parent['cases'],reference=parent['reference'],
            baseline_closed=parent['final_closed'],final_closed=parent['final_closed'],gains=[],
            authority_database_bytes=authority.stat().st_size,evidence_counts=[len(x) for x in evidence])
        profile_path=PARENT.parent/'frontier-profiles.json.gz'
        import gzip
        profile=json.loads(gzip.decompress(profile_path.read_bytes()))[0]
        claim=dict(source=profile['source'],source_sha256=sha_key(profile['source']),
            options=r['options'],state_limit=32)
        if claim['source_sha256']!='a38c8326bbc493edae23be08aa73a85b288d74cf5a80dde578d126891e21ae92':
            raise ValueError('Changed retained frontier selection')
        r['selection']=dict(path=str(profile_path),sha256=sha(profile_path),source_sha256=claim['source_sha256'])
        claim_path=out/'claim.json';claim_path.write_text(encode(claim)+'\n')
        r['claim']=dict(path=str(claim_path),sha256=sha(claim_path))
        samples=[];deltas=[]
        for repeat,order in enumerate((('eager','local'),('local','eager'))):
            for mode in order:
                delta=tmp/f'{mode}-{repeat}.sqlite3';deltas.append(delta)
                print(json.dumps(dict(phase='matched expansion',mode=mode,repeat=repeat)),flush=True)
                tick=time.perf_counter()
                command=[sys.executable,str(Path(__file__).resolve()),'--worker',mode,
                    '--authority',str(authority),'--claim',str(claim_path.resolve()),'--delta',str(delta)]
                process=subprocess.run(command,cwd=tmp,text=True,capture_output=True)
                elapsed=time.perf_counter()-tick
                if process.returncode:
                    (out/f'failed-{mode}-{repeat}.txt').write_text(process.stdout+process.stderr)
                    raise RuntimeError('Failed worker; output preserved')
                sample=json.loads(process.stdout);sample.update(mode=mode,repeat=repeat,process_seconds=elapsed)
                samples.append(sample)
                print(json.dumps({key:sample[key] for key in ('mode','preparation_seconds','advance_seconds',
                    'export_seconds','process_seconds','working_database_bytes','delta_rows')}),flush=True)
        first=samples[0]
        for sample in samples:
            for key in ('result','admitted','counts','delta_rows','delta_sha256'):
                if sample[key]!=first[key]: raise ValueError('Matched operation differs: '+key)
        record=first['result']['record']
        # Keep this checkpoint narrowly specified: no implied new coverage.
        if (record['probing']['status']!='clear' or record['edge'] is not None or first['admitted'] or
                sum(first['delta_rows'].values())!=1 or first['delta_rows']['cnf_probe_windows_v1']!=1):
            raise ValueError('Unexpected frontier outcome; needs a broader checkpoint audit')
        r['samples']=samples;r['new_probe_variables']=sorted({a['variable'] for a in record['probing']['attempts']})
        r['summary']={mode:{key:sum(s[key] for s in samples if s['mode']==mode)/2 for key in
            ('preparation_seconds','advance_seconds','export_seconds','operation_seconds','process_seconds','working_database_bytes')}
            for mode in ('eager','local')}
        tick=time.perf_counter();delta_path=out/'proof-delta.sqlite3.gz';compressed(deltas[0],delta_path)
        r['delta']=dict(path=str(delta_path),sha256=sha(delta_path),database_sha256=sha(deltas[0]),
            bytes=delta_path.stat().st_size,database_bytes=deltas[0].stat().st_size)
        r['compression_seconds']=time.perf_counter()-tick
        tick=time.perf_counter();merged=tmp/'merged';shutil.copyfile(authority,merged);apply_delta(merged,deltas[0])
        r['merge_seconds']=time.perf_counter()-tick
        tick=time.perf_counter();r['cold_delta_check']=check_delta(merged,deltas[0],r['options'])
        r['cold_delta_check_seconds']=time.perf_counter()-tick
        r['logical_table_digests']=digests(merged);r['expanded_database_bytes']=merged.stat().st_size
        merged_sha=sha(merged);apply_delta(merged,deltas[0]);assert sha(merged)==merged_sha
        assert sha(authority)==before and digests(authority)==r['seed_table_digests']
        r['history_unchanged']=True;r['idempotent_merge']=True
        # Reopen independently and replay only saved evidence. Do not acquire
        # the following block during the resume check.
        with local_inventory(merged,tmp/'cold-local',r['options']) as (h,store):
            h.set_admission_budget(0);routes=SourceProbeRoutes(h,claim['source'])
            saved=routes.windows[encode([claim['source'],4])]
            assert saved==record
            _,ranked=choices(h,claim['source'],64,Counter())
            r['next_ordinary_variables']=ranked[len(record['probing']['attempts'])//2:][:4]
            r['resume_read_counts']=dict(store.counts)
            assert not any(store.export_delta(tmp/'empty-delta').values())
        r['result']=archive_json(out/'result.json.gz',first['result'])
    r['pipeline_seconds']=time.perf_counter()-started
    (out/'report.json').write_text(json.dumps(r,sort_keys=True,indent=2)+'\n')
    print(json.dumps(dict(summary=r['summary'],next_variables=r['next_ordinary_variables'],
        pipeline_seconds=r['pipeline_seconds'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('output',type=Path,nargs='?')
    p.add_argument('--worker',choices=('eager','local'));p.add_argument('--authority',type=Path)
    p.add_argument('--claim',type=Path);p.add_argument('--delta',type=Path)
    a=p.parse_args()
    if a.worker: print(json.dumps(worker(a.worker,a.authority,json.loads(a.claim.read_text()),a.delta)))
    else: run(a.output)
