#!/usr/bin/env python3
"""Observe exact ordered subset-search repetition without changing results."""
from collections import Counter, OrderedDict
import gzip
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import experiments.cnf_implied_subsumption as subset
from experiments.cnf_additive_elimination import AdditiveEliminationInventory
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_retained_plans import sha


def main(out):
    out.mkdir(exist_ok=False)
    path=Path('experiments/results/cnf-additive-elimination-originals/report.json'); report=json.loads(path.read_text())
    mode=next(r for r in report['results'] if r['mode']=='add_two'); case=73
    sources={}; calls=[]; old=subset.indexed_certificate; elapsed=0
    def observed(cnf,counts,*,phase='discovery'):
        nonlocal elapsed
        key=encode(cnf); index=sources.setdefault(key,len(sources)); started=time.perf_counter()
        result=old(cnf,counts,phase=phase); seconds=time.perf_counter()-started; elapsed+=seconds
        calls.append(dict(source=index,phase=phase,seconds=seconds,certificate=result)); return result
    started=time.perf_counter()
    with tempfile.TemporaryDirectory() as tmp:
        db=Path(tmp)/'a.db'
        with gzip.open(report['seed']['path'],'rb') as src,db.open('wb') as dst: shutil.copyfileobj(src,dst)
        assert sha(db)==report['seed']['database_sha256']
        h=AdditiveEliminationInventory(db,**mode['configuration'])
        with patch.object(subset,'indexed_certificate',observed): found=h.inspect(report['cases'][case]['source'])
        h.close(); digest=sha(db)
    prior=Path('experiments/results/cnf-additive-elimination-originals/discovery-profile.json')
    profile=json.loads(prior.read_text()); assert digest==profile['database_sha256']
    stats=[]
    for slots in (0,64,256,1024):
        pools={role:OrderedDict() for role in ('proposal','check')}; totals=Counter()
        for row in calls:
            role='check' if 'check' in row['phase'] else 'proposal'; pool=pools[role]; key=row['source']
            totals[role+'_calls']+=1
            if key in pool:
                totals[role+'_hits']+=1; pool.move_to_end(key)
            elif slots:
                pool[key]=None
                if len(pool)>slots: pool.popitem(last=False); totals[role+'_evictions']+=1
        stats.append(dict(slots_per_role=slots,**totals))
    record=dict(script_sha256=sha(Path(__file__)),report_sha256=sha(path),case=case,original_case=report['cases'][case]['original_case'],
        options=mode['configuration'],summary=found['summary'],instrumented_discovery_seconds=found['seconds'],
        observed_kernel_seconds=elapsed,total_seconds=time.perf_counter()-started,source_count=len(sources),call_count=len(calls),
        phase_counts=dict(Counter(r['phase'] for r in calls)),lru_simulations=stats,
        preserved_archive=profile['archive_path'],database_sha256=digest,profile_report_sha256=sha(prior),
        limitations=['Single previously costly source, observed with additional trace overhead; no performance claim.',
        'Proposal and checking caches are simulated separately; no unchecked proposal is reused for independent checking.',
        'Ordered clauses and literal encodings are part of exact identity; no cross-edit inference.'])
    payload=dict(sources=[json.loads(k) for k in sources],calls=calls)
    trace=out/'calls.json.gz'
    with trace.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0) as dst: dst.write((encode(payload)+'\n').encode())
    record['trace_sha256']=sha(trace); (out/'report.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record))


if __name__=='__main__': main(Path(sys.argv[1]))
