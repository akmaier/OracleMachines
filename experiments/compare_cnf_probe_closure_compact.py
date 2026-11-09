#!/usr/bin/env python3
"""Supplement the frozen matched study with compact policy metadata only."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import random
import shutil
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
from experiments.cnf_probe_closure_compact import CompactProbeClosureInventory
from experiments.cnf_fused_conditioning import FusedShortestClauseInventory
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_probe_learning import MODES as PREVIOUS_MODES
from experiments.compare_cnf_fused_conditioning import root_lift as previous_root_lift
from experiments.compare_cnf_pattern_inventory import audit, memory_profile
from solver.test_cnf_fused_conditioning import check_fused_tree
from solver.test_cnf_pattern_inventory import assignments

MODES = dict(compact=(CompactProbeClosureInventory, dict(max_depth=2, probe_limit=4, learn_limit=4)))


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
    previous=Path('experiments/results/cnf-probe-closure-reuse');input_report=previous/'report.json'
    prior=json.loads(input_report.read_text())
    cases=prior['cases']
    expected=[any(holds(c['source'],a) for a in assignments(c['source']))
              if len({abs(l) for clause in c['source'] for l in clause})<=8 else None for c in cases]
    # Frozen comparison rows retain their original timings; do not relabel them as new samples.
    for name, digest in prior['fingerprints'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==digest, name
    records=list(prior['records']);archives=list(prior['archives'])
    for entry in archives:
        raw=gzip.decompress((previous/entry['path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest()==entry['database_sha256']
        shutil.copyfile(previous/entry['path'],out/entry['path'])
    answers=[r['answer'] for r in records if r['mode']=='baseline']
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
    profiles=prior['allocation_profiles']+[dict(mode=mode,**memory_profile([cases[i] for i in allocation_indices],options,cls))
              for mode,(cls,options) in MODES.items()]
    prior_checks=prior['prior_archive_checks']
    files=list(dict.fromkeys([Path(__file__),Path('experiments/cnf_probe_closure_compact.py'),
        Path('solver/test_cnf_probe_closure_compact.py')]+[Path(p) for p in prior['fingerprints']]))
    report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        fingerprints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        input_report_sha256=hashlib.sha256(input_report.read_bytes()).hexdigest(),
        cases=cases,original_case_count=len(prior['cases']),records=records,archives=archives,
        allocation_profiles=profiles,allocation_case_indices=allocation_indices,prior_archive_checks=prior_checks,
        modes=dict(prior['modes'],**{mode:dict(inventory=cls.__name__,options=options) for mode,(cls,options) in MODES.items()}),
        reference_report=str(input_report), inherited_modes=list(prior['modes']),
        limitations=['Single sequential samples; synthetic workloads; not a significance estimate or industrial comparison',
          'Existing independent decision solver unchanged; discovery coverage is not a SAT answer',
          'All operation times charge recognition, checking, serialization, persistence, solving and successful root lifts',
          'Generation, truth tables, summary walks, compression and initialization excluded from operation times',
          'Cold replay checks every alternative and source plus every ordinary solver certificate',
          'Same 1209 inputs as the frozen reference; no new cases or changed probe budgets',
          'Probe limits bound candidate variables per eligible residual, not global work or total forced rewrites',
          'Binary incidence ranking; no-conflict means inconclusive, not satisfiable or no forced values',
          'Earlier probe priorities preserved; up to four clauses learned from saved original-source reasons',
          'One bounded continuation probe pass; a child requires strict support decrease, otherwise retain the failed attempt',
          'Repeated continuation proofs reference original traces only after source validation and an inactive-batch delta check',
          'Subset Python allocation diagnostic excludes native SQLite memory, RSS and full-corpus peak',
          'Only the compact mode is newly measured here; prior mode records and archived failures are inherited verbatim'])
    (out/'report.json').write_text(json.dumps(report,separators=(',',':'))+'\n')
    summary=[];paired={(r['mode'],r['case']):r for r in records}
    for mode in report['modes']:
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
