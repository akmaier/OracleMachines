#!/usr/bin/env python3
"""Attribute fresh admission costs without changing the measured policy."""
from pathlib import Path
from collections import Counter
import sys, tempfile
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_child_stream as study
from experiments.validate_cnf_unsat_support import bound
from experiments.cnf_residual_dag import normalize, restrict, token, holds
base = study.base


def run(out):
    report = base.load(out / 'report.json'); p = bound(report['protocol'])
    samples = [(e, bound(e)) for e in report['samples']]; details = {}; summaries = report['summary']; exposed = []
    with tempfile.TemporaryDirectory() as td:
        for entry, sample in samples:
            if entry['repeat']: continue
            mode = entry['mode']; path = Path(td) / mode; base.restore_archive(sample['archive'], path)
            s = study.native.ResidualSolver(path)
            try: archive = study.native.rows(s)
            finally: s.close()
            by_hash = {base.key_sha(k): (k, v) for k, v in archive.items()}; details[mode] = {}
            records = bound(sample['queries'])
            available = set(by_hash) - {h for r in records for h in r['new_ids']}
            for r in records:
                choice = r['local_choice']; admission = r['admission']; node = base.load_json(archive[r['child']['root']]); proof = node.get('proof', {})
                row = dict(case=r['case'], template_case=r['template_case'], answer=r['record']['answer'], new_nodes=r['new_nodes'],
                    native_bytes=sum(len(k) + len(v) for h in r['new_ids'] for k, v in [by_hash[h]]),
                    ordinary_nodes=len(r['ordinary_ids']), near_nodes=len(r['near_ids']),
                    expansion_nodes=sum(c['metrics'].get('expanded_nodes', 0) for c in (r['child'], r['premise']) if c is not None),
                    child_expansions=r['child']['metrics'].get('expanded_nodes', 0), child_root=r['child']['root'], child_kind=proof.get('kind', 'model'),
                    child_split_nodes=r['child']['metrics'].get('split_nodes', 0),
                    eligibility=r['local_eligible'], admission_reason=None if admission is None else admission['reason'],
                    proposal=None if admission is None or admission['proposal'] is None else admission['proposal'].get('clause'),
                    selected=None if choice is None else choice.get('clause'),
                    probe_counts=r['probe_counts'], summary=study.summarize([r]), seconds=r['seconds'])
                if proof.get('child'):
                    row['next_kind'] = base.load_json(archive[proof['child']]).get('proof', {}).get('kind', 'model')
                details[mode][r['case']] = row
                if admission is not None and admission['reason'] == 'no-proposal':
                    counts = Counter(); target = r['record']['source']
                    for g in r['record']['guards']:
                        target = restrict(target, {abs(l): l < 0 for l in g['removed_clause']}, counts)
                    cnf, names = normalize(target, counts); baseline = r['local_probe']['baseline']
                    assert token(cnf, counts) == baseline['root'] and baseline['conflict'] is None
                    fixed = {abs(l): l > 0 for l, _ in baseline['trace']}
                    residual = restrict(cnf, fixed, counts); normalized, child_names = normalize(residual, counts)
                    key = token(normalized, counts)
                    known = base.key_sha(key) in available | set(r['ordinary_ids']) | set(r['near_ids'])
                    model = None; checked_counts = {}; answer = None
                    if known:
                        s = study.native.ResidualSolver(path)
                        try:
                            s.db.execute('PRAGMA query_only=ON'); checked = s._read(key, normalized, purpose='exposed_residual')
                            answer = checked['answer']; checked_counts = dict(s.counts)
                            if answer:
                                local_model = {**fixed, **dict(zip(child_names, checked['model']))}
                                model = {v: local_model.get(i, False) for i, v in enumerate(names, 1)}
                                assert holds(target, model)
                        finally: s.close()
                    exposed.append(dict(mode=mode, case=r['case'], unit_steps=len(fixed), residual=[list(c) for c in normalized],
                        residual_root=key, residual_known=known, answer=answer, target_model=model,
                        two_cnf=all(len(c) <= 2 for c in normalized),
                        probe_attempts=len(r['local_probe']['attempts']), discovery_propagation=r['probe_counts'].get('propagation_literal_visits', 0),
                        fallback_propagation=r['child']['metrics'].get('propagation_literal_visits', 0),
                        diagnostic_counts=dict(counts), checked_counts=checked_counts))
                available.update(r['new_ids'])
    changes = [dict(case=cid, baseline=details['baseline'][cid], admitted=r) for cid, r in details['admitted'].items()
               if r['admission_reason'] is not None or r['new_nodes'] != details['baseline'][cid]['new_nodes'] or r['native_bytes'] != details['baseline'][cid]['native_bytes']]
    remaining = sorted((r for r in details['admitted'].values() if r['child_expansions']), key=lambda r: (-r['child_expansions'], r['case']))
    b, a = summaries['baseline'], summaries['admitted']; comparisons = {}
    for key in ('new_nodes', 'new_payload_units', 'expanded_nodes', 'propagation_literal_visits', 'mean_query_seconds', 'mean_complete_worker_seconds', 'mean_peak_rss_bytes'):
        comparisons[key] = dict(baseline=b[key], admitted=a[key], difference=a[key] - b[key], percent=None if not b[key] else 100 * (a[key] - b[key]) / b[key])
    for mode in study.MODES:
        values = summaries[mode]['sidecar_bytes']; comparisons.setdefault('mean_sidecar_bytes', {})[mode] = sum(values) / len(values)
    side = comparisons['mean_sidecar_bytes']; side['percent'] = 100 * (side['admitted'] - side['baseline']) / side['baseline']
    pairs = []
    for repeat, order in enumerate(p['orders']):
        rows = {e['mode']: s['summary'] for e, s in samples if e['repeat'] == repeat}
        pairs.append(dict(repeat=repeat, order=order, baseline_seconds=rows['baseline']['complete_worker_seconds'],
            admitted_seconds=rows['admitted']['complete_worker_seconds'], difference=rows['admitted']['complete_worker_seconds'] - rows['baseline']['complete_worker_seconds']))
    result = dict(passed=True, report=study.binding(out / 'report.json'), comparisons=comparisons, paired_complete_times=pairs,
        changes=changes, remaining_child_work=remaining, exposed_residuals=exposed,
        limitations=['Changes are contributions on matched streams whose prefixes can diverge, not isolated same-prefix causal gains.',
                    'Two timing pairs and process peak RSS provide no stable general runtime or live-memory bound. Cold replay includes all inherited composed records.',
                    'The unchanged rule is evaluated on 192 new roots from three old template families. No new general structural authority or unrestricted-SAT efficiency follows.',
                    'Exposed-residual recognition is a read-only posthoc diagnostic. It checks exact pre-query availability and a native answer, but no modified policy has been measured.'])
    base.write(out / 'cost-attribution.json', result)
    print(base.encode(dict(comparisons=comparisons, pairs=pairs,
        changes=[dict(case=r['case'], reason=r['admitted']['admission_reason'], rows=[r['baseline']['new_nodes'], r['admitted']['new_nodes']], expansions=[r['baseline']['child_expansions'], r['admitted']['child_expansions']]) for r in changes],
        remaining=[dict(case=r['case'], expansions=r['child_expansions'], kind=r['child_kind'], next_kind=r.get('next_kind')) for r in remaining])), flush=True)


if __name__ == '__main__': run(Path(sys.argv[1]))
