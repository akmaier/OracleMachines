#!/usr/bin/env python3
"""Price bounded single-assumption guards at the unchanged historical prefixes."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditioned_core as previous
from experiments.cnf_assumption_guard import probe, publish_guard
from experiments.cnf_clause_deletion_guard import FORMAT, check_guard
from experiments.cnf_partition_screen import publish_screened_branch
from experiments.cnf_guard_chain import make_record, GuardChainBank
from experiments.validate_cnf_unsat_support import bound
base = previous.base
binding = previous.binding
FIELDS = previous.FIELDS
OLD_FIELDS = previous.OLD_FIELDS
PARENT = Path('experiments/results/cnf-conditioned-core-exposed')
FILES = ('experiments/cnf_assumption_guard.py', 'solver/test_cnf_assumption_guard.py',
         'experiments/compare_cnf_assumption_guard.py', 'experiments/validate_cnf_assumption_guard.py')


def inherited(parent):
    return previous.inherited(parent) + bound(parent['conditioned_core_decisions'])


def run(out):
    out.mkdir(exist_ok=False)
    started = time.perf_counter()
    prior = base.load(PARENT / 'protocol.json')
    sources = dict(base.load(PARENT / 'validation.json')['source_fingerprints'])
    for f, h in sources.items():
        assert base.sha(f) == h, f
    sources.update({f: base.sha(f) for f in FILES})
    p = dict(parent=binding(PARENT / 'checkpoint.json'), prior_study=binding(PARENT / 'report.json'),
             diagnosis=binding(PARENT / 'assumption-reduction-probe.json'),
             historical_protocol=prior['historical_protocol'], historical_trial=prior['historical_trial'],
             targets=prior['targets'], source_fingerprints=sources, limit=2,
             modes=['baseline', 'native-guard', 'trace-guard'],
             limitations=[
                 'Nine arms on three selected historical queries, with exact original pre-query states. Two candidate clauses per case come from the earlier conditioned-core diagnostic; its full-bank discovery cost remains separate and is not an inexpensive recognizer.',
                 'Probe the unsplit target first, then at most two supplied candidates in their original order. Stop at the first unit-refuted strengthened premise. Charge failed probes. A failed probe establishes no entailment or satisfiability claim.',
                 'Both candidate arms pay identical probing. Native-guard solves the selected premise normally; trace-guard reuses its retained unit trace through the frozen native checker. Each still solves the one restricted child and checks all guard composition and witness lifting.',
                 'Record preparation, normalization, probe/verification counts, publication, child work, warm checking, serialization, prefix reconstruction and cold replay. Retained payload is not peak memory. Single samples establish no stable runtime or fresh-coverage claim.',
                 'Remaining general residual search is unrestricted. No minimum-cost expansion, compact closure, minimum support or polynomial arbitrary-SAT guarantee.'])
    base.write(out / 'protocol.json', p)
    hp = bound(p['historical_protocol']); authority = bound(hp['parent'])
    trial = bound(p['historical_trial']); old_rows = bound(trial['queries'])
    prior_samples = [bound(e) for e in bound(p['prior_study'])['samples']]
    samples = []
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        def read(entry, name):
            path = tmp / name; base.restore_archive(entry, path); s = previous.ResidualSolver(path)
            try: return previous.rows(s)
            finally: s.close()
        initial = read(authority['reference_union'], 'initial')
        final = read(trial['archive'], 'final')
        prefixes = previous.history.partition_study.prefixes(initial, final, old_rows)
        for selection in p['targets']:
            cid = selection['case']; old = next(r for r in old_rows if r['case'] == cid); before = prefixes[cid]
            for mode in p['modes']:
                tick = time.perf_counter(); dest = out / f'{cid}-{mode}'; dest.mkdir()
                path = tmp / 'arm'; shutil.copyfile(tmp / 'initial', path)
                s = previous.history.previous.ordinary.AccountedResidualSolver(path)
                with s.db: s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', [(k, v) for k, v in before.items() if k not in initial])
                open_seconds = time.perf_counter() - tick
                try:
                    phase = time.perf_counter()
                    target, _, indices, prepared, normal_counts, near_counts = previous.prepare(s, hp, old)
                    preparation_seconds = time.perf_counter() - phase
                    preparation_solver_counts = dict(s.counts); assert previous.rows(s) == before
                    guards = list(old['record']['guards']); choice = trace = None; probe_counts = Counter()
                    probe_metrics = {}; selection_seconds = 0.; premise = None; premise_seconds = 0.
                    guard_counts = Counter(); guard_metrics = {}
                    if mode != 'baseline':
                        s.counts = Counter(); phase = time.perf_counter()
                        with patch.object(s, '_expand', side_effect=AssertionError('Probe search')), patch.object(s, '_store', side_effect=AssertionError('Probe publication')):
                            choice, trace = probe(s, target, selection['missing'], p['limit'], probe_counts)
                        selection_seconds = time.perf_counter() - phase; probe_metrics = dict(s.counts)
                    if choice is not None and choice['kind'] == 'guard':
                        phase = time.perf_counter()
                        if mode == 'trace-guard':
                            with patch.object(s, '_expand', side_effect=AssertionError('Retained premise search')):
                                guard, _, target, premise = publish_guard(s, target, choice, guard_counts)
                        else:
                            stronger = [list(c) for c in target] + [choice['clause']]
                            premise = s.solve(stronger); assert premise['answer'] is False
                            guard = dict(format=FORMAT, stronger=stronger, stronger_root=premise['root'], removed_clause=choice['clause'])
                            _, target = check_guard(s, target, guard, guard_counts)
                        guard_metrics = dict(s.counts - Counter(premise['metrics']))
                        guards.append(guard); premise_seconds = time.perf_counter() - phase
                    phase = time.perf_counter()
                    child = (publish_screened_branch(s, target, choice['screen'])
                             if mode == 'trace-guard' and choice is not None and choice['kind'] == 'terminal'
                             else s.solve(target))
                    child_seconds = time.perf_counter() - phase
                    assert child['answer'] == old['record']['answer']
                    before_counts = Counter(s.counts); phase = time.perf_counter()
                    record = make_record(s, old['record']['source'], guards, child)
                    composition_seconds = time.perf_counter() - phase; composition_metrics = dict(s.counts - before_counts)
                    with patch.object(s, '_expand', side_effect=AssertionError('Warm search')), patch.object(s, '_store', side_effect=AssertionError('Warm publication')):
                        phase = time.perf_counter(); bank = GuardChainBank(s, [record]); warm_setup_seconds = time.perf_counter() - phase
                        phase = time.perf_counter(); answer = bank.lookup(record['source']); warm_seconds = time.perf_counter() - phase
                        assert answer['answer'] == record['answer']
                    after = previous.rows(s); assert before.items() <= after.items()
                    delta = [(k, v) for k, v in after.items() if k not in before]
                    if mode == 'baseline':
                        prior_baseline = next(r for r in prior_samples if r['case'] == cid and r['mode'] == 'baseline')
                        assert dict(delta) == dict(bound(prior_baseline['delta'])) and record == bound(prior_baseline['records'])[0]
                finally: s.close()
                phase = time.perf_counter(); base.write(dest / 'delta.json', delta); base.write(dest / 'records.json', [record])
                serialization_seconds = time.perf_counter() - phase
                catalogs = [(n, bound(authority[n])) for n in OLD_FIELDS]
                cold = previous.audit_records(path, [record], [], prepared, catalogs, indices)
                result = dict(case=cid, mode=mode, candidates=selection['missing'], choice=choice, probe=trace,
                    prefix_nodes=len(before), prefix_digest=base.key_sha(base.encode(sorted(before.items()))),
                    delta=binding(dest / 'delta.json'), records=binding(dest / 'records.json'),
                    new_nodes=len(delta), new_payload_units=sum(len(k) + len(v) for k, v in delta),
                    retained_bytes=sum((dest / f).stat().st_size for f in ('delta.json', 'records.json')),
                    expanded_nodes=sum(c['metrics'].get('expanded_nodes', 0) for c in (child, premise) if c is not None),
                    child=child, premise=premise, preparation_solver_counts=preparation_solver_counts,
                    normal_counts=normal_counts, near_counts=near_counts, probe_counts=dict(probe_counts), probe_metrics=probe_metrics,
                    guard_counts=dict(guard_counts), guard_metrics=guard_metrics, composition_metrics=composition_metrics,
                    open_seconds=open_seconds, preparation_seconds=preparation_seconds, selection_seconds=selection_seconds,
                    premise_seconds=premise_seconds, child_seconds=child_seconds, composition_seconds=composition_seconds,
                    warm_setup_seconds=warm_setup_seconds, warm_seconds=warm_seconds, serialization_seconds=serialization_seconds,
                    cold=cold, seconds=time.perf_counter() - tick)
                base.write(dest / 'report.json', result); samples.append(binding(dest / 'report.json'))
                print(base.encode({k: result[k] for k in ('case', 'mode', 'expanded_nodes', 'new_nodes', 'new_payload_units')}), flush=True)
    base.write(out / 'report.json', dict(protocol=binding(out / 'protocol.json'), samples=samples, seconds=time.perf_counter() - started))


if __name__ == '__main__':
    run(Path(sys.argv[1]))
