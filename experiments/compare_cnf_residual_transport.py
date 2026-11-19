#!/usr/bin/env python3
"""Frozen source-variable transport with a compact-coordinate ablation."""
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
from experiments.cnf_residual_transport import ResidualTransportSolver,TABLE as HINT_TABLE
from itertools import product
import json
from experiments.cnf_affine_negative import NegativeStore,TABLE as AFFINE_TABLE,FORMAT as AFFINE_FORMAT
from experiments.cnf_support_plan import PlannedNegativeSolver
from experiments.cnf_publication_batches import BatchedPublicationSolver
from experiments.cnf_proof_normalization_reuse import ProofNormalizationSolver
from experiments.cnf_ordered_normalization import OrderedNormalizationSolver
from experiments.cnf_canonical_verify import CanonicalVerifySnapshot
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore
from experiments.cnf_residual_dag import normalize,token
base=prior.base;binding=prior.binding;bound=prior.bound
PARENT=Path('experiments/results/cnf-partial-residual-pool')
MODES=('base','compact','mapped')
CLASSES=dict(base=InputSafeAffineProbeSolver,compact=ResidualTransportSolver,mapped=ResidualTransportSolver)
TABLES=larger.TABLES+(AFFINE_TABLE,)
FILES=('experiments/cnf_residual_transport.py','experiments/compare_cnf_residual_transport.py','solver/test_cnf_residual_transport.py')
SPLITS=dict(mapping=(3,4,5),holdout=(144,150,156))


def catalog(split):
    cases=[]
    if split=='mapping':
        for size in SPLITS[split]:
            core=[list(c) for c in product(*[(-v,v) for v in range(10,10+size)])]
            edit=core+[[v-9,v,20+v] for v in range(10,10+size)]
            deleted=edit[1:];start=len(cases)
            for variant,source in zip(('base','edit','delete','repeat'),(core,edit,deleted,edit)):
                cnf,names=normalize(source)
                cases.append(dict(case=len(cases),family='coordinate-shift',size=size,sample=0,
                    variant=variant,base_case=start,source=source,root=token(cnf,Counter()),
                    variables=len(names),clauses=len(cnf),literals=sum(map(len,cnf))))
        return cases
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
    assert not {c['root'] for c in cases['mapping']} & {c['root'] for c in cases['holdout']}
    for split,values in cases.items():base.write(out/(split+'-cases.json'),values)
    base.write(out/'protocol.json',dict(parent=binding(PARENT/'checkpoint.json'),source_fingerprints=sources,
        cases={s:binding(out/(s+'-cases.json')) for s in SPLITS},node_limit=LIMIT,
        negative_limits=dict(negative_capacity=16,negative_literal_limit=4096,negative_node_limit=256,negative_support_literals=131072),plan_byte_limit=4*1024*1024,
        affine_limits=dict(affine_variables=256,affine_clauses=4096,affine_literals=16384,affine_xors=65536),
        transport_limits=dict(transport_capacity=32,transport_bytes=512*1024,transport_stage_limit=32,
            transport_probes=32,transport_candidates=4,transport_literals=1024,transport_variables=256,
            transport_depth=128,transport_map_bytes=512*1024),
        orders=[list(MODES),list(reversed(MODES))],preparation_seconds=time.perf_counter()-tick,limits=[
        'Three policies: preceding safe affine baseline; mapped hints; identical hint admission/map capture/persistence with compact-coordinate matching. Two opposite orders, twelve serial empty-archive workers.',
        'Fresh 144/150/156 holdout: six generators, two seeds, base/edit/repeat, 108 attempts and 72 roots. Mapping diagnostic: widths 3/4/5, base/edit/deleted-premise/repeat, 12 attempts. No donor or generator labels reach search.',
        'The mapping diagnostic uses affine_variables=1 in every mode to expose native map transport. Holdout retains the preceding affine budgets. Diagnostic design is not representative coverage evidence.',
        'At most 32 staged hints/query, 32 retained hints, 512 KiB separate stage and pool charges; 32 probes/query and four anchor-matching candidates/probe. Whole-source containment only; no causal extraction added.',
        'Maps have at most 256 variables and 64-bit positive IDs, depth at most 128, and 512 KiB charged live map tuples. An ineligible map only disables this optional retrieval.',
        'Only order-preserving mappings already carried by normalization are retained. Stable external variable IDs propose correspondence; arbitrary renaming/isomorphism is not discovered.',
        'The native subset checker remains authority. Persisted map hints never authenticate answers or lift conditional residuals to unconditioned sources. Only committed native origins qualify for post-query metadata commit.',
        'Cold restart reloads bounded map metadata. Metadata is a mutable separate hint table; native and affine proof archives remain append-only. All misses, capture, checking, maintenance, persistence, warm/cold replay and reconstruction are charged.',
        'Retained charges exclude transient copies, root/input normalization, all proof checking and full native search state. SQLite pages and hostile enlarged metadata tables have separate costs. No uniform polynomial SAT bound follows.']))



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
        if mode!='base':options.update(p['transport_limits']);options['transport']=mode=='mapped'
        if split=='mapping':options['affine_variables']=1
        s=CLASSES[mode](path,node_limit=p['node_limit'],**options)
        with s.db:s.db.execute(f'CREATE TABLE IF NOT EXISTS {HINT_TABLE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
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
            hints=dict(s.db.execute(f'SELECT id,payload FROM {HINT_TABLE}'))
            memory=prior.deep_size((s.checked,s.equivalences.checked,s.equivalences.old.checked,
                                   s.equivalences.old.legacy.checked,s.binary_cores.checked,getattr(s,"witness_pool",{}),getattr(s,"negative_pool",{}),terminal.checked,getattr(s,"transport_pool",{})))
            warm_tick=time.perf_counter()
            with patch.object(s,'_expand',side_effect=AssertionError('Warm expansion')):
                for c,r in zip(cases,records):
                    if r['result'] is None:continue
                    got=attempt(s,c['source']);assert got['status']==r['status'];warm.append(dict(case=c['case'],**got))
            warm_seconds=time.perf_counter()-warm_tick
            assert prior.native_rows(s)==final and prior.extension_rows(s)==ext and affine_rows(s)==affine
            assert dict(s.db.execute(f'SELECT id,payload FROM {HINT_TABLE}'))==hints
        except BaseException:
            s.close();base.write(out/'partial.json',records);base.archive(path,out);raise
        else:s.close()
        audit=cold(path,cases,records)
        tick=time.perf_counter();s=CLASSES[mode](path,node_limit=p['node_limit'],**options)
        reconstruction=dict(transport_seed_entries=len(getattr(s,'transport_pool',{})),transport_seed_counts=getattr(s,'transport_setup_counts',{}),transport_seed_seconds=getattr(s,'transport_setup_seconds',0),negative_seed_entries=len(getattr(s,'negative_pool',{})),seed_seconds=getattr(s,'witness_setup_seconds',0),seed_counts=getattr(s,'witness_setup_counts',{}))
        reconstruction['setup_seconds']=time.perf_counter()-tick
        try:
            with patch.object(s,'_expand',side_effect=AssertionError('Cold exact-root expansion')):
                for c,r in zip(cases,records):
                    if r['result'] is not None:assert attempt(s,c['source'])['status']==r['status']
            assert dict(s.db.execute(f'SELECT id,payload FROM {HINT_TABLE}'))==hints
            reconstruction['transport_replay_entries']=len(getattr(s,'transport_pool',{}))
            reconstruction['pool_entries']=len(getattr(s,'witness_pool',{}))
            reconstruction['negative_replay_entries']=len(getattr(s,'negative_pool',{}))
        finally:s.close()
        reconstruction['seconds']=time.perf_counter()-tick
        base.write(out/'queries.json',records);base.write(out/'warm.json',warm);archive=base.archive(path,out)
    summary=dict(hint_rows=len(hints),hint_payload=sum(len(k)+len(v.encode()) for k,v in hints.items()),hint_digest=base.key_sha(base.encode(sorted(hints.items()))),mode=mode,split=split,queries=len(cases),statuses=dict(Counter(r['status'] for r in records)),node_limit=p['node_limit'],sqlite_settings=settings,
        affine_nodes=len(affine),affine_payload=sum(len(k)+len(v) for k,v in affine.items()),affine_digest=base.key_sha(base.encode(sorted(affine.items()))),
        native_nodes=len(final),extension_nodes=len(ext),native_payload=sum(len(k)+len(v) for k,v in final.items()),extension_payload=sum(len(k)+len(v) for k,v in ext.items()),
        native_digest=base.key_sha(base.encode(sorted(final.items()))),extension_digest=base.key_sha(base.encode(sorted(ext.items()))),
        counters=dict(counts),checked_python_bytes=memory,setup_seconds=setup,query_seconds=sum(r['seconds'] for r in records),solve_seconds=sum(r['solve_seconds'] for r in records),
        warm_seconds=warm_seconds,cold_seconds=audit['seconds'],reconstruction_seconds=reconstruction['seconds'],compression_seconds=archive['seconds'],complete_worker_seconds=time.perf_counter()-began,
        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024),
        database_bytes=archive['database_bytes'],compressed_bytes=archive['compressed_bytes'],sidecar_bytes=sum((out/f).stat().st_size for f in ('queries.json','warm.json')),
        transport_peak_bytes=max(r['metrics'].get('transport_retained_bytes',0) for r in records),transport_peak_entries=max(r['metrics'].get('transport_retained_entries',0) for r in records),transport_map_peak_bytes=max(r['metrics'].get('transport_map_peak_bytes',0) for r in records),transport_stage_peak_bytes=max(r['metrics'].get('transport_stage_peak_bytes',0) for r in records),
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
