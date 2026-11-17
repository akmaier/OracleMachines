#!/usr/bin/env python3
"""Historical pricing and fresh matched streams for target-local guard discovery."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import resource, shutil, subprocess, sys, tempfile, time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_assumption_guard as old
from experiments import compare_cnf_premise_guard as prep
from experiments import compare_cnf_partition_screen as partition
from experiments.cnf_local_guard import probe
from experiments.cnf_assumption_guard import publish_guard
from experiments.cnf_partition_screen import publish_screened_branch
from experiments.cnf_guard_chain import make_record, GuardChainBank
from experiments.cnf_premise_guard import PremiseGuardSelector
from experiments.cnf_incremental_archive import ResidualAppendCursor
from experiments.validate_cnf_unsat_support import bound
base = old.base; binding = old.binding; native = old.previous
FIELDS = old.FIELDS; OLD_FIELDS = old.OLD_FIELDS
PARENT = Path('experiments/results/cnf-assumption-guard')
FILES = ('experiments/cnf_local_guard.py', 'solver/test_cnf_local_guard.py',
         'experiments/compare_cnf_local_guard.py', 'experiments/validate_cnf_local_guard.py')
MODES = ('baseline', 'local')


def inherited(parent): return old.inherited(parent) + bound(parent['assumption_guard_decisions'])


def exclusions(parent):
    records = sum((bound(parent[f]) for f in FIELDS), []) + inherited(parent)
    return [dict(query_root=k) for k in sorted({r['query_root'] for r in records})]


def evaluate(s, source, target, guards, mode, eligible, limit):
    start = time.perf_counter(); guards = list(guards); choice = trace = None
    probe_counts = Counter(); probe_metrics = {}; selection_seconds = 0.; premise = None
    premise_seconds = 0.; guard_counts = Counter(); guard_metrics = {}
    if mode == 'local' and eligible:
        s.counts = Counter(); tick = time.perf_counter()
        with patch.object(s, '_expand', side_effect=AssertionError('Local discovery search')), patch.object(s, '_store', side_effect=AssertionError('Local discovery publication')):
            choice, trace = probe(s, target, limit, probe_counts)
        selection_seconds = time.perf_counter() - tick; probe_metrics = dict(s.counts)
    if choice is not None and choice['kind'] == 'guard':
        tick = time.perf_counter()
        with patch.object(s, '_expand', side_effect=AssertionError('Premise search')):
            guard, _, target, premise = publish_guard(s, target, choice, guard_counts)
        guard_metrics = dict(s.counts - Counter(premise['metrics'])); guards.append(guard)
        premise_seconds = time.perf_counter() - tick
    tick = time.perf_counter()
    child = (publish_screened_branch(s, target, choice['screen']) if choice is not None and choice['kind'] == 'terminal' else s.solve(target))
    child_seconds = time.perf_counter() - tick; tick = time.perf_counter(); before = Counter(s.counts)
    record = make_record(s, source, guards, child)
    composition_seconds = time.perf_counter() - tick; composition_metrics = dict(s.counts - before)
    return dict(record=record, local_eligible=eligible, local_choice=choice, local_probe=trace, child=child, premise=premise,
                probe_counts=dict(probe_counts), probe_metrics=probe_metrics, guard_counts=dict(guard_counts), guard_metrics=guard_metrics,
                composition_metrics=composition_metrics, selection_seconds=selection_seconds, premise_seconds=premise_seconds,
                child_seconds=child_seconds, composition_seconds=composition_seconds, evaluation_seconds=time.perf_counter() - start)


def summarize(records):
    acquired = [c for r in records for c in (r['child'], r['premise']) if c is not None]
    metrics = Counter()
    for c in acquired: metrics.update(c['metrics'])
    return dict(expanded_nodes=metrics['expanded_nodes'], trace_publications=metrics['screen_trace_publications'],
                local_calls=sum(r['local_probe'] is not None for r in records),
                local_guards=sum(bool(r['local_choice'] and r['local_choice']['kind'] == 'guard') for r in records),
                local_terminals=sum(bool(r['local_choice'] and r['local_choice']['kind'] == 'terminal') for r in records),
                premise_probes=sum(r['probe_counts'].get('local_premise_probes', 0) for r in records),
                propagation_literal_visits=metrics['propagation_literal_visits'] + sum(r['probe_counts'].get('propagation_literal_visits', 0) for r in records))


def history(out, p):
    out.mkdir(); tick = time.perf_counter(); hp = bound(p['historical_protocol']); authority = bound(hp['parent'])
    trial = bound(p['historical_trial']); old_rows = bound(trial['queries']); samples = []
    prior_samples = [bound(e) for e in bound(p['historical_baselines'])['samples']]
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        def read(entry, name):
            path = tmp / name; base.restore_archive(entry, path); s = native.ResidualSolver(path)
            try: return native.rows(s)
            finally: s.close()
        initial = read(authority['reference_union'], 'initial'); final = read(trial['archive'], 'final')
        prefixes = partition.partition_study.prefixes(initial, final, old_rows)
        for cid in p['historical_cases']:
            old_row = next(r for r in old_rows if r['case'] == cid); before = prefixes[cid]
            for mode in MODES:
                start = time.perf_counter(); dest = out / f'{cid}-{mode}'; dest.mkdir(); path = tmp / 'arm'
                shutil.copyfile(tmp / 'initial', path); s = prep.ordinary.AccountedResidualSolver(path)
                with s.db: s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)', [(k, v) for k, v in before.items() if k not in initial])
                open_seconds = time.perf_counter() - start
                try:
                    phase = time.perf_counter(); target, _, indices, prepared, normal_counts, near_counts = native.prepare(s, hp, old_row)
                    preparation_seconds = time.perf_counter() - phase; preparation_metrics = dict(s.counts)
                    assert native.rows(s) == before
                    result = evaluate(s, old_row['record']['source'], target, old_row['record']['guards'], mode, True, p['variable_limit'])
                    assert result['record']['answer'] == old_row['record']['answer']
                    after = native.rows(s); assert before.items() <= after.items(); delta = [(k, v) for k, v in after.items() if k not in before]
                    if mode == 'baseline':
                        expected = next(r for r in prior_samples if r['case'] == cid and r['mode'] == 'baseline')
                        assert dict(delta) == dict(bound(expected['delta'])) and result['record'] == bound(expected['records'])[0]
                    with patch.object(s, '_expand', side_effect=AssertionError('Warm search')), patch.object(s, '_store', side_effect=AssertionError('Warm publication')):
                        phase = time.perf_counter(); bank = GuardChainBank(s, [result['record']]); warm_setup_seconds = time.perf_counter() - phase
                        phase = time.perf_counter(); assert bank.lookup(result['record']['source'])['answer'] == result['record']['answer']; warm_seconds = time.perf_counter() - phase
                finally: s.close()
                phase = time.perf_counter(); base.write(dest / 'delta.json', delta); base.write(dest / 'records.json', [result['record']]); serialization_seconds = time.perf_counter() - phase
                cold = native.audit_records(path, [result['record']], [], prepared, [(n, bound(authority[n])) for n in OLD_FIELDS], indices)
                result.update(case=cid, mode=mode, prefix_nodes=len(before), prefix_digest=base.key_sha(base.encode(sorted(before.items()))),
                              delta=binding(dest / 'delta.json'), records=binding(dest / 'records.json'), new_nodes=len(delta),
                              new_payload_units=sum(len(k) + len(v) for k, v in delta), retained_bytes=sum((dest / f).stat().st_size for f in ('delta.json', 'records.json')),
                              normal_counts=normal_counts, near_counts=near_counts, preparation_metrics=preparation_metrics,
                              open_seconds=open_seconds, preparation_seconds=preparation_seconds, warm_setup_seconds=warm_setup_seconds,
                              warm_seconds=warm_seconds, serialization_seconds=serialization_seconds, cold=cold, seconds=time.perf_counter() - start,
                              summary=summarize([result]))
                base.write(dest / 'report.json', result); samples.append(binding(dest / 'report.json'))
                print(base.encode(dict(cohort='historical', case=cid, mode=mode, rows=len(delta), bytes=result['new_payload_units'], **result['summary'])), flush=True)
    base.write(out / 'report.json', dict(samples=samples, seconds=time.perf_counter() - tick))


def worker(out, p, catalog, mode):
    out.mkdir(); start = time.perf_counter(); parent = bound(p['parent']); records = []; warm = []
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'proofs'; base.restore_archive(parent['reference_union'], path)
        s = prep.ordinary.AccountedResidualSolver(path, node_limit=p['node_limit']); initial = native.rows(s); cursor = ResidualAppendCursor(s)
        try:
            tick = time.perf_counter()
            with patch.object(s, '_expand', side_effect=AssertionError('Preparation search')):
                bank, extensions, indices, prepared, cofactors = prep.setup(s, p)
                selector = prep.ordinary.AlternativeGuardSelector(p['alternative_budget']); near = PremiseGuardSelector(prepared['cores'])
                retained = partition.banks(s, inherited(parent))
            preparation_seconds = time.perf_counter() - tick; near_setup_counts = dict(near.counts); assert not cursor.take()
            setup_seconds = time.perf_counter() - start
            for case in catalog['cases']:
                tick = time.perf_counter(); s.counts = Counter(); source = case['source']; assert partition.lookup(retained, source) is None
                target, ordinary, ordinary_counts = prep.prepare(s, source, p, bank, extensions, cofactors, selector)
                ordinary_ids = cursor.take(); ordinary_metrics = dict(s.counts)
                guards = [] if ordinary['guard'] is None else [ordinary['guard']]
                eligible = bool(guards) and not ordinary['target_known'] and ordinary['cofactor'] is None
                near_choice = None; near_counts = Counter(); before_counts = Counter(s.counts); phase = time.perf_counter()
                if eligible:
                    with patch.object(s, '_expand', side_effect=AssertionError('Near guard search')):
                        old_counts = Counter(near.counts); near_choice, guard, target = near.select(s, target); near_counts.update(near.counts - old_counts)
                        if guard is not None: guards.append(guard)
                near_seconds = time.perf_counter() - phase; near_metrics = dict(s.counts - before_counts); near_ids = cursor.take()
                before_counts = Counter(s.counts); cnf, _, key = s._canonical(target); known = s._read(key, cnf, purpose='local_target') is not None
                eligibility_metrics = dict(s.counts - before_counts)
                result = evaluate(s, source, target, guards, mode, not known, p['variable_limit']); added = cursor.take()
                all_added = list(ordinary_ids) + list(near_ids) + list(added)
                result.update(case=case['case'], template_case=case['template_case'], ordinary=ordinary, ordinary_counts=dict(ordinary_counts),
                    ordinary_metrics=ordinary_metrics, ordinary_ids=sorted(map(base.key_sha, ordinary_ids)), near_eligible=eligible, near_choice=near_choice,
                    near_counts=dict(near_counts), near_metrics=near_metrics, near_ids=sorted(map(base.key_sha, near_ids)), near_seconds=near_seconds,
                    eligibility_metrics=eligibility_metrics, new_ids=sorted(map(base.key_sha, all_added)), new_nodes=len(all_added), seconds=time.perf_counter() - tick)
                records.append(result)
            tick = time.perf_counter(); retained = partition.banks(s, inherited(parent) + [r['record'] for r in records]); warm_setup_seconds = time.perf_counter() - tick
            with patch.object(s, '_expand', side_effect=AssertionError('Warm search')), patch.object(s, '_store', side_effect=AssertionError('Warm publication')):
                for case in catalog['cases']:
                    tick = time.perf_counter(); answer = partition.lookup(retained, case['source']); assert answer is not None
                    warm.append(dict(case=case['case'], result=answer, seconds=time.perf_counter() - tick))
            assert not cursor.take(); final = native.rows(s); assert initial.items() <= final.items(); census = s.archive_storage()
        except BaseException:
            s.close(); base.write(out / 'partial.json', records); base.archive(path, out); raise
        else: s.close()
        cold = native.audit_records(path, inherited(parent) + [r['record'] for r in records], bound(parent['conditioned_core_projections']),
                                    prepared, [(n, bound(parent[n])) for n in OLD_FIELDS], indices)
        tick = time.perf_counter(); base.write(out / 'queries.json', records); base.write(out / 'warm.json', warm); serialization_seconds = time.perf_counter() - tick
        archive = base.archive(path, out)
    summary = dict(mode=mode, queries=len(records), positive=sum(r['record']['answer'] for r in records), nodes=len(final),
                   new_nodes=len(final) - len(initial), new_payload_units=sum(len(k) + len(v) for k, v in final.items() if k not in initial),
                   **summarize(records), setup_seconds=setup_seconds, preparation_seconds=preparation_seconds,
                   query_seconds=sum(r['seconds'] for r in records), warm_setup_seconds=warm_setup_seconds, warm_query_seconds=sum(r['seconds'] for r in warm),
                   serialization_seconds=serialization_seconds, cold_seconds=cold['seconds'], compression_seconds=archive['seconds'],
                   database_bytes=archive['database_bytes'], compressed_bytes=archive['compressed_bytes'],
                   sidecar_bytes=sum((out / f).stat().st_size for f in ('queries.json', 'warm.json')),
                   row_digest=base.key_sha(base.encode(sorted(final.items()))), repeat_new_nodes=0,
                   peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024))
    result = dict(summary=summary, queries=binding(out / 'queries.json'), warm=binding(out / 'warm.json'), archive=archive, cold=cold,
                  near_setup_counts=near_setup_counts, near_counts=dict(near.counts), census=census, cursor_counts=dict(cursor.stats))
    base.write(out / 'report.json', result); result['summary']['complete_worker_seconds'] = time.perf_counter() - start; base.write(out / 'report.json', result)


def run(out):
    out.mkdir(exist_ok=False); parent = base.load(PARENT / 'checkpoint.json'); old_p = base.load(PARENT / 'protocol.json')
    bank_p = base.load('experiments/results/cnf-premise-guard/protocol.json'); sources = dict(base.load(PARENT / 'validation.json')['source_fingerprints'])
    for f, h in sources.items(): assert base.sha(f) == h, f
    sources.update({f: base.sha(f) for f in FILES}); base.write(out / 'previous-decisions.json', exclusions(parent))
    p = dict(parent=binding(PARENT / 'checkpoint.json'), source_fingerprints=sources, support_index=parent['extended_support_proposals'], causal_index=parent['causal_support_proposals'],
             template_catalog=bank_p['template_catalog'], cores=bank_p['cores'], bank_catalog=bank_p['bank_catalog'], previous_decisions=binding(out / 'previous-decisions.json'),
             historical_protocol=old_p['historical_protocol'], historical_trial=old_p['historical_trial'], historical_baselines=binding(PARENT / 'report.json'),
             diagnosis=binding(PARENT / 'discovery-probe.json'), historical_cases=[43, 172, 70], node_limit=100000, alternative_budget=1,
             variable_limit=4, per_template=64, orders=[MODES, MODES[::-1]],
             limitations=[
                 'Six historical exact-prefix arms and 192 new neighbouring CNFs excluded from all inherited ordinary/composed query roots and native roots. Fresh streams use two reversed-order pairs in separate processes, without concurrent tests or profiles.',
                 'Fixed target-local policy: one baseline propagation, exclude forced variables, rank by original binary incidence and source identifier, try false then true for at most four variables, stop at first unit-refuted premise. No bank scan at this discovery stage; inherited ordinary preparation remains charged.',
                 'Fresh local discovery runs on every still-unknown target after the shared ordinary and optional premise-first guard stages, including targets without an earlier guard. General remaining solving uses the frozen decider. No optimal-cost guarantee or broad generalization beyond this generator.',
                 'A terminal baseline trace or selected premise trace is reused through the native verifier. Failed probes, normalization/ranking, remaining solving, composition, source sidecars, serialization, compression, full cold replay and process RSS are retained.',
                 'Source-bound chains persist separately from ordinary catalogs; model witnesses are rebound to the preserved union when needed. Original payloads and all alternative certificates remain retained. No new Lean or unrestricted-SAT resource bound.'])
    base.write(out / 'protocol.json', p)
    history(out / 'historical', p)
    tick = time.perf_counter()
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / 'initial'; base.restore_archive(parent['reference_union'], path); s = native.ResidualSolver(path)
        try: catalog = prep.ordinary.eager.previous.inputs(s, p)
        finally: s.close()
    base.write(out / 'cases.json', catalog); base.write(out / 'preflight.json', dict(seconds=time.perf_counter() - tick, selection=catalog['selection']))
    samples = []
    for repeat, order in enumerate(p['orders']):
        for mode in order:
            dest = out / f'{mode}-{repeat}'
            subprocess.run([sys.executable, __file__, 'worker', str(dest), str(out / 'protocol.json'), str(out / 'cases.json'), mode], check=True, stdout=subprocess.DEVNULL)
            samples.append(dict(repeat=repeat, mode=mode, **binding(dest / 'report.json'))); print('fresh', mode, repeat, flush=True)
    summary = {}
    for mode in MODES:
        data = [bound(e)['summary'] for e in samples if e['mode'] == mode]; first = data[0]
        timed = [k for k in first if k.endswith('_seconds') or k == 'peak_rss_bytes']
        fixed = [k for k in first if k not in timed and k not in ('mode', 'sidecar_bytes')]
        for other in data[1:]:
            for k in fixed: assert first[k] == other[k], k
        summary[mode] = {**{k: first[k] for k in fixed}, **{'mean_' + k: sum(r[k] for r in data) / len(data) for k in timed}, 'sidecar_bytes': [r['sidecar_bytes'] for r in data]}
    base.write(out / 'report.json', dict(protocol=binding(out / 'protocol.json'), historical=binding(out / 'historical/report.json'),
                                       cases=binding(out / 'cases.json'), samples=samples, summary=summary))
    print(base.encode(summary), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'worker': worker(Path(sys.argv[2]), base.load(sys.argv[3]), base.load(sys.argv[4]), sys.argv[5])
    else: run(Path(sys.argv[1]))
