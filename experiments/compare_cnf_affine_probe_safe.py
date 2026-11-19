#!/usr/bin/env python3
"""Frozen bounded affine probes against planned reuse and witness-only search."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_larger_mixtures as larger
prior=larger.prior
from experiments.cnf_larger_mixtures import generate,FAMILIES,attempt,LIMIT
from experiments.cnf_witness_pool import WitnessPoolSolver
from experiments.cnf_affine_probe_safe import InputSafeAffineProbeSolver
from experiments.cnf_affine_negative import NegativeStore,TABLE as AFFINE_TABLE,FORMAT as AFFINE_FORMAT
from experiments.cnf_support_plan import PlannedNegativeSolver
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_proof_normalization_reuse import ProofNormalizationSolver
from experiments.cnf_ordered_normalization import OrderedNormalizationSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_residual_dag import normalize,token
base=prior.base;binding=prior.binding;bound=prior.bound
PARENT=Path('experiments/results/cnf-support-plan')
MODES=('pool','plan','probe')
CLASSES=dict(pool=WitnessPoolSolver,plan=PlannedNegativeSolver,probe=InputSafeAffineProbeSolver)
TABLES=larger.TABLES+(AFFINE_TABLE,)
FILES=('experiments/cnf_affine_probe.py','experiments/compare_cnf_affine_probe.py','solver/test_cnf_affine_probe.py',
       'experiments/cnf_affine_probe_safe.py','experiments/compare_cnf_affine_probe_safe.py','solver/test_cnf_affine_probe_safe.py')
SPLITS=dict(exposed=(42,66,90),holdout=(96,108,120))


def catalog(split):
    cases=[]
    for size in SPLITS[split]:
        for family in FAMILIES:
            for sample in (0,1):
                start=len(cases)
                for variant,source in zip(('base','edit','repeat'),generate(family,size,sample)):
                    cnf,names=normalize(source)
                    cases.append(dict(case=len(cases),family=family,size=size,sample=sample,
                        variant=variant,base_case=start,source=source,root=token(cnf,Counter()),
                        variables=len(names),clauses=len(cnf),literals=sum(map(len,cnf))))
    return cases


def prepare(out):
    out.mkdir(exist_ok=True);assert not (out/'protocol.json').exists();tick=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');sources=dict(parent['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    cases={split:catalog(split) for split in SPLITS}
    assert not {c['root'] for c in cases['exposed']} & {c['root'] for c in cases['holdout']}
    for split,values in cases.items():base.write(out/(split+'-cases.json'),values)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,
        cases={s:binding(out/(s+'-cases.json')) for s in SPLITS},node_limit=LIMIT,
        negative_limits=dict(negative_capacity=16,negative_literal_limit=4096,negative_node_limit=256,negative_support_literals=131072),plan_byte_limit=4*1024*1024,
        affine_limits=dict(affine_variables=256,affine_clauses=4096,affine_literals=16384,affine_xors=65536),
        orders=[list(MODES),list(reversed(MODES))],preparation_seconds=time.perf_counter()-tick,limits=[
        'Exposed sizes 42/66/90 and fresh holdout sizes 96/108/120: six designs, two seeds, base/edit/repeat, 108 attempts each. No outcome filtering or generator labels.',
        'Compare witness-only search, planned negative reuse, and planned reuse with a bounded top-level affine-negative probe. All workers start empty with native expansion cap 256.',
        'Probe bounds apply to normalized source width/clauses/literals and discovery XORs. Canonicalization, exact lookup/checking, publication, allocator overhead and full fallback remain outside them.',
        'Only a checked contradiction in the existing affine-negative-v1 authority returns early. Consistent, incomplete or budget-stopped probes fall back without a verdict. No native certificate depends on this extension.',
        'Affine publication is an immediate checked transaction before native batching starts. Every arm creates the empty affine table, charging setup consistently. Cached extension checks require the exclusively owned append-only connection.',
        'Snapshot finite outer/inner CNF iterables before the multi-pass kernel; charge copying and its transient storage. Earlier list-only timing is retained separately and superseded by this run.',
        'Charge setup, all probe misses, extraction, elimination, independent verification, publication, native fallback, retained graph sizing, warm/cold replay, cold reconstruction, sidecars and compression. Study preparation and posthoc audit are separate.',
        'Keep both latency baselines, all original unknowns and any regressions. New checked negatives broaden completed decisions, not a tractable decomposition of every CNF or uniform polynomial SAT bound.']))


def affine_rows(s):
    present=s.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",(AFFINE_TABLE,)).fetchone()
    return dict(s.db.execute(f'SELECT id,payload FROM {AFFINE_TABLE}')) if present else {}


def check_answer(s,store,source,result,terminal=None):
    if result['authority']!=AFFINE_FORMAT:return prior.check_answer(s,store,source,result)
    cnf,_,root=s._canonical(source);assert result['root']==root and result['answer'] is False and result['model'] is None
    terminal=terminal or NegativeStore(s);assert terminal.read(root,cnf) is not None



def cold(path,cases,records):
    tick=time.perf_counter();before=base.sha(path);s=CanonicalVerifySnapshot(path);store=MultiEquivalenceStore(s);terminal=NegativeStore(s)
    try:
        native=prior.native_rows(s);ext=prior.extension_rows(s);affine=affine_rows(s)
        for key in native:assert s._read(key) is not None
        for key in ext:assert store.read(key) is not None
        for key in affine:assert terminal.read(key) is not None
        for c,r in zip(cases,records):
            if r['result'] is not None:check_answer(s,store,c['source'],r['result'],terminal)
            else:assert r['status']=='unresolved'
        result=dict(native=len(native),extensions=len(ext),affine=len(affine),completed=sum(r['result'] is not None for r in records),metrics=dict(s.counts))
    finally:s.close()
    assert before==base.sha(path);result['seconds']=time.perf_counter()-tick;return result


def worker(out,p,mode,split):
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=bound(p['cases'][split]);out.mkdir();began=time.perf_counter();records=[];warm=[];marks={t:0 for t in TABLES}
    totals=Counter();counts=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';options=dict(p['negative_limits']) if mode in ('plan','probe') else {}
        if mode in ('plan','probe'):options['plan_byte_limit']=p['plan_byte_limit']
        if mode=='probe':options.update(p['affine_limits'])
        s=CLASSES[mode](path,node_limit=p['node_limit'],**options)
        terminal=getattr(s,'affine',None) or NegativeStore(s,create=True)
        settings={k:s.db.execute('PRAGMA '+k).fetchone()[0] for k in ('journal_mode','synchronous')};setup=time.perf_counter()-began
        try:
            for c in cases:
                tick=time.perf_counter();r=attempt(s,c['source']);new={}
                assert not s.db.in_transaction and not s.db.pending and not s.db.active
                assert getattr(s,'_support_plan',None) is None
                assert getattr(s,'_proof_memo',None) is None and s._verification_canonical is None
                for table in TABLES:
                    added=s.db.execute(f'SELECT rowid,id,payload FROM {table} WHERE rowid>? ORDER BY rowid',(marks[table],)).fetchall()
                    if added:marks[table]=added[-1][0]
                    new[table]=[key for _,key,_ in added]
                    totals[table+'_nodes']+=len(added);totals[table+'_payload']+=sum(len(k)+len(v) for _,k,v in added)
                counts.update(r['metrics']);records.append(dict(case=c['case'],**r,new_ids=new,retained=dict(totals),seconds=time.perf_counter()-tick))
            final=prior.native_rows(s);ext=prior.extension_rows(s);affine=affine_rows(s)
            memory=prior.deep_size((s.checked,s.equivalences.checked,s.equivalences.old.checked,
                                   s.equivalences.old.legacy.checked,s.binary_cores.checked,getattr(s,"witness_pool",{}),getattr(s,"negative_pool",{}),terminal.checked))
            warm_tick=time.perf_counter()
            with patch.object(s,'_expand',side_effect=AssertionError('Warm expansion')):
                for c,r in zip(cases,records):
                    if r['result'] is None:continue
                    got=attempt(s,c['source']);assert got['status']==r['status'];warm.append(dict(case=c['case'],**got))
            warm_seconds=time.perf_counter()-warm_tick
            assert prior.native_rows(s)==final and prior.extension_rows(s)==ext and affine_rows(s)==affine
        except BaseException:
            s.close();base.write(out/'partial.json',records);base.archive(path,out);raise
        else:s.close()
        audit=cold(path,cases,records)
        tick=time.perf_counter();s=CLASSES[mode](path,node_limit=p['node_limit'],**options)
        reconstruction=dict(negative_seed_entries=len(getattr(s,'negative_pool',{})),seed_seconds=getattr(s,'witness_setup_seconds',0),seed_counts=getattr(s,'witness_setup_counts',{}))
        reconstruction['setup_seconds']=time.perf_counter()-tick
        try:
            with patch.object(s,'_expand',side_effect=AssertionError('Cold exact-root expansion')):
                for c,r in zip(cases,records):
                    if r['result'] is not None:assert attempt(s,c['source'])['status']==r['status']
            reconstruction['pool_entries']=len(getattr(s,'witness_pool',{}))
            reconstruction['negative_replay_entries']=len(getattr(s,'negative_pool',{}))
        finally:s.close()
        reconstruction['seconds']=time.perf_counter()-tick
        base.write(out/'queries.json',records);base.write(out/'warm.json',warm);archive=base.archive(path,out)
    summary=dict(mode=mode,split=split,queries=len(cases),statuses=dict(Counter(r['status'] for r in records)),node_limit=p['node_limit'],sqlite_settings=settings,
        affine_nodes=len(affine),affine_payload=sum(len(k)+len(v) for k,v in affine.items()),affine_digest=base.key_sha(base.encode(sorted(affine.items()))),
        native_nodes=len(final),extension_nodes=len(ext),native_payload=sum(len(k)+len(v) for k,v in final.items()),extension_payload=sum(len(k)+len(v) for k,v in ext.items()),
        native_digest=base.key_sha(base.encode(sorted(final.items()))),extension_digest=base.key_sha(base.encode(sorted(ext.items()))),
        counters=dict(counts),checked_python_bytes=memory,setup_seconds=setup,query_seconds=sum(r['seconds'] for r in records),solve_seconds=sum(r['solve_seconds'] for r in records),
        warm_seconds=warm_seconds,cold_seconds=audit['seconds'],reconstruction_seconds=reconstruction['seconds'],compression_seconds=archive['seconds'],complete_worker_seconds=time.perf_counter()-began,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],sidecar_bytes=sum((out/f).stat().st_size for f in ('queries.json','warm.json')),
        plan_peak_bytes=max(r['metrics'].get('plan_peak_bytes',0) for r in records),
        negative_peak_entries=max(r['metrics'].get('negative_retained_entries',0) for r in records),negative_peak_literals=max(r['metrics'].get('negative_retained_literals',0) for r in records),
        witness_peak_bytes=max(r['metrics'].get('witness_peak_bytes',0) for r in records),witness_peak_entries=max(r['metrics'].get('witness_peak_entries',0) for r in records),
        batch_peak_payload=max(r['metrics'].get('batch_peak_payload',0) for r in records),batch_peak_records=max(r['metrics'].get('batch_peak_records',0) for r in records))
    base.write(out/'report.json',dict(summary=summary,queries=binding(out/'queries.json'),archive=archive,cold=audit,reconstruction=reconstruction))


def run(out):
    p=base.load(out/'protocol.json');samples=[];summaries={}
    for split in SPLITS:
        for repeat,order in enumerate(p['orders']):
            for mode in order:
                dest=out/f'{split}-{mode}-{repeat}'
                subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),mode,split],check=True)
                samples.append(dict(mode=mode,split=split,repeat=repeat,**binding(dest/'report.json')))
                print('finished',split,repeat,mode,flush=True)
        summaries[split]={}
        for mode in MODES:
            values=[bound(s)['summary'] for s in samples if s['mode']==mode and s['split']==split];first=values[0]
            timed=[k for k in first if k.endswith('_seconds') or k=='peak_rss_bytes']
            fixed=[k for k in first if k not in timed and k not in ('mode','sidecar_bytes')]
            for v in values[1:]:
                for k in fixed:assert v[k]==first[k],k
            summaries[split][mode]={**{k:first[k] for k in fixed},**{'mean_'+k:sum(v[k] for v in values)/len(values) for k in timed},'sidecar_bytes':[v['sidecar_bytes'] for v in values]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,summary=summaries))
    print(base.encode({s:{m:{k:v for k,v in a.items() if k in ('statuses','native_nodes','mean_query_seconds','mean_complete_worker_seconds','witness_peak_bytes','database_bytes')} for m,a in arms.items()} for s,arms in summaries.items()}),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4],sys.argv[5])
    else:run(Path(sys.argv[1]))
