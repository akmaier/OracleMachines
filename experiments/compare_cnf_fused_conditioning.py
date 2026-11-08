#!/usr/bin/env python3
"""Matched discovery study: exact conditioning/closure fusion versus explicit intermediates."""
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
from experiments.cnf_affine_patterns import AffinePatternInventory, AFFINE_FAMILIES
from experiments.cnf_affine_projection import ProjectionPatternInventory
from experiments.cnf_simplification import SimplifyingPatternInventory
from experiments.cnf_conditioning import ShortestClauseInventory
from experiments.cnf_fused_conditioning import FusedConditioningInventory, FusedShortestClauseInventory
from experiments.compare_cnf_conditioning import MODES as CONDITIONING_MODES
from solver.test_cnf_fused_conditioning import check_fused_tree
from experiments.compare_cnf_simplification import new_cases as simplification_cases, MODES as SIMPLIFICATION_MODES
from experiments.compare_cnf_affine_projection import new_cases as projection_cases, MODES as PROJECTION_MODES
from solver.test_cnf_simplification import check_simplified_tree
from experiments.compare_cnf_matching import domain_cnf
from experiments.compare_cnf_affine_patterns import new_cases as affine_cases, MODES as AFFINE_MODES
from solver.test_cnf_affine_projection import check_projected_tree
from experiments.cnf_pattern_inventory import PatternInventory
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_pattern_inventory import scenarios, node_summary, audit, memory_profile, MODES as OLD_MODES
from solver.test_cnf_pattern_inventory import assignments, parity, check_pointwise

MODES = dict(solver_only=(SimplifyingPatternInventory, None),
             frequency=(SimplifyingPatternInventory, dict(max_depth=2, simplify_pure=False)),
             fused_frequency=(FusedConditioningInventory, dict(max_depth=2, simplify_pure=False)),
             shortest=(ShortestClauseInventory, dict(max_depth=2, simplify_pure=False)),
             fused_shortest=(FusedShortestClauseInventory, dict(max_depth=2, simplify_pure=False)),
             combined=(SimplifyingPatternInventory, dict(max_depth=2)),
             fused_combined=(FusedConditioningInventory, dict(max_depth=2, simplify_pure=True)))


def root_lift(h, discovery, model):
    root=h._load(discovery['root']['key']);names=discovery['root']['names']
    if root['kind'] in ('project','simplify'):
        child_model={j:model[names[v-1]] for j,v in enumerate(root['edge']['names'],1)}
        h.lift(discovery['root']['key'],child_model)
    elif root['kind']=='or':
        ai=root['selected'];attempt=root['alternatives'][ai];v=attempt['variable']
        value=model[names[v-1]];edge=attempt['edges'][int(value)]
        child_model={j:model[names[x-1]] for j,x in enumerate(edge['names'],1)}
        if hasattr(h,'lift_conditioned'):
            h.lift_conditioned(discovery['root']['key'],ai,value,child_model)
        else:
            # The baseline branch has no hidden forced choices: restriction is
            # pointwise exact, and missing variables occur in satisfied clauses.
            assert holds(h._load(edge['key'])['cnf'],child_model)
            lifted={abs(l):False for c in root['cnf'] for l in c};lifted[v]=value
            lifted.update((x,child_model[j]) for j,x in enumerate(edge['names'],1))
            assert holds(root['cnf'],lifted)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=False)
    input_report=Path('experiments/results/cnf-conditioning/report.json')
    cases = json.loads(input_report.read_text())['cases']
    expected = [any(holds(c['source'], a) for a in assignments(c['source']))
                if len({abs(lit) for clause in c['source'] for lit in clause}) <= 8 else None for c in cases]
    records, archives, answers = [], [], None
    for mode, (cls, options) in MODES.items():
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'history.sqlite3'
            start = time.perf_counter();solver = ResidualSolver(path)
            h = cls(path, **options) if options is not None else None
            initialization = time.perf_counter()-start
            current_answers = []
            for i, case in enumerate(cases):
                start = time.perf_counter()
                discovery = h.inspect(case['source']) if h else None
                solved = solver.solve(case['source'])
                lift_seconds = 0
                if discovery and solved['answer']:
                    lift_start = time.perf_counter()
                    root_lift(h,discovery,solved['model'])
                    lift_seconds = time.perf_counter()-lift_start
                elapsed = time.perf_counter()-start
                current_answers.append(solved['answer'])
                assert expected[i] is None or expected[i] == solved['answer']
                assert answers is None or answers[i] == solved['answer']
                if solved['answer']:
                    assert holds(case['source'], solved['model'])
                if discovery:
                    key = discovery['root']['key']
                    if discovery['profile']['shape']['variables'] <= 8:
                        check_fused_tree(h, key)
                    discovery['dag'] = node_summary(h, key)
                    discovery['root_hash'] = hashlib.sha256(key.encode()).hexdigest()
                    del discovery['root'], discovery['source_id']
                records.append(dict(case=i, mode=mode, total_seconds=elapsed, discovery=discovery,
                                    answer=solved['answer'], solver_seconds=solved['seconds'], lifting_seconds=lift_seconds,
                                    solver_metrics=solved['metrics'], solver_nodes=solved['archive_nodes']))
            answers = current_answers
            storage = h.storage() if h else {}
            warm_seconds = 0
            if h:
                start = time.perf_counter()
                for case in cases:
                    result = h.inspect(case['source'])
                    assert result['metrics'].get('inserted_nodes', 0) == 0
                    assert result['metrics']['inserted_sources'] == 0
                warm_seconds = time.perf_counter()-start
                assert h.storage() == storage
                h.close()
            solver.close()
            raw = path.read_bytes();name = f'archive-{mode}.sqlite3.gz'
            (out/name).write_bytes(gzip.compress(raw, mtime=0))
            verified = audit(Path(tmp)/'cold.sqlite3', raw, options, cls)
            archives.append(dict(mode=mode, path=name, database_bytes=len(raw), compressed_bytes=(out/name).stat().st_size,
                                 database_sha256=hashlib.sha256(raw).hexdigest(), initialization_seconds=initialization,
                                 warm_inventory_seconds=warm_seconds, storage=storage, audit=verified))
        print(mode, 'checked', flush=True)
    selected = [c for c in cases if c.get('label') in ('overlapping_parity', 'guard_activated', 'mixed_matching')]
    profiles = [dict(mode=mode, **memory_profile(selected, options, cls)) for mode, (cls, options) in MODES.items()]
    previous = Path('experiments/results/cnf-conditioning')
    prior = json.loads((previous/'report.json').read_text())
    prior_checks = []
    for entry in prior['archives']:
        raw = gzip.decompress((previous/entry['path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == entry['database_sha256']
        with tempfile.TemporaryDirectory() as tmp:
            previous_cls, previous_options = CONDITIONING_MODES[entry['mode']]
            checked = audit(Path(tmp)/'prior.sqlite3', raw, previous_options, previous_cls)
        prior_checks.append(dict(path=str(previous/entry['path']), **checked))
    files = [Path(__file__), Path('experiments/cnf_affine_patterns.py'), Path('experiments/cnf_pattern_inventory.py'),
             Path('experiments/compare_cnf_pattern_inventory.py'), Path('experiments/cnf_residual_dag.py'),
             Path('solver/test_cnf_affine_patterns.py'), Path('solver/test_cnf_pattern_inventory.py'),
             Path('experiments/cnf_affine_projection.py'), Path('solver/test_cnf_affine_projection.py'),
             Path('experiments/compare_cnf_affine_patterns.py'), Path('experiments/compare_cnf_affine_projection.py'),
             Path('experiments/cnf_simplification.py'), Path('solver/test_cnf_simplification.py'),
             Path('experiments/cnf_conditioning.py'), Path('solver/test_cnf_conditioning.py'),
             Path('experiments/compare_cnf_simplification.py'), Path('experiments/compare_cnf_conditioning.py'),
             Path('experiments/cnf_fused_conditioning.py'),Path('solver/test_cnf_fused_conditioning.py')]
    report = dict(source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  fingerprints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  modes={mode:dict(inventory=cls.__name__, options=options) for mode, (cls, options) in MODES.items()},
                  families=AFFINE_FAMILIES, cases=cases, original_case_count=949, records=records,
                  archives=archives, allocation_profiles=profiles, allocation_case_labels=[c['label'] for c in selected],
                  prior_archive_checks=prior_checks, input_report_sha256=hashlib.sha256(input_report.read_bytes()).hexdigest(),
                  limitations=['Analysis only; same unmodified decision solver runs in every mode',
                      'Single sequential samples on synthetic/exhaustive/seeded sources, not significance estimates',
                      'Certificate coverage is exact for the normalized encoding, not all affine-equivalent encodings',
                      'Consistent affine equations plus arbitrary leftover clauses are not certified tractable',
                      'Projection is exact existential elimination; witness lifting checked, ordinary decision solver/history unchanged',
                      'Projected equations use bounded direct CNF encoding; a cap miss retains the original planner',
                      'Successful root projection/simplification and OR branch model lifts are included in operation time; exhaustive fibers are separate',
                      'Operation times include recognition, checking, serialization, persistence and solving; initialization separate',
                      'Generation, truth tables, inter-operation checks, summary walks and offline compression excluded',
                      'Cold replay audits all attempted alternatives, all sources and all ordinary solver certificates',
                      'Tracemalloc covers only six stated cases in separate reruns; excludes SQLite native memory and RSS',
                      'Both full source and compiled evidence retained; semantic compression is not physical source deletion',
                      'Unit propagation reuses the existing solver routine; standard reductions newly expose structure in the inventory',
                      'Pure absence is checked on the complete current residual, including every coupling',
                      'Scan-based discovery/checking is not claimed linear or optimal',
                      'No new Lean implementation refinement or unrestricted polynomial SAT bound',
                      'Shortest-clause polarity products are a MOMS-inspired policy, not a new tractable family',
                      'Candidate cap and branch depth match; actual work differs due to early stopping and residual reuse',
                      'All 949 sources are unchanged from the prior conditioning study; no fresh holdout is claimed',
                      'Fusion preserves whole-input recognition and component priority; intermediate profiles are reconstructed',
                      'An edge carries unit/pure reasons and composes the final child binding into parent variable IDs'])
    paired = {(r['mode'],r['case']):r for r in records}
    for old,new in (('frequency','fused_frequency'),('shortest','fused_shortest'),('combined','fused_combined')):
        for i in range(len(cases)):
            a,b=paired[old,i]['discovery'],paired[new,i]['discovery']
            assert a['profile']==b['profile'] and a['summary']==b['summary'],(old,new,i)
            assert a['metrics'].get('conditioning_candidates',0)==b['metrics'].get('conditioning_candidates',0),(old,new,i)
    report['paired_policy_checks']='Every source: identical profile, coverage summary and acquired conditioning-candidate count'
    (out/'report.json').write_text(json.dumps(report, separators=(',', ':'))+'\n')
    summary = []
    for mode in MODES:
        rows = [r for r in records if r['mode'] == mode]
        entry = dict(mode=mode, total_seconds=sum(r['total_seconds'] for r in rows),
                     original_seconds=sum(r['total_seconds'] for r in rows[:949]),
                     archive=next(a for a in archives if a['mode'] == mode))
        if mode != 'solver_only':
            entry['discovery_seconds'] = sum(r['discovery']['seconds'] for r in rows)
            entry['groups'] = {group:dict(inputs=sum(c['group'] == group for c in cases),
                closed=sum(r['discovery']['summary']['closed'] for r in rows if cases[r['case']]['group'] == group),
                unresolved_literals=sum(r['discovery']['dag']['unresolved_distinct_literals'] for r in rows if cases[r['case']]['group'] == group))
                for group in sorted({c['group'] for c in cases})}
            entry['cells'] = dict(Counter(r['discovery']['profile']['cell'] for r in rows))
            for i, case in enumerate(cases):
                if case['group'] in ('variant', 'edit_variant', 'projection_variant', 'simplification_variant'):
                    assert rows[i]['discovery']['profile']['cell'] == rows[i-1]['discovery']['profile']['cell']
        summary.append(entry)
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases), archives=len(archives))), flush=True)


if __name__ == '__main__':
    main()
