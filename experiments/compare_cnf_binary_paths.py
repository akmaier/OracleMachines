#!/usr/bin/env python3
"""Matched checked binary-path reductions with shared proof prefixes."""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import json
import random
from pathlib import Path
import subprocess
import sys
import tempfile
import time

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.cnf_binary_paths import BinaryPathInventory
from experiments.cnf_polarity_horn import PolarityHornInventory
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.cnf_pattern_inventory import encode
import experiments.compare_cnf_polarity_horn as traversal
from experiments.compare_cnf_polarity_horn import node_summary, selected_nodes, root_lift as previous_root_lift
traversal.UNARY = traversal.UNARY + ('binary_paths',)


def root_lift(h, discovery, model):
    root=h._load(discovery['root']['key'])
    if root['kind']!='binary_paths':return previous_root_lift(h,discovery,model)
    names=discovery['root']['names']
    child={i:model[names[v-1]] for i,v in enumerate(root['edge']['names'],1)}
    assert holds(root['cnf'],h.lift(discovery['root']['key'],child))
from experiments.compare_cnf_indexed_restriction import OPTIONS, cold_audit
from experiments.compare_cnf_pattern_inventory import memory_profile

MODES=dict(baseline=PolarityHornInventory,binary_paths=BinaryPathInventory)


def fresh_cases():
    """Fixed before viewing results; these sources never tune the frozen policy."""
    rng=random.Random(202611091650);cases=[]
    for n in (12,24,40):
        for sample in range(8):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),
                      2 if sample%2 and rng.random()<.15 else 3)) for _ in range(4*n)]
            names=list(range(1,n+1));rng.shuffle(names)
            mapping={v:w*rng.choice((-1,1)) for v,w in enumerate(names,1)}
            signed=[tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]
            edited=source[1:]+[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),3))]
            # A second, independently recognizable Horn component tests exact
            # AND composition alongside the newly generated hard component.
            horn=[(-(n+i),n+i+1) for i in range(1,7)]+[(n+1,)]
            for variant,cnf in (('random',source),('signed',signed),('edit',edited),('mixture',source+horn)):
                cases.append(dict(group='fresh_'+variant,n=n,seed_sample=sample,source=cnf))
    return cases


def sha(raw):return hashlib.sha256(raw).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--suite',choices=('frontier','fresh','full'),default='frontier')
    parser.add_argument('--reverse',action='store_true');args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    modes=dict(reversed(list(MODES.items()))) if args.reverse else MODES
    input_path=Path('experiments/results/cnf-polarity-horn/report.json');prior=json.loads(input_path.read_text())
    cases=([dict(group='saved_frontier',source=n['cnf'],prior_key_sha256=n['key_sha256']) for n in prior['frontiers']['polarity']]
           if args.suite=='frontier' else fresh_cases() if args.suite=='fresh' else prior['cases'])
    options=dict(OPTIONS,max_depth=1) if args.suite!='full' else OPTIONS
    previous={r['case']:r for r in prior['records'] if r['mode']=='polarity'}
    records=[];archives=[];frontiers={};answers=None
    for mode,cls in modes.items():
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
                if args.suite=='full':
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
                if 'binary_paths' in node:
                    cert=node['binary_paths'];ranking['reduction' if cert['removed'] else 'inconclusive']+=1;ranking_bytes+=len(encode(cert).encode())
            storage=h.storage();start=time.perf_counter()
            for case in cases:
                r=h.inspect(case['source']);assert r['metrics'].get('inserted_nodes',0)==0 and r['metrics']['inserted_sources']==0
            warm=time.perf_counter()-start;assert storage==h.storage();h.close();solver.close();raw=path.read_bytes()
            if mode=='baseline' and args.suite=='full':
                old=next(a for a in prior['archives'] if a['mode']=='polarity');assert sha(raw)==old['database_sha256'];dest=Path(old['path'])
            else:
                dest=out/f'archive-{mode}.sqlite3.gz';dest.write_bytes(gzip.compress(raw,mtime=0))
            audit=cold_audit(Path(tmp)/'cold.db',raw,cls,options)
            archives.append(dict(mode=mode,path=str(dest),database_bytes=len(raw),database_sha256=sha(raw),
                compressed_bytes=dest.stat().st_size,initialization_seconds=initialization,warm_seconds=warm,storage=storage,
                kinds=dict(kinds),ranking_outcomes=dict(ranking),ranking_certificate_bytes=ranking_bytes,audit=audit))
        print(mode,'checked',flush=True)
        (out/f'checkpoint-{mode}.json').write_text(json.dumps(dict(records=[r for r in records if r['mode']==mode],archive=archives[-1]),separators=(',',':'))+'\n')
    indices=[0,1,2,3] if args.suite!='full' else [858,875,907,970,1042,1061]
    allocation=[dict(mode=m,**memory_profile([cases[i] for i in indices],options,c)) for m,c in MODES.items()]
    files=list(dict.fromkeys([str(Path(__file__)),'experiments/cnf_binary_paths.py','solver/test_cnf_binary_paths.py']+list(prior['fingerprints'])))
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        input_sha256=sha(input_path.read_bytes()),fingerprints={p:sha(Path(p).read_bytes()) for p in files},
        suite=args.suite,execution_order=list(modes),cases=cases,records=records,archives=archives,frontiers=frontiers,
        allocation_case_indices=indices,allocation_profiles=allocation,modes={m:dict(inventory=c.__name__,options=options) for m,c in MODES.items()},
        limitations=['The same conditioning/probe/learning caps apply; the added path pass has a separately charged 64-root reachability limit',
            'Original binary clauses are retained; only wider clauses entailed by checked source-linked paths can be removed',
            'Shared proof prefixes are persisted and replayed without reachability discovery; empty proposals are inconclusive',
            'All ordinary answers and root profiles agree; bounded structural coverage gains and losses are both retained',
            'Fresh seed fixed before results; fresh cases are synthetic signed, edited and disjoint-mixture controls',
            'Frontier suite adds one split to each of 106 saved leaves in both modes; not original-source coverage',
            'Total includes discovery, checking, serialization, persistence, ordinary solving and root lifts',
            'Loading, summaries, hashing, compression and initialization excluded or recorded separately; warm and cold separate',
            'Allocation is a four-case diagnostic (six for full) excluding native SQLite/RSS/full-corpus peak',
            'Distinct policy keys preserve old rows but may duplicate unchanged state; no uniform SAT or least-cost guarantee'])
    paired={(r['mode'],r['case']):r for r in records}
    for i in range(len(cases)):
        a,b=(paired[m,i]['discovery'] for m in MODES)
        assert a['profile']==b['profile']
    (out/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n');summary=[]
    paired={(r['mode'],r['case']):r for r in records}
    for mode in MODES:
        rows=[r for r in records if r['mode']==mode];fs=frontiers[mode]
        summary.append(dict(mode=mode,total_seconds=sum(r['total_seconds'] for r in rows),
            discovery_seconds=sum(r['discovery']['seconds'] for r in rows),solver_seconds=sum(r['solver_seconds'] for r in rows),
            closed=sum(r['discovery']['summary']['closed'] for r in rows),
            non_tiny_closed=None if args.suite!='full' else sum(r['discovery']['summary']['closed'] for r in rows[512:]),
            gains=[r['case'] for r in rows if r['discovery']['summary']['closed'] and not paired['baseline',r['case']]['discovery']['summary']['closed']],
            losses=[r['case'] for r in rows if not r['discovery']['summary']['closed'] and paired['baseline',r['case']]['discovery']['summary']['closed']],
            frontier_leaves=len(fs),frontier_literals=sum(sum(map(len,n['cnf'])) for n in fs),
            metrics=dict(sum((Counter(r['operation_metrics']) for r in rows),Counter())),
            archive=next(a for a in archives if a['mode']==mode)))
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    for mode in MODES:(out/f'checkpoint-{mode}.json').unlink()
    print(json.dumps([{k:r[k] for k in ('mode','total_seconds','discovery_seconds','closed','gains','losses','frontier_leaves')} for r in summary]),flush=True)


if __name__=='__main__':main()
