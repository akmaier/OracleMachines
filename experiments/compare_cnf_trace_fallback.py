#!/usr/bin/env python3
"""Matched retained-prefix fallback controls and fresh three-policy streams."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil, subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_local_guard as old
from experiments import compare_cnf_child_admission as gate
from experiments import compare_cnf_propagated_reuse as previous
from experiments.cnf_trace_fallback import select
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.validate_cnf_partition_screen import check_composed
from experiments.validate_cnf_unsat_support import bound
base = old.base; binding = old.binding; native = old.native; prep = old.prep
FIELDS = old.FIELDS; OLD_FIELDS = old.OLD_FIELDS
PARENT = Path('experiments/results/cnf-propagated-reuse')
FILES = ('experiments/cnf_trace_fallback.py', 'solver/test_cnf_trace_fallback.py',
         'experiments/compare_cnf_trace_fallback.py', 'experiments/validate_cnf_trace_fallback.py')
MODES = ('baseline', 'propagated', 'retained')
original_evaluate = old.evaluate; original_inherited = old.inherited; original_summarize = old.summarize


def inherited(parent):
    return previous.inherited(parent) + bound(parent['propagated_reuse_decisions'])


def exclusions(parent):
    records = sum((bound(parent[f]) for f in FIELDS), []) + inherited(parent)
    return [dict(query_root=k) for k in sorted({r['query_root'] for r in records})]


def evaluate(s, source, target, guards, mode, eligible, limit):
    if mode == 'retained' and eligible:
        with patch.object(gate, 'select', select):
            return gate.evaluate(s, source, target, guards, 'admitted', limit)
    return previous.evaluate(s, source, target, guards, mode, eligible, limit)


def summarize(records):
    summary = original_summarize(records)
    summary.update(admission_calls=sum(r['admission'] is not None for r in records),
                   admission_reasons=dict(Counter(r['admission']['reason'] for r in records if r['admission'] is not None)))
    summary['retained_prefixes'] = sum(bool(r['local_choice'] and r['local_choice']['kind'] == 'fallback-trace') for r in records)
    summary['propagated_reuses'] = sum(bool(r['local_choice'] and r['local_choice']['kind'] == 'propagated') for r in records)
    return summary


def worker(out, p, catalog, mode):
    assert mode in MODES
    with patch.object(old, 'inherited', inherited), patch.object(old, 'evaluate', evaluate), patch.object(old, 'summarize', summarize):
        old.worker(out, p, catalog, mode)


def contexts(p, tmp):
    cases = previous.contexts(p, tmp)
    stream = bound(p['fallback_stream']); protocol = bound(stream['protocol']); trial = bound(p['fallback_trial'])
    path = tmp / 'fallback-initial'; base.restore_archive(bound(protocol['parent'])['reference_union'], path)
    s = native.ResidualSolver(path)
    try: before = native.rows(s)
    finally: s.close()
    path = tmp / 'fallback-final'; base.restore_archive(trial['archive'], path); s = native.ResidualSolver(path)
    try: final = native.rows(s)
    finally: s.close()
    by_hash = {base.key_sha(k): k for k in final}
    for row in bound(trial['queries']):
        if row['case'] in p['fallback_cases']:
            prefix = dict(before); ids = row['ordinary_ids'] + row['near_ids']
            for h in ids:
                key = by_hash[h]; assert key not in prefix; prefix[key] = final[key]
            cases.append(dict(cohort='fallback-stream', case=row['case'], before=prefix, source=row['record']['source'],
                guards=row['record']['guards'], expected_answer=row['record']['answer'], preparation_ids=ids))
        for h in row['new_ids']:
            key = by_hash[h]; assert key not in before; before[key] = final[key]
    assert before == final and len(cases) == 9
    return cases


def controls(out, p):
    out.mkdir(); started = time.perf_counter(); samples = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td); tick = time.perf_counter(); cases = contexts(p, tmp)
        reconstruction_seconds = time.perf_counter() - tick
        for case in cases:
            tick = time.perf_counter(); prefix = tmp / 'prefix'; prefix.unlink(missing_ok=True)
            s = old.native.ResidualSolver(prefix)
            with s.db: s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', case['before'].items())
            s.close(); prefix_write_seconds = time.perf_counter() - tick
            for mode in MODES:
                tick = time.perf_counter(); dest = out / f"{case['cohort']}-{case['case']}-{mode}"; dest.mkdir()
                path = tmp / 'arm'; shutil.copyfile(prefix, path); s = old.prep.ordinary.AccountedResidualSolver(path)
                open_seconds = time.perf_counter() - tick
                try:
                    phase = time.perf_counter(); target = case['source']
                    with patch.object(s, '_expand', side_effect=AssertionError('Guard replay search')), patch.object(s, '_store', side_effect=AssertionError('Guard replay publication')):
                        for g in case['guards']: _, target = check_guard(s, target, g)
                    guard_replay_seconds = time.perf_counter() - phase; guard_replay_metrics = dict(s.counts)
                    result = evaluate(s, case['source'], target, case['guards'], mode, True, p['variable_limit'])
                    assert result['record']['answer'] == case['expected_answer']
                    after = old.native.rows(s); assert case['before'].items() <= after.items()
                    delta = [(k, v) for k, v in after.items() if k not in case['before']]
                    phase = time.perf_counter()
                    with patch.object(s, '_expand', side_effect=AssertionError('Warm search')), patch.object(s, '_store', side_effect=AssertionError('Warm publication')):
                        check_composed(s, result['record'])
                    warm_seconds = time.perf_counter() - phase
                finally: s.close()
                phase = time.perf_counter(); s = old.native.ResidualSolver(path)
                try:
                    s.db.execute('PRAGMA query_only=ON')
                    with patch.object(s, '_expand', side_effect=AssertionError('Cold search')), patch.object(s, '_store', side_effect=AssertionError('Cold publication')):
                        check_composed(s, result['record'])
                    cold_metrics = dict(s.counts)
                finally: s.close()
                cold_seconds = time.perf_counter() - phase; phase = time.perf_counter()
                base.write(dest / 'delta.json', delta); base.write(dest / 'records.json', [result['record']])
                retained_bytes = sum((dest / f).stat().st_size for f in ('delta.json', 'records.json'))
                serialization_seconds = time.perf_counter() - phase
                result.update(cohort=case['cohort'], case=case['case'], mode=mode,
                    input_guards=case['guards'], input_target=[list(c) for c in target], preparation_ids=case['preparation_ids'],
                    prefix_nodes=len(case['before']), prefix_digest=base.key_sha(base.encode(sorted(case['before'].items()))),
                    delta=old.binding(dest / 'delta.json'), records=old.binding(dest / 'records.json'),
                    new_nodes=len(delta), new_payload_units=sum(len(k) + len(v) for k, v in delta), retained_bytes=retained_bytes,
                    summary=summarize([result]), prefix_write_seconds=prefix_write_seconds, open_seconds=open_seconds,
                    guard_replay_seconds=guard_replay_seconds, guard_replay_metrics=guard_replay_metrics,
                    warm_seconds=warm_seconds, cold_seconds=cold_seconds, cold_metrics=cold_metrics,
                    serialization_seconds=serialization_seconds, complete_arm_seconds=time.perf_counter() - tick)
                base.write(dest / 'report.json', result); samples.append(old.binding(dest / 'report.json'))
                print(base.encode(dict(cohort=case['cohort'], case=case['case'], mode=mode,
                    rows=result['new_nodes'], native_bytes=result['new_payload_units'], summary=result['summary'],
                    reason=None if result['admission'] is None else result['admission']['reason'])), flush=True)
    base.write(out / 'report.json', dict(samples=samples, prefix_reconstruction_seconds=reconstruction_seconds, seconds=time.perf_counter() - started))


def run(out):
    out.mkdir(exist_ok=False); parent = base.load(PARENT / 'checkpoint.json'); prior = base.load(PARENT / 'protocol.json')
    bank = base.load('experiments/results/cnf-premise-guard/protocol.json')
    sources = dict(base.load(PARENT / 'validation.json')['source_fingerprints'])
    for f, h in sources.items(): assert base.sha(f) == h, f
    sources.update({f: base.sha(f) for f in FILES})
    base.write(out / 'previous-decisions.json', exclusions(parent))
    p = dict(parent=binding(PARENT / 'checkpoint.json'), source_fingerprints=sources,
        support_index=parent['extended_support_proposals'], causal_index=parent['causal_support_proposals'],
        template_catalog=bank['template_catalog'], cores=bank['cores'], bank_catalog=bank['bank_catalog'],
        previous_decisions=binding(out / 'previous-decisions.json'), prior_stream=prior['prior_stream'],
        control_protocol=binding(Path('experiments/results/cnf-child-admission/protocol.json')),
        control_reports=binding(PARENT / 'controls/report.json'),
        reuse_trial=prior['reuse_trial'], reuse_case=85,
        fallback_stream=binding(PARENT / 'report.json'), fallback_trial=binding(PARENT / 'propagated-0/report.json'), fallback_cases=[36, 186],
        node_limit=100000, alternative_budget=1, variable_limit=4, per_template=64, orders=[MODES, MODES[::-1]],
        limitations=['Nine exact-prefix controls and 192 new excluded neighbours from three existing templates; no arbitrary-SAT coverage claim.',
                    'Native baseline, propagated-residual reuse and retained-prefix fallback use identical shared preparation; each fresh mode has two reversed-order workers.',
                    'If the previous selector declines a candidate but its baseline has a nonempty forced prefix, reuse that baseline trace for the original target. The rejected guard is not published; remaining residual acquisition is unrestricted.',
                    'The existing screened publisher checks every unit and final certificate. One explicit trace publication replaces the original target expansion; child expansion budget, native branch policy and dependency lookup remain unchanged.',
                    'Recognition, normalization, lookup, verification, discovery misses, fallback, sidecars, persistence and full cold replay remain charged. No tests, profiles or builds overlap timed production.',
                    'The old exact-prefix controls and all prior native payloads are preserved. No new Lean, minimum-cost or unrestricted-SAT complexity bound.'])
    base.write(out / 'protocol.json', p)
    controls(out / 'controls', p)
    tick = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'initial'; base.restore_archive(parent['reference_union'], path); s = native.ResidualSolver(path)
        try: catalog = prep.ordinary.eager.previous.inputs(s, p)
        finally: s.close()
    assert len(catalog['cases']) == 192
    base.write(out / 'cases.json', catalog); base.write(out / 'preflight.json', dict(seconds=time.perf_counter() - tick, selection=catalog['selection']))
    samples = []
    for repeat, order in enumerate(p['orders']):
        for mode in order:
            dest = out / f'{mode}-{repeat}'
            subprocess.run([sys.executable, __file__, 'worker', str(dest), str(out / 'protocol.json'), str(out / 'cases.json'), mode], check=True, stdout=subprocess.DEVNULL)
            samples.append(dict(repeat=repeat, mode=mode, **binding(dest / 'report.json'))); print('fresh', repeat, mode, flush=True)
    summary = {}
    for mode in MODES:
        data = [bound(e)['summary'] for e in samples if e['mode'] == mode]; first = data[0]
        timed = [k for k in first if k.endswith('_seconds') or k == 'peak_rss_bytes']
        fixed = [k for k in first if k not in timed and k not in ('mode', 'sidecar_bytes')]
        for other in data[1:]:
            for k in fixed: assert first[k] == other[k], k
        summary[mode] = {**{k: first[k] for k in fixed}, **{'mean_' + k: sum(r[k] for r in data) / len(data) for k in timed}, 'sidecar_bytes': [r['sidecar_bytes'] for r in data]}
    base.write(out / 'report.json', dict(protocol=binding(out / 'protocol.json'), controls=binding(out / 'controls/report.json'), cases=binding(out / 'cases.json'), samples=samples, summary=summary))
    print(base.encode(summary), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'worker': worker(Path(sys.argv[2]), base.load(sys.argv[3]), base.load(sys.argv[4]), sys.argv[5])
    else: run(Path(sys.argv[1]))
