#!/usr/bin/env python3
"""Recover full-study finalization from completed, cold-audited checkpoints.

The timed acquisitions and audits are never repeated or re-estimated. Only the
separate small allocation diagnostic is repeated. The original runner is frozen.
"""
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.compare_cnf_retained_plans import MODES, OPTIONS, allocation, encode, sha


def main(out):
    if (out/'report.json').exists():raise FileExistsError(out/'report.json')
    input_path=Path('experiments/results/cnf-binary-paths-full/report.json');prior=json.loads(input_path.read_text())
    checkpoints=[json.loads((out/f'checkpoint-{m}.json').read_text()) for m in MODES]
    records=[r for c in checkpoints for r in c['records']];archives=[c['archive'] for c in checkpoints]
    for a in archives:
        digest=hashlib.sha256();size=0
        with gzip.open(a['path'],'rb') as f:
            while data:=f.read(1024*1024):digest.update(data);size+=len(data)
        assert digest.hexdigest()==a['database_sha256'] and size==a['database_bytes'] and a['audit']['bytes_unchanged']
    paired={(r['mode'],r['case']):r for r in records};reference={(r['mode'],r['case']):r for r in prior['records']}
    for i in range(len(prior['cases'])):
        a,b=(paired[m,i] for m in MODES)
        assert a['answer']==b['answer']==reference['baseline',i]['answer']
        assert encode(a['discovery']['profile'])==encode(b['discovery']['profile'])==encode(reference['baseline',i]['discovery']['profile'])
        assert a['discovery']['summary']==reference['binary_paths',i]['discovery']['summary']
        if reference['baseline',i]['discovery']['summary']['closed']:assert b['discovery']['summary']['closed']
    seed_entry=next(a for a in prior['archives'] if a['mode']=='baseline');allocations=[];indices=[858,875,907,970,1042,1061]
    with tempfile.TemporaryDirectory() as tmp:
        seed=Path(tmp)/'seed.db';start=time.perf_counter()
        with gzip.open(seed_entry['path'],'rb') as src,seed.open('wb') as dst:shutil.copyfileobj(src,dst)
        repeat_restore=time.perf_counter()-start;assert sha(seed)==seed_entry['database_sha256']
        for mode,cls in MODES.items():
            allocations.append(dict(mode=mode,indices=indices,**allocation(seed,cls,OPTIONS,[prior['cases'][i] for i in indices])))
    summary=[]
    for mode in MODES:
        rows=[r for r in records if r['mode']==mode]
        summary.append(dict(mode=mode,closed=sum(r['discovery']['summary']['closed'] for r in rows),
            non_tiny_closed=sum(r['discovery']['summary']['closed'] for r in rows[512:]),
            discovery_seconds=sum(r['discovery']['seconds'] for r in rows),total_seconds=sum(r['total_seconds'] for r in rows),
            solver_seconds=sum(r['solver_seconds'] for r in rows),
            gains=[r['case'] for r in rows if r['discovery']['summary']['closed'] and not paired['reacquire',r['case']]['discovery']['summary']['closed']],
            losses=[r['case'] for r in rows if not r['discovery']['summary']['closed'] and paired['reacquire',r['case']]['discovery']['summary']['closed']],
            metrics=dict(sum((Counter(r['discovery']['metrics']) for r in rows),Counter())),
            prepared_metrics=dict(sum((Counter(r['discovery'].get('prepared_metrics',{})) for r in rows),Counter())),
            root_kinds=dict(Counter(r['root_kind'] for r in rows)),archive=next(a for a in archives if a['mode']==mode)))
    runner='experiments/compare_cnf_retained_plans.py';frozen=out/'benchmark-at-acquisition.py.txt'
    files=list(dict.fromkeys([runner,'experiments/cnf_retained_plans.py','solver/test_cnf_retained_plans.py']+list(prior['fingerprints'])))
    fingerprints={p:sha(p) for p in files};fingerprints[runner]=sha(frozen)
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        input_report_sha256=sha(input_path),suite='full',options=OPTIONS,execution_order=list(MODES),seed=seed_entry,
        seed_restore_seconds=None,allocation_seed_restore_repeat_seconds=repeat_restore,
        fingerprints=fingerprints,finalization_fingerprints={runner:sha(runner),str(Path(__file__)):sha(__file__)},
        cases=prior['cases'],records=records,archives=archives,allocations=allocations,
        limitations=['Finalization recovered from complete saved acquisitions and byte-preserving cold audits after tuple/list equality failed. All canonical profiles and answers agree.',
         'Timed runner fingerprint resolves to benchmark-at-acquisition.py.txt. Only final profile comparison changes in the current runner; runtime and certificate code are unchanged.',
         'Original initial restore timer was not checkpointed and is null, not estimated. The allocation-only repeat restore is separately measured.',
         'Seed is already-acquired history. Its acquisition and 417370112 bytes remain liabilities; this is not a from-scratch comparison.',
         'Total includes all lookup, verification, discovery, persistence, ordinary solving and model checks. The ordinary solve timer includes a full storage census on each query.',
         'Cloning, initialization, summary walks, preservation scans, compression, cold/warm replay and allocation diagnostics are excluded or separate.',
         'Every seed row and all failed alternatives remain retained. Cold audits check both policies and ordinary solver evidence without changing bytes.',
         'References require exact normalized source, depth and fixed policy; no arbitrary semantic transport or late upgrade of cached misses.',
         'Allocation is a repeated six-case Python diagnostic, not RSS/native SQLite/full-history peak. One synthetic comparison is not a significance estimate or uniform SAT bound.'])
    (out/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    for mode in MODES:
        (out/f'checkpoint-{mode}.json').unlink();(out/f'acquisition-{mode}.json').unlink()
    print(json.dumps([{k:s[k] for k in ('mode','non_tiny_closed','discovery_seconds','total_seconds','gains','losses')} for s in summary]),flush=True)


if __name__=='__main__':main(Path(sys.argv[1]))
