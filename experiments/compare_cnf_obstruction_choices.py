#!/usr/bin/env python3
"""Matched obstruction-guided conditioning, retaining gains and regressions."""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_obstruction_choices import ObstructionChoicesInventory
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_pattern_inventory import encode
from experiments.compare_cnf_polarity_horn import node_summary, selected_nodes, root_lift
from experiments.compare_cnf_indexed_restriction import OPTIONS, cold_audit
from experiments.compare_cnf_pattern_inventory import memory_profile

MODES=dict(baseline=PolarityHornInventory,obstruction=ObstructionChoicesInventory)


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--frontier',action='store_true');args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    input_path=Path('experiments/results/cnf-polarity-horn/report.json');prior=json.loads(input_path.read_text())
    cases=([dict(group='saved_frontier',source=n['cnf'],prior_key_sha256=n['key_sha256']) for n in prior['frontiers']['polarity']]
           if args.frontier else prior['cases'])
    options=dict(OPTIONS,max_depth=1) if args.frontier else OPTIONS
    previous={r['case']:r for r in prior['records'] if r['mode']=='polarity'}
    records=[];archives=[];frontiers={};answers=None
    for mode,cls in MODES.items():
        gc.collect()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.db';start=time.perf_counter();solver=ResidualSolver(path);h=cls(path,**options)
            initialization=time.perf_counter()-start;current=[];leaves={}
            for i,case in enumerate(cases):
                if i%100==0:print(mode,'case',i,flush=True)
                start=time.perf_counter();r=h.inspect(case['source']);solved=solver.solve(case['source'])
                if solved['answer']:root_lift(h,r,solved['model'])
                elapsed=time.perf_counter()-start;metrics=dict(h.counts);current.append(solved['answer'])
                if answers is not None:assert solved['answer']==answers[i]
                if solved['answer']:assert holds(case['source'],solved['model'])
                if not args.frontier:
                    assert solved['answer']==previous[i]['answer']
                    assert encode(r['profile'])==encode(previous[i]['discovery']['profile'])
                    if mode=='baseline':assert r['summary']==previous[i]['discovery']['summary']
                r['dag']=node_summary(h,r['root']['key'])
                for k,n in selected_nodes(h,r['root']['key']):
                    if n['kind']=='unresolved':leaves[k]=n
                r['root_hash']=sha(r['root']['key'].encode());del r['root'],r['source_id']
                records.append(dict(mode=mode,case=i,total_seconds=elapsed,discovery=r,answer=solved['answer'],
                                    solver_seconds=solved['seconds'],operation_metrics=metrics))
            answers=current;frontiers[mode]=[dict(key_sha256=sha(k.encode()),cnf=n['cnf'],polarity=n.get('polarity')) for k,n in leaves.items()]
            ranking=Counter();ranking_bytes=0;kinds=Counter()
            for payload, in h.db.execute('SELECT payload FROM cnf_patterns_v1'):
                node=json.loads(payload);kinds[node['kind']]+=1
                if 'conditioning_obstruction' in node:
                    cert=node['conditioning_obstruction'];ranking[cert['outcome']]+=1;ranking_bytes+=len(encode(cert).encode())
            storage=h.storage();start=time.perf_counter()
            for case in cases:
                r=h.inspect(case['source']);assert r['metrics'].get('inserted_nodes',0)==0 and r['metrics']['inserted_sources']==0
            warm=time.perf_counter()-start;assert storage==h.storage();h.close();solver.close();raw=path.read_bytes()
            if mode=='baseline' and not args.frontier:
                old=next(a for a in prior['archives'] if a['mode']=='polarity');assert sha(raw)==old['database_sha256'];dest=Path(old['path'])
            else:
                dest=out/f'archive-{mode}.sqlite3.gz';dest.write_bytes(gzip.compress(raw,mtime=0))
            audit=cold_audit(Path(tmp)/'cold.db',raw,cls,options)
            archives.append(dict(mode=mode,path=str(dest),database_bytes=len(raw),database_sha256=sha(raw),
                compressed_bytes=dest.stat().st_size,initialization_seconds=initialization,warm_seconds=warm,storage=storage,
                kinds=dict(kinds),ranking_outcomes=dict(ranking),ranking_certificate_bytes=ranking_bytes,audit=audit))
        print(mode,'checked',flush=True)
        (out/f'checkpoint-{mode}.json').write_text(json.dumps(dict(records=[r for r in records if r['mode']==mode],archive=archives[-1]),separators=(',',':'))+'\n')
    indices=[0,1,2,3] if args.frontier else [858,875,907,970,1042,1061]
    allocation=[dict(mode=m,**memory_profile([cases[i] for i in indices],options,c)) for m,c in MODES.items()]
    files=list(dict.fromkeys([str(Path(__file__)),'experiments/cnf_obstruction_choices.py','solver/test_cnf_obstruction_choices.py']+list(prior['fingerprints'])))
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        input_sha256=sha(input_path.read_bytes()),fingerprints={p:sha(Path(p).read_bytes()) for p in files},
        frontier_experiment=args.frontier,cases=cases,records=records,archives=archives,frontiers=frontiers,
        allocation_case_indices=indices,allocation_profiles=allocation,modes={m:dict(inventory=c.__name__,options=options) for m,c in MODES.items()},
        limitations=['Optional heuristic; fixed depth/candidate/probe/learning budgets do not guarantee identical coverage',
            'Every original-root answer and root recognition profile must agree; source coverage gains and losses are both retained',
            'Path source clauses rank candidates, never prune them or certify original SAT/UNSAT',
            'New conditioning certificates are persisted and independently replayed; checker never reruns auxiliary discovery',
            'Earlier reductions and terminal Horn renaming are unchanged; different choices can change descendants',
            'One sequential synthetic comparison; no significance, industrial or uniform-SAT claim',
            'Frontier mode gives each of 106 saved depth-exhausted leaves one additional split in both modes; not new whole-source coverage',
            'Total includes discovery, verification, serialization, persistence, ordinary solving and root lifts',
            'Loading, summaries, hashing, compression and initialization excluded or recorded separately; warm and cold replay separate',
            'Allocation diagnostic covers only recorded subset and excludes native SQLite/RSS/full-corpus peak',
            'Distinct policy keys preserve old rows but can duplicate unchanged structures across histories'])
    (out/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n');summary=[]
    paired={(r['mode'],r['case']):r for r in records}
    for mode in MODES:
        rows=[r for r in records if r['mode']==mode];fs=frontiers[mode]
        summary.append(dict(mode=mode,total_seconds=sum(r['total_seconds'] for r in rows),
            discovery_seconds=sum(r['discovery']['seconds'] for r in rows),solver_seconds=sum(r['solver_seconds'] for r in rows),
            closed=sum(r['discovery']['summary']['closed'] for r in rows),
            non_tiny_closed=None if args.frontier else sum(r['discovery']['summary']['closed'] for r in rows[512:]),
            gains=[r['case'] for r in rows if r['discovery']['summary']['closed'] and not paired['baseline',r['case']]['discovery']['summary']['closed']],
            losses=[r['case'] for r in rows if not r['discovery']['summary']['closed'] and paired['baseline',r['case']]['discovery']['summary']['closed']],
            frontier_leaves=len(fs),frontier_literals=sum(sum(map(len,n['cnf'])) for n in fs),
            metrics=dict(sum((Counter(r['operation_metrics']) for r in rows),Counter())),
            archive=next(a for a in archives if a['mode']==mode)))
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    for mode in MODES:(out/f'checkpoint-{mode}.json').unlink()
    print(json.dumps([{k:r[k] for k in ('mode','total_seconds','discovery_seconds','closed','gains','losses','frontier_leaves')} for r in summary]),flush=True)


if __name__=='__main__':main()
