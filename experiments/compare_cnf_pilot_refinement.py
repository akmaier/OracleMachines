#!/usr/bin/env python3
"""Case-11 committed refinement versus one completed pilot step on two saved routes."""
from collections import Counter
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
base = nested.base
PARENT = Path('experiments/results/cnf-saved-split-reuse')
MODES = ('committed', 'pilot')


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
            session = (PilotRefinement(h,root,target['source'],target.get('resume_pilot_state')) if mode=='pilot'
                else ScopedNestedRefinement(h,root,target.get('resume_decisions',{})))
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
        database_bytes=final['archive']['database_bytes'], compressed_bytes=final['archive']['compressed_bytes'])
    base.write(out/'report.json', dict(summary=summary,samples=samples))


def run(out):
    out.mkdir(exist_ok=False); cp=base.load(PARENT/'checkpoint.json'); previous=base.load(PARENT/'validation.json')
    sources=dict(previous['source_fingerprints'])
    for p,digest in sources.items(): assert base.sha(p)==digest,p
    for p in ('experiments/cnf_pilot_refinement.py','experiments/compare_cnf_pilot_refinement.py','solver/test_cnf_pilot_refinement.py'):
        sources[p]=base.sha(p)
    protocol=dict(checkpoint=binding(PARENT/'checkpoint.json'),target=binding(PARENT/'next-discovery.json'),queries=cp['queries'],
        options=base.OPTIONS,state_limit=128,pair_limit=16,max_batches=4,
        orders=[MODES,tuple(reversed(MODES))],source_fingerprints=sources,
        pilot_width=2,pilot_completed_steps_per_route=1,
        limitations=['Both modes retain the entire identical parent, scoped registry and canonical complete auditor. Only work scheduling differs.',
            'The optional pilot compares the two best initial saved routes, using one completed nested acquisition on each, then minimum pending-count/remaining-literal-count/frontier-count/variable order.',
            'All pilot work shares the same 128-admission and 16-operation batch allowance as continuation. Partial acquisitions remain on their current arm until complete. Every intermediate pattern and pair remains stored.',
            'The current pilot requires an unresolved choice source below a unary root prefix with at least two saved alternatives. This is not a general component scheduler or an optimality claim.',
            'Case 11 is a known development input, not a holdout; two reversed paired fresh-process repetitions. No per-arm budget or policy tuning.',
            'Wall time includes restoration, setup, selection, pilot and committed work, bookkeeping, compression, query and full cold checking; excludes interpreter imports and final summary write. RSS includes all phases.'])
    base.write(out/'protocol.json',protocol);samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        trials=[base.load(s['path'])['summary'] for s in samples if s['mode']==mode]
        a=trials[0]
        fixed=('batches','closed','covered','entered','unique_admissions','stored','probes','assumptions','reused_pairs','added_pairs','database_bytes','compressed_bytes','pattern_digest','pair_digest','initial','final_registry','final_main_inventory_checked_nodes','normalization_counts','pilot_completed','pilot_entered','pilot_probes','source_choice')
        for b in trials[1:]:
            for k in fixed: assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in (
            'startup_seconds','operation_seconds','bookkeeping_seconds','query_check_seconds','cold_seconds','compression_seconds','stream_wall_seconds','peak_rss_raw')}}
    base.write(out/'report.json',dict(protocol_sha256=base.sha(out/'protocol.json'),samples=samples,summary=summary))
    print(base.encode({m:{k:v for k,v in s.items() if k not in ('initial','final_registry')} for m,s in summary.items()}),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker': worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else: run(Path(sys.argv[1]))
