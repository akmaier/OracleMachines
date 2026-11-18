#!/usr/bin/env python3
"""Audit bounded normalization reuse against exact decisions and preserved history."""
from collections import Counter
from pathlib import Path
import copy,json,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_query_canonical_cache as study
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore,discover_all,check_blocks,dependency,TABLE as V3,FORMAT as F3
from experiments.cnf_binary_equivalence import TABLE as V1
from experiments.cnf_compact_equivalence import TABLE as V2,dependency as old_dependency
from experiments.cnf_binary_core_cache import BinaryCoreCache,TABLE as CACHE
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_affine_negative import TABLE as AFFINE
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_cross_family import truth_table
from experiments.cnf_residual_dag import normalize,token
base=study.base;previous=study.previous
TABLES=('cnf_residual_v1',AFFINE,V1,V2,V3,CACHE)
PILOTS=('binary_equivalence_decisions','compact_equivalence_decisions','binary_core_cache_decisions','multiblock_equivalence_decisions','known_quotient_decisions')


def ordinary_counts(counts):
    return {k:v for k,v in counts.items() if not k.startswith('canonical_cache_') and k not in ('normalization_literal_visits','key_serialized_bytes')}


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);cases=study.bound(p['cases']);report=base.load(out/'report.json')
    assert cases==study.bound(p['workload_origin']) and len(cases)==104
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    oldv=base.load(study.PARENT/'validation.json');manifests=dict(oldv['parent_manifests']);path=study.PARENT/'manifest.json'
    manifests[str(path)]=dict(sha256=base.sha(path),artifacts_checked=len(base.load(path)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'];m=base.load(path)['artifacts'];assert len(m)==entry['artifacts_checked']
        for f,h in m.items():assert base.sha(f)==h,f
        artifacts+=len(m)
    assert len(manifests)==113 and artifacts==7807
    truths=[truth_table(c['source']) for c in cases];base.write(out/'truth.json',truths)
    states={};by_mode={};audits=[];choice_audits=0;hit_audits=0
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);initial_path=tmp/'initial';base.restore_archive(parent['reference_union'],initial_path);s=SnapshotResidualSolver(initial_path)
        try:initial={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in TABLES}
        finally:s.close()
        assert [len(v) for v in initial.values()]==[28886,26,42,53,22,34]
        for sample in report['samples']:
            data=study.bound(sample);rows=study.bound(data['queries']);path=tmp/(sample['mode']+str(sample['repeat']));base.restore_archive(data['archive'],path)
            assert len(rows)==104;s=SnapshotResidualSolver(path);store=MultiEquivalenceStore(s)
            try:
                native=study.native_rows(s);ext=study.extension_rows(s);available=set();extensions=set()
                for c,r,truth in zip(cases,rows,truths):
                    assert r['case']==c['case'];n=set(r['new_native_ids']);e=set(r['new_extension_ids']);rr=r['result']
                    assert not n&available and not e&extensions and len(n)==r['native_nodes'] and len(e)==r['extension_nodes']
                    assert len(n)==len(r['new_native_ids']) and len(e)==len(r['new_extension_ids'])
                    assert r['native_payload']==sum(len(k)+len(native[k]) for k in n)
                    assert r['extension_payload']==sum(len(k)+len(ext[k]) for k in e)
                    trace=rr.get('quotient_choice')
                    if trace is not None:
                        assert sample['mode']!='single';cnf,_=normalize(c['source']);blocks=discover_all(cnf,Counter());assert len(blocks)>1
                        targets=[check_blocks(cnf,b,Counter())[0] for b in (blocks,blocks[:1])]
                        keys=[token(normalize(t)[0],Counter()) for t in targets];full_known=keys[0] in available
                        expected=[dict(kind='all',key=keys[0],known=full_known)]
                        if not full_known:expected.append(dict(kind='first',key=keys[1],known=keys[1] in available))
                        assert trace['candidates']==expected
                        selected='first' if not full_known and keys[1] in available else 'all';assert trace['selected']==selected
                        hit=full_known or keys[1] in available;choice_audits+=1;hit_audits+=int(hit)
                        if hit:
                            selected_key=keys[1 if selected=='first' else 0];node=s._read(selected_key)
                            assert node is not None and node['answer']==rr['answer']
                            assert n<=({rr['root']} if rr['answer'] else set()) and not rr['metrics'].get('expanded_nodes',0)
                    for k in n:
                        proof=json.loads(native[k]).get('proof',{})
                        assert {proof[f] for f in ('child','low','high') if f in proof}<=available|n
                    for k in e:
                        node=json.loads(ext[k]);child=(dependency if node['format']==F3 else old_dependency)(s,k,node)[1]
                        assert child in available|n
                    available|=n;extensions|=e
                    assert rr['root'] in (available if rr['authority']=='native' else extensions)
                    study.check_answer(s,store,c['source'],rr);assert rr['answer']==truth['answer']
                    if sample['mode'] in ('cached','small'):
                        capacity=128*1024 if sample['mode']=='cached' else 8*1024
                        assert rr['canonical_cache_capacity']==capacity
                        assert rr['metrics']['canonical_cache_peak_bytes']<=capacity
                        assert rr['metrics']['canonical_cache_calls']==rr['metrics'].get('canonical_cache_hits',0)+rr['metrics'].get('canonical_cache_misses',0)
                assert available==set(native) and extensions==set(ext)
                assert native.items()<=initial['cnf_residual_v1'].items()
                for k,payload in ext.items():assert initial[V3 if json.loads(payload)['format']==F3 else V2][k]==payload
                if sample['mode'] in states:assert (native,ext)==states[sample['mode']]
                else:states[sample['mode']]=(native,ext)
                if sample['repeat']==0:by_mode[sample['mode']]=rows
            finally:s.close()
            audits.append(study.cold(path,cases,rows))
        assert choice_audits==144 and hit_audits==84
        comparison_fields=('new_native_ids','new_extension_ids','new_cache_ids','native_nodes','extension_nodes','native_payload','extension_payload','cache_entries','cache_payload')
        result_fields=('answer','model','root','authority','quotient_choice')
        for mode in ('cached','small'):
            assert states[mode]==states['known']
            for repeat in range(2):
                rows=base.load(out/f'{mode}-{repeat}/queries.json')
                for a,b in zip(by_mode['known'],rows):
                    for field in comparison_fields:assert a[field]==b[field],(mode,field)
                    for field in result_fields:assert a['result'][field]==b['result'][field],(mode,field)
                    x=a['result']['metrics'];y=b['result']['metrics'];assert ordinary_counts(x)==ordinary_counts(y)
                    assert x['normalization_literal_visits']==y['normalization_literal_visits']+y.get('canonical_cache_reused_literals',0)
                    assert y['canonical_cache_validated_literals']==x['normalization_literal_visits']
        for mode in ('single','known'):
            old=base.load(study.PARENT/f'{mode}-0/queries.json')
            for a,b in zip(old,by_mode[mode]):
                for f in comparison_fields:assert a[f]==b[f]
                for f in result_fields+('metrics',):assert a['result'].get(f)==b['result'].get(f)
        s=previous.native.ResidualSolver(initial_path)
        try:_,_,indices,prepared,_=previous.prep.setup(s,base.load('experiments/results/cnf-targeted-backbone/protocol.json'))
        finally:s.close()
        used=[(n,study.bound(parent[n])) for n in previous.OLD_FIELDS]
        historical=previous.audit_records(initial_path,previous.inherited(parent),study.bound(parent['conditioned_core_projections']),prepared,used,indices)
        old_records=sum((study.bound(parent[f]) for f in PILOTS),[])
        s=SnapshotResidualSolver(initial_path);store=MultiEquivalenceStore(s);terminal=TerminalStore(s);cache=BinaryCoreCache(s)
        try:
            for root in initial['cnf_residual_v1']:assert s._read(root) is not None
            for root in initial[V1]:assert store.old.legacy.read(root) is not None
            for root in initial[V2]:assert store.old.read(root) is not None
            for root in initial[V3]:assert store.read(root)['format']==F3
            for root in initial[AFFINE]:assert terminal.read(root) is not None
            for key,payload in initial[CACHE].items():cache.verify(key,payload)
            for r in old_records:study.check_answer(s,store,r['source'],dict(r['result'],authority=r['authority']))
            for t,rows in initial.items():assert rows==dict(s.db.execute(f'SELECT id,payload FROM {t}'))
        finally:s.close()
        assert base.sha(initial_path)==parent['reference_union']['database_sha256']
    sources=dict(p['source_fingerprints']);sources['experiments/validate_cnf_query_canonical_cache.py']=base.sha(__file__)
    checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],source_fingerprints=sources,
        query_canonical_cache_study=study.binding(out/'report.json'),query_canonical_cache_solver='experiments.cnf_query_canonical_cache.QueryCanonicalSolver')
    # No new mathematical results: bind the unchanged parent union/decisions rather
    # than create another identical multi-megabyte archive or duplicate histories.
    base.write(out/'checkpoint.json',checkpoint)
    pairs=[]
    for repeat in range(2):
        rows={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        for mode in ('cached','small'):
            pairs.append(dict(repeat=repeat,mode=mode,**{k:rows[mode][k]-rows['known'][k] for k in ('query_seconds','warm_seconds','cold_seconds','complete_worker_seconds')}))
    base.write(out/'attribution.json',dict(pairs=pairs,
        solve_seconds={m:[sum(x['result']['seconds'] for x in base.load(out/f'{m}-{r}/queries.json')) for r in range(2)] for m in study.MODES},
        warm_cache_hits={m:[sum(x['metrics'].get('canonical_cache_hits',0) for x in base.load(out/f'{m}-{r}/warm.json')) for r in range(2)] for m in study.MODES},
        limits=['Both cache arms preserve acquisition counters and exact certificates. Only pure normalization/key generation is reused.',
            'Same 104 replayed small inputs; no new coverage or representative general-SAT speedup.',
            'Cache object bounds are conservative retained-state charges, not total runtime/RSS/transient-allocation bounds.']))
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        preserved_tables={t:len(rows) for t,rows in initial.items()},reference_union_unchanged=True,new_native=0,new_extensions=0,
        query_audits=8*len(cases),truth_tables=len(truths),choice_audits=choice_audits,known_hit_audits=hit_audits,
        exact_cache_query_comparisons=4*len(cases),old_composed_records=len(previous.inherited(parent)),old_pilot_records=len(old_records),
        audits=audits,historical_cold=historical,checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result)
    print(base.encode({k:result[k] for k in ('passed','reference_union_unchanged','query_audits','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
