#!/usr/bin/env python3
"""Compare unchanged quotient acquisition with compact negative records."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_equivalence as prior
from experiments.cnf_compact_equivalence import CompactBinaryEquivalenceSolver,CompactEquivalenceStore,TABLE as COMPACT_TABLE,FORMAT as COMPACT_FORMAT
from experiments.cnf_binary_equivalence import BinaryEquivalenceSolver,EquivalenceStore,TABLE,FORMAT
from experiments.cnf_targeted_backbone import AccountedTargetedBackboneSolver
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_residual_dag import normalize,token,holds
from experiments.cnf_cross_family import generate,FAMILIES,SIZES
previous=prior.previous
base=prior.base;binding=prior.binding;bound=prior.bound
PARENT=Path('experiments/results/cnf-binary-equivalence')
MODES=('targeted','quotient','compact')
FILES=('experiments/cnf_compact_equivalence.py','experiments/compare_cnf_compact_equivalence.py','solver/test_cnf_compact_equivalence.py')


def native_rows(s):return dict(s.db.execute('SELECT id,payload FROM cnf_residual_v1 ORDER BY id'))
def extension_rows(s,table=None):
    if table is None:
        tables={r[0] for r in s.db.execute('SELECT name FROM sqlite_master WHERE type=?',('table',))}
        table=COMPACT_TABLE if COMPACT_TABLE in tables else TABLE
    if not s.db.execute('SELECT 1 FROM sqlite_master WHERE name=?',(table,)).fetchone():return {}
    return dict(s.db.execute(f'SELECT id,payload FROM {table} ORDER BY id'))


def check_answer(s,store,source,r):
    cnf,names,root=s._canonical(source);assert root==r['root']
    if r.get('authority','native') in (FORMAT,COMPACT_FORMAT):
        assert not r['answer'] and r['model'] is None
        node=store.legacy.read(root) if r['authority']==FORMAT else store.read(root)
        assert node is not None and node['format']==r['authority']
    else:
        assert r.get('authority','native')=='native'
        node=s._read(root,cnf);assert node is not None and node['answer']==r['answer']
        if r['answer']:
            model={int(k):v for k,v in r['model'].items()};assert holds(source,model)


def cold(path,cases,records):
    before=base.sha(path);tick=time.perf_counter();s=SnapshotResidualSolver(path);store=CompactEquivalenceStore(s)
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
    base.write(out/'cases.json',base.load(PARENT/'cases.json'))
    p=dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,cases=binding(out/'cases.json'),
        workload_origin=binding(PARENT/'cases.json'),orders=[list(MODES),list(reversed(MODES))],limits=[
        'All arms start from empty archives on the same 68-input catalog. Known-in-parent labels describe the original pilot; these are repeated inputs, not fresh production coverage.',
        'Targeted is the native control. Quotient and compact have identical discovery/substitution and native children; only negative persistence/replay changes.',
        'V2 stores format, answer and evidence. Its canonical full source key and checked substitution reconstruct the source and native negative child. Old v1 rows stay readable and unchanged.',
        'Setup, discovery, checking, publication, metadata scans, warm reuse, cold replay, serialization and compression are timed. Imports/source audits, truth checks, union/history audits and final reports are outside worker timing.',
        'Optional top-level pilot only. No new mathematical coverage, recursive production integration or unrestricted SAT bound follows.'])
    base.write(out/'protocol.json',p)


def worker(out,p,mode):
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=bound(p['cases']);out.mkdir();began=time.perf_counter();records=[];warm=[]
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';cls={'targeted':AccountedTargetedBackboneSolver,'quotient':BinaryEquivalenceSolver,'compact':CompactBinaryEquivalenceSolver}[mode]
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
