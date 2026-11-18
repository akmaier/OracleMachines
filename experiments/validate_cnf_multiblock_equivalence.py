#!/usr/bin/env python3
"""Audit multiblock quotients, chronological reuse and preserved authorities."""
from collections import Counter
from pathlib import Path
import copy,json,shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_multiblock_equivalence as study
from experiments.cnf_multiblock_equivalence import MultiEquivalenceStore,discover_all,check_blocks,dependency,TABLE as V3,FORMAT as F3
from experiments.cnf_binary_equivalence import TABLE as V1,FORMAT as F1
from experiments.cnf_compact_equivalence import TABLE as V2,dependency as old_dependency
from experiments.cnf_binary_core_cache import BinaryCoreCache,TABLE as CACHE
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_affine_negative import TABLE as AFFINE
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_cross_family import truth_table
from experiments.cnf_residual_dag import normalize,token
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
    assert len(manifests)==111 and artifacts==7722
    truths=[truth_table(c['source']) for c in cases];base.write(out/'truth.json',truths)
    states={};by_mode={};audits=[];records=[];alternatives=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);initial_path=tmp/'initial';base.restore_archive(parent['reference_union'],initial_path);s=SnapshotResidualSolver(initial_path)
        try:initial={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in ('cnf_residual_v1',AFFINE,V1,V2,CACHE)}
        finally:s.close()
        assert [len(v) for v in initial.values()]==[28691,26,42,42,34]
        union=dict(initial['cnf_residual_v1']);v2=dict(initial[V2]);v3={}
        for sample in report['samples']:
            data=study.bound(sample);rows=study.bound(data['queries']);path=tmp/(sample['mode']+str(sample['repeat']));base.restore_archive(data['archive'],path)
            assert len(rows)==68;s=SnapshotResidualSolver(path);store=MultiEquivalenceStore(s)
            try:
                native=study.native_rows(s);ext=study.extension_rows(s);available=set();extensions=set()
                for c,r,truth in zip(cases,rows,truths):
                    assert r['case']==c['case'];n=set(r['new_native_ids']);e=set(r['new_extension_ids'])
                    assert not n&available and not e&extensions and len(n)==r['native_nodes'] and len(e)==r['extension_nodes']
                    assert len(n)==len(r['new_native_ids']) and len(e)==len(r['new_extension_ids'])
                    assert r['native_payload']==sum(len(k)+len(native[k]) for k in n)
                    assert r['extension_payload']==sum(len(k)+len(ext[k]) for k in e)
                    for k in n:
                        proof=json.loads(native[k]).get('proof',{})
                        assert {proof[f] for f in ('child','low','high') if f in proof}<=available|n
                    for k in e:
                        node=json.loads(ext[k]);child=(dependency if node['format']==F3 else old_dependency)(s,k,node)[1]
                        assert child in available|n
                    available|=n;extensions|=e
                    assert r['result']['root'] in (available if r['result']['authority']=='native' else extensions)
                    study.check_answer(s,store,c['source'],r['result']);assert r['result']['answer']==truth['answer']
                assert available==set(native) and extensions==set(ext)
                if sample['mode'] in states:assert (native,ext)==states[sample['mode']]
                else:states[sample['mode']]=(native,ext)
                if sample['repeat']==0:
                    by_mode[sample['mode']]=rows
                    if sample['mode']=='cached':records=[dict(source=c['source'],result={k:r['result'][k] for k in ('answer','model','root')},authority=r['result']['authority']) for c,r in zip(cases,rows)]
            finally:s.close()
            audits.append(study.cold(path,cases,rows))
            for key,payload in native.items():
                if key in union and union[key]!=payload:
                    assert json.loads(union[key])['answer']==json.loads(payload)['answer'];alternatives.append(dict(root=key,archive=data['archive']))
                union.setdefault(key,payload)
            for key,payload in ext.items():
                dest=v3 if json.loads(payload)['format']==F3 else v2
                if key in dest:assert dest[key]==payload
                dest.setdefault(key,payload)
        assert v2==initial[V2] and states['all']==states['cached']
        for a,b in zip(by_mode['all'],by_mode['cached']):
            for field in ('new_native_ids','new_extension_ids','native_nodes','native_payload','extension_nodes','extension_payload'):assert a[field]==b[field]
            for field in ('answer','model','root','authority'):assert a['result'][field]==b['result'][field]
            for key,value in a['result']['metrics'].items():
                if key.startswith('binary_') or key in ('expanded_nodes','propagation_literal_visits','multi_applied_blocks','multi_applied_merges','multi_checked_edges'):
                    assert b['result']['metrics'].get(key,0)==value
        # Record both quotient alternatives before each query in each actual stream.
        prefix={m:set() for m in ('single','cached')};opportunities=[];deltas=[]
        for c,a,b in zip(cases,by_mode['single'],by_mode['cached']):
            cnf,_=normalize(c['source']);blocks=discover_all(cnf,Counter())
            if blocks and len(blocks)>1:
                targets=[check_blocks(cnf,choice,Counter())[0] for choice in (blocks[:1],blocks)]
                keys=[token(normalize(t)[0],Counter()) for t in targets]
                assert all(truth_table(t)['answer']==truths[c['case']]['answer'] for t in targets)
                opportunities.append(dict(case=c['case'],group=c['group'],family=c['family'],old_case=c.get('old_case'),blocks=len(blocks),
                    target_keys=keys,known_at_prefix={m:[k in prefix[m] for k in keys] for m in prefix},
                    native_delta=b['native_nodes']-a['native_nodes']))
            for m,r in (('single',a),('cached',b)):prefix[m].update(r['new_native_ids'])
            delta={k:b['result']['metrics'].get(k,0)-a['result']['metrics'].get(k,0) for k in ('expanded_nodes','propagation_literal_visits')}
            delta.update(native_nodes=b['native_nodes']-a['native_nodes'],native_payload=b['native_payload']-a['native_payload'],extension_payload=b['extension_payload']-a['extension_payload'])
            if any(delta.values()):deltas.append(dict(case=c['case'],group=c['group'],family=c['family'],old_case=c.get('old_case'),delta=delta))
        assert len(opportunities)==12
        path=tmp/'union';shutil.copyfile(initial_path,path);s=previous.native.ResidualSolver(path)
        try:
            with s.db:
                s.db.executemany('INSERT OR IGNORE INTO cnf_residual_v1 VALUES (?,?)',union.items())
                s.db.execute(f'CREATE TABLE {V3} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)');s.db.executemany(f'INSERT INTO {V3} VALUES (?,?)',v3.items())
            for t,rows in initial.items():assert rows.items()<=dict(s.db.execute(f'SELECT id,payload FROM {t}')).items()
            _,_,indices,prepared,_=previous.prep.setup(s,base.load(study.prior.prior.prior.PARENT/'protocol.json'))
        finally:s.close()
        used=[(n,study.bound(parent[n])) for n in previous.OLD_FIELDS]
        historical=previous.audit_records(path,previous.inherited(parent),study.bound(parent['conditioned_core_projections']),prepared,used,indices)
        old_records=sum((study.bound(parent[f]) for f in ('binary_equivalence_decisions','compact_equivalence_decisions','binary_core_cache_decisions')),[])
        s=SnapshotResidualSolver(path);store=MultiEquivalenceStore(s);terminal=TerminalStore(s);cache=BinaryCoreCache(s)
        try:
            for root in union:assert s._read(root) is not None
            for root in initial[V1]:assert store.old.legacy.read(root) is not None
            for root in initial[V2]:assert store.old.read(root) is not None
            for root in v3:assert store.read(root)['format']==F3
            for root in initial[AFFINE]:assert terminal.read(root) is not None
            for key,payload in initial[CACHE].items():cache.verify(key,payload)
            for r in old_records+records:study.check_answer(s,store,r['source'],dict(r['result'],authority=r['authority']))
        finally:s.close()
        assert base.sha(initial_path)==parent['reference_union']['database_sha256']
        dest=out/'reference-union';dest.mkdir(exist_ok=True);archive=base.archive(path,dest)
    base.write(out/'decisions.json',records)
    sources=dict(p['source_fingerprints']);sources['experiments/validate_cnf_multiblock_equivalence.py']=base.sha(__file__)
    checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        multiblock_equivalence_study=study.binding(out/'report.json'),multiblock_equivalence_decisions=study.binding(out/'decisions.json'),
        multiblock_equivalence_solver='experiments.cnf_multiblock_equivalence.MultiEquivalenceSolver',multiblock_equivalence_reader='experiments.cnf_multiblock_equivalence.MultiEquivalenceStore')
    base.write(out/'checkpoint.json',checkpoint)
    pairs=[]
    for repeat in range(2):
        rows={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        for mode in ('all','cached'):
            pairs.append(dict(repeat=repeat,mode=mode,**{k:rows[mode][k]-rows['single'][k] for k in ('query_seconds','cold_seconds','complete_worker_seconds')}))
    base.write(out/'attribution.json',dict(pairs=pairs,multiblock_sources=opportunities,query_deltas=deltas,
        solve_seconds={m:[sum(x['result']['seconds'] for x in base.load(out/f'{m}-{r}/queries.json')) for r in range(2)] for m in study.MODES},
        limits=['Same pilot inputs. More reduction is not automatically less acquisition: retain lost reuse and storage regressions.',
            'Prefix alternatives are measured in each actual stream before the source query. Comparing a final archive would leak future answers.',
            'Top-level only; all source clauses and checking costs retained. No unrestricted resource bound.']))
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        preserved_tables={t:len(rows) for t,rows in initial.items()},native_union=len(union),new_native=len(union)-len(initial['cnf_residual_v1']),new_multiblock_records=len(v3),
        query_audits=6*len(cases),truth_tables=len(truths),multiblock_truth_pairs=len(opportunities),old_composed_records=len(previous.inherited(parent)),old_pilot_records=len(old_records),new_records=len(records),
        alternate_native_occurrences=alternatives,audits=audits,historical_cold=historical,equal_acquisitions=68,
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result)
    print(base.encode({k:result[k] for k in ('passed','native_union','new_native','new_multiblock_records','query_audits','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
