#!/usr/bin/env python3
"""Attribute binary filtering costs and diagnose remaining futile polarities."""
from collections import Counter
from pathlib import Path
import sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_probe as study
from experiments.cnf_partition_screen import screen_branch
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.validate_cnf_unsat_support import bound
base = study.base


def audit_filter_counts(row):
    d = row['local_probe']; expected = dict(binary_filter_clause_visits=0,
        binary_filter_literal_visits=0, binary_filter_name_transports=0, binary_probe_skips=0)
    if d is not None and d['binary_filter'] is not None:
        cnf = base.load_json(d['baseline']['root'].split(':', 1)[1])
        fixed = {abs(l): l > 0 for l, _ in d['baseline']['trace']}
        residual = [[l for l in c if abs(l) not in fixed] for c in cnf
                    if not any(abs(l) in fixed and fixed[abs(l)] == (l > 0) for l in c)]
        binaries = [c for c in residual if len(c) == 2]
        expected.update(binary_filter_clause_visits=len(residual), binary_filter_literal_visits=2*len(binaries),
                        binary_filter_name_transports=len({abs(l) for c in binaries for l in c}),
                        binary_probe_skips=len(d['binary_filter']['skipped']))
    assert all(row['probe_counts'].get(k, 0) == v for k, v in expected.items())


def analyze(out):
    started = time.perf_counter(); report = base.load(out / 'report.json')
    cases = {c['case']: c for c in bound(report['cases'])['cases']}
    groups = {}; details = []; diagnosis = []; family_candidates = []; modes = {}; digests = set(); counter_audits = 0
    for entry in report['samples']:
        data = bound(entry); records = bound(data['queries']); mode = entry['mode']
        if mode == 'filtered':
            for row in records: audit_filter_counts(row); counter_audits += 1
        modes[mode, entry['repeat']] = data['summary']; digests.add(data['summary']['row_digest'])
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
                    if mode == 'positive' and row['local_probe'] is not None:
                        target = row['record']['source']
                        assert row['local_choice'] is None or row['local_choice']['kind'] == 'fallback-trace'
                        for g in row['record']['guards']: _, target = check_guard(s, target, g)
                        for attempt in row['local_probe']['attempts']:
                            screen = attempt['screen']
                            if screen['conflict'] is not None: continue
                            cnf, probe_names, root = s._canonical([list(c) for c in target]+[attempt['clause']])
                            assert root == screen['root'] and screen['conflict'] is None
                            fixed = {abs(l): l > 0 for l, _ in screen['trace']}
                            residual = [[l for l in c if abs(l) not in fixed] for c in cnf
                                if not any(abs(l) in fixed and fixed[abs(l)] == (l > 0) for l in c)]
                            recognized = ('constant' if not residual else
                                'two-cnf' if all(len(c) <= 2 for c in residual) else
                                'horn' if all(sum(l > 0 for l in c) <= 1 for c in residual) else
                                'dual-horn' if all(sum(l < 0 for l in c) <= 1 for c in residual) else None)
                            if recognized is not None:
                                candidate = dict(case=row['case'], family=case['family'],
                                    assumption=attempt['clause'], recognized=recognized,
                                    residual_variables=len({abs(l) for c in residual for l in c}),
                                    residual_literals=sum(map(len, residual)))
                                if not residual:
                                    model = {name: fixed.get(i+1, False) for i, name in enumerate(probe_names)}
                                    assert all(any(model[abs(l)] == (l > 0) for l in c) for c in [list(c) for c in target]+[attempt['clause']])
                                    candidate.update(verified_target_model=sorted(model.items()), target_root=s._canonical(target)[2])
                                family_candidates.append(candidate)
                    if mode != 'filtered' or row['local_probe'] is None: continue
                    probe = row['local_probe']
                    if not probe['attempts']: continue
                    assert row['local_choice'] is None or row['local_choice']['kind'] == 'fallback-trace'
                    target = row['record']['source']
                    for g in row['record']['guards']: _, target = check_guard(s, target, g)
                    cnf, names, root = s._canonical(target)
                    assert root == probe['baseline']['root'] and probe['baseline']['conflict'] is None
                    fixed = {abs(l): l > 0 for l, _ in probe['baseline']['trace']}
                    residual = [[l for l in c if abs(l) not in fixed] for c in cnf
                                if not any(abs(l) in fixed and fixed[abs(l)] == (l > 0) for l in c)]
                    assert all(len(c) >= 2 for c in residual)
                    binary_literals = {names[abs(l)-1]*(1 if l > 0 else -1) for c in residual if len(c) == 2 for l in c}
                    futile = []; counts = Counter()
                    for attempt in probe['attempts']:
                        literal, = attempt['clause']
                        assert abs(literal) not in {names[v-1] for v in fixed}
                        if -literal in binary_literals: continue
                        # Binary clauses containing only the satisfied polarity
                        # disappear; none can seed a further unit deduction.
                        assert attempt['screen']['conflict'] is None
                        actual = screen_branch(s, [list(c) for c in target]+[[literal]], counts)
                        assert actual == attempt['screen']; futile.append(literal)
                    diagnosis.append(dict(case=row['case'], family=case['family'], attempted_probes=len(probe['attempts']),
                        polarity_futile_probes=futile, replayed_polarity_probe_counts=dict(counts)))
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
    controls = [bound(e) for e in bound(report['controls'])['samples']]; control_summary = {}
    for mode in ('positive', 'filtered'):
        rows = [r for r in controls if r['mode'] == mode]
        if mode == 'filtered':
            for row in rows: audit_filter_counts(row); counter_audits += 1
        control_summary[mode] = dict(study.summarize(rows), new_rows=sum(r['new_nodes'] for r in rows),
            native_bytes=sum(r['new_payload_units'] for r in rows), retained_bytes=sum(r['retained_bytes'] for r in rows),
            report_bytes=sum(Path(e['path']).stat().st_size for e in bound(report['controls'])['samples'] if bound(e)['mode'] == mode),
            evaluation_seconds=sum(r['evaluation_seconds'] for r in rows))
    result = dict(groups=summary, cases=details, controls=control_summary, polarity_diagnosis=diagnosis,
        filter_counter_audits=counter_audits,
        conditioned_family_candidates=family_candidates,
        all_modes_identical_native_payloads=len(digests) == 1,
        remaining_polarity_futile_probes=sum(len(d['polarity_futile_probes']) for d in diagnosis),
        remaining_polarity_propagation=sum(d['replayed_polarity_probe_counts'].get('propagation_literal_visits', 0) for d in diagnosis),
        timing_pairs=[dict(repeat=i, query_delta=modes['filtered', i]['query_seconds']-modes['positive', i]['query_seconds'],
                          complete_delta=modes['filtered', i]['complete_worker_seconds']-modes['positive', i]['complete_worker_seconds']) for i in range(2)],
        seconds=time.perf_counter()-started,
        limitations=['Polarity refinement and conditioned family recognition are posthoc diagnoses, not enabled in the measured filter.',
                     'A recognized conditioned family is not a SAT result: a checked model or negative family proof must still be acquired and recomposed. One refuted branch alone does not refute the target.',
                     'The residual must be unit-closed and consistent, and the assumed variable unassigned. This only excludes single-assumption unit refutations.',
                     'Matched historical controls include incidence/trace overhead even when nothing can be skipped. Two timing pairs on finite generators do not establish general scaling.'])
    base.write(out / 'attribution.json', result)
    print(base.encode({k: result[k] for k in ('all_modes_identical_native_payloads', 'remaining_polarity_futile_probes', 'remaining_polarity_propagation', 'timing_pairs', 'controls')}))


if __name__ == '__main__': analyze(Path(sys.argv[1]))
