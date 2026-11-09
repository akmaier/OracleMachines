#!/usr/bin/env python3
"""Matched delta-checked closure reuse with all discovery outcomes retained."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.cnf_failed_literal import FailedLiteralInventory
from experiments.cnf_common_consequence import CommonConsequenceInventory
from experiments.cnf_probe_equivalence import ProbeEquivalenceInventory
from experiments.cnf_probe_learning import ProbeLearningInventory
from experiments.cnf_probe_closure_reuse import ProbeClosureReuseInventory
from experiments.cnf_fused_conditioning import FusedShortestClauseInventory
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_probe_learning import MODES as PREVIOUS_MODES
from experiments.compare_cnf_fused_conditioning import root_lift as previous_root_lift
from experiments.compare_cnf_pattern_inventory import audit, memory_profile
from solver.test_cnf_fused_conditioning import check_fused_tree
from solver.test_cnf_pattern_inventory import assignments

MODES = dict(solver_only=(FailedLiteralInventory, None),
             baseline=(ProbeLearningInventory, dict(max_depth=2, probe_limit=4, learn_limit=4)),
             reuse=(ProbeClosureReuseInventory, dict(max_depth=2, probe_limit=4, learn_limit=4)))


def new_cases():
    rng=random.Random(20261109033545);cases=[]
    for n in (20,32,48):
        for _ in range(8):
            source=[tuple(rng.choice((-1,1))*v for v in rng.sample(range(1,n+1),3))
                    for _ in range(round(4.25*n))]
            cases.append(dict(group='reuse_holdout3',label=f'n{n}',source=source))
    fixture=[(1,2),(-2,-3),(-2,3,7),(4,-5),(4,-6),(5,6,7),(-1,-4,7)]
    for blocks in (1,2,4,8):
        source=[tuple((abs(l)+7*b)*(1 if l>0 else -1) for l in c)
                for b in range(blocks) for c in fixture]
        cases.append(dict(group='reuse_control',label=f'blocks{blocks}',source=source))
        names=list(range(1,7*blocks+1));rng.shuffle(names)
        mapping={i+1:(v*71+3)*rng.choice((-1,1)) for i,v in enumerate(names)}
        variant=[tuple(mapping[abs(l)]*(1 if l>0 else -1) for l in reversed(c)) for c in reversed(source)]
        cases.append(dict(group='reuse_transfer',label=f'blocks{blocks}',source=variant))
        changed=(source[:-1] if blocks==1 else source+[(-7,14),(7,-14)])
        cases.append(dict(group='reuse_edit',label=f'blocks{blocks}',source=changed))
    return cases


def node_summary(h, root):
    seen, stack, leaves = set(), [root], []
    while stack:
        key=stack.pop()
        if key in seen:continue
        seen.add(key);node=h._load(key)
        if node['kind']=='and':stack.extend(e['key'] for e in node['edges'])
        elif node['kind']=='or':stack.extend(e['key'] for e in node['alternatives'][node['selected']]['edges'])
        elif node['kind'] in ('project','simplify','probe'):stack.append(node['edge']['key'])
        elif node['kind']=='unresolved':leaves.append(node['profile']['shape'])
    return dict(selected_distinct_nodes=len(seen), unresolved_distinct_leaves=len(leaves),
                unresolved_distinct_literals=sum(x['literals'] for x in leaves), unresolved_shapes=leaves)


def root_lift(h, discovery, model):
    root=h._load(discovery['root']['key']);names=discovery['root']['names']
    if root['kind']=='probe':
        child={j:model[names[v-1]] for j,v in enumerate(root['edge']['names'],1)}
        h.lift(discovery['root']['key'],child)
    else:previous_root_lift(h,discovery,model)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    out=args.output;out.mkdir(parents=True,exist_ok=False)
    previous=Path('experiments/results/cnf-probe-learning');input_report=previous/'report.json'
    prior=json.loads(input_report.read_text())
    cases=prior['cases']+new_cases()
    expected=[any(holds(c['source'],a) for a in assignments(c['source']))
              if len({abs(l) for clause in c['source'] for l in clause})<=8 else None for c in cases]
    records,archives,answers=[],[],None
    for mode,(cls,options) in MODES.items():
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'history.sqlite3';start=time.perf_counter()
            solver=ResidualSolver(path);h=cls(path,**options) if options is not None else None
            initialization=time.perf_counter()-start;current_answers=[]
            for i,case in enumerate(cases):
                start=time.perf_counter();discovery=h.inspect(case['source']) if h else None
                solved=solver.solve(case['source']);lift_seconds=0
                if discovery and solved['answer']:
                    ls=time.perf_counter();root_lift(h,discovery,solved['model']);lift_seconds=time.perf_counter()-ls
                elapsed=time.perf_counter()-start;current_answers.append(solved['answer'])
                assert expected[i] is None or expected[i]==solved['answer']
                assert answers is None or answers[i]==solved['answer']
                if solved['answer']:assert holds(case['source'],solved['model'])
                if discovery:
                    key=discovery['root']['key']
                    if discovery['profile']['shape']['variables']<=8:check_fused_tree(h,key)
                    discovery['dag']=node_summary(h,key);discovery['root_hash']=hashlib.sha256(key.encode()).hexdigest()
                    del discovery['root'],discovery['source_id']
                records.append(dict(case=i,mode=mode,total_seconds=elapsed,discovery=discovery,
                    answer=solved['answer'],solver_seconds=solved['seconds'],lifting_seconds=lift_seconds,
                    solver_metrics=solved['metrics'],solver_nodes=solved['archive_nodes']))
            answers=current_answers;storage=h.storage() if h else {};warm=0
            if h:
                start=time.perf_counter()
                for case in cases:
                    result=h.inspect(case['source'])
                    assert result['metrics'].get('inserted_nodes',0)==0 and result['metrics']['inserted_sources']==0
                warm=time.perf_counter()-start;assert storage==h.storage();h.close()
            solver.close();raw=path.read_bytes();name=f'archive-{mode}.sqlite3.gz'
            (out/name).write_bytes(gzip.compress(raw,mtime=0))
            verified=audit(Path(tmp)/'cold.sqlite3',raw,options,cls)
            archives.append(dict(mode=mode,path=name,database_bytes=len(raw),compressed_bytes=(out/name).stat().st_size,
                database_sha256=hashlib.sha256(raw).hexdigest(),initialization_seconds=initialization,
                warm_inventory_seconds=warm,storage=storage,audit=verified))
        print(mode,'checked',flush=True)
    # Diagnostic allocations and prior cold checks are separate from operation timings.
    allocation_indices=[858,875,907,970,1042,1061]
    profiles=[dict(mode=mode,**memory_profile([cases[i] for i in allocation_indices],options,cls))
              for mode,(cls,options) in MODES.items()]
    prior_checks=[]
    for entry in prior['archives']:
        raw=gzip.decompress((previous/entry['path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==entry['database_sha256']
        cls,options=PREVIOUS_MODES[entry['mode']]
        with tempfile.TemporaryDirectory() as tmp:checked=audit(Path(tmp)/'prior.sqlite3',raw,options,cls)
        prior_checks.append(dict(path=str(previous/entry['path']),**checked))
    files=list(dict.fromkeys([Path(__file__),Path('experiments/cnf_probe_closure_reuse.py'),
        Path('solver/test_cnf_probe_closure_reuse.py')]+[Path(p) for p in prior['fingerprints']]))
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        input_report_sha256=hashlib.sha256(input_report.read_bytes()).hexdigest(),
        cases=cases,original_case_count=len(prior['cases']),records=records,archives=archives,
        allocation_profiles=profiles,allocation_case_indices=allocation_indices,prior_archive_checks=prior_checks,
        modes={mode:dict(inventory=cls.__name__,options=options) for mode,(cls,options) in MODES.items()},
        limitations=['Single sequential samples; synthetic workloads; not a significance estimate or industrial comparison',
          'Existing independent decision solver unchanged; discovery coverage is not a SAT answer',
          'All operation times charge recognition, checking, serialization, persistence, solving and successful root lifts',
          'Generation, truth tables, summary walks, compression and initialization excluded from operation times',
          'Cold replay checks every alternative and source plus every ordinary solver certificate',
          'Study adds 24 fresh random sources and 12 crafted/transfer/invalidation controls to all 1173 prior inputs',
          'Probe limits bound candidate variables per eligible residual, not global work or total forced rewrites',
          'Binary incidence ranking; no-conflict means inconclusive, not satisfiable or no forced values',
          'Earlier probe priorities preserved; up to four clauses learned from saved original-source reasons',
          'One bounded continuation probe pass; a child requires strict support decrease, otherwise retain the failed attempt',
          'Repeated continuation proofs reference original traces only after source validation and an inactive-batch delta check',
          'Subset Python allocation diagnostic excludes native SQLite memory, RSS and full-corpus peak',
          'Both policies have identical probe budgets; active additions and fresh assumptions still use full propagation'])
    (out/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    summary=[];paired={(r['mode'],r['case']):r for r in records}
    for mode in MODES:
        rows=[r for r in records if r['mode']==mode]
        entry=dict(mode=mode,total_seconds=sum(r['total_seconds'] for r in rows),
                   old_seconds=sum(r['total_seconds'] for r in rows[:len(prior['cases'])]),archive=next(a for a in archives if a['mode']==mode))
        if mode!='solver_only':
            entry['discovery_seconds']=sum(r['discovery']['seconds'] for r in rows)
            entry['groups']={g:dict(inputs=sum(c['group']==g for c in cases),
                closed=sum(r['discovery']['summary']['closed'] for r in rows if cases[r['case']]['group']==g),
                unresolved_literals=sum(r['discovery']['dag']['unresolved_distinct_literals'] for r in rows if cases[r['case']]['group']==g))
                for g in sorted({c['group'] for c in cases})}
            entry['metrics']=dict(sum((Counter(r['discovery']['metrics']) for r in rows),Counter()))
            entry['gains']=[i for i in range(len(cases)) if rows[i]['discovery']['summary']['closed'] and not paired['baseline',i]['discovery']['summary']['closed']]
            entry['losses']=[i for i in range(len(cases)) if not rows[i]['discovery']['summary']['closed'] and paired['baseline',i]['discovery']['summary']['closed']]
        summary.append(entry)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases),archives=len(archives))),flush=True)


if __name__=='__main__':main()
