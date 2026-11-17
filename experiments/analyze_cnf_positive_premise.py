#!/usr/bin/env python3
"""Attribute model-recovery savings, all additional checks and fresh misses."""
from pathlib import Path
import sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_positive_premise as study
from experiments.analyze_cnf_binary_probe import audit_filter_counts
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.validate_cnf_unsat_support import bound
base = study.base


def audit_counts(row, target):
    audit_filter_counts(row)
    a = row['admission']; d = None if a is None else a['discovery']; choice = row['local_choice']
    success = a is not None and a['reason'] == 'positive-premise-model'
    scanned = (a['positive_premise_attempt'] + 1 if success else
        len(d['attempts']) if d is not None and (choice is None or choice['kind'] == 'fallback-trace') else 0)
    expected = dict(positive_premise_attempts_scanned=scanned, positive_premise_models=int(success),
        positive_premise_literals_copied=0, positive_premise_model_literals=0, positive_premise_reason_literals=0)
    if success:
        attempt = d['attempts'][a['positive_premise_attempt']]
        cnf = base.load_json(attempt['screen']['root'].split(':', 1)[1])
        ids = [cid for _, cid in attempt['screen']['trace']]
        assert len(ids) == len(set(ids))  # A used unit reason becomes satisfied.
        expected.update(positive_premise_literals_copied=sum(map(len, target))+1,
            positive_premise_model_literals=sum(map(len, target))+1,
            positive_premise_reason_literals=sum(len(cnf[cid]) for cid in ids))
    assert all(row['probe_counts'].get(k, 0) == v for k, v in expected.items())


def analyze(out):
    started = time.perf_counter(); report = base.load(out/'report.json')
    cases = {c['case']: c for c in bound(report['cases'])['cases']}
    details = []; groups = {}; modes = {}; audits = 0
    for entry in report['samples']:
        data = bound(entry); records = bound(data['queries']); mode = entry['mode']
        modes[mode, entry['repeat']] = data['summary']
        with tempfile.TemporaryDirectory() as td:
            path = Path(td)/'proofs'; base.restore_archive(data['archive'], path); s = study.native.ResidualSolver(path)
            try:
                rows = study.native.rows(s); sizes = {base.key_sha(k): len(k)+len(v) for k, v in rows.items()}
                for row in records:
                    if mode == 'recovered':
                        target = row['record']['source']
                        # A successful guard appends one guard after selection.
                        guards = row['record']['guards']
                        if row['local_choice'] and row['local_choice']['kind'] == 'guard': guards = guards[:-1]
                        for g in guards: _, target = check_guard(s, target, g)
                        audit_counts(row, target); audits += 1
                    if entry['repeat'] != 0: continue
                    details.append(dict(case=row['case'], family=cases[row['case']]['family'], mode=mode,
                        configuration=cases[row['case']]['configuration'], answer=row['record']['answer'],
                        new_rows=row['new_nodes'], native_bytes=sum(sizes[h] for h in row['new_ids']),
                        expanded_nodes=row['child']['metrics'].get('expanded_nodes', 0),
                        discovery_propagation=row['probe_counts'].get('propagation_literal_visits', 0),
                        child_propagation=row['child']['metrics'].get('propagation_literal_visits', 0),
                        reason=None if row['admission'] is None else row['admission']['reason'],
                        familiarity=row['familiarity']))
            finally: s.close()
        for family in sorted({c['family'] for c in cases.values()}):
            selected = [r for r in records if cases[r['case']]['family'] == family]
            summary = study.summarize(selected)
            summary.update(queries=len(selected), rows=sum(r['new_nodes'] for r in selected),
                query_seconds=sum(r['seconds'] for r in selected),
                discovery_propagation=sum(r['probe_counts'].get('propagation_literal_visits', 0) for r in selected),
                child_propagation=sum(r['child']['metrics'].get('propagation_literal_visits', 0) for r in selected))
            groups.setdefault(family, {}).setdefault(mode, []).append(summary)
    controls = []
    for cohort in ('controls', 'reverse_control'):
        for entry in bound(report[cohort])['samples']:
            row = bound(entry)
            if row['mode'] == 'recovered': audit_counts(row, row['input_target']); audits += 1
            controls.append(dict(cohort=row['cohort'], case=row['case'], mode=row['mode'], order=cohort,
                new_rows=row['new_nodes'], native_bytes=row['new_payload_units'], retained_bytes=row['retained_bytes'],
                report_bytes=Path(entry['path']).stat().st_size,
                reason=row['admission']['reason'], summary=row['summary'],
                probe_counts=row['probe_counts'], probe_metrics=row['probe_metrics'],
                child_metrics=row['child']['metrics'],
                **{k: row[k] for k in ('selection_seconds', 'child_seconds', 'evaluation_seconds',
                    'warm_seconds', 'cold_seconds', 'open_seconds', 'prefix_write_seconds',
                    'serialization_seconds', 'complete_arm_seconds')}))
    result = dict(groups=groups, cases=details, controls=controls, counter_audits=audits,
        timing_pairs=[dict(repeat=i, query_delta=modes['recovered', i]['query_seconds']-modes['filtered', i]['query_seconds'],
            complete_delta=modes['recovered', i]['complete_worker_seconds']-modes['filtered', i]['complete_worker_seconds']) for i in range(2)],
        seconds=time.perf_counter()-started,
        limitations=['This posthoc attribution is not part of the timed policy; all additional recovery counters are independently recomputed.',
            'Saved case50 motivated implementation and is not a held-out coverage sample. Fresh family labels are metadata only.',
            'Exact-prefix opening, prefix writing and query-local replay are reported separately; fresh complete workers include the inherited bank and full cold replay.',
            'Positive recovery does not add missing probes, stop earlier discovery or solve nonterminal recognized families.'])
    base.write(out/'attribution.json', result)
    print(base.encode(dict(counter_audits=audits, timing_pairs=result['timing_pairs'],
        successes=[d for d in details if d['reason']=='positive-premise-model'])))


if __name__ == '__main__': analyze(Path(sys.argv[1]))
