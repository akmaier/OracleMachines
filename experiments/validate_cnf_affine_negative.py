#!/usr/bin/env python3
"""Independent evidence reconstruction and preservation for affine refutations."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import json
import sys
import tempfile
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_negative as study
from experiments.cnf_affine_negative import NegativeStore, compile_proof, TABLE, CHAIN, check_composed
from experiments.validate_cnf_affine_completion import expected, inspect_bridge
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.cnf_snapshot_replay import audit
base=study.base;bound=study.bound


def audit_counts(e,counts):
    a=e['affine'];expected=dict(affine_verified_certificates=1,affine_negative_nodes_checked=1,
        affine_verification_literals=sum(len(eq['variables'])*len(eq['clauses']) for eq in a['equations']),
        affine_verification_xors=sum(len(r['using']) for r in a['reductions']))
    if e['status']=='linear-conflict':expected['affine_negative_conflicts_checked']=1
    else:
        d=e['free'];n=1<<d
        expected.update(affine_space_vectors_checked=d+1,
            affine_space_particular_equation_checks=len(a['equations']),
            affine_space_kernel_equation_checks=len(a['equations'])*d,
            affine_negative_direct_xors=d*(n//2),affine_negative_rejections_checked=n,
            affine_negative_spaces_checked=1)
    for k,v in expected.items():assert counts.get(k,0)==v,(k,counts.get(k),v)


def validate(out):
    began=time.perf_counter();report=base.load(out/'report.json');p=bound(report['protocol']);parent=bound(p['parent'])
    sources=dict(p['sources']);verification_revision=None
    for name,h in p['sources'].items():
        if name==__file__ or name=='experiments/validate_cnf_affine_negative.py':
            if base.sha(name)!=h:
                saved=out/'validation-v0.py.txt'
                assert base.sha(saved)==h
                verification_revision=dict(initial=study.binding(saved),current=study.binding(name),
                    reason='Posthoc validator preserves separately checked alternative native witnesses and compares guarded targets in JSON list form; runtime sources unchanged.')
                sources[name]=base.sha(name)
        else:assert base.sha(name)==h,name
    pv=bound(p['parent_validation']);manifests=dict(pv['parent_manifests'])
    mf=study.PARENT/'manifest.json';manifests[str(mf)]=dict(sha256=base.sha(mf),artifacts_checked=len(base.load(mf)['artifacts']))
    artifacts=0
    for name,entry in manifests.items():
        assert base.sha(name)==entry['sha256'],name
        old=base.load(name);assert len(old['artifacts'])==entry['artifacts_checked']
        for name,h in old['artifacts'].items():assert base.sha(name)==h,name
        artifacts+=len(old['artifacts'])
    assert len(manifests)==102 and artifacts==7171
    extension={};records=[];summary=[];counter_audits=0;alternatives=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);cases=study.contexts(tmp);catalog={(c['cohort'],c['case']):c for c in cases}
        path=tmp/'union';base.restore_archive(parent['reference_union'],path);s=study.prior.native.ResidualSolver(path)
        try:initial=study.rows(s)
        finally:s.close()
        assert len(initial)==26743
        expected_order=[(c['cohort'],c['case'],i,m) for c in cases for i,order in enumerate(p['orders']) for m in order]
        assert len(report['samples'])==len(expected_order)==52
        for entry,order in zip(report['samples'],expected_order):
            row=bound(entry);assert (row['cohort'],row['case'],row['repeat'],row['mode'])==order
            c=catalog[order[:2]];prefix=c['before'];delta=bound(row['native_delta']);ext=bound(row['extension_delta'])
            assert row['prefix_nodes']==len(prefix) and row['prefix_digest']==base.key_sha(base.encode(sorted(prefix.items())))
            assert row['record']==bound(row['records'])[0] and row['record']['source']==c['source']
            s=study.prior.native.ResidualSolver()
            try:
                with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',prefix.items())
                store=NegativeStore(s,create=True)
                target=c['source']
                for guard in c['guards']:_,target=check_guard(s,target,guard)
                assert [list(c) for c in target]==row['input_target'] and c['guards']==row['input_guards']
                available=set(map(base.key_sha,prefix))
                with patch.object(s,'_expand',side_effect=AssertionError('Audit search')),patch.object(s,'_store',side_effect=AssertionError('Audit native publication')):
                    choice,trace=expected(s,target,4,available,row['admission'])
                    assert choice==row['local_choice'] and trace==row['admission']
                    e=trace.get('affine_bridge')
                    wants=row['mode']=='negative' and e is not None and e['status'] in ('linear-conflict','space-exhausted')
                    assert row['extension']==wants
                    for key,payload in delta:
                        assert key not in prefix and key in initial
                        if initial[key]!=payload:
                            alternatives.append(dict(arm=entry,root_sha256=base.key_sha(key),
                                retained_sha256=base.key_sha(initial[key]),alternative_sha256=base.key_sha(payload)))
                    with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',delta)
                    for key,payload in ext.items():
                        assert wants and key==row['child']['root'] and json.loads(payload)['proof']==compile_proof(e)
                        if key in extension:assert extension[key]==payload
                        extension[key]=payload
                    with s.db:s.db.executemany(f'INSERT INTO {TABLE} VALUES (?,?)',ext.items())
                    if wants:
                        assert not delta and len(ext)==1 and row['record']['format']==CHAIN
                        cnf,_,_=s._canonical(target);_,detail=inspect_bridge(s,target,e);assert detail==e
                        # Directly test every retained rejecting source clause too.
                        if e['status']=='space-exhausted':
                            for i,cid in enumerate(e['rejected']):
                                mask=e['space']['particular'];gray=i^(i>>1)
                                for j,v in enumerate(e['space']['directions']):
                                    if gray>>j&1:mask^=v
                                assert all(bool(mask&(1<<(abs(l)-1)))!=(l>0) for l in cnf[cid])
                            assert row['child']['metrics']['affine_negative_packed_literals']==sum(len(cnf[i]) for i in set(e['rejected']))
                        audit_counts(e,row['child']['metrics']);counter_audits+=1
                        check_composed(store,row['record'])
                        assert row['child']['metrics'].get('expanded_nodes',0)==0
                        assert row['child']['metrics']['affine_negative_inserted_nodes']==1
                        if row['repeat']==0:records.append(row['record'])
                    else:
                        assert not ext;study.check_native(s,row['record'])
                    assert row['record']['answer']==c['expected_answer']
            finally:s.close()
            assert row['new_native_nodes']==len(delta) and row['new_native_bytes']==sum(len(k)+len(v) for k,v in delta)
            assert row['new_extension_nodes']==len(ext) and row['new_extension_bytes']==sum(len(k)+len(v) for k,v in ext.items())
            summary.append(dict(cohort=row['cohort'],case=row['case'],repeat=row['repeat'],mode=row['mode'],extension=row['extension'],
                native_nodes=row['new_native_nodes'],native_bytes=row['new_native_bytes'],
                extension_nodes=row['new_extension_nodes'],extension_bytes=row['new_extension_bytes'],
                propagation=row['child']['metrics'].get('propagation_literal_visits',0),
                selection_seconds=row['selection_seconds'],child_seconds=row['child_seconds'],query_seconds=row['evaluation_seconds'],
                cold_seconds=row['cold_seconds'],complete_seconds=row['complete_arm_seconds'],sidecar_bytes=row['retained_bytes'],database_bytes=row['database_bytes']))
        assert len(extension)==len(records)==7 and counter_audits==14
        s=study.prior.native.ResidualSolver(path)
        try:
            store=NegativeStore(s,create=True)
            for key,payload in extension.items():store.verify(key,json.loads(payload))
            with s.db:s.db.executemany(f'INSERT INTO {TABLE} VALUES (?,?)',extension.items())
            assert study.rows(s)==initial
        finally:s.close()
        full=audit(path,[]);assert full['checked_nodes']==26743
        before=base.sha(path);s=study.SnapshotResidualSolver(path);store=NegativeStore(s)
        tick=time.perf_counter()
        try:
            for key in extension:assert store.read(key) is not None
            for r in records:check_composed(store,r)
            negative_cold=dict(seconds=time.perf_counter()-tick,metrics=dict(s.counts),records=len(records))
            assert study.rows(s)==initial and study.extension_rows(s)==extension
        finally:s.close()
        assert base.sha(path)==before
        dest=out/'extended-union';dest.mkdir();archive=base.archive(path,dest)
    base.write(out/'negative-decisions.json',records)
    checkpoint=dict(format='affine-negative-checkpoint-v1',native_parent=p['parent'],native_reference_union=parent['reference_union'],
        extended_archive=archive,negative_decisions=study.binding(out/'negative-decisions.json'),
        reader='experiments.cnf_affine_negative.NegativeStore',native_table_unchanged=True)
    base.write(out/'checkpoint.json',checkpoint)
    groups={}
    for mode in ('affine','negative'):
        rs=[r for r in summary if r['mode']==mode]
        groups[mode]={k:sum(r[k] for r in rs)/2 for k in ('native_nodes','native_bytes','extension_nodes','extension_bytes','propagation',
            'selection_seconds','child_seconds','query_seconds','cold_seconds','complete_seconds','sidecar_bytes')}
    pairs=[]
    for repeat in range(2):
        a=[r for r in summary if r['mode']=='affine' and r['repeat']==repeat]
        b=[r for r in summary if r['mode']=='negative' and r['repeat']==repeat]
        pairs.append(dict(repeat=repeat,**{k:sum(r[k] for r in b)-sum(r[k] for r in a) for k in ('query_seconds','cold_seconds','complete_seconds')}))
    validation=dict(passed=True,source_fingerprints=sources,verification_revision=verification_revision,alternative_native_occurrences=alternatives,parent_manifests=manifests,prior_artifacts_checked=artifacts,
        native_preserved=26743,negative_certificates=7,records=records,arms=52,counter_audits=counter_audits,
        full_native_replay=full,negative_cold=negative_cold,groups=groups,pairs=pairs,summary=summary,
        report=study.binding(out/'report.json'),checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',validation)
    print(base.encode(dict(groups=groups,pairs=pairs,negative_certificates=7,passed=True)),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
