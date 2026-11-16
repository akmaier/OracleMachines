#!/usr/bin/env python3
"""Compare per-batch full audits with one full audit for a bounded query group."""
from collections import Counter,defaultdict
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_scoped_refinement as previous
from experiments.cnf_query_checkpoint import check_query
from experiments.cnf_scoped_refinement import ScopedNestedRefinement
base=previous.base
PARENT=Path('experiments/results/cnf-scoped-refinement')
MODES=('each_batch','group_end')
binding=previous.binding


def worker(out,protocol,mode):
    out.mkdir(exist_ok=False);started=time.perf_counter();samples=[];setup=[]
    parent=base.load(protocol['checkpoint']['path']);queries=base.load(protocol['queries']['path'])
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'h';base.restore_archive(parent['archive'],path)
        h=base.CompleteAdmissionInventory(path,**protocol['options']);h.set_admission_budget(0)
        initial=base.rows(h);initial_pairs=dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
        startup=time.perf_counter()-started
        try:
            for index,case in enumerate(protocol['cases']):
                query=queries[case];root=query['roots'][0];tick=time.perf_counter()
                assert root==h._canonical(query['source'],0)[2]
                session=ScopedNestedRefinement(h,root)
                setup.append(dict(case=case,seconds=time.perf_counter()-tick,already_closed=session.coverage.closed()[0],
                    main_inventory_checked_nodes=len(h.checked),registry=session.registry.statistics()))
                for batch in range(protocol['max_batches_per_case']):
                    dest=out/f'case-{case}-batch-{batch}';dest.mkdir()
                    result=session.batch(state_limit=protocol['state_limit'],pair_limit=protocol['pair_limit'])
                    tick=time.perf_counter();rows=base.rows(h);pairs=dict(h.db.execute(f'SELECT id,payload FROM {base.split.TABLE}'))
                    assert initial.items()<=rows.items() and initial_pairs.items()<=pairs.items()
                    flags,plan=base.compose(h,[root],session.registry,Counter())
                    proof=base.expand(h,plan,[root],session.registry,Counter())
                    base.split.verify_positive(h,proof,proof['roots'],list(session.records.values()),Counter())
                    assert flags==[result['closed']]
                    result.update(mode=mode,case=case,batch=batch,target_proof=proof,patterns=len(rows),pairs=len(pairs),
                        registry=session.registry.statistics(),main_inventory_checked_nodes=len(h.checked),
                        pattern_digest=base.key_sha(base.encode(sorted(rows.items()))),
                        pair_digest=base.key_sha(base.encode(sorted(pairs.items()))))
                    result['bookkeeping_seconds']=time.perf_counter()-tick
                    result['archive']=base.archive(path,dest)
                    result['query_cold']=check_query(path,protocol['options'],query['source'],root,proof,result['closed'])
                    last=(index==len(protocol['cases'])-1 and (result['closed'] or batch==protocol['max_batches_per_case']-1))
                    result['full_cold']=previous.audit(path,protocol) if mode=='each_batch' or last else None
                    base.write(dest/'report.json',result);samples.append(binding(dest/'report.json'))
                    print(base.encode(dict(mode=mode,case=case,batch=batch,closed=result['closed'],stored=result['stored'],
                        entered=result['entered'],probes=result['probes'],reason=result['reason'],full_audit=result['full_cold'] is not None)),flush=True)
                    if result['closed']:break
        finally:h.close()
    records=[base.load(s['path']) for s in samples];final=records[-1];assert final['full_cold'] is not None
    summary=dict(mode=mode,batches=len(records),cases=[dict(case=c,closed=[r for r in records if r['case']==c][-1]['closed'],
        batches=sum(r['case']==c for r in records),stored=sum(r['stored'] for r in records if r['case']==c),
        probes=sum(r['probes'] for r in records if r['case']==c)) for c in protocol['cases']],
        covered=final['full_cold']['coverage']['covered'],entered=sum(r['entered'] for r in records),
        unique_admissions=len({k for r in records for k in r['admitted_ids']}),stored=sum(r['stored'] for r in records),
        probes=sum(r['probes'] for r in records),assumptions=sum(r['selection_counts'].get('bootstrap_fresh_assumptions',0) for r in records),
        reused_pairs=sum(r['selection_counts'].get('bootstrap_reused_pairs',0) for r in records),
        added_pairs=final['pairs']-len(initial_pairs),full_audits=sum(r['full_cold'] is not None for r in records),
        query_audits=len(records),positive_query_claims=sum(r['query_cold']['positive_claim_checked'] for r in records),
        patterns=final['patterns'],pairs=final['pairs'],pattern_digest=final['pattern_digest'],pair_digest=final['pair_digest'],
        database_bytes=final['archive']['database_bytes'],compressed_bytes=final['archive']['compressed_bytes'],
        retained_snapshot_bytes=sum(r['archive']['compressed_bytes'] for r in records),
        startup_seconds=startup,query_setup_seconds=sum(r['seconds'] for r in setup),
        operation_seconds=sum(r['seconds'] for r in records),bookkeeping_seconds=sum(r['bookkeeping_seconds'] for r in records),
        query_cold_seconds=sum(r['query_cold']['seconds'] for r in records),full_cold_seconds=sum(r['full_cold']['seconds'] for r in records if r['full_cold']),
        compression_seconds=sum(r['archive']['seconds'] for r in records),stream_wall_seconds=time.perf_counter()-started,
        peak_rss_raw=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,platform=sys.platform,
        peak_rss_unit='bytes' if sys.platform=='darwin' else 'KiB' if sys.platform.startswith('linux') else 'platform-dependent')
    base.write(out/'report.json',dict(summary=summary,setup=setup,samples=samples))


def run(out):
    out.mkdir(exist_ok=False);parent=base.load(PARENT/'checkpoint.json');validation=base.load(PARENT/'validation.json')
    sources=dict(validation['source_fingerprints'])
    for p,d in sources.items():assert base.sha(p)==d,p
    for p in ('experiments/cnf_query_checkpoint.py','experiments/compare_cnf_grouped_checkpoints.py','solver/test_cnf_query_checkpoint.py'):
        sources[p]=base.sha(p)
    historical=Path('experiments/results/cnf-split-registry/report.json');means=defaultdict(list)
    for sample in base.load(historical)['samples']:
        if sample['mode']=='incremental':
            assert base.sha(sample['path'])==sample['sha256']
            for row in base.load(sample['path'])['records']:means[row['case']].append(row['seconds'])
    cases=sorted(parent['uncovered_originals'],key=lambda c:(-sum(means[c])/len(means[c]),c))[:3]
    assert cases==[23,18,15]
    protocol=dict(checkpoint=binding(PARENT/'checkpoint.json'),queries=parent['queries'],options=base.OPTIONS,cases=cases,
        selection_measurement=binding(historical),state_limit=128,pair_limit=16,max_batches_per_case=4,
        orders=[MODES,tuple(reversed(MODES))],source_fingerprints=sources,
        limitations=['Both modes use one full authoritative history and the unchanged scoped scheduling/acquisition policy. Only full-audit timing differs.',
            'Every intermediate snapshot and every query report is persisted; both modes independently check each positive query proof on its exact snapshot.',
            'Each_batch completely checks every batch; group_end checks the complete history once at group end. Intermediate snapshots are not claimed globally certified in group_end mode.',
            'A missing positive proof is not a negative SAT verdict. Unrelated corruption detection is delayed in group_end; publication of a globally verified checkpoint requires the successful final full audit.',
            'Known development inputs selected by historical cost, not new holdouts. Three cases, at most four bounded batches per case. Two reversed fresh-process repetitions.',
            'Wall time includes all setup, expansion, snapshots, query proofs, full audits, compression and bookkeeping, except interpreter imports and final summary write. Process RSS includes all phases and imports.',
            'Earlier history acquisition remains charged in the preserved parent experiments. No inference default or unrestricted-SAT efficiency claim changes.'])
    base.write(out/'protocol.json',protocol);samples=[]
    for repeat,order in enumerate(protocol['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')))
    summary={}
    for mode in MODES:
        a,b=[base.load(s['path'])['summary'] for s in samples if s['mode']==mode]
        timed={k for k in a if k.endswith('_seconds') or k=='peak_rss_raw'}
        fixed={k:a[k] for k in a if k not in timed and k not in ('platform','peak_rss_unit','mode')}
        for k,v in fixed.items():assert b[k]==v,k
        summary[mode]={**fixed,**{'mean_'+k:(a[k]+b[k])/2 for k in timed}}
    base.write(out/'report.json',dict(protocol_sha256=base.sha(out/'protocol.json'),samples=samples,summary=summary))
    print(base.encode(summary),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else:run(Path(sys.argv[1]))
