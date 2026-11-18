#!/usr/bin/env python3
"""Frozen larger mixtures: three unchanged solvers, explicit unknowns and append deltas."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import resource,subprocess,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_ordered_normalization as prior
from experiments.cnf_larger_mixtures import catalog,attempt,LIMIT
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_proof_normalization_reuse import ProofNormalizationSolver
from experiments.cnf_ordered_normalization import OrderedNormalizationSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_residual_dag import normalize,token
base=prior.base;binding=prior.binding;bound=prior.bound
PARENT=Path('experiments/results/cnf-ordered-normalization')
MODES=('batch32','memo128','ordered')
CLASSES=dict(batch32=BatchedPublicationSolver,memo128=ProofNormalizationSolver,ordered=OrderedNormalizationSolver)
TABLES=('cnf_residual_v1','cnf_binary_equivalence_v2','cnf_binary_equivalence_v3')
FILES=('experiments/cnf_larger_mixtures.py','experiments/compare_cnf_larger_mixtures.py','solver/test_cnf_larger_mixtures.py')


def prepare(out):
    out.mkdir(exist_ok=True);assert not (out/'protocol.json').exists();tick=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');sources=dict(parent['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES});cases=catalog()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'old';base.restore_archive(parent['reference_union'],path);s=CanonicalVerifySnapshot(path)
        try:
            known=set(prior.native_rows(s))
            for table in ('cnf_binary_equivalence_v1',)+TABLES[1:]:known.update(prior.extension_rows(s,table))
        finally:s.close()
    for c in cases:
        cnf,names=normalize(c['source']);c['root']=token(cnf,Counter());c['variables']=len(names)
        c['clauses']=len(cnf);c['literals']=sum(map(len,cnf));c['known_in_parent']=c['root'] in known
        if c['variant']=='repeat':assert c['root']==cases[c['base_case']]['root']
    base.write(out/'cases.json',cases)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,
        cases=binding(out/'cases.json'),node_limit=LIMIT,orders=[list(MODES),list(reversed(MODES))],
        preparation_seconds=time.perf_counter()-tick,limits=[
        '108 frozen queries: six generator families, scales 24/48/72, two seeds, base/edit/monotonically relabelled repeat. Shared mixtures have two fewer constructed variables; actual support is recorded.',
        'No solver-driven selection. Novelty is reported against the parent native/extension roots, not enforced by filtering. Labels never enter the solver. This designed catalog is not representative arbitrary SAT.',
        'Exactly 256 native expansions per source attempt. A specific budget exception is recorded as unresolved with no answer; other errors abort. The cap is not a bound on discovery, proof compilation, time or memory.',
        'All three algorithms are unchanged. Each worker starts empty; verified committed prefixes survive budget stops and can help later attempts. Partial pending batches roll back.',
        'Per-query append deltas use monotonically increasing committed rowids, avoiding repeated full-history scans. Setup, metadata deltas, normalization, recognition, solving, checks, persistence, final retained-object walk, warm replay, cold replay and compression are charged.',
        'Preparation is reported separately. Imports/source hashes, posthoc classification/profiling, exhaustive small tests and full history audits are outside worker timing. Cold readers are identical; only completed queries are warmed.']))


def cold(path,cases,records):
    tick=time.perf_counter();before=base.sha(path);s=CanonicalVerifySnapshot(path);store=MultiEquivalenceStore(s)
    try:
        native=prior.native_rows(s);ext=prior.extension_rows(s)
        for key in native:assert s._read(key) is not None
        for key in ext:assert store.read(key) is not None
        for c,r in zip(cases,records):
            if r['result'] is not None:prior.check_answer(s,store,c['source'],r['result'])
            else:assert r['status']=='unresolved'
        result=dict(native=len(native),extensions=len(ext),completed=sum(r['result'] is not None for r in records),metrics=dict(s.counts))
    finally:s.close()
    assert before==base.sha(path);result['seconds']=time.perf_counter()-tick;return result


def worker(out,p,mode):
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    cases=bound(p['cases']);out.mkdir();began=time.perf_counter();records=[];warm=[];marks={t:0 for t in TABLES}
    totals=Counter();counts=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'db';s=CLASSES[mode](path,node_limit=p['node_limit'])
        settings={k:s.db.execute('PRAGMA '+k).fetchone()[0] for k in ('journal_mode','synchronous')};setup=time.perf_counter()-began
        try:
            for c in cases:
                tick=time.perf_counter();r=attempt(s,c['source']);new={}
                assert not s.db.in_transaction and not s.db.pending and not s.db.active
                assert getattr(s,'_proof_memo',None) is None and s._verification_canonical is None
                for table in TABLES:
                    added=s.db.execute(f'SELECT rowid,id,payload FROM {table} WHERE rowid>? ORDER BY rowid',(marks[table],)).fetchall()
                    if added:marks[table]=added[-1][0]
                    new[table]=[key for _,key,_ in added]
                    totals[table+'_nodes']+=len(added);totals[table+'_payload']+=sum(len(k)+len(v) for _,k,v in added)
                counts.update(r['metrics']);records.append(dict(case=c['case'],**r,new_ids=new,retained=dict(totals),seconds=time.perf_counter()-tick))
            final=prior.native_rows(s);ext=prior.extension_rows(s)
            memory=prior.deep_size((s.checked,s.equivalences.checked,s.equivalences.old.checked,
                                   s.equivalences.old.legacy.checked,s.binary_cores.checked))
            warm_tick=time.perf_counter()
            with patch.object(s,'_expand',side_effect=AssertionError('Warm expansion')):
                for c,r in zip(cases,records):
                    if r['result'] is None:continue
                    got=attempt(s,c['source']);assert got['status']==r['status'];warm.append(dict(case=c['case'],**got))
            warm_seconds=time.perf_counter()-warm_tick
            assert prior.native_rows(s)==final and prior.extension_rows(s)==ext
        except BaseException:
            s.close();base.write(out/'partial.json',records);base.archive(path,out);raise
        else:s.close()
        audit=cold(path,cases,records)
        base.write(out/'queries.json',records);base.write(out/'warm.json',warm);archive=base.archive(path,out)
    summary=dict(mode=mode,queries=len(cases),statuses=dict(Counter(r['status'] for r in records)),node_limit=p['node_limit'],sqlite_settings=settings,
        native_nodes=len(final),extension_nodes=len(ext),native_payload=sum(len(k)+len(v) for k,v in final.items()),extension_payload=sum(len(k)+len(v) for k,v in ext.items()),
        native_digest=base.key_sha(base.encode(sorted(final.items()))),extension_digest=base.key_sha(base.encode(sorted(ext.items()))),
        counters=dict(counts),checked_python_bytes=memory,setup_seconds=setup,query_seconds=sum(r['seconds'] for r in records),solve_seconds=sum(r['solve_seconds'] for r in records),
        warm_seconds=warm_seconds,cold_seconds=audit['seconds'],compression_seconds=archive['seconds'],complete_worker_seconds=time.perf_counter()-began,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],sidecar_bytes=sum((out/f).stat().st_size for f in ('queries.json','warm.json')),
        proof_memo_peak_bytes=max(r['metrics'].get('proof_memo_peak_bytes',0) for r in records),
        batch_peak_payload=max(r['metrics'].get('batch_peak_payload',0) for r in records),batch_peak_records=max(r['metrics'].get('batch_peak_records',0) for r in records))
    base.write(out/'report.json',dict(summary=summary,queries=binding(out/'queries.json'),archive=archive,cold=audit))


def run(out):
    p=base.load(out/'protocol.json');samples=[]
    for repeat,order in enumerate(p['orders']):
        for mode in order:
            dest=out/f'{mode}-{repeat}';subprocess.run([sys.executable,__file__,'worker',str(dest),str(out/'protocol.json'),mode],check=True)
            samples.append(dict(mode=mode,repeat=repeat,**binding(dest/'report.json')));print('finished',repeat,mode,flush=True)
    summaries={}
    for mode in MODES:
        values=[bound(s)['summary'] for s in samples if s['mode']==mode];first=values[0]
        timed=[k for k in first if k.endswith('_seconds') or k=='peak_rss_bytes'];fixed=[k for k in first if k not in timed and k not in ('mode','sidecar_bytes')]
        for v in values[1:]:
            for k in fixed:assert v[k]==first[k],k
        summaries[mode]={**{k:first[k] for k in fixed},**{'mean_'+k:sum(v[k] for v in values)/len(values) for k in timed},'sidecar_bytes':[v['sidecar_bytes'] for v in values]}
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,summary=summaries))
    print(base.encode({m:{k:v for k,v in s.items() if k!='counters'} for m,s in summaries.items()}),flush=True)


if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(Path(sys.argv[2]))
    elif sys.argv[1]=='worker':worker(Path(sys.argv[2]),base.load(sys.argv[3]),sys.argv[4])
    else:run(Path(sys.argv[1]))
