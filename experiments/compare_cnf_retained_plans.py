#!/usr/bin/env python3
"""Charge cross-policy references against fresh acquisition on the same history."""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import tracemalloc

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_binary_paths import BinaryPathInventory
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_retained_plans import RetainedPlanInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_binary_paths import fresh_cases, root_lift
from experiments.compare_cnf_indexed_restriction import OPTIONS

MODES=dict(reacquire=BinaryPathInventory,retained=RetainedPlanInventory)


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def selected(h,root):
    seen=set();stack=[(h,root)]
    while stack:
        reader,key=stack.pop()
        if key in seen:continue
        seen.add(key);n=reader._load(key);yield key,n
        if n['kind']=='retained_plan':stack.append((h.prepared,n['reference']))
        elif n['kind']=='and':stack.extend((reader,e['key']) for e in n['edges'])
        elif n['kind']=='or':stack.extend((reader,e['key']) for e in n['alternatives'][n['selected']]['edges'])
        elif 'edge' in n:stack.append((reader,n['edge']['key']))


def check_old_rows(seed,path):
    old=sqlite3.connect(f'file:{seed}?mode=ro',uri=True);new=sqlite3.connect(f'file:{path}?mode=ro',uri=True);counts={}
    for table in ('cnf_patterns_v1','cnf_pattern_sources_v1','cnf_residual_v1'):
        count=0
        if not old.execute('SELECT 1 FROM sqlite_master WHERE name=?',(table,)).fetchone():continue
        for key,payload in old.execute(f'SELECT id,payload FROM {table}'):
            assert new.execute(f'SELECT payload FROM {table} WHERE id=?',(key,)).fetchone()==(payload,)
            count+=1
        counts[table]=count
    old.close();new.close();return counts


def audit(path,cls,options):
    before=sha(path);start=time.perf_counter();h=cls(path,**options)
    old=h.prepared if isinstance(h,RetainedPlanInventory) else PolarityHornInventory(path,**options)
    configs={encode(h.config):h,encode(old.config):old};nodes=sources=0
    for key, in h.db.execute('SELECT id FROM cnf_patterns_v1'):
        configs[encode(json.loads(key)[1])]._load(key);nodes+=1
    node_counts=dict(h.counts);old_counts=dict(old.counts)
    for key,payload in h.db.execute('SELECT id,payload FROM cnf_pattern_sources_v1'):
        saved=json.loads(payload);reader=configs[encode(saved['config'])];r=reader.inspect(saved['source'])
        assert r['source_id']==key and r['root']==saved['root']
        assert not r['metrics'].get('inserted_nodes',0) and not r['metrics']['inserted_sources'];sources+=1
    old.close();h.close();solver=ResidualSolver(path);residuals=0
    for key, in solver.db.execute('SELECT id FROM cnf_residual_v1'):
        assert solver._read(key) is not None;residuals+=1
    assert not solver.counts.get('expanded_nodes',0)
    assert solver.db.execute('PRAGMA integrity_check').fetchone()[0]=='ok';solver.close()
    assert sha(path)==before
    return dict(seconds=time.perf_counter()-start,nodes=nodes,sources=sources,residuals=residuals,
                node_metrics=node_counts,prepared_metrics=old_counts,bytes_unchanged=True)


def allocation(seed,cls,options,cases):
    with tempfile.TemporaryDirectory() as tmp:
        p=Path(tmp)/'memory.db';shutil.copyfile(seed,p);gc.collect();tracemalloc.start()
        h=cls(p,**options)
        for case in cases:h.inspect(case['source'])
        current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();h.close()
    return dict(current_python_bytes=current,peak_python_bytes=peak,cases=len(cases))


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--suite',choices=('full','fresh','empty'),default='full');ap.add_argument('--reverse',action='store_true')
    args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    input_path=Path('experiments/results/cnf-binary-paths-full/report.json');prior=json.loads(input_path.read_text())
    seed_entry=next(a for a in prior['archives'] if a['mode']=='baseline')
    cases=prior['cases'] if args.suite=='full' else fresh_cases();options=OPTIONS
    modes=dict(reversed(list(MODES.items()))) if args.reverse else MODES
    reference={(r['mode'],r['case']):r for r in prior['records']};records=[];archives=[];allocations=[]
    with tempfile.TemporaryDirectory() as tmp:
        seed=Path(tmp)/'seed.db';start=time.perf_counter()
        if args.suite=='empty':
            h=PolarityHornInventory(seed,**options);h.close();s=ResidualSolver(seed);s.close()
        else:
            with gzip.open(seed_entry['path'],'rb') as src,seed.open('wb') as dst:shutil.copyfileobj(src,dst)
            assert sha(seed)==seed_entry['database_sha256']
        seed_restore=time.perf_counter()-start;seed_bytes=seed.stat().st_size
        for mode,cls in modes.items():
            path=Path(tmp)/f'{mode}.db';start=time.perf_counter();shutil.copyfile(seed,path);clone_seconds=time.perf_counter()-start
            gc.collect();start=time.perf_counter();h=cls(path,**options);solver=ResidualSolver(path);init=time.perf_counter()-start
            initial=h.storage();leaves={}
            for i,case in enumerate(cases):
                if i%200==0:print(mode,'case',i,flush=True)
                start=time.perf_counter();r=h.inspect(case['source']);solved=solver.solve(case['source'])
                root=h._load(r['root']['key'])
                if solved['answer']:
                    assert holds(case['source'],solved['model'])
                    if root['kind']=='retained_plan':
                        local={j:solved['model'][v] for j,v in enumerate(r['root']['names'],1)}
                        assert holds(root['cnf'],h.lift(r['root']['key'],local))
                    else:root_lift(h,r,solved['model'])
                elapsed=time.perf_counter()-start
                if args.suite=='full':
                    assert solved['answer']==reference['baseline',i]['answer']
                    assert encode(r['profile'])==encode(reference['baseline',i]['discovery']['profile'])
                    if mode=='reacquire':assert r['summary']==reference['binary_paths',i]['discovery']['summary']
                    if mode=='retained' and reference['baseline',i]['discovery']['summary']['closed']:assert r['summary']['closed']
                for k,n in selected(h,r['root']['key']):
                    if n['kind']=='unresolved':leaves[k]=n
                root_hash=hashlib.sha256(r['root']['key'].encode()).hexdigest();del r['root'],r['source_id']
                records.append(dict(mode=mode,case=i,total_seconds=elapsed,discovery=r,root_hash=root_hash,
                                    root_kind=root['kind'],answer=solved['answer'],solver_seconds=solved['seconds']))
            storage=h.storage();start=time.perf_counter()
            for case in cases:
                r=h.inspect(case['source']);assert not r['metrics'].get('inserted_nodes',0) and not r['metrics']['inserted_sources']
            warm=time.perf_counter()-start;assert storage==h.storage();h.close();solver.close()
            preserved=check_old_rows(seed,path);raw_hash=sha(path);dbbytes=path.stat().st_size
            checked=audit(path,cls,options);dest=out/f'archive-{mode}.sqlite3.gz'
            with path.open('rb') as src,dest.open('wb') as raw:
                with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as dst:shutil.copyfileobj(src,dst)
            archive=dict(mode=mode,path=str(dest),database_bytes=dbbytes,database_sha256=raw_hash,
                seed_bytes=seed_bytes,added_database_bytes=dbbytes-seed_bytes,storage=storage,
                added_storage={k:storage[k]-initial[k] for k in storage},initial_storage=initial,
                clone_seconds=clone_seconds,initialization_seconds=init,warm_seconds=warm,
                old_rows_preserved=preserved,audit=checked,frontier_leaves=len(leaves),
                frontier_literals=sum(sum(map(len,n['cnf'])) for n in leaves.values()))
            archives.append(archive)
            indices=[858,875,907,970,1042,1061] if args.suite=='full' else [0,1,2,3]
            allocations.append(dict(mode=mode,indices=indices,**allocation(seed,cls,options,[cases[i] for i in indices])))
            (out/f'checkpoint-{mode}.json').write_text(json.dumps(dict(records=[r for r in records if r['mode']==mode],archive=archive),separators=(',',':'))+'\n')
            print(mode,'audited',flush=True)
    paired={(r['mode'],r['case']):r for r in records};summary=[]
    for i in range(len(cases)):
        a,b=(paired[m,i] for m in MODES);assert a['answer']==b['answer'] and a['discovery']['profile']==b['discovery']['profile']
        if args.suite=='empty':assert a['discovery']['summary']==b['discovery']['summary']
    for mode in modes:
        rows=[r for r in records if r['mode']==mode]
        summary.append(dict(mode=mode,closed=sum(r['discovery']['summary']['closed'] for r in rows),
            non_tiny_closed=None if args.suite!='full' else sum(r['discovery']['summary']['closed'] for r in rows[512:]),
            discovery_seconds=sum(r['discovery']['seconds'] for r in rows),total_seconds=sum(r['total_seconds'] for r in rows),
            solver_seconds=sum(r['solver_seconds'] for r in rows),
            gains=[r['case'] for r in rows if r['discovery']['summary']['closed'] and not paired['reacquire',r['case']]['discovery']['summary']['closed']],
            losses=[r['case'] for r in rows if not r['discovery']['summary']['closed'] and paired['reacquire',r['case']]['discovery']['summary']['closed']],
            metrics=dict(sum((Counter(r['discovery']['metrics']) for r in rows),Counter())),
            prepared_metrics=dict(sum((Counter(r['discovery'].get('prepared_metrics',{})) for r in rows),Counter())),
            root_kinds=dict(Counter(r['root_kind'] for r in rows)),archive=next(a for a in archives if a['mode']==mode)))
    files=list(dict.fromkeys([str(Path(__file__)),'experiments/cnf_retained_plans.py','solver/test_cnf_retained_plans.py']+list(prior['fingerprints'])))
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        input_report_sha256=sha(input_path),suite=args.suite,options=options,execution_order=list(modes),
        seed=None if args.suite=='empty' else seed_entry,seed_restore_seconds=seed_restore,
        fingerprints={p:sha(p) for p in files},cases=cases,records=records,archives=archives,allocations=allocations,
        limitations=['Seed is already-acquired history; its original acquisition and retained bytes remain liabilities, not free preprocessing',
         'Both modes start from identical cold cloned history, with empty checker caches; total charges lookup, validation, acquisition, persistence, solver and root lifts',
         'Only exact normalized CNF, same depth and fixed old policy are referenced. General semantic equivalence and arbitrary policy transport remain absent',
         'Closed means certified structural coverage, not a SAT answer. Ordinary solver remains unchanged',
         'Every seed row is checked unchanged; cold audit verifies both policies and solver evidence, including all old failed alternatives',
         'Summary walks, row-preservation audits, hashing, compression, seed restoration, cloning, initialization, cold and warm replay are excluded from acquisition or separately reported',
         'Python allocation is a small-case diagnostic excluding native SQLite, RSS and full-history peak',
         'New references store source/profile/key copies; old graph and unchecked alternatives are still retained',
         'Single synthetic comparison per suite, not a significance estimate or uniform SAT bound'])
    (out/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    for mode in modes:(out/f'checkpoint-{mode}.json').unlink()
    print(json.dumps([{k:s[k] for k in ('mode','closed','non_tiny_closed','discovery_seconds','total_seconds','gains','losses')} for s in summary]),flush=True)


if __name__=='__main__':main()
