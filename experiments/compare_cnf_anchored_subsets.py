#!/usr/bin/env python3
"""Matched exact subset indices; identical prior archives are referenced, not duplicated."""
import argparse
from collections import Counter
import gc
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import tracemalloc
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_anchored_subsets import AnchoredAdditiveInventory
from experiments.cnf_additive_elimination import AdditiveEliminationInventory
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_residual_dag import ResidualSolver
from experiments.cnf_accounted_residuals import AccountedResidualSolver,CENSUS
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_additive_elimination import query
from experiments.compare_cnf_retained_plans import sha,audit,check_old_rows


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--suite',choices=('remaining','originals','fresh'),required=True)
    ap.add_argument('--output',type=Path,required=True);ap.add_argument('--reverse',action='store_true');args=ap.parse_args()
    out=args.output;out.mkdir(exist_ok=False)
    input_path=Path('experiments/results/cnf-additive-elimination-'+args.suite+'/report.json');prior=json.loads(input_path.read_text())
    old=next(r for r in prior['results'] if r['mode']=='add_two');cases=prior['cases'];options=old['configuration']
    modes=dict(baseline=AdditiveEliminationInventory,anchored=AnchoredAdditiveInventory)
    if args.reverse:modes=dict(reversed(list(modes.items())))
    files=set(prior['fingerprints'])|{'experiments/cnf_anchored_subsets.py','experiments/compare_cnf_anchored_subsets.py','solver/test_cnf_anchored_subsets.py'}
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),suite=args.suite,
        prior_report_sha256=sha(input_path),prior_report=str(input_path),cases=cases,options=options,execution_order=list(modes),
        fingerprints={p:sha(p) for p in sorted(files)},results=[],limitations=[
        'One ordered matched comparison; selected prior failures and reused controls, not an untouched holdout.',
        'The same certificates, plans, answers and database bytes are required; no structural coverage change or SAT-search speedup.',
        'Archive construction remains previously paid work. Restore, clone, opening, preservation, cold audit and allocation are separate.',
        'Four-case Python allocation excludes native memory, RSS and full-history peak.'])
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp);seed=tmp/'seed.db';started=time.perf_counter()
        if prior['seed']:
            with gzip.open(prior['seed']['path'],'rb') as src,seed.open('wb') as dst:shutil.copyfileobj(src,dst)
            assert sha(seed)==prior['seed']['database_sha256']
        else:
            h=PolarityHornInventory(seed,**prior['options']);h.close();s=ResidualSolver(seed);s.close()
        report['seed_restore_seconds']=time.perf_counter()-started;report['seed_bytes']=seed.stat().st_size
        for mode,cls in modes.items():
            path=tmp/(mode+'.db');started=time.perf_counter();shutil.copyfile(seed,path);clone=time.perf_counter()-started
            gc.collect();started=time.perf_counter();h=cls(path,**options);solver=AccountedResidualSolver(path);opening=time.perf_counter()-started;rows=[]
            for i,case in enumerate(cases):
                if i%20==0:print(mode,'query',i,flush=True)
                found,row=query(h,solver,case['source']);row['case']=i;rows.append(row)
                for field in ('case','answer','profile','summary','root_sha256','root_kind','solver_metrics'):
                    assert encode(row[field])==encode(old['records'][i][field]),(mode,i,field)
            assert solver.archive_storage()==solver.db.execute(CENSUS).fetchone()
            storage=h.storage();started=time.perf_counter()
            for case in cases:
                _,row=query(h,solver,case['source'])
                assert not row['discovery_metrics'].get('inserted_nodes',0) and not row['solver_metrics'].get('expanded_nodes',0)
            warm=time.perf_counter()-started;h.close();solver.close()
            digest=sha(path);assert digest==old['database_sha256'];assert path.stat().st_size==old['database_bytes']
            started=time.perf_counter();preserved=check_old_rows(seed,path);preservation=time.perf_counter()-started
            result=dict(mode=mode,records=rows,clone_seconds=clone,opening_seconds=opening,warm_seconds=warm,storage=storage,
                database_sha256=digest,database_bytes=path.stat().st_size,archive_path=old['archive_path'],archive_sha256=old['archive_sha256'],
                old_rows_preserved=preserved,preservation_seconds=preservation)
            checkpoint=out/('checkpoint-'+mode+'.json');checkpoint.write_text(encode(result)+'\n')
            print(mode,'acquired identical archive; cold audit',flush=True)
            result['audit']=audit(path,cls,options)
            memory=tmp/('memory-'+mode+'.db');shutil.copyfile(seed,memory);gc.collect();tracemalloc.start()
            h=cls(memory,**options);solver=AccountedResidualSolver(memory)
            for case in cases[:4]:query(h,solver,case['source'])
            current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();h.close();solver.close()
            result['allocation']=dict(indices=list(range(min(4,len(cases)))),current_python_bytes=current,peak_python_bytes=peak)
            report['results'].append(result);checkpoint.write_text(encode(result)+'\n');print(mode,'verified',flush=True)
    summaries=[]
    for r in report['results']:
        rows=r['records'];metrics=Counter()
        for row in rows:metrics.update(row['discovery_metrics'])
        summaries.append(dict(mode=r['mode'],closed=sum(row['summary']['closed'] for row in rows),
            query_seconds=sum(row['total_seconds'] for row in rows),discovery_seconds=sum(row['discovery_seconds'] for row in rows),
            cold_seconds=r['audit']['seconds'],database_bytes=r['database_bytes'],peak_python_bytes=r['allocation']['peak_python_bytes'],metrics=dict(metrics)))
    (out/'report.json').write_text(encode(report)+'\n');(out/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    for mode in modes:(out/('checkpoint-'+mode+'.json')).unlink()
    print(json.dumps([{k:v for k,v in r.items() if k!='metrics'} for r in summaries]),flush=True)


if __name__=='__main__':main()
