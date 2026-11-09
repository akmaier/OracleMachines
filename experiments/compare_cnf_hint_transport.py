#!/usr/bin/env python3
"""Matched immediate-core expansion controls with portable implication evidence.

This samples learned-parent edges, not complete original-source plans. The hint
mode adds an explicit bounded pass before the unchanged core planner; it does
not silently raise the original planner's budget or claim whole-source gains.
"""
import argparse
from collections import Counter
import gc
import gzip
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time
import tracemalloc

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments.analyze_cnf_conditioning import load_nodes
from experiments.cnf_hint_transport import CoreHintStore, HintAssistedInventory, transport_hints, discover_rup, check_rup
from experiments.cnf_learning_core import CoreLearningInventory
from experiments.cnf_pattern_inventory import encode
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_pattern_inventory import audit
from experiments.compare_cnf_learning_core import node_summary, root_lift
from solver.test_cnf_pattern_inventory import assignments
from solver.test_cnf_fused_conditioning import check_fused_tree
from solver.test_cnf_learning_core import core_source, core_common_source, core_equivalence_source

OPTIONS=dict(max_depth=2,probe_limit=4,learn_limit=4)


def sha(data):return hashlib.sha256(data).hexdigest()


def fresh_cases():
    rng=random.Random(20261109064108);cases=[]
    for n in (20,32,48):
        for _ in range(8):
            cases.append(dict(group='fresh3',label=f'n{n}',source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),3))
                                                                   for _ in range(round(4.25*n))]))
    fixtures=[core_source(),core_common_source(),core_equivalence_source()]
    for blocks in (1,2,4,8):
        source=[tuple((abs(l)+8*b)*(1 if l>0 else -1) for l in c) for b in range(blocks) for c in fixtures[b%3]]
        cases.append(dict(group='control',label=f'blocks{blocks}',source=source))
        names=list(range(1,8*blocks+1));rng.shuffle(names)
        mapping={i+1:(v*43+5)*rng.choice((-1,1)) for i,v in enumerate(names)}
        cases.append(dict(group='signed',label=f'blocks{blocks}',source=[tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]))
        cases.append(dict(group='edit',label=f'blocks{blocks}',source=source[:-1] if blocks==1 else source+[(-8,16),(8,-16)]))
    return cases


def archive(out,name,raw,options,cls):
    path=out/f'archive-{name}.sqlite3.gz';path.write_bytes(gzip.compress(raw,mtime=0))
    with tempfile.TemporaryDirectory() as tmp:
        target=Path(tmp)/'cold.db'
        checked=audit(target,raw,options,cls)
        if cls is HintAssistedInventory:
            start=time.perf_counter();h=cls(target,**options);extra=h.audit_hints();h.close()
            checked['hint_seconds']=time.perf_counter()-start;checked.update(extra)
            assert target.read_bytes()==raw
    return dict(mode=name,path=path.name,database_bytes=len(raw),compressed_bytes=path.stat().st_size,
                database_sha256=sha(raw),audit=checked)


def operation(h,solver,case,mode):
    core=case['transport']['core'];depth=case['depth'];start=time.perf_counter()
    if mode=='baseline':
        h.counts=Counter();ds=time.perf_counter();edge=h._edge(core,depth);node=h._load(edge['key'])
        discovered=dict(seconds=time.perf_counter()-ds,metrics=dict(h.counts),summary=node['summary'],edge=edge)
    else:
        result=h.inspect_hints(core,case['transport']['hints'],depth);plan=result['plan'];edge=plan['edge']
        discovered=dict(seconds=result['seconds'],metrics=result['metrics'],hint_metrics=result['hint_metrics'],
                        summary=plan['summary'],plan=plan,key_sha256=sha(result['key'].encode()),edge=edge)
    solved=solver.solve(core)
    if solved['answer']:
        assert holds(core,solved['model'])
        if mode=='baseline':root_lift(h,dict(root=edge),solved['model'])
        else:
            child={j:solved['model'][v] for j,v in enumerate(edge['names'],1)}
            h.lift_hint_plan(plan,child)
    elapsed=time.perf_counter()-start
    return dict(total_seconds=elapsed,discovery=discovered,answer=solved['answer'],solver_seconds=solved['seconds'])


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
    previous=Path('experiments/results/cnf-learning-core');prior=json.loads((previous/'report.json').read_text())
    old=load_nodes(previous,next(a for a in prior['archives'] if a['mode']=='core'))
    parents={k:dict(cnf=n['cnf'],probing=n['profile']['probing'],depth=n['depth'],origin='prior')
             for k,n in old.items() if n['kind']=='probe' and n['profile']['probing']['status']=='learned'}
    original_parent_count=len(parents);fresh=fresh_cases();fresh_records=[];archives=[]
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'fresh.db';h=CoreLearningInventory(path,**OPTIONS);solver=ResidualSolver(path)
        for c in fresh:
            start=time.perf_counter();d=h.inspect(c['source']);solved=solver.solve(c['source'])
            if solved['answer']:root_lift(h,d,solved['model'])
            elapsed=time.perf_counter()-start
            if d['profile']['shape']['variables']<=8:check_fused_tree(h,d['root']['key'])
            fresh_records.append(dict(total_seconds=elapsed,summary=d['summary'],answer=solved['answer'],metrics=d['metrics']))
        for key,payload in h.db.execute('SELECT id,payload FROM cnf_patterns_v1'):
            n=json.loads(payload)
            if n['kind']=='probe' and n['profile']['probing']['status']=='learned' and key not in parents:
                parents[key]=dict(cnf=n['cnf'],probing=n['profile']['probing'],depth=n['depth'],origin='fresh')
        h.close();solver.close();raw=path.read_bytes()
        archives.append(archive(out,'fresh-inputs',raw,OPTIONS,CoreLearningInventory))
    print('fresh inputs checked',flush=True)
    cases=[];preparation_seconds=0.;preparation_counts=Counter()
    for key,p in parents.items():
        counts=Counter();start=time.perf_counter();t=transport_hints(p['cnf'],p['probing'],4,4,counts)
        elapsed=time.perf_counter()-start;preparation_seconds+=elapsed;preparation_counts.update(counts)
        if p['origin']=='prior':assert encode(t['core'])==encode(old[old[key]['edge']['key']]['cnf'])
        cases.append(dict(p,parent_sha256=sha(key.encode()),transport=t,preparation_seconds=elapsed,preparation_counts=dict(counts)))
    # Conditional fresh-search control: it is given the very same candidate
    # clauses and cores. Candidate extraction/parent checking is separately billed.
    fresh_proofs=[];proof_counts=Counter();proof_seconds=0.
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'proofs.db';store=CoreHintStore(path)
        for i,c in enumerate(cases):
            core=c['transport']['core']
            for hint in c['transport']['hints']:
                counts=Counter();start=time.perf_counter();proof=discover_rup(core,hint['clause'],counts)
                assert proof is not None;check_rup(core,hint['clause'],proof,counts);store.put(core,hint['clause'],proof)
                elapsed=time.perf_counter()-start;proof_seconds+=elapsed;proof_counts.update(counts)
                fresh_proofs.append(dict(case=i,clause=hint['clause'],proof=proof,seconds=elapsed,metrics=dict(counts)))
        storage=store.storage();store.close();raw=path.read_bytes();file=out/'archive-fresh-proofs.sqlite3.gz';file.write_bytes(gzip.compress(raw,mtime=0))
        start=time.perf_counter();store=CoreHintStore(path);n=store.audit();store.close();cold=time.perf_counter()-start;assert raw==path.read_bytes()
        archives.append(dict(mode='fresh-proofs',path=file.name,database_bytes=len(raw),compressed_bytes=file.stat().st_size,
                             database_sha256=sha(raw),storage=storage,audit=dict(hints=n,seconds=cold,bytes_unchanged=True)))
    records=[];answers=None
    for mode,cls in (('baseline',CoreLearningInventory),('hints',HintAssistedInventory)):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'plans.db';h=cls(path,**OPTIONS);solver=ResidualSolver(path);current=[]
            for i,c in enumerate(cases):
                r=operation(h,solver,c,mode);current.append(r['answer']);r.update(case=i,mode=mode)
                assert answers is None or answers[i]==r['answer']
                if len({abs(l) for cl in c['transport']['core'] for l in cl})<=8:
                    assert any(holds(c['transport']['core'],a) for a in assignments(c['transport']['core']))==r['answer']
                    check_fused_tree(h,r['discovery']['edge']['key'])
                r['discovery']['dag']=node_summary(h,r['discovery']['edge']['key'])
                records.append(r)
            answers=current;storage=h.storage();extra=h.hint_storage() if mode=='hints' else {}
            start=time.perf_counter()
            for c in cases:
                if mode=='hints':
                    w=h.inspect_hints(c['transport']['core'],c['transport']['hints'],c['depth'])
                    assert w['metrics'].get('hint_plans_inserted',0)==0 and w['hint_metrics'].get('hint_inserted',0)==0
                else:
                    h.counts=Counter();h._edge(c['transport']['core'],c['depth']);assert h.counts.get('inserted_nodes',0)==0
            warm=time.perf_counter()-start;assert storage==h.storage()
            if mode=='hints':assert extra==h.hint_storage()
            h.close();solver.close();a=archive(out,mode,path.read_bytes(),OPTIONS,cls);a.update(storage=storage,hint_storage=extra,warm_seconds=warm);archives.append(a)
        print(mode,'checked',flush=True)
    # Small matched allocation diagnostic, outside all primary timings.
    allocation_indices=sorted(range(len(cases)),key=lambda i:-sum(map(len,cases[i]['transport']['core'])))[:6]
    allocations=[]
    for mode,cls in (('baseline',CoreLearningInventory),('hints',HintAssistedInventory)):
        gc.collect()
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'memory.db';tracemalloc.start();h=cls(path,**OPTIONS);solver=ResidualSolver(path)
            for i in allocation_indices:operation(h,solver,cases[i],mode)
            gc.collect();current,peak=tracemalloc.get_traced_memory();tracemalloc.stop();h.close();solver.close()
            allocations.append(dict(mode=mode,current_traced_bytes=current,peak_traced_bytes=peak))
    paired={(r['mode'],r['case']):r for r in records};summaries=[]
    for mode in ('baseline','hints'):
        rows=[r for r in records if r['mode']==mode]
        summaries.append(dict(mode=mode,cases=len(cases),closed=sum(r['discovery']['summary']['closed'] for r in rows),
            total_seconds=sum(r['total_seconds'] for r in rows),discovery_seconds=sum(r['discovery']['seconds'] for r in rows),
            unresolved_literals=sum(r['discovery']['dag']['unresolved_distinct_literals'] for r in rows),
            gains=[r['case'] for r in rows if r['discovery']['summary']['closed'] and not paired['baseline',r['case']]['discovery']['summary']['closed']],
            losses=[r['case'] for r in rows if not r['discovery']['summary']['closed'] and paired['baseline',r['case']]['discovery']['summary']['closed']],
            metrics=dict(sum((Counter(r['discovery']['metrics']) for r in rows),Counter())),
            hint_metrics=dict(sum((Counter(r['discovery'].get('hint_metrics',{})) for r in rows),Counter()))))
    files=list(dict.fromkeys([Path(__file__),Path('experiments/cnf_hint_transport.py'),Path('solver/test_cnf_hint_transport.py'),
                             Path('formal/OracleMachines/ProofFragments.lean')]+[Path(p) for p in prior['fingerprints']]))
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={str(p):sha(p.read_bytes()) for p in files},input_report_sha256=sha((previous/'report.json').read_bytes()),
        original_parent_count=original_parent_count,fresh_cases=fresh,fresh_records=fresh_records,cases=cases,
        preparation_seconds=preparation_seconds,preparation_counts=dict(preparation_counts),fresh_proof_seconds=proof_seconds,
        fresh_proof_counts=dict(proof_counts),fresh_proofs=fresh_proofs,records=records,archives=archives,
        allocation_indices=allocation_indices,allocations=allocations,
        limitations=['Learned-parent sample; local child coverage is not original-source coverage or a complete discovery policy',
          'Explicit hint mode adds a bounded pass before the unchanged planner; budgets and whole-plan work are not equal',
          'Transport preparation includes full parent checking, index reconstruction, projection and core-only proof checking',
          'Fresh proof search is conditional on the same prepared cores and candidate clauses; not an end-to-end comparison',
          'Reported plan time excludes separately reported transport preparation and fresh-source generation; warm/cold separate',
          'Generation, archive decoding/compression, truth tables and post-run diagnostics excluded from primary operation times',
          'Single sequential synthetic samples, no industrial or statistical speed claim',
          'Six-core Python allocation diagnostic excludes preparation, native SQLite, RSS and full-corpus peak',
          'Core-only proof checking removes parent dependency but inherited hint contexts remain explicit in plan identities'])
    (out/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    (out/'summary.json').write_text(json.dumps(summaries,indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases),archives=len(archives))),flush=True)


if __name__=='__main__':main()
