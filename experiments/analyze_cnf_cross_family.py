#!/usr/bin/env python3
"""Posthoc family attribution and necessary-condition audit for failed literals."""
from collections import Counter
from pathlib import Path
import sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cross_family as study
from experiments.cnf_partition_screen import screen_branch
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.validate_cnf_unsat_support import bound
base = study.base


def analyze(out):
    started = time.perf_counter(); report = base.load(out / 'report.json')
    catalog = bound(report['cases']); cases = {c['case']: c for c in catalog['cases']}
    groups = {}; details = []; diagnosis = []; modes = {}; row_digests = {}
    for entry in report['samples']:
        data = bound(entry); records = bound(data['queries']); mode = entry['mode']
        modes[mode, entry['repeat']] = data['summary']
        row_digests[mode, entry['repeat']] = data['summary']['row_digest']
        for family in sorted({c['family'] for c in cases.values()}):
            selected = [r for r in records if cases[r['case']]['family'] == family]
            summary = study.summarize(selected)
            summary.update(queries=len(selected), positive=sum(r['record']['answer'] for r in selected),
                ordinary_rows=sum(len(r['ordinary_ids']) for r in selected), near_rows=sum(len(r['near_ids']) for r in selected),
                rows=sum(r['new_nodes'] for r in selected),
                query_seconds=sum(r['seconds'] for r in selected),
                selection_seconds=sum(r['selection_seconds'] for r in selected),
                child_seconds=sum(r['child_seconds'] for r in selected),
                discovery_propagation=sum(r['probe_counts'].get('propagation_literal_visits', 0) for r in selected),
                child_propagation=sum(r['child']['metrics'].get('propagation_literal_visits', 0) for r in selected),
                composition_seconds=sum(r['composition_seconds'] for r in selected))
            groups.setdefault(family, {}).setdefault(mode, []).append(summary)
        if entry['repeat'] != 0: continue
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'proofs'; base.restore_archive(data['archive'], path); s = study.native.ResidualSolver(path)
            try:
                rows = study.native.rows(s); sizes = {base.key_sha(k): len(k)+len(v) for k, v in rows.items()}
                for row in records:
                    case = cases[row['case']]
                    details.append(dict(case=row['case'], family=case['family'], configuration=case['configuration'], mode=mode,
                        familiarity=row['familiarity'], answer=row['record']['answer'], new_rows=row['new_nodes'],
                        native_bytes=sum(sizes[h] for h in row['new_ids']),
                        expanded_nodes=row['child']['metrics'].get('expanded_nodes', 0),
                        discovery_propagation=row['probe_counts'].get('propagation_literal_visits', 0),
                        child_propagation=row['child']['metrics'].get('propagation_literal_visits', 0),
                        selection_seconds=row['selection_seconds'], child_seconds=row['child_seconds']))
                    if mode != 'positive' or row['local_probe'] is None: continue
                    target = row['record']['source']
                    # No local guard is accepted on this corpus. If this changes,
                    # do not accidentally include a newly proposed guard here.
                    assert row['local_choice'] is None
                    for g in row['record']['guards']: _, target = check_guard(s, target, g)
                    cnf, names, root = s._canonical(target); probe = row['local_probe']
                    assert root == probe['baseline']['root'] and probe['baseline']['conflict'] is None
                    fixed = {abs(l): l > 0 for l, _ in probe['baseline']['trace']}
                    residual = [[l for l in c if abs(l) not in fixed] for c in cnf
                                if not any(abs(l) in fixed and fixed[abs(l)] == (l > 0) for l in c)]
                    assert all(len(c) >= 2 for c in residual)
                    binary_names = {names[abs(l)-1] for c in residual if len(c) == 2 for l in c}
                    futile = []; counts = Counter()
                    for attempt in probe['attempts']:
                        literal, = attempt['clause']
                        assert abs(literal) not in {names[v-1] for v in fixed}
                        if abs(literal) in binary_names: continue
                        # With no binary incidence in the unit-closed residual,
                        # one assignment creates no new unit or empty clause.
                        assert attempt['screen']['conflict'] is None
                        actual = screen_branch(s, [list(c) for c in target]+[[literal]], counts)
                        assert actual == attempt['screen']
                        futile.append(literal)
                    diagnosis.append(dict(case=row['case'], family=case['family'],
                        fixed_variables=len(fixed), residual_clauses=len(residual), binary_variables=len(binary_names),
                        attempted_probes=len(probe['attempts']), structurally_futile_probes=futile,
                        replayed_futile_probe_counts=dict(counts)))
            finally: s.close()
    summary = {}
    for family, by_mode in groups.items():
        summary[family] = {}
        for mode, samples in by_mode.items():
            first = samples[0]; timed = [k for k in first if k.endswith('_seconds')]
            assert all(all(r[k] == first[k] for k in first if k not in timed) for r in samples)
            summary[family][mode] = {**{k: v for k, v in first.items() if k not in timed},
                **{'mean_'+k: sum(r[k] for r in samples)/len(samples) for k in timed},
                'native_bytes': sum(d['native_bytes'] for d in details if d['family'] == family and d['mode'] == mode)}
    result = dict(groups=summary, cases=details, necessary_condition=diagnosis,
        all_modes_identical_native_payloads=len(set(row_digests.values())) == 1,
        total_attempted_probes=sum(d['attempted_probes'] for d in diagnosis),
        structurally_futile_probes=sum(len(d['structurally_futile_probes']) for d in diagnosis),
        futile_propagation_visits=sum(d['replayed_futile_probe_counts'].get('propagation_literal_visits', 0) for d in diagnosis),
        timing_pairs=[dict(repeat=i, query_delta=modes['positive', i]['query_seconds']-modes['baseline', i]['query_seconds'],
                          complete_delta=modes['positive', i]['complete_worker_seconds']-modes['baseline', i]['complete_worker_seconds']) for i in range(2)],
        seconds=time.perf_counter()-started,
        limitations=['Posthoc necessary-condition diagnosis is charged separately and does not change timed selection.',
                     'No binary incidence must be checked after complete, consistent baseline unit propagation. It excludes only single-assumption unit refutations, not SAT difficulty or deeper conditioning.',
                     'Memory measures are process RSS, archive bytes and sidecar bytes, not an asymptotic live-memory bound. Each worker includes the inherited archive and 3,045 earlier composed records.'])
    base.write(out / 'attribution.json', result)
    print(base.encode({k: result[k] for k in ('all_modes_identical_native_payloads', 'total_attempted_probes', 'structurally_futile_probes', 'futile_propagation_visits', 'timing_pairs')}))


if __name__ == '__main__': analyze(Path(sys.argv[1]))
