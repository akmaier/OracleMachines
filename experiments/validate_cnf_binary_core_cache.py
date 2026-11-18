#!/usr/bin/env python3
"""Audit exact discovery reuse, chronological acquisition and preserved histories."""
from collections import Counter
from pathlib import Path
import copy,json,shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_binary_core_cache as study
from experiments.cnf_binary_core_cache import BinaryCoreCache,core_key,parse_key,transport,encode,TABLE as CACHE
from experiments.cnf_binary_equivalence import discover,TABLE as V1,EquivalenceStore
from experiments.cnf_compact_equivalence import TABLE as V2,CompactEquivalenceStore,dependency
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_affine_negative import TABLE as AFFINE
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_cross_family import truth_table
base=study.base;previous=study.previous


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);cases=study.bound(p['cases']);report=base.load(out/'report.json')
    assert cases==study.bound(p['workload_origin'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    oldv=base.load(study.PARENT/'validation.json');manifests=dict(oldv['parent_manifests']);path=study.PARENT/'manifest.json'
    manifests[str(path)]=dict(sha256=base.sha(path),artifacts_checked=len(base.load(path)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'];m=base.load(path)['artifacts'];assert len(m)==entry['artifacts_checked']
        for f,h in m.items():assert base.sha(f)==h,f
        artifacts+=len(m)
    assert len(manifests)==110 and artifacts==7683
    truths=[truth_table(c['source']) for c in cases];base.write(out/'truth.json',truths)
    states={};by_mode={};audits=[];records=[];equal=Counter()
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);initial_path=tmp/'initial';base.restore_archive(parent['reference_union'],initial_path);s=SnapshotResidualSolver(initial_path)
        try:
            initial={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in ('cnf_residual_v1',AFFINE,V1,V2)}
            assert not study.cache_rows(s)
        finally:s.close()
        assert [len(v) for v in initial.values()]==[28691,26,42,42]
        for sample in report['samples']:
            data=study.bound(sample);rows=study.bound(data['queries']);path=tmp/(sample['mode']+str(sample['repeat']));base.restore_archive(data['archive'],path)
            assert len(rows)==68;s=SnapshotResidualSolver(path);store=CompactEquivalenceStore(s);cache=BinaryCoreCache(s)
            try:
                native=study.native_rows(s);ext=study.extension_rows(s);saved=study.cache_rows(s)
                available=set();extensions=set();cache_seen=set();canonical_cache={}
                for c,r,truth in zip(cases,rows,truths):
                    assert r['case']==c['case'];n=set(r['new_native_ids']);e=set(r['new_extension_ids'])
                    assert not n&available and not e&extensions and len(n)==r['native_nodes'] and len(e)==r['extension_nodes']
                    assert len(n)==len(r['new_native_ids']) and len(e)==len(r['new_extension_ids'])
                    assert r['native_payload']==sum(len(k)+len(native[k]) for k in n)
                    assert r['extension_payload']==sum(len(k)+len(ext[k]) for k in e)
                    for k in n:
                        proof=json.loads(native[k]).get('proof',{})
                        assert {proof[f] for f in ('child','low','high') if f in proof}<=available|n
                    for k in e:assert dependency(s,k,json.loads(ext[k]))[1] in available|n
                    available|=n;extensions|=e
                    assert r['result']['root'] in (available if r['result']['authority']=='native' else extensions)
                    study.check_answer(s,store,c['source'],r['result']);assert r['result']['answer']==truth['answer']
                    cnf,_,_=s._canonical(c['source'])
                    if sample['mode']!='compact':
                        eligible=all(len(x)>=2 for x in cnf) and any(len(x)==2 for x in cnf) and any(len(x)>2 for x in cnf)
                        expected_new=set()
                        if eligible:
                            ids=[i for i,x in enumerate(cnf) if len(x)==2];key=core_key(tuple(cnf[i] for i in ids))
                            # Independent full-source recognition must equal the local tree transported here.
                            evidence=discover(cnf,Counter());inverse={cid:i for i,cid in enumerate(ids)}
                            local=transport(evidence,inverse,Counter());canonical_cache[key]=encode(local)
                            if key not in cache_seen:expected_new.add(key)
                            cache_seen.add(key)
                            if saved:
                                assert saved[key]==encode(local)
                                assert transport(json.loads(saved[key]),ids,Counter())==evidence
                        assert set(r['new_cache_ids'])==expected_new and r['cache_entries']==len(cache_seen)
                        assert r['cache_payload']==sum(len(k)+len(v) for k,v in canonical_cache.items())
                assert available==set(native) and extensions==set(ext)
                if sample['mode']=='persistent':assert canonical_cache==saved
                else:assert not saved
                if sample['mode'] in states:assert (native,ext,canonical_cache)==states[sample['mode']]
                else:states[sample['mode']]=(native,ext,canonical_cache)
                for key,payload in saved.items():cache.verify(key,payload)
                if sample['repeat']==0:
                    by_mode[sample['mode']]=rows
                    if sample['mode']=='persistent':records=[dict(source=c['source'],result={k:r['result'][k] for k in ('answer','model','root')},authority=r['result']['authority']) for c,r in zip(cases,rows)]
            finally:s.close()
            audits.append(study.cold(path,cases,rows))
        for mode in ('memory','persistent'):
            assert states[mode][:2]==states['compact'][:2]
            for a,b in zip(by_mode['compact'],by_mode[mode]):
                for name in ('new_native_ids','new_extension_ids','native_nodes','native_payload','extension_nodes','extension_payload'):assert a[name]==b[name]
                for name in ('answer','model','root','authority'):assert a['result'][name]==b['result'][name]
                for k,v in a['result']['metrics'].items():
                    if k.startswith('binary_') or k in ('expanded_nodes','propagation_literal_visits','equiv_checked_edges','equiv_certificate_walk_edges','equiv_positive_lifts'):
                        assert b['result']['metrics'].get(k,0)==v,(mode,a['case'],k)
                equal['chronological_acquisitions']+=1
        assert states['memory'][2]==states['persistent'][2];new_cache=states['persistent'][2]
        # All measured certificate rows already occur in the parent trial archive;
        # preserve the union's chosen alternatives rather than overwrite them.
        alternatives=[]
        for key,payload in states['compact'][0].items():
            assert key in initial['cnf_residual_v1']
            if initial['cnf_residual_v1'][key]!=payload:
                alternatives.append(key)
                assert json.loads(initial['cnf_residual_v1'][key])['answer']==json.loads(payload)['answer']
        assert states['compact'][1]==initial[V2]
        path=tmp/'union';shutil.copyfile(initial_path,path);s=previous.native.ResidualSolver(path)
        try:
            with s.db:
                s.db.execute(f'CREATE TABLE {CACHE} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                s.db.executemany(f'INSERT INTO {CACHE} VALUES (?,?)',new_cache.items())
            for table,rows in initial.items():assert dict(s.db.execute(f'SELECT id,payload FROM {table}'))==rows
            _,_,indices,prepared,_=previous.prep.setup(s,base.load(study.prior.prior.PARENT/'protocol.json'))
        finally:s.close()
        used=[(n,study.bound(parent[n])) for n in previous.OLD_FIELDS]
        historical=previous.audit_records(path,previous.inherited(parent),study.bound(parent['conditioned_core_projections']),prepared,used,indices)
        old_records=study.bound(parent['binary_equivalence_decisions'])+study.bound(parent['compact_equivalence_decisions'])
        s=SnapshotResidualSolver(path);store=CompactEquivalenceStore(s);terminal=TerminalStore(s);cache=BinaryCoreCache(s)
        try:
            for root in initial['cnf_residual_v1']:assert s._read(root) is not None
            for root in initial[V1]:assert store.legacy.read(root) is not None
            for root in initial[V2]:assert store.read(root) is not None
            for root in initial[AFFINE]:assert terminal.read(root) is not None
            for key,payload in new_cache.items():cache.verify(key,payload)
            for r in old_records+records:study.check_answer(s,store,r['source'],dict(r['result'],authority=r['authority']))
        finally:s.close()
        assert base.sha(initial_path)==parent['reference_union']['database_sha256']
        dest=out/'reference-union';dest.mkdir(exist_ok=True);archive=base.archive(path,dest)
    base.write(out/'decisions.json',records)
    sources=dict(p['source_fingerprints']);sources['experiments/validate_cnf_binary_core_cache.py']=base.sha(__file__)
    checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        binary_core_cache_study=study.binding(out/'report.json'),binary_core_cache_decisions=study.binding(out/'decisions.json'),
        binary_core_cache_solver='experiments.cnf_binary_core_cache.CachedBinaryEquivalenceSolver',binary_core_cache_reader='experiments.cnf_binary_core_cache.BinaryCoreCache')
    base.write(out/'checkpoint.json',checkpoint)
    pairs=[]
    for repeat in range(2):
        rows={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        for mode in ('memory','persistent'):
            pairs.append(dict(repeat=repeat,mode=mode,**{k:rows[mode][k]-rows['compact'][k] for k in ('query_seconds','cold_seconds','complete_worker_seconds')}))
    base.write(out/'attribution.json',dict(pairs=pairs,equal_acquisition=dict(equal),
        solve_seconds={m:[sum(x['result']['seconds'] for x in base.load(out/f'{m}-{r}/queries.json')) for r in range(2)] for m in study.MODES},
        prior_structural_opportunities=study.binding('experiments/results/cnf-binary-equivalence/attribution.json'),
        limits=['Same 68 inputs; all proof payloads and source decisions unchanged. No new source coverage.',
            'Only identical binary clauses in identical coordinates share entries; discovery misses are not UNSAT answers.',
            'Persisted outcomes are recomputed once on first use; cold replay includes this cost.',
            'Complete-worker timings include per-query metadata scans and cache serialization for the audit; not just the public solve API.']))
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        preserved_tables={t:len(rows) for t,rows in initial.items()},new_cache_entries=len(new_cache),query_audits=6*len(cases),truth_tables=len(truths),
        old_composed_records=len(previous.inherited(parent)),old_pilot_records=len(old_records),new_records=len(records),
        alternate_native_keys=alternatives,audits=audits,historical_cold=historical,equal_acquisition=dict(equal),
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result)
    print(base.encode({k:result[k] for k in ('passed','new_cache_entries','query_audits','truth_tables','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
