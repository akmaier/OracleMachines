#!/usr/bin/env python3
"""Audit known-quotient choices against actual query prefixes and old history."""
from collections import Counter
from pathlib import Path
import copy,json,shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_known_quotient as study
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


def validate(out):
    began=time.perf_counter();p=base.load(out/'protocol.json');parent=study.bound(p['parent']);cases=study.bound(p['cases']);report=base.load(out/'report.json')
    assert cases[:68]==study.bound(p['workload_origin']) and len(cases)==104
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    oldv=base.load(study.PARENT/'validation.json');manifests=dict(oldv['parent_manifests']);path=study.PARENT/'manifest.json'
    manifests[str(path)]=dict(sha256=base.sha(path),artifacts_checked=len(base.load(path)['artifacts']))
    artifacts=0
    for path,entry in manifests.items():
        assert base.sha(path)==entry['sha256'];m=base.load(path)['artifacts'];assert len(m)==entry['artifacts_checked']
        for f,h in m.items():assert base.sha(f)==h,f
        artifacts+=len(m)
    assert len(manifests)==112 and artifacts==7761
    truths=[truth_table(c['source']) for c in cases];base.write(out/'truth.json',truths)
    states={};by_mode={};audits=[];records=[];alternatives=[];choices=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);initial_path=tmp/'initial';base.restore_archive(parent['reference_union'],initial_path);s=SnapshotResidualSolver(initial_path)
        try:initial={t:dict(s.db.execute(f'SELECT id,payload FROM {t}')) for t in ('cnf_residual_v1',AFFINE,V1,V2,V3,CACHE)}
        finally:s.close()
        assert [len(v) for v in initial.values()]==[28736,26,42,42,11,34]
        old_keys=set().union(*(set(initial[t]) for t in ('cnf_residual_v1',V1,V2,V3)))
        for c in cases[68:]:assert c['root'] not in old_keys and not c['known_in_parent']
        assert len({c['root'] for c in cases})==len(cases)
        union=dict(initial['cnf_residual_v1']);v2=dict(initial[V2]);v3=dict(initial[V3])
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
                        assert sample['mode']=='known';cnf,_=normalize(c['source']);blocks=discover_all(cnf,Counter());assert len(blocks)>1
                        targets=[check_blocks(cnf,b,Counter())[0] for b in (blocks,blocks[:1])]
                        keys=[token(normalize(t)[0],Counter()) for t in targets];full_known=keys[0] in available
                        expected=[dict(kind='all',key=keys[0],known=full_known)]
                        if not full_known:expected.append(dict(kind='first',key=keys[1],known=keys[1] in available))
                        assert trace['candidates']==expected
                        selected='first' if not full_known and keys[1] in available else 'all'
                        assert trace['selected']==selected
                        hit=full_known or keys[1] in available
                        if hit:
                            selected_key=keys[1 if selected=='first' else 0];node=s._read(selected_key)
                            assert node is not None and node['answer']==rr['answer']
                            assert n<=({rr['root']} if rr['answer'] else set())
                            assert not rr['metrics'].get('expanded_nodes',0)
                        if sample['repeat']==0:choices.append(dict(case=c['case'],group=c['group'],family=c['family'],answer=rr['answer'],trace=trace,known_hit=hit,new_native=len(n)))
                    for k in n:
                        proof=json.loads(native[k]).get('proof',{})
                        assert {proof[f] for f in ('child','low','high') if f in proof}<=available|n
                    for k in e:
                        node=json.loads(ext[k]);child=(dependency if node['format']==F3 else old_dependency)(s,k,node)[1]
                        assert child in available|n
                    available|=n;extensions|=e
                    assert rr['root'] in (available if rr['authority']=='native' else extensions)
                    study.check_answer(s,store,c['source'],rr);assert rr['answer']==truth['answer']
                assert available==set(native) and extensions==set(ext)
                if sample['mode'] in states:assert (native,ext)==states[sample['mode']]
                else:states[sample['mode']]=(native,ext)
                if sample['repeat']==0:
                    by_mode[sample['mode']]=rows
                    if sample['mode']=='known':records=[dict(source=c['source'],result={k:r['result'][k] for k in ('answer','model','root')},authority=r['result']['authority']) for c,r in zip(cases,rows)]
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
        assert len(choices)==24 and sum(c['known_hit'] for c in choices)==14
        assert [c['case'] for c in choices if c['trace']['selected']=='first']==[7,34,94,103]
        # The first 68 queries reproduce both original comparator acquisitions.
        for mode,prior_mode in (('single','single'),('all','cached')):
            old=base.load(study.PARENT/f'{prior_mode}-0/queries.json')
            for a,b in zip(old,by_mode[mode][:68]):
                for f in ('new_native_ids','new_extension_ids','native_payload','extension_payload'):assert a[f]==b[f]
        path=tmp/'union';shutil.copyfile(initial_path,path);s=previous.native.ResidualSolver(path)
        try:
            with s.db:
                s.db.executemany('INSERT OR IGNORE INTO cnf_residual_v1 VALUES (?,?)',union.items())
                for table,entries in ((V2,v2),(V3,v3)):s.db.executemany(f'INSERT OR IGNORE INTO {table} VALUES (?,?)',entries.items())
            for t,rows in initial.items():assert rows.items()<=dict(s.db.execute(f'SELECT id,payload FROM {t}')).items()
            _,_,indices,prepared,_=previous.prep.setup(s,base.load(study.prior.prior.prior.prior.PARENT/'protocol.json'))
        finally:s.close()
        used=[(n,study.bound(parent[n])) for n in previous.OLD_FIELDS]
        historical=previous.audit_records(path,previous.inherited(parent),study.bound(parent['conditioned_core_projections']),prepared,used,indices)
        old_records=sum((study.bound(parent[f]) for f in ('binary_equivalence_decisions','compact_equivalence_decisions','binary_core_cache_decisions','multiblock_equivalence_decisions')),[])
        s=SnapshotResidualSolver(path);store=MultiEquivalenceStore(s);terminal=TerminalStore(s);cache=BinaryCoreCache(s)
        try:
            for root in union:assert s._read(root) is not None
            for root in initial[V1]:assert store.old.legacy.read(root) is not None
            for root in v2:assert store.old.read(root) is not None
            for root in v3:assert store.read(root)['format']==F3
            for root in initial[AFFINE]:assert terminal.read(root) is not None
            for key,payload in initial[CACHE].items():cache.verify(key,payload)
            for r in old_records+records:study.check_answer(s,store,r['source'],dict(r['result'],authority=r['authority']))
        finally:s.close()
        assert base.sha(initial_path)==parent['reference_union']['database_sha256']
        dest=out/'reference-union';dest.mkdir(exist_ok=True);archive=base.archive(path,dest)
    base.write(out/'decisions.json',records)
    sources=dict(p['source_fingerprints']);sources['experiments/validate_cnf_known_quotient.py']=base.sha(__file__)
    checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        known_quotient_study=study.binding(out/'report.json'),known_quotient_decisions=study.binding(out/'decisions.json'),
        known_quotient_solver='experiments.cnf_known_quotient.KnownQuotientSolver')
    base.write(out/'checkpoint.json',checkpoint)
    pairs=[]
    for repeat in range(2):
        rows={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        for control in ('single','all'):
            pairs.append(dict(repeat=repeat,control=control,**{k:rows['known'][k]-rows[control][k] for k in ('query_seconds','cold_seconds','complete_worker_seconds')}))
    segments={}
    for mode,rows in by_mode.items():
        segments[mode]={}
        for name,lo,hi in (('pilot',0,68),('fresh',68,104)):
            entries=rows[lo:hi];counts=Counter()
            for r in entries:counts.update(r['result']['metrics'])
            segments[mode][name]=dict(queries=len(entries),positive=sum(r['result']['answer'] for r in entries),counters=dict(counts),
                **{k:sum(r[k] for r in entries) for k in ('native_nodes','native_payload','extension_nodes','extension_payload')})
    costly=sorted([dict(case=c['case'],family=c['family'],group=c['group'],propagation=r['result']['metrics'].get('propagation_literal_visits',0),expansions=r['result']['metrics'].get('expanded_nodes',0)) for c,r in zip(cases,by_mode['known'])],key=lambda x:-x['propagation'])
    base.write(out/'attribution.json',dict(pairs=pairs,choices=choices,segments=segments,costliest_queries=costly,
        solve_seconds={m:[sum(x['result']['seconds'] for x in base.load(out/f'{m}-{r}/queries.json')) for r in range(2)] for m in study.MODES},
        limits=['At most two native targets; no global minimum over block subsets or cold proof costs.',
            'All chosen hits are checked against native records available before their actual source query.',
            'The 36 new sources are excluded against parent roots; twelve are designed quotient-preserving edits, not an independent representative sample.']))
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        preserved_tables={t:len(rows) for t,rows in initial.items()},native_union=len(union),new_native=len(union)-len(initial['cnf_residual_v1']),v2_union=len(v2),v3_union=len(v3),
        query_audits=6*len(cases),truth_tables=len(truths),fresh_exclusions=36,choice_audits=48,known_hit_audits=28,old_composed_records=len(previous.inherited(parent)),old_pilot_records=len(old_records),new_records=len(records),
        alternate_native_occurrences=alternatives,audits=audits,historical_cold=historical,
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result)
    print(base.encode({k:result[k] for k in ('passed','native_union','new_native','v2_union','v3_union','query_audits','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
