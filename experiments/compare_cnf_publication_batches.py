#!/usr/bin/env python3
"""Compare bounded publication batches with identical checked dependency streams."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_canonical_verify as prior
from experiments.cnf_query_canonical_cache import QueryCanonicalSolver
from experiments.cnf_canonical_verify import CanonicalVerifySolver,CanonicalVerifySnapshot
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_known_quotient import KnownQuotientSolver
from experiments.cnf_multiblock_equivalence import discover_all
from experiments.cnf_multiblock_equivalence import MultiEquivalenceSolver,MultiEquivalenceStore,TABLE as MULTI_TABLE,FORMAT as MULTI_FORMAT
from experiments.cnf_binary_core_cache import CachedBinaryEquivalenceSolver,BinaryCoreCache,TABLE as CACHE_TABLE,encode as cache_encode
from experiments.cnf_compact_equivalence import CompactBinaryEquivalenceSolver,CompactEquivalenceStore,TABLE as COMPACT_TABLE,FORMAT as COMPACT_FORMAT
from experiments.cnf_binary_equivalence import BinaryEquivalenceSolver,EquivalenceStore,TABLE,FORMAT
from experiments.cnf_targeted_backbone import AccountedTargetedBackboneSolver
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_residual_dag import normalize,token,holds
from experiments.cnf_cross_family import generate,FAMILIES,SIZES
previous=prior.previous
base=prior.base;binding=prior.binding;bound=prior.bound
PARENT=Path('experiments/results/cnf-canonical-verify')
MODES=('linear','batch1','batch32')
FILES=('experiments/cnf_publication_batches.py','experiments/compare_cnf_publication_batches.py','solver/test_cnf_publication_batches.py')


def native_rows(s):return dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
def extension_rows(s,table=None):
    if table is not None:return prior.extension_rows(s,table)
    result={}
    for name in (COMPACT_TABLE,MULTI_TABLE):
        rows=prior.extension_rows(s,name);assert not result.keys()&rows.keys();result.update(rows)
    return result


def check_answer(s,store,source,r):
    if r.get('authority')==MULTI_FORMAT:
        cnf,names,root=s._canonical(source);assert root==r['root'] and not r['answer'] and r['model'] is None
        assert store.read(root)['format']==MULTI_FORMAT
    else:prior.check_answer(s,store,source,r)


def cache_rows(s):
    if not s.db.execute('SELECT 1 FROM sqlite_master WHERE name=?',(CACHE_TABLE,)).fetchone():return {}
    return dict(s.db.execute(f'SELECT id,payload FROM {CACHE_TABLE} ORDER BY id'))


def retained(s):
    return {k:cache_encode(v) for k,v in s.binary_cores.checked.items()} if hasattr(s,'binary_cores') else {}


def deep_size(value,seen=None):
    seen=set() if seen is None else seen
    if id(value) in seen:return 0
    seen.add(id(value));size=sys.getsizeof(value)
    if isinstance(value,dict):size+=sum(deep_size(k,seen)+deep_size(v,seen) for k,v in value.items())
    elif isinstance(value,(tuple,list)):size+=sum(deep_size(v,seen) for v in value)
    return size


def cold(path,cases,records,linear=False):
    before=base.sha(path);tick=time.perf_counter();s=(CanonicalVerifySnapshot if linear else SnapshotResidualSolver)(path);store=MultiEquivalenceStore(s)
    try:
        native=native_rows(s);extensions=extension_rows(s)
        for root in native:assert s._read(root) is not None
        for root in extensions:assert store.read(root) is not None
        for c,r in zip(cases,records):check_answer(s,store,c['source'],r['result'])
        result=dict(native_nodes=len(native),extension_nodes=len(extensions),queries=len(records),counts=dict(s.counts))
    finally:s.close()
    assert base.sha(path)==before;result['seconds']=time.perf_counter()-tick;return result


def prepare(out):
    out.mkdir(exist_ok=True);assert not (out/'protocol.json').exists();parent=base.load(PARENT/'checkpoint.json')
    sources=dict(parent['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    cases=base.load(PARENT/'cases.json');assert len(cases)==104
    base.write(out/'cases.json',cases)
    p=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,cases=binding(out/'cases.json'),
        workload_origin=binding(PARENT/'cases.json'),orders=[list(MODES),list(reversed(MODES))],limits=[
        'Same 104-input catalog from empty archives. Earlier novelty labels refer to the previous study; these are replayed inputs, not new coverage.',
        'Linear is the unchanged direct-recognition control. Batch1 and batch32 group at most one or 32 inserted records and 256 KiB of encoded key/payload, except an oversized single record committed alone.',
        'All original proof checks and INSERT order remain. Successful queries commit before return; failure rolls back only the pending suffix and invalidates its checked entries. Already committed prefixes survive. Partial-query visibility differs from per-record publication.',
        'The wrapper requires exclusive ownership and an idle connection. Uncertain rollback poisons the instance. No journal/synchronous mode changes; raw private connection manipulation is outside the contract.',
        'Payload/record limits bound pending publication units, not SQLite journals, page caches or whole-solver RAM. The extra pending-key object charge and peak RSS are recorded. The existing full proof cache remains.',
        'Setup, proof recognition, normalization, keying, discovery, solving, checking, metadata, byte sizing, batching/commit, warm/cold replay, sidecars and compression are timed. Every arm uses the same direct cold reader.',
        'Imports/source audits, truth/history audits and final reports are outside worker timing. No new SAT coverage or unrestricted bound.'
])
    base.write(out/'protocol.json',p)


def worker(out,p,mode):
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=bound(p['cases']);out.mkdir();began=time.perf_counter();records=[];warm=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';cls=CanonicalVerifySolver if mode=='linear' else BatchedPublicationSolver
        options=dict(cache=True) if mode=='linear' else dict(cache=True,batch_rows=1 if mode=='batch1' else 32,batch_payload_bytes=256*1024)
        s=cls(path,**options);settings={k:s.db.execute('PRAGMA '+k).fetchone()[0] for k in ('journal_mode','synchronous')};setup_seconds=time.perf_counter()-began
        try:
            for c in cases:
                tick=time.perf_counter();before=native_rows(s);oldext=extension_rows(s);oldcache=retained(s);r=s.solve(c['source'])
                assert getattr(s,'_verification_canonical',None) is None and not s.db.in_transaction and not getattr(s.db,'pending',[]) and not getattr(s.db,'active',False)
                after=native_rows(s);ext=extension_rows(s);cache=retained(s);assert before.items()<=after.items() and oldext.items()<=ext.items()
                records.append(dict(case=c['case'],result=r,new_cache_ids=sorted(set(cache)-set(oldcache)),cache_entries=len(cache),cache_payload=sum(len(k)+len(v) for k,v in cache.items()),new_native_ids=sorted(set(after)-set(before)),new_extension_ids=sorted(set(ext)-set(oldext)),
                    native_nodes=len(after)-len(before),native_payload=sum(len(k)+len(v) for k,v in after.items() if k not in before),
                    extension_nodes=len(ext)-len(oldext),extension_payload=sum(len(k)+len(v) for k,v in ext.items() if k not in oldext),seconds=time.perf_counter()-tick))
            final=native_rows(s);extensions=extension_rows(s);final_cache=retained(s);cache_memory=deep_size(s.binary_cores.checked) if hasattr(s,'binary_cores') else 0;warm_tick=time.perf_counter()
            with patch.object(s,'_expand',side_effect=AssertionError('Warm expansion')):
                for c,r in zip(cases,records):
                    got=s.solve(c['source']);assert got['answer']==r['result']['answer'];warm.append(got)
            assert native_rows(s)==final and extension_rows(s)==extensions and retained(s)==final_cache
            warm_seconds=time.perf_counter()-warm_tick
        except BaseException:
            s.close();base.write(out/'partial.json',records);base.archive(path,out);raise
        else:s.close()
        try:audit=cold(path,cases,records,linear=True)
        except BaseException:
            base.write(out/'partial.json',records);base.archive(path,out);raise
        base.write(out/'queries.json',records);base.write(out/'warm.json',warm);archive=base.archive(path,out)
    counters=Counter()
    for r in records:counters.update(r['result']['metrics'])
    summary=dict(mode=mode,sqlite_settings=settings,batch_rows=getattr(s.db,'rows',0),batch_payload_limit=getattr(s.db,'payload_limit',0),batch_peak_records=max(r['result']['metrics'].get('batch_peak_records',0) for r in records),batch_peak_payload=max(r['result']['metrics'].get('batch_peak_payload',0) for r in records),batch_peak_python_bytes=max(r['result']['metrics'].get('batch_peak_python_bytes',0) for r in records),queries=len(cases),positive=sum(r['result']['answer'] for r in records),native_nodes=len(final),
        native_payload=sum(len(k)+len(v) for k,v in final.items()),extension_nodes=len(extensions),extension_payload=sum(len(k)+len(v) for k,v in extensions.items()),
        canonical_cache_capacity=getattr(s,'canonical_cache_bytes',0),canonical_cache_peak_bytes=max(r['result']['metrics'].get('canonical_cache_peak_bytes',0) for r in records),canonical_cache_peak_entries=max(r['result']['metrics'].get('canonical_cache_peak_entries',0) for r in records),counters=dict(counters),cache_entries=len(final_cache),cache_payload=sum(len(k)+len(v) for k,v in final_cache.items()),cache_python_bytes=cache_memory,cache_digest=base.key_sha(base.encode(sorted(final_cache.items()))),setup_seconds=setup_seconds,query_seconds=sum(r['seconds'] for r in records),warm_seconds=warm_seconds,cold_seconds=audit['seconds'],
        compression_seconds=archive['seconds'],complete_worker_seconds=time.perf_counter()-began,
        database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],
        sidecar_bytes=sum((out/f).stat().st_size for f in ('queries.json','warm.json')),
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        native_digest=base.key_sha(base.encode(sorted(final.items()))),extension_digest=base.key_sha(base.encode(sorted(extensions.items()))))
    base.write(out/'report.json',dict(summary=summary,queries=binding(out/'queries.json'),archive=archive,cold=audit))


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}'
            subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')));print('finished',repeat,mode,flush=True)
    summaries={}
    for mode in MODES:
        items=[bound(r)['summary'] for r in samples if r['mode']==mode];first=items[0]
        timed=[k for k in first if k.endswith('_seconds') or k=='peak_rss_bytes']
        fixed=[k for k in first if k not in timed and k not in ('mode','sidecar_bytes')]
        for other in items[1:]:
            for k in fixed:assert first[k]==other[k],k
        summaries[mode]={**{k:first[k] for k in fixed},**{'mean_'+k:sum(v[k] for v in items)/len(items) for k in timed},'sidecar_bytes':[v['sidecar_bytes'] for v in items]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,summary=summaries))
    print(base.encode({m:{k:v for k,v in s.items() if k!='counters'} for m,s in summaries.items()}),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else:run(Path(sys.argv[1]))
