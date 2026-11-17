#!/usr/bin/env python3
"""Equal-state controls for a child-admission gate; no fresh-stream claim."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_local_guard as old
from experiments.cnf_child_admission import select
from experiments.cnf_assumption_guard import publish_guard
from experiments.cnf_partition_screen import publish_screened_branch
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.cnf_guard_chain import make_record
from experiments.validate_cnf_partition_screen import check_composed
from experiments.validate_cnf_unsat_support import bound
base = old.base
PARENT = Path('experiments/results/cnf-local-guard')
FILES = ('experiments/cnf_child_admission.py', 'solver/test_cnf_child_admission.py',
         'experiments/compare_cnf_child_admission.py', 'experiments/validate_cnf_child_admission.py')
MODES = ('baseline', 'local', 'admitted')


def contexts(p, tmp):
    result = []
    def read(entry, name):
        path = tmp / name; base.restore_archive(entry, path); s = old.native.ResidualSolver(path)
        try: return old.native.rows(s)
        finally: s.close()
    hp = bound(p['historical_protocol']); ht = bound(p['historical_trial'])
    fi = read(bound(hp['parent'])['reference_union'], 'historical-initial')
    ff = read(ht['archive'], 'historical-final'); fr = bound(ht['queries'])
    fp = bound(p['prior_protocol']); ft = bound(p['fresh_trial'])
    ni = read(bound(fp['parent'])['reference_union'], 'fresh-initial')
    nf = read(ft['archive'], 'fresh-final'); nr = bound(ft['queries'])
    for cohort, initial, final, records, wanted in (
        ('historical', fi, ff, fr, p['historical_cases']),
        ('fresh-baseline', ni, nf, nr, p['fresh_cases'])):
        available = dict(initial); by_hash = {base.key_sha(k): k for k in final}
        assert len(by_hash) == len(final) and initial.items() <= final.items()
        for row in records:
            if row['case'] in wanted:
                before = dict(available)
                preparation_ids = [] if cohort == 'historical' else row['ordinary_ids'] + row['near_ids']
                for h in preparation_ids:
                    k = by_hash[h]; assert k not in before; before[k] = final[k]
                result.append(dict(cohort=cohort, case=row['case'], before=before,
                    source=row['record']['source'], guards=row['record']['guards'],
                    expected_answer=row['record']['answer'], preparation_ids=preparation_ids))
            for h in row['new_ids']:
                k = by_hash[h]; assert k not in available; available[k] = final[k]
        assert available == final
    assert len(result) == len(p['historical_cases']) + len(p['fresh_cases'])
    return result


def evaluate(s, source, target, guards, mode, limit):
    if mode != 'admitted':
        result = old.evaluate(s, source, target, guards, mode, True, limit)
        result['admission'] = None
        return result
    start = time.perf_counter(); guards = list(guards); counts = Counter(); s.counts = Counter()
    with patch.object(s, '_expand', side_effect=AssertionError('Selection search')), patch.object(s, '_store', side_effect=AssertionError('Selection publication')):
        choice, trace = select(s, target, limit, counts)
    selection_seconds = time.perf_counter() - start; probe_metrics = dict(s.counts)
    premise = None; guard_counts = Counter(); guard_metrics = {}; premise_seconds = 0.
    if choice and choice['kind'] == 'guard':
        tick = time.perf_counter()
        with patch.object(s, '_expand', side_effect=AssertionError('Premise search')):
            guard, _, target, premise = publish_guard(s, target, choice, guard_counts)
        guards.append(guard); guard_metrics = dict(s.counts - Counter(premise['metrics']))
        premise_seconds = time.perf_counter() - tick
    tick = time.perf_counter()
    if choice and choice['kind'] == 'guard':
        with patch.object(s, '_expand', side_effect=AssertionError('Admitted child search')):
            child = (s.solve(target) if choice['child']['known'] else
                     publish_screened_branch(s, target, choice['child']['screen']))
    elif choice:
        child = publish_screened_branch(s, target, choice['screen'])
    else:
        child = s.solve(target)
    child_seconds = time.perf_counter() - tick; tick = time.perf_counter(); before = Counter(s.counts)
    record = make_record(s, source, guards, child)
    return dict(record=record, local_eligible=True, local_choice=choice, local_probe=trace['discovery'],
                admission=trace, child=child, premise=premise, probe_counts=dict(counts), probe_metrics=probe_metrics,
                guard_counts=dict(guard_counts), guard_metrics=guard_metrics, composition_metrics=dict(s.counts - before),
                selection_seconds=selection_seconds, premise_seconds=premise_seconds, child_seconds=child_seconds,
                composition_seconds=time.perf_counter() - tick, evaluation_seconds=time.perf_counter() - start)


def run(out):
    out.mkdir(exist_ok=False); start = time.perf_counter(); prior = base.load(PARENT / 'protocol.json')
    sources = dict(base.load(PARENT / 'validation.json')['source_fingerprints'])
    for f, h in sources.items(): assert base.sha(f) == h, f
    sources.update({f: base.sha(f) for f in FILES})
    p = dict(parent=old.binding(PARENT / 'checkpoint.json'), source_fingerprints=sources,
        prior_protocol=old.binding(PARENT / 'protocol.json'), historical_protocol=prior['historical_protocol'],
        historical_trial=prior['historical_trial'], historical_controls=old.binding(PARENT / 'historical/report.json'),
        fresh_trial=old.binding(PARENT / 'baseline-0/report.json'), historical_cases=[43, 172, 70],
        fresh_cases=[144, 167, 190], variable_limit=4, modes=MODES,
        limitations=['Eighteen exact-prefix controls after shared ordinary/near preparation; six selected prior cases, no new excluded queries.',
                    'Prefix reconstruction and copies are separately timed. Original preparation costs remain in the bound prior trials; do not interpret this experiment as complete stream timing.',
                    'All modes start with identical native rows and an empty checked-node cache, then replay the same accepted guards. Single samples per arm provide no stable timing or memory claim.',
                    'Admission requires an existing checked child or unit-refuted child, with syntactic two-CNF/Horn/dual-Horn priority. Nonterminal rejection may lose useful savings; arbitrary remaining search stays in fallback.'])
    base.write(out / 'protocol.json', p); samples = []
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
                    result = evaluate(s, case['source'], target, case['guards'], mode, p['variable_limit'])
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
                    summary=old.summarize([result]), prefix_write_seconds=prefix_write_seconds, open_seconds=open_seconds,
                    guard_replay_seconds=guard_replay_seconds, guard_replay_metrics=guard_replay_metrics,
                    warm_seconds=warm_seconds, cold_seconds=cold_seconds, cold_metrics=cold_metrics,
                    serialization_seconds=serialization_seconds, complete_arm_seconds=time.perf_counter() - tick)
                base.write(dest / 'report.json', result); samples.append(old.binding(dest / 'report.json'))
                print(base.encode(dict(cohort=case['cohort'], case=case['case'], mode=mode,
                    rows=result['new_nodes'], native_bytes=result['new_payload_units'], summary=result['summary'],
                    reason=None if result['admission'] is None else result['admission']['reason'])), flush=True)
    base.write(out / 'report.json', dict(protocol=old.binding(out / 'protocol.json'), samples=samples,
                                       prefix_reconstruction_seconds=reconstruction_seconds, seconds=time.perf_counter() - start))


if __name__ == '__main__': run(Path(sys.argv[1]))
