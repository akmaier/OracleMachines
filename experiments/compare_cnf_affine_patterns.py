#!/usr/bin/env python3
"""Matched discovery study: direct affine extraction, exact leftover interaction."""
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
from experiments.cnf_pattern_inventory import PatternInventory
from experiments.cnf_residual_dag import ResidualSolver, holds
from experiments.compare_cnf_pattern_inventory import scenarios, node_summary, audit, memory_profile, MODES as OLD_MODES
from solver.test_cnf_pattern_inventory import assignments, parity, check_pointwise

MODES = dict(solver_only=(PatternInventory, None),
             baseline0=(PatternInventory, dict(max_depth=0)),
             affine0=(AffinePatternInventory, dict(max_depth=0)),
             baseline2=(PatternInventory, dict(max_depth=2)),
             affine2=(AffinePatternInventory, dict(max_depth=2)))


def new_cases():
    cases = []
    for n in (8, 10, 12):
        cases.append(dict(group='growing', label=f'cube_{n}',
                          source=parity(range(1, n+1), 0)+parity(range(1, n+1), 1)))
    for count in (4, 8, 16, 32):
        source = [c for i in range(count) for c in parity(range(2*i+1, 2*i+5), 1)]
        cases.append(dict(group='growing', label=f'overlap_{count}', source=source))
        cases.append(dict(group='growing', label=f'coupled_{count}', source=source+[(1, 2*count+2)]))
    rng = random.Random(202611082121)
    for _ in range(48):
        source = [tuple(rng.choice((-1, 1))*v for v in rng.sample(range(1, 7), rng.randrange(2, 5)))
                  for _ in range(rng.randrange(6, 25))]
        cases.append(dict(group='new_random', source=source))
    p = parity((1, 2, 3, 4), 1)
    edits = [('deleted_sign', p[:-1]), ('extra_sign', p+[parity((1, 2, 3, 4), 0)[0]]),
             ('redundant_wide', p+[(1, 2, 3, 4, 5)]),
             ('contradictory_core_coupled', p+parity((1, 2, 3, 4), 0)+[(1, 5, 6)]),
             ('nontrivial_dependency', parity((1, 2, 3), 0)+parity((2, 3, 4), 0)+parity((1, 4), 1))]
    for label, source in edits:
        cases.append(dict(group='edit', label=label, source=source))
        names = sorted({abs(lit) for c in source for lit in c});shuffled = names[:];rng.shuffle(shuffled)
        mapping = dict(zip(names, (v*79+5 for v in shuffled)))
        variant = [tuple(mapping[abs(lit)]*(1 if lit > 0 else -1) for lit in reversed(c)) for c in reversed(source)]
        cases.append(dict(group='edit_variant', label=label, source=variant+variant[:1]+[(9999, -9999)]))
    return cases


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    out = parser.parse_args().output
    out.mkdir(parents=True, exist_ok=False)
    cases = scenarios()+new_cases()
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
                elapsed = time.perf_counter()-start
                current_answers.append(solved['answer'])
                assert expected[i] is None or expected[i] == solved['answer']
                assert answers is None or answers[i] == solved['answer']
                if solved['answer']:
                    assert holds(case['source'], solved['model'])
                if discovery:
                    key = discovery['root']['key']
                    if discovery['profile']['shape']['variables'] <= 8:
                        check_pointwise(h, key)
                    discovery['dag'] = node_summary(h, key)
                    discovery['root_hash'] = hashlib.sha256(key.encode()).hexdigest()
                    del discovery['root'], discovery['source_id']
                records.append(dict(case=i, mode=mode, total_seconds=elapsed, discovery=discovery,
                                    answer=solved['answer'], solver_seconds=solved['seconds'],
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
    previous = Path('experiments/results/cnf-pattern-inventory')
    prior = json.loads((previous/'report.json').read_text())
    prior_checks = []
    for entry in prior['archives']:
        raw = gzip.decompress((previous/entry['path']).read_bytes())
        assert hashlib.sha256(raw).hexdigest() == entry['database_sha256']
        with tempfile.TemporaryDirectory() as tmp:
            checked = audit(Path(tmp)/'prior.sqlite3', raw, OLD_MODES[entry['mode']])
        prior_checks.append(dict(path=str(previous/entry['path']), **checked))
    files = [Path(__file__), Path('experiments/cnf_affine_patterns.py'), Path('experiments/cnf_pattern_inventory.py'),
             Path('experiments/compare_cnf_pattern_inventory.py'), Path('experiments/cnf_residual_dag.py'),
             Path('solver/test_cnf_affine_patterns.py'), Path('solver/test_cnf_pattern_inventory.py')]
    report = dict(source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
                  fingerprints={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  modes={mode:dict(inventory=cls.__name__, options=options) for mode, (cls, options) in MODES.items()},
                  families=AFFINE_FAMILIES, cases=cases, original_case_count=len(scenarios()), records=records,
                  archives=archives, allocation_profiles=profiles, allocation_case_labels=[c['label'] for c in selected],
                  prior_archive_checks=prior_checks,
                  limitations=['Analysis only; same unmodified decision solver runs in every mode',
                      'Single sequential samples on synthetic/exhaustive/seeded sources, not significance estimates',
                      'Certificate coverage is exact for the normalized encoding, not all affine-equivalent encodings',
                      'Consistent affine equations plus arbitrary leftover clauses are not certified tractable',
                      'No substitution of affine solutions into coupling clauses or solver/history integration',
                      'Operation times include recognition, checking, serialization, persistence and solving; initialization separate',
                      'Generation, truth tables, inter-operation checks, summary walks and offline compression excluded',
                      'Cold replay audits all attempted alternatives, all sources and all ordinary solver certificates',
                      'Tracemalloc covers only six stated cases in separate reruns; excludes SQLite native memory and RSS',
                      'Both full source and compiled evidence retained; semantic compression is not physical source deletion',
                      'No new Lean implementation refinement or unrestricted polynomial SAT bound'])
    (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    summary = []
    for mode in MODES:
        rows = [r for r in records if r['mode'] == mode]
        entry = dict(mode=mode, total_seconds=sum(r['total_seconds'] for r in rows),
                     original_seconds=sum(r['total_seconds'] for r in rows[:664]),
                     archive=next(a for a in archives if a['mode'] == mode))
        if mode != 'solver_only':
            entry['discovery_seconds'] = sum(r['discovery']['seconds'] for r in rows)
            entry['groups'] = {group:dict(inputs=sum(c['group'] == group for c in cases),
                closed=sum(r['discovery']['summary']['closed'] for r in rows if cases[r['case']]['group'] == group),
                unresolved_literals=sum(r['discovery']['dag']['unresolved_distinct_literals'] for r in rows if cases[r['case']]['group'] == group))
                for group in sorted({c['group'] for c in cases})}
            entry['cells'] = dict(Counter(r['discovery']['profile']['cell'] for r in rows))
            for i, case in enumerate(cases):
                if case['group'] in ('variant', 'edit_variant'):
                    assert rows[i]['discovery']['profile']['cell'] == rows[i-1]['discovery']['profile']['cell']
        summary.append(entry)
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(dict(cases=len(cases), archives=len(archives))), flush=True)


if __name__ == '__main__':
    main()
