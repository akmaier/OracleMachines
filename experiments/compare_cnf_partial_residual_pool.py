#!/usr/bin/env python3
"""Frozen bounded retrieval of committed partial-search refutations."""
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
from experiments.cnf_partial_residual_pool import PartialResidualSolver
from experiments.cnf_affine_negative import NegativeStore,TABLE as AFFINE_TABLE,FORMAT as AFFINE_FORMAT
from experiments.cnf_support_plan import PlannedNegativeSolver
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_proof_normalization_reuse import ProofNormalizationSolver
from experiments.cnf_ordered_normalization import OrderedNormalizationSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_residual_dag import normalize,token
base=prior.base;binding=prior.binding;bound=prior.bound
PARENT=Path('experiments/results/cnf-affine-probe-safe')
MODES=('base','partial')
CLASSES=dict(base=InputSafeAffineProbeSolver,partial=PartialResidualSolver)
TABLES=larger.TABLES+(AFFINE_TABLE,)
FILES=('experiments/cnf_partial_residual_pool.py','experiments/compare_cnf_partial_residual_pool.py','solver/test_cnf_partial_residual_pool.py')
SPLITS=dict(exposed=(96,108,120),holdout=(126,132,138))


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
        partial_limits=dict(partial_capacity=64,partial_literals=1024,partial_bytes=512*1024,partial_rows=64,partial_row_bytes=256*1024,
            partial_probes=32,partial_candidates=4,partial_support_nodes=32,partial_support_literals=8192,partial_plan_bytes=128*1024),
        orders=[list(MODES),list(reversed(MODES))],preparation_seconds=time.perf_counter()-tick,limits=[
        'Exposed 96/108/120 and fresh 126/132/138 scales: six designs, two seeds, base/edit/repeat, 108 attempts each. No outcome selection or generator labels in search.',
        'Compare the preceding input-safe affine policy with the same solver plus partial native proof hints. Eight serial workers start empty with native expansion cap 256.',
        'After a completed query or native budget stop, read at most 64 newest committed native rows since the cursor; skip rows above 256 KiB key+payload bytes. Admit nonterminal negative hints only, at most 1024 literals each.',
        'Keep at most 64 entries under a conservative 512 KiB retained pool/index charge. Two deterministic longest-clause anchors generate at most four candidates per probe, at most 32 probes per query.',
        'Whole-source containment or at most one missing clause can qualify. One causal plan per query permits 32 support nodes, 8192 source literals and a 128 KiB accepted-plan charge. Recheck the native origin, core and target through unchanged authority.',
        'Hints are not verdicts. A residual refutation cannot be lifted to its unconditioned source without checking. Exact reuse already exists; coordinate/rank mismatches and fixed candidate order can miss useful supports.',
        'Admission occurs only after committed state. Cold reconstruction scans the bounded archive tail, not a durable restoration of the earlier candidate order. Native/affine proof persistence is unchanged.',
        'Charge input copying, all misses, admission/index maintenance, plan discovery/emission, verification, publication, retained graph sizing, warm/cold replay, reconstruction, sidecars and compression. Preparation and posthoc audits are separate.',
        'Pool/plan limits exclude decoded payload and other transient workspace, prerequisite proof checking, full checked graph, publication and fallback. Fixed limits do not bound total arbitrary-SAT work or establish uniform polynomial expansion.']))


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
        path=Path(td)/'db';options=dict(p['negative_limits'])
        options['plan_byte_limit']=p['plan_byte_limit']
        options.update(p['affine_limits'])
        if mode=='partial':options.update(p['partial_limits'])
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
                                   s.equivalences.old.legacy.checked,s.binary_cores.checked,getattr(s,"witness_pool",{}),getattr(s,"negative_pool",{}),terminal.checked,getattr(s,"partial_pool",{}),getattr(s,"partial_index",{})))
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
        reconstruction=dict(partial_seed_entries=len(getattr(s,'partial_pool',{})),partial_seed_counts=getattr(s,'partial_setup_counts',{}),partial_seed_seconds=getattr(s,'partial_setup_seconds',0),negative_seed_entries=len(getattr(s,'negative_pool',{})),seed_seconds=getattr(s,'witness_setup_seconds',0),seed_counts=getattr(s,'witness_setup_counts',{}))
        reconstruction['setup_seconds']=time.perf_counter()-tick
        try:
            with patch.object(s,'_expand',side_effect=AssertionError('Cold exact-root expansion')):
                for c,r in zip(cases,records):
                    if r['result'] is not None:assert attempt(s,c['source'])['status']==r['status']
            reconstruction['partial_replay_entries']=len(getattr(s,'partial_pool',{}))
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
        partial_peak_bytes=max(r['metrics'].get('partial_peak_bytes',0) for r in records),partial_peak_entries=max(r['metrics'].get('partial_peak_entries',0) for r in records),
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
