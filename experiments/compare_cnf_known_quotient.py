#!/usr/bin/env python3
"""Compare exact known-quotient selection on the pilot and excluded fresh extensions."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_multiblock_equivalence as prior
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
PARENT=Path('experiments/results/cnf-multiblock-equivalence')
MODES=('single','all','known')
FILES=('experiments/cnf_known_quotient.py','experiments/compare_cnf_known_quotient.py','solver/test_cnf_known_quotient.py')


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


def cold(path,cases,records):
    before=base.sha(path);tick=time.perf_counter();s=SnapshotResidualSolver(path);store=MultiEquivalenceStore(s)
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
    cases=base.load(PARENT/'cases.json');assert len(cases)==68
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'parent';base.restore_archive(parent['reference_union'],path);s=SnapshotResidualSolver(path)
        try:
            known=set(native_rows(s))
            for table in ('cnf_binary_equivalence_v1','cnf_binary_equivalence_v2','cnf_binary_equivalence_v3'):
                known.update(prior.extension_rows(s,table))
        finally:s.close()
    seen={c['root'] for c in cases}
    def add(source,group,family,**metadata):
        root=token(normalize(source)[0],Counter())
        if root in seen or root in known:return False
        seen.add(root);cases.append(dict(case=len(cases),source=source,group=group,family=family,root=root,known_in_parent=False,**metadata));return True
    for family in FAMILIES:
        for size in SIZES:
            for sample in (0,1):
                for attempt in range(725,10725):
                    if add(generate(family,size,sample,attempt),'fresh-control',family,size=size,sample=sample,attempt=attempt):break
                else:raise ValueError('No excluded generated source')
    for original in base.load(PARENT/'attribution.json')['multiblock_sources']:
        cnf,_=normalize(cases[original['case']]['source']);block=discover_all(cnf,Counter())[0]
        rep=block['representative'];member=block['forward'][0][1];n=max(abs(l) for c in cnf for l in c)
        for signed in (v*sign for v in range(1,n+1) if v not in (rep,abs(member)) for sign in (1,-1)):
            raw=[list(c) for c in cnf]+[[rep,-member,signed,n+1]]
            if add(raw,'fresh-quotient-preserving-edit',cases[original['case']]['family'],base_case=original['case']):break
        else:raise ValueError('No excluded wide edit')
    assert len(cases)==104
    base.write(out/'cases.json',cases)
    p=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,cases=binding(out/'cases.json'),
        workload_origin=binding(PARENT/'cases.json'),orders=[list(MODES),list(reversed(MODES))],limits=[
        'Each arm starts empty. The original 68-input pilot is followed by 24 generated sources and twelve quotient-preserving wide edits, excluded against all parent native and equivalence roots.',
        'Single uses prior memory-cached first-block discovery. All uses cached complete blocks. Known checks the full native quotient then, only on a miss, the first-block native quotient; at most two candidates.',
        'Certificate formats and native recursive acquisition remain unchanged. Known hits transport checked native models or reuse native negative dependencies with the selected source evidence.',
        'Setup, discovery, extraction/keying, checking both alternatives, canonicalization, lookup, acquisition, publication, metadata scans, warm reuse, cold replay, sidecars and compression are timed.',
        'Imports/source audits, truth and history audits and final reports are outside timing. Fresh controls are a small designed extension, not representative arbitrary SAT coverage.'
])
    base.write(out/'protocol.json',p)


def worker(out,p,mode):
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=bound(p['cases']);out.mkdir();began=time.perf_counter();records=[];warm=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';cls={'single':CachedBinaryEquivalenceSolver,'all':MultiEquivalenceSolver,'known':KnownQuotientSolver}[mode]
        s=cls(path,**(dict(persistent_cache=False) if mode=='single' else dict(cache=True)));setup_seconds=time.perf_counter()-began
        try:
            for c in cases:
                tick=time.perf_counter();before=native_rows(s);oldext=extension_rows(s);oldcache=retained(s);r=s.solve(c['source'])
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
        try:audit=cold(path,cases,records)
        except BaseException:
            base.write(out/'partial.json',records);base.archive(path,out);raise
        base.write(out/'queries.json',records);base.write(out/'warm.json',warm);archive=base.archive(path,out)
    counters=Counter()
    for r in records:counters.update(r['result']['metrics'])
    summary=dict(mode=mode,queries=len(cases),positive=sum(r['result']['answer'] for r in records),native_nodes=len(final),
        native_payload=sum(len(k)+len(v) for k,v in final.items()),extension_nodes=len(extensions),extension_payload=sum(len(k)+len(v) for k,v in extensions.items()),
        counters=dict(counters),cache_entries=len(final_cache),cache_payload=sum(len(k)+len(v) for k,v in final_cache.items()),cache_python_bytes=cache_memory,cache_digest=base.key_sha(base.encode(sorted(final_cache.items()))),setup_seconds=setup_seconds,query_seconds=sum(r['seconds'] for r in records),warm_seconds=warm_seconds,cold_seconds=audit['seconds'],
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
