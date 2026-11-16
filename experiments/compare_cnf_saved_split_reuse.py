#!/usr/bin/env python3
"""Case-6 continuation with and without its saved source-split certificates."""
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
from experiments.cnf_saved_split_reuse import restore_variant, candidates
from unittest.mock import patch
base = nested.base
PARENT = Path('experiments/results/cnf-canonical-audit')
MODES = ('retained', 'ablated')


def binding(path): return dict(path=str(path), sha256=base.sha(path))


def worker(out, protocol, mode):
    out.mkdir(exist_ok=False); started = time.perf_counter(); samples = []
    cp = base.load(protocol['checkpoint']['path']); target = base.load(protocol['target']['path'])
    queries = base.load(protocol['queries']['path']); root = queries[target['case']]['roots'][0]
    with tempfile.TemporaryDirectory() as td:
        path = Path(td)/'h'; variant=restore_variant(cp,path,target['source'],ablate=mode=='ablated')
        h = base.CompleteAdmissionInventory(path, **protocol['options']); h.set_admission_budget(0)
        initial = base.rows(h); pairs = dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
        try:
            assert root == h._canonical(target['original_source'], 0)[2]
            session = ScopedNestedRefinement(h, root, target.get('resume_decisions', {}))
            assert not session.coverage.closed()[0]
            startup = time.perf_counter()-started
            initial_stats = dict(main_inventory_checked_nodes=len(h.checked), registry=session.registry.statistics(), variant=variant)
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
        database_bytes=final['archive']['database_bytes'], compressed_bytes=final['archive']['compressed_bytes'])
    base.write(out/'report.json', dict(summary=summary,samples=samples))


def run(out):
    out.mkdir(exist_ok=False); cp=base.load(PARENT/'checkpoint.json'); previous=base.load(PARENT/'validation.json')
    sources=dict(previous['source_fingerprints'])
    for p,digest in sources.items(): assert base.sha(p)==digest,p
    for p in ('experiments/cnf_saved_split_reuse.py','experiments/compare_cnf_saved_split_reuse.py','solver/test_cnf_saved_split_reuse.py'):
        sources[p]=base.sha(p)
    protocol=dict(checkpoint=binding(PARENT/'checkpoint.json'),target=binding(PARENT/'next-discovery.json'),queries=cp['queries'],
        options=base.OPTIONS,state_limit=128,pair_limit=16,max_batches=4,
        orders=[MODES,tuple(reversed(MODES))],source_fingerprints=sources,
        limitations=['Both modes use the unchanged scoped refinement and canonical full auditor. Only four saved source-split records are omitted in the isolated control copy.',
            'The control retains every pattern row and every other split. It reconstructs missing certificates normally; all acquisitions from both variants are preserved in the final union.',
            'This intervention changes selection information and certificate reuse together. It is not a fresh empty-history solve or an isolation of closed-branch checking alone.',
            'All source records, original bindings, proofs and complete archives receive independent cold checks. No validity flag is trusted.',
            'Case 6 is a known development input, not a holdout; two reversed paired fresh-process repetitions, with identical budgets and no per-arm policy tuning.',
            'Wall time includes restoration/control preparation, setup, work, bookkeeping, compression, query and full checking; excludes interpreter imports and final summary write. RSS includes imports and all phases.'])
    diagnostic_start=time.perf_counter();diagnostic=[];queries=base.load(cp['queries']['path'])
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'h';base.restore_archive(cp['archive'],path);before=base.sha(path)
        h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        try:
            with base.no_acquisition(),patch.object(h,'_admit',side_effect=AssertionError('diagnostic admission')),patch.object(base.split,'discover_simplification',side_effect=AssertionError('diagnostic assumption')):
                for q in queries:
                    if q['selected_depth'] is not None:continue
                    session=ScopedNestedRefinement(h,q['roots'][0]);closed={session.coverage.keys[i] for i in session.coverage.justified}
                    for source in session.by_source:
                        if source in closed or h._load(source)['kind']!='unresolved':continue
                        rows=candidates(session,source);old=min(rows,key=lambda r:r['old_rank']);alternate=min(rows,key=lambda r:r['open_distinct_rank'])
                        diagnostic.append(dict(case=q['case'],source_sha256=base.key_sha(source),candidates=rows,
                            old_variable=old['variable'],alternate_variable=alternate['variable'],same_choice=old['identity_sha256']==alternate['identity_sha256']))
        finally:h.close();assert base.sha(path)==before
    base.write(out/'diagnostic.json',dict(checkpoint=protocol['checkpoint'],rows=diagnostic,seconds=time.perf_counter()-diagnostic_start,
        no_acquisition=True,changed_choices=sum(not r['same_choice'] for r in diagnostic),scope='Existing unresolved sources reachable from the twelve original depth-zero roots; heuristic ranks, not optimality certificates.'))
    protocol['diagnostic']=binding(out/'diagnostic.json')
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
        fixed=('batches','closed','covered','entered','stored','probes','assumptions','reused_pairs','added_pairs','database_bytes','compressed_bytes','pattern_digest','pair_digest','initial','final_registry','final_main_inventory_checked_nodes','normalization_counts')
        for b in trials[1:]:
            for k in fixed: assert a[k]==b[k],k
        summary[mode]={**{k:a[k] for k in fixed},**{'mean_'+k:sum(t[k] for t in trials)/len(trials) for k in (
            'startup_seconds','operation_seconds','bookkeeping_seconds','query_check_seconds','cold_seconds','compression_seconds','stream_wall_seconds','peak_rss_raw')}}
    base.write(out/'report.json',dict(protocol_sha256=base.sha(out/'protocol.json'),samples=samples,summary=summary))
    print(base.encode({m:{k:v for k,v in s.items() if k not in ('initial','final_registry')} for m,s in summary.items()}),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker': worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else: run(Path(sys.argv[1]))
