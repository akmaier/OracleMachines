#!/usr/bin/env python3
"""Case-21 committed, always-pilot and progress-gated scheduling comparison."""
from collections import Counter
from unittest.mock import patch
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_nested_refinement as nested
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
from experiments.cnf_canonical_audit import audit
from experiments.cnf_query_checkpoint import check_query
from experiments.cnf_pilot_refinement import PilotRefinement
from experiments.cnf_progress_pilot import ProgressPilotRefinement
from experiments.cnf_saved_split_reuse import candidates
base = nested.base
PARENT = Path('experiments/results/cnf-pilot-transfer')
MODES = ('committed', 'pilot', 'gated')


def binding(path): return dict(path=str(path), sha256=base.sha(path))


def worker(out, protocol, mode):
    out.mkdir(exist_ok=False); started = time.perf_counter(); samples = []
    cp = base.load(protocol['checkpoint']['path']); target = base.load(protocol['target']['path'])
    queries = base.load(protocol['queries']['path']); root = queries[target['case']]['roots'][0]
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'h'; base.restore_archive(cp['archive'], path)
        h = base.CompleteAdmissionInventory(path, **protocol['options']); h.set_admission_budget(0)
        initial = base.rows(h); pairs = dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
        try:
            assert root == h._canonical(target['original_source'], 0)[2]
            if mode == 'gated':
                session = ProgressPilotRefinement(h, root, target['source'], target.get('resume_gated_state'))
            elif mode == 'pilot':
                session = PilotRefinement(h, root, target['source'], target.get('resume_pilot_state'))
            elif mode == 'committed':
                session = ScopedNestedRefinement(h, root, target.get('resume_decisions', {}))
            else:
                raise ValueError('Unknown mode')
            assert not session.coverage.closed()[0]
            startup = time.perf_counter()-started
            initial_stats = dict(main_inventory_checked_nodes=len(h.checked), registry=session.registry.statistics())
            for batch in range(protocol['max_batches']):
                dest = out/f'batch-{batch}'; dest.mkdir()
                result = session.batch(state_limit=protocol['state_limit'], pair_limit=protocol['pair_limit'])
                tick = time.perf_counter(); current = base.rows(h)
                current_pairs = dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
                assert initial.items() <= current.items() and pairs.items() <= current_pairs.items()
                flags, plan = base.compose(h, [root], session.registry, Counter())
                proof = base.expand(h, plan, [root], session.registry, Counter())
                base.split.verify_positive(h, proof, proof['roots'], list(session.records.values()), Counter())
                assert flags == [result['closed']]
                result.setdefault('pilot_state',None)
                result.update(mode=mode, batch=batch, target_proof=proof, patterns=len(current), pairs=len(current_pairs),
                    registry=session.registry.statistics(), main_inventory_checked_nodes=len(h.checked),
                    pattern_digest=base.key_sha(base.encode(sorted(current.items()))),
                    pair_digest=base.key_sha(base.encode(sorted(current_pairs.items()))))
                result['bookkeeping_seconds'] = time.perf_counter()-tick
                result['archive'] = base.archive(path, dest)
                result['query_check'] = check_query(path, protocol['options'], target['original_source'], root, proof, result['closed'])
                result['cold'] = audit(path, protocol, canonical=True)
                base.write(dest/'report.json', result); samples.append(binding(dest/'report.json'))
                print(base.encode(dict(mode=mode,batch=batch,closed=result['closed'],covered=result['cold']['coverage']['covered'],
                    stored=result['stored'],probes=result['probes'],reason=result['reason'],seconds=result['seconds'])), flush=True)
                if result['closed']: break
        finally:
            h.close()
    records = [base.load(e['path']) for e in samples]; final = records[-1]
    summary = dict(mode=mode, batches=len(records), initial=initial_stats, closed=final['closed'],
        covered=final['cold']['coverage']['covered'], entered=sum(r['entered'] for r in records),
        unique_admissions=len({k for r in records for k in r['admitted_ids']}),
        stored=sum(r['stored'] for r in records), probes=sum(r['probes'] for r in records),
        assumptions=sum(r['selection_counts'].get('bootstrap_fresh_assumptions',0) for r in records),
        reused_pairs=sum(r['selection_counts'].get('bootstrap_reused_pairs',0) for r in records),
        added_pairs=final['pairs']-len(pairs), final_main_inventory_checked_nodes=final['main_inventory_checked_nodes'],
        final_registry=final['registry'], pattern_digest=final['pattern_digest'], pair_digest=final['pair_digest'],
        startup_seconds=startup, operation_seconds=sum(r['seconds'] for r in records),
        bookkeeping_seconds=sum(r['bookkeeping_seconds'] for r in records),
        query_check_seconds=sum(r['query_check']['seconds'] for r in records), cold_seconds=sum(r['cold']['seconds'] for r in records),
        compression_seconds=sum(r['archive']['seconds'] for r in records), stream_wall_seconds=time.perf_counter()-started,
        peak_rss_raw=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, platform=sys.platform,
        peak_rss_unit='bytes' if sys.platform=='darwin' else 'KiB' if sys.platform.startswith('linux') else 'platform-dependent',
        normalization_counts=final['cold']['normalization_counts'],
        pilot_completed=None if final['pilot_state'] is None else final['pilot_state']['completed'],
        pilot_entered=0 if final['pilot_state'] is None else sum(e['entered'] for e in final['pilot_state']['events']),
        pilot_probes=0 if final['pilot_state'] is None else sum(e['probes'] for e in final['pilot_state']['events']),
        source_choice=base.load_json(final['decisions'][target['source']])[1],
        gate_action=None if mode != 'gated' else final['pilot_state']['gate'],
        gate_baseline=None if mode != 'gated' else final['pilot_state']['baseline'],
        database_bytes=final['archive']['database_bytes'], compressed_bytes=final['archive']['compressed_bytes'])
    base.write(out/'report.json', dict(summary=summary,samples=samples))



def run(out):
    out.mkdir(exist_ok=False)
    cp = base.load(PARENT/'checkpoint.json'); validation = base.load(PARENT/'validation.json')
    sources = dict(validation['source_fingerprints'])
    for path, digest in sources.items():
        assert base.sha(path) == digest, path
    for path in ('experiments/cnf_progress_pilot.py', 'experiments/compare_cnf_progress_pilot.py',
                 'experiments/validate_cnf_progress_pilot.py', 'solver/test_cnf_progress_pilot.py'):
        sources[path] = base.sha(path)
    protocol = base.load(PARENT/'protocol.json')
    protocol.update(checkpoint=binding(PARENT/'checkpoint.json'), target=binding(PARENT/'next-discovery.json'),
        queries=cp['queries'], source_fingerprints=sources, inherited_policy=binding(PARENT/'protocol.json'),
        orders=[MODES, tuple(reversed(MODES))],
        progress_gate='After first completed trial: skip second iff selected unresolved literal mass strictly decreases, or whole query closes. Otherwise use the unchanged second-trial/commit rule.')
    protocol['limitations'] = [
        'Case 21 is an existing development input from a new category for these policies, not a holdout. The gate was proposed from cases 11/13 before this acquisition; no tuning on case 21.',
        'All modes use the same full parent, acquisition rules, scoped checker and full canonical cold audit. The gate changes scheduling only; independent proof checking establishes coverage.',
        'Same 128-admission and 16-operation allowance per batch; at most four batches. All pilot work shares this allowance. No per-route budget reset. Losing and partial acquisitions remain stored.',
        'Only a unary selected prefix and two saved source alternatives are supported. Strict decrease of unresolved literal mass is a heuristic, not a lower bound on future cost or a guarantee of best expansion.',
        'The first-trial baseline is captured before acquisition and persisted through interruptions. The second trial is skipped only after completion. Saved gate state schedules work, not proof acceptance.',
        'Two reversed-order fresh-process triples. Wall time includes restoration, setup, acquisition, gating, bookkeeping, compression, query/full cold checks; excludes imports/final summary. RSS includes all phases.',
        'Preflight is acquisition-free and separately timed. Each timed worker reconstructs independently. Parent acquisition is charged in earlier experiments.'
    ]
    tick = time.perf_counter(); target = base.load(protocol['target']['path'])
    root = base.load(protocol['queries']['path'])[target['case']]['roots'][0]
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'h'; base.restore_archive(cp['archive'], path); before = base.sha(path)
        h = base.CompleteAdmissionInventory(path, **protocol['options']); h.set_admission_budget(0)
        try:
            with base.no_acquisition(), patch.object(h, '_admit', side_effect=AssertionError('preflight acquisition')):
                session = ProgressPilotRefinement(h, root, target['source'])
                assert not session.coverage.closed()[0]
                preflight = dict(case=target['case'], unary_prefix_accepted=True,
                    candidates=candidates(session, target['source']), baseline=session.baseline,
                    variables=[session.records[k]['variable'] for k in session.candidates], no_acquisition=True)
        finally:
            h.close(); assert base.sha(path) == before
    preflight['seconds'] = time.perf_counter()-tick
    base.write(out/'preflight.json', preflight); protocol['preflight'] = binding(out/'preflight.json')
    base.write(out/'protocol.json', protocol)
    samples = []
    for repeat, order in enumerate(protocol['orders']):
        for mode in order:
            dest = out/f'{mode}-{repeat}'
            subprocess.run([sys.executable, __file__, 'worker', str(dest), str(out/'protocol.json'), mode], check=True)
            samples.append(dict(mode=mode, repeat=repeat, **binding(dest/'report.json')))
    summary = {}
    for mode in MODES:
        trials = [base.load(s['path'])['summary'] for s in samples if s['mode'] == mode]; first = trials[0]
        timed = [k for k in first if k.endswith('_seconds') or k == 'peak_rss_raw']
        fixed = [k for k in first if k not in timed and k != 'mode']
        for other in trials[1:]:
            for k in fixed:
                assert first[k] == other[k], k
        summary[mode] = {**{k:first[k] for k in fixed},
                        **{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in timed}}
    base.write(out/'report.json', dict(protocol_sha256=base.sha(out/'protocol.json'), samples=samples, summary=summary))
    print(base.encode({m:{k:v for k,v in s.items() if k not in ('initial','final_registry')} for m,s in summary.items()}), flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'worker':
        worker(Path(sys.argv[2]), base.load(sys.argv[3]), sys.argv[4])
    else:
        run(Path(sys.argv[1]))
