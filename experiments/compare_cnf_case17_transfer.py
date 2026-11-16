#!/usr/bin/env python3
"""Frozen-policy transfer and the marginal value of case-16 history.

Both arms refine case 17 with the unchanged nested policy. Only their initial
history differs. Each repetition runs in a fresh process for lifecycle/RSS data.
"""
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_nested_refinement as nested
base=nested.base

PARENT=Path('experiments/results/cnf-nested-refinement')
MODES=('retained','before_case16')


def binding(path):return dict(path=str(path),sha256=base.sha(path))


def worker(out,protocol,mode):
    out.mkdir(exist_ok=False);started=time.perf_counter();samples=[]
    target=base.load(protocol['target']['path']);queries=base.load(protocol['queries']['path'])
    root=queries[target['case']]['roots'][0];cp=base.load(protocol['checkpoints'][mode]['path'])
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'h';base.restore_archive(cp['archive'],path)
        h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        initial=base.rows(h);initial_pairs=dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
        try:
            for key in initial:assert base.owner(h,key)._load(key) is not None
            session=nested.NestedRefinement(h,root);initial_coverage=nested.all_coverage(h,session.registry,queries)
            base.split.verify_positive(h,initial_coverage['proof'],initial_coverage['roots'],list(session.records.values()),base.Counter())
            assert initial_coverage['covered']==cp['coverage'] and not session.coverage.closed()[0]
            startup=time.perf_counter()-started
            for batch in range(protocol['max_batches']):
                destination=out/f'batch-{batch}';destination.mkdir()
                result=session.batch(state_limit=protocol['state_limit'],pair_limit=protocol['pair_limit'])
                tick=time.perf_counter();current=base.rows(h);current_pairs=dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
                assert initial.items()<=current.items() and initial_pairs.items()<=current_pairs.items()
                result.update(mode=mode,batch=batch,coverage=nested.all_coverage(h,session.registry,queries),
                    patterns=len(current),pairs=len(current_pairs),registry=session.registry.statistics(),
                    added_pattern_ids=sorted(map(base.key_sha,set(current)-set(initial))),
                    added_pair_ids=sorted(map(base.key_sha,set(current_pairs)-set(initial_pairs))),
                    added_pattern_digest=base.key_sha(base.encode(sorted((k,v) for k,v in current.items() if k not in initial))),
                    added_pair_digest=base.key_sha(base.encode(sorted((k,v) for k,v in current_pairs.items() if k not in initial_pairs))))
                result['bookkeeping_seconds']=time.perf_counter()-tick
                result['archive']=base.archive(path,destination)
                result['cold']=nested.replay(path,protocol,result)
                base.write(destination/'report.json',result);samples.append(binding(destination/'report.json'))
                print(base.encode(dict(mode=mode,batch=batch,closed=result['closed'],covered=result['coverage']['covered'],
                    entered=result['entered'],stored=result['stored'],probes=result['probes'],pairs=len(result['operations']),
                    reason=result['reason'],seconds=result['seconds'])),flush=True)
                if result['closed']:break
        finally:h.close()
    records=[base.load(s['path']) for s in samples];final=records[-1]
    summary=dict(mode=mode,initial_patterns=len(initial),initial_pairs=len(initial_pairs),initial_covered=initial_coverage['covered'],
        batches=len(records),closed=final['closed'],covered=final['coverage']['covered'],
        entered=sum(r['entered'] for r in records),unique_admissions=len({k for r in records for k in r['admitted_ids']}),
        stored=sum(r['stored'] for r in records),probes=sum(r['probes'] for r in records),
        assumptions=sum(r['selection_counts'].get('bootstrap_fresh_assumptions',0) for r in records),
        reused_pairs=sum(r['selection_counts'].get('bootstrap_reused_pairs',0) for r in records),
        added_pairs=len(final['added_pair_ids']),added_pattern_digest=final['added_pattern_digest'],added_pair_digest=final['added_pair_digest'],
        startup_seconds=startup,operation_seconds=sum(r['seconds'] for r in records),
        bookkeeping_seconds=sum(r['bookkeeping_seconds'] for r in records),
        cold_seconds=sum(r['cold']['seconds'] for r in records),compression_seconds=sum(r['archive']['seconds'] for r in records),
        stream_wall_seconds=time.perf_counter()-started,peak_rss_raw=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        peak_rss_unit='bytes' if sys.platform=='darwin' else 'KiB' if sys.platform.startswith('linux') else 'platform-dependent',
        platform=sys.platform,database_bytes=final['archive']['database_bytes'],compressed_bytes=final['archive']['compressed_bytes'])
    base.write(out/'report.json',dict(summary=summary,samples=samples))


def run(out):
    out.mkdir(exist_ok=False);target=base.load(PARENT/'next-discovery.json');previous=base.load(PARENT/'validation.json')
    checkpoints={'retained':binding(PARENT/'checkpoint.json'),
                 'before_case16':binding(Path('experiments/results/cnf-bootstrap-conditioning/checkpoint.json'))}
    parent=base.load(checkpoints['retained']['path']);sources=dict(previous['source_fingerprints'])
    for p,digest in sources.items():assert base.sha(p)==digest,p
    sources=base.source_fingerprints(sources);sources['experiments/compare_cnf_case17_transfer.py']=base.sha(__file__)
    protocol=dict(target=binding(PARENT/'next-discovery.json'),checkpoints=checkpoints,queries=parent['queries'],
        options=base.OPTIONS,state_limit=128,pair_limit=16,max_batches=4,orders=[MODES,tuple(reversed(MODES))],
        source_fingerprints=sources,policy_binding=binding(Path('experiments/cnf_nested_refinement.py')),
        rationale='Test unchanged conditional refinement on case 17; isolate the marginal contribution of the 547 patterns and 66 pairs acquired for case 16.',
        limitations=['Case 17 is a known unresolved development input, not a new holdout. No policy tuning or extra batch is allowed within this comparison.',
            'The earlier history starts with 5/24 coverage and the full retained union with 6/24; compare target closure and acquisition, not their unequal starting totals.',
            'Each stream has a fresh process; wall time includes all batch snapshots and cold checking, but not interpreter/import startup or the final summary write.',
            'Peak RSS includes all phases and imports, not isolated cache memory. Paired timings are only two repetitions.',
            'All old rows and every unfinished batch are preserved. Closed is structural coverage, not a SAT/UNSAT verdict.'])
    base.write(out/'protocol.json',protocol);samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        a,b=[base.load(s['path'])['summary'] for s in samples if s['mode']==mode]
        for key in ('closed','covered','entered','stored','probes','assumptions','added_pattern_digest','added_pair_digest'):
            assert a[key]==b[key],key
        summary[mode]={**{k:a[k] for k in ('initial_patterns','initial_pairs','initial_covered','batches','closed','covered',
            'entered','unique_admissions','stored','probes','assumptions','added_pairs','reused_pairs','database_bytes','compressed_bytes')},
            **{'mean_'+k:(a[k]+b[k])/2 for k in ('startup_seconds','operation_seconds','bookkeeping_seconds',
                'cold_seconds','compression_seconds','stream_wall_seconds','peak_rss_raw')}}
    base.write(out/'report.json',dict(protocol_sha256=base.sha(out/'protocol.json'),samples=samples,summary=summary))
    print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else:run(Path(sys.argv[1]))
