#!/usr/bin/env python3
"""Matched top-level quotient acquisition pilot; no historical-prefix claims."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_targeted_backbone as previous
from experiments.cnf_binary_equivalence import BinaryEquivalenceSolver,EquivalenceStore,TABLE,FORMAT
from experiments.cnf_targeted_backbone import AccountedTargetedBackboneSolver
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_residual_dag import normalize,token,holds
from experiments.cnf_cross_family import generate,FAMILIES,SIZES
base=previous.base;binding=previous.binding;bound=previous.bound
PARENT=Path('experiments/results/cnf-targeted-backbone')
MODES=('targeted','quotient')
FILES=('experiments/cnf_binary_equivalence.py','experiments/compare_cnf_binary_equivalence.py','solver/test_cnf_binary_equivalence.py')


def native_rows(s):return dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
def extension_rows(s):
    if not s.db.execute('SELECT 1 FROM sqlite_master WHERE name=?',(TABLE,)).fetchone():return {}
    return dict(s.db.execute(f'SELECT id,payload FROM {TABLE} ORDER BY id'))


def check_answer(s,store,source,r):
    cnf,names,root=s._canonical(source);assert root==r['root']
    if r.get('authority','native')==FORMAT:
        assert not r['answer'] and r['model'] is None;assert store.read(root) is not None
    else:
        assert r.get('authority','native')=='native'
        node=s._read(root,cnf);assert node is not None and node['answer']==r['answer']
        if r['answer']:
            model={int(k):v for k,v in r['model'].items()};assert holds(source,model)


def cold(path,cases,records):
    before=base.sha(path);tick=time.perf_counter();s=SnapshotResidualSolver(path);store=EquivalenceStore(s)
    try:
        native=native_rows(s);extensions=extension_rows(s)
        for root in native:assert s._read(root) is not None
        for root in extensions:assert store.read(root) is not None
        for c,r in zip(cases,records):check_answer(s,store,c['source'],r['result'])
        result=dict(native_nodes=len(native),extension_nodes=len(extensions),queries=len(records),counts=dict(s.counts))
    finally:s.close()
    assert base.sha(path)==before;result['seconds']=time.perf_counter()-tick;return result


def prepare(out):
    out.mkdir(exist_ok=False);parent=base.load(PARENT/'checkpoint.json')
    sources=dict(parent['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'parent';base.restore_archive(parent['reference_union'],path);s=SnapshotResidualSolver(path)
        try:rows=native_rows(s)
        finally:s.close()
    by_hash={base.key_sha(k):base.load_json(v) for k,v in rows.items()}
    selected=[r for r in base.load(PARENT/'attribution.json')['frontier']['interactions'] if r['equivalence_blocks'] and not r['forced_literals'] and r['native_kind']=='split']
    assert len(selected)==11;cases=[];seen=set()
    def add(source,group,family,**metadata):
        key=token(normalize(source)[0],Counter());assert key not in seen
        seen.add(key);cases.append(dict(case=len(cases),source=source,group=group,family=family,known_in_parent=key in rows,root=key,**metadata))
    for r in selected:add(by_hash[r['root_sha256']]['cnf'],'saved',r['family'],old_case=r['case'],saved_root=r['root_sha256'])
    for r in selected:
        source=by_hash[r['root_sha256']]['cnf'];n=max(abs(l) for c in source for l in c);a,b=1,n
        add(source+[[n+1,a,b]],'added-free-clause',r['family'],old_case=r['case'])
        add(source+[[n+1,a,b],[-n-1,a,b]],'added-coupling',r['family'],old_case=r['case'])
        # Deletion can invalidate the old equivalence; recognition must start anew.
        cid=next(i for i,c in enumerate(source) if len(c)==2)
        add(source[:cid]+source[cid+1:],'deleted-binary',r['family'],old_case=r['case'],deleted_clause=source[cid])
    for family in FAMILIES:
        for size in SIZES:
            for sample in (0,1):
                for attempt in range(137,10137):
                    source=generate(family,size,sample,attempt);key=token(normalize(source)[0],Counter())
                    if key not in seen and key not in rows:break
                else:raise ValueError('No fresh generated control')
                add(source,'fresh-control',family,size=size,sample=sample,attempt=attempt)
    assert len(cases)==68
    base.write(out/'cases.json',cases)
    p=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,cases=binding(out/'cases.json'),
        orders=[list(MODES),list(reversed(MODES))],limits=['Both arms start from an empty archive and share previous answers within this stream. Saved inputs are counterfactual reconstruction, not production-prefix replay.',
        'Only top-level solve attempts one largest binary SCC block; recursive native acquisition is unchanged. Family/group metadata never enters search.',
        'Negative substitution proofs use an explicit separate reader/table. Their child dependencies must be ordinary native UNSAT proofs; native search never reads the new table.',
        'All setup, discovery, substitution, proof checking, counters, persistence, warm reuse, cold replay, serialization and compression are timed. Truth audits, parent-history union and final report writing are outside worker timing.',
        'No historical preprocessing, affine/guard admission benefit, arbitrary SAT coverage or end-to-end production speedup is inferred from this pilot.'])
    base.write(out/'protocol.json',p)


def worker(out,p,mode):
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=bound(p['cases']);out.mkdir();began=time.perf_counter();records=[];warm=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';cls=BinaryEquivalenceSolver if mode=='quotient' else AccountedTargetedBackboneSolver
        s=cls(path);setup_seconds=time.perf_counter()-began
        try:
            for c in cases:
                tick=time.perf_counter();before=native_rows(s);oldext=extension_rows(s);r=s.solve(c['source'])
                after=native_rows(s);ext=extension_rows(s);assert before.items()<=after.items() and oldext.items()<=ext.items()
                records.append(dict(case=c['case'],result=r,new_native_ids=sorted(set(after)-set(before)),new_extension_ids=sorted(set(ext)-set(oldext)),
                    native_nodes=len(after)-len(before),native_payload=sum(len(k)+len(v) for k,v in after.items() if k not in before),
                    extension_nodes=len(ext)-len(oldext),extension_payload=sum(len(k)+len(v) for k,v in ext.items() if k not in oldext),seconds=time.perf_counter()-tick))
            final=native_rows(s);extensions=extension_rows(s);warm_tick=time.perf_counter()
            with patch.object(s,'_expand',side_effect=AssertionError('Warm expansion')):
                for c,r in zip(cases,records):
                    got=s.solve(c['source']);assert got['answer']==r['result']['answer'];warm.append(got)
            assert native_rows(s)==final and extension_rows(s)==extensions
            warm_seconds=time.perf_counter()-warm_tick
        except BaseException:
            s.close();base.write(out/'partial.json',records);base.archive(path,out);raise
        else:s.close()
        audit=cold(path,cases,records)
        base.write(out/'queries.json',records);base.write(out/'warm.json',warm);archive=base.archive(path,out)
    counters=Counter()
    for r in records:counters.update(r['result']['metrics'])
    summary=dict(mode=mode,queries=len(cases),positive=sum(r['result']['answer'] for r in records),native_nodes=len(final),
        native_payload=sum(len(k)+len(v) for k,v in final.items()),extension_nodes=len(extensions),extension_payload=sum(len(k)+len(v) for k,v in extensions.items()),
        counters=dict(counters),setup_seconds=setup_seconds,query_seconds=sum(r['seconds'] for r in records),warm_seconds=warm_seconds,cold_seconds=audit['seconds'],
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
