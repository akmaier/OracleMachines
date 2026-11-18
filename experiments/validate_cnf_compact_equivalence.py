#!/usr/bin/env python3
"""Validate compact reconstruction, unchanged acquisition and both old authorities."""
from collections import Counter
from pathlib import Path
import copy,json,shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_compact_equivalence as study
from experiments.cnf_binary_equivalence import TABLE as V1,FORMAT as F1,EquivalenceStore
from experiments.cnf_compact_equivalence import TABLE as V2,FORMAT as F2,CompactEquivalenceStore,dependency
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
    assert len(manifests)==109 and artifacts==7642
    truths=[truth_table(c['source']) for c in cases];base.write(out/'truth.json',truths)
    answers=None;states={};records=[];alternatives=[];audits=[];equal=Counter();by_mode={}
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);initial_path=tmp/'initial';base.restore_archive(parent['reference_union'],initial_path);s=SnapshotResidualSolver(initial_path)
        try:
            initial=study.native_rows(s);affine=dict(s.db.execute(f'SELECT id,payload FROM {AFFINE}'))
            oldext=study.extension_rows(s,V1);assert not study.extension_rows(s,V2)
        finally:s.close()
        assert (len(initial),len(affine),len(oldext))==(28691,26,42)
        union=dict(initial);v1=dict(oldext);v2={}
        for sample in report['samples']:
            data=study.bound(sample);rows=study.bound(data['queries']);path=tmp/(sample['mode']+str(sample['repeat']));base.restore_archive(data['archive'],path)
            assert len(rows)==68
            s=SnapshotResidualSolver(path);store=CompactEquivalenceStore(s)
            try:
                final=study.native_rows(s);ext=study.extension_rows(s);available=set();ext_available=set()
                for c,r,truth in zip(cases,rows,truths):
                    assert r['case']==c['case'];n=set(r['new_native_ids']);e=set(r['new_extension_ids'])
                    assert len(n)==len(r['new_native_ids']) and len(e)==len(r['new_extension_ids'])
                    assert not n&available and not e&ext_available
                    assert len(n)==r['native_nodes'] and len(e)==r['extension_nodes']
                    assert r['native_payload']==sum(len(k)+len(final[k]) for k in n)
                    assert r['extension_payload']==sum(len(k)+len(ext[k]) for k in e)
                    for k in n:
                        node=json.loads(final[k]);proof=node.get('proof',{})
                        assert {proof[f] for f in ('child','low','high') if f in proof}<=available|n
                    for k in e:
                        node=json.loads(ext[k]);child=node['child'] if node['format']==F1 else dependency(s,k,node)[1]
                        assert child in available|n
                    available|=n;ext_available|=e;rr=r['result']
                    assert rr['root'] in (ext_available if rr.get('authority') in (F1,F2) else available)
                    study.check_answer(s,store,c['source'],rr);assert rr['answer']==truth['answer']
                assert available==set(final) and ext_available==set(ext)
                got=[r['result']['answer'] for r in rows]
                if answers is None:answers=got
                else:assert answers==got
                if sample['mode'] in states:assert (final,ext)==states[sample['mode']]
                else:states[sample['mode']]=(final,ext)
                if sample['repeat']==0:
                    by_mode[sample['mode']]=rows
                    if sample['mode']=='compact':
                        records=[dict(source=c['source'],result={k:r['result'][k] for k in ('answer','model','root')},authority=r['result'].get('authority','native')) for c,r in zip(cases,rows)]
            finally:s.close()
            audits.append(study.cold(path,cases,rows))
            for k,value in final.items():
                if k in union and union[k]!=value:
                    assert json.loads(union[k])['answer']==json.loads(value)['answer'];alternatives.append(dict(root=k,archive=data['archive']))
                union.setdefault(k,value)
            destination=v2 if sample['mode']=='compact' else v1
            for k,value in ext.items():
                if k in destination:assert destination[k]==value
                destination.setdefault(k,value)
        assert union==initial and v1==oldext
        assert states['quotient'][0]==states['compact'][0]
        assert set(states['quotient'][1])==set(states['compact'][1])
        # Independently compare derived identities with the redundant v1 fields.
        s=SnapshotResidualSolver(tmp/'compact0')
        try:
            for key,payload in states['compact'][1].items():
                before=json.loads(states['quotient'][1][key]);node=json.loads(payload);cnf,child=dependency(s,key,node)
                assert before['cnf']==[list(c) for c in cnf] and before['child']==child and before['evidence']==node['evidence']
                equal['negative_reconstructions']+=1
        finally:s.close()
        for a,b in zip(by_mode['quotient'],by_mode['compact']):
            assert a['new_native_ids']==b['new_native_ids'] and a['new_extension_ids']==b['new_extension_ids']
            assert a['result']['model']==b['result']['model'] and a['result']['root']==b['result']['root']
            # All search/discovery counters match; persistence and canonical-key
            # reconstruction are deliberately allowed to differ and are charged.
            prefixes=('equiv_discovery','equiv_width','equiv_graph','equiv_scc','equiv_tree','equiv_blocks','equiv_variables','binary_')
            for k,v in a['result']['metrics'].items():
                if k.startswith(prefixes) or k in ('expanded_nodes','propagation_literal_visits'):
                    assert b['result']['metrics'].get(k,0)==v,(a['case'],k)
            equal['chronological_acquisitions']+=1
        path=tmp/'union';shutil.copyfile(initial_path,path);s=previous.native.ResidualSolver(path)
        try:
            with s.db:
                s.db.execute(f'CREATE TABLE {V2} (id TEXT PRIMARY KEY,payload TEXT NOT NULL)')
                s.db.executemany(f'INSERT INTO {V2} VALUES (?,?)',v2.items())
            assert study.native_rows(s)==initial and study.extension_rows(s,V1)==oldext
            assert dict(s.db.execute(f'SELECT id,payload FROM {AFFINE}'))==affine
            # The production preparation policy was not changed by the pilot.
            _,_,indices,prepared,_=previous.prep.setup(s,base.load(study.prior.PARENT/'protocol.json'))
        finally:s.close()
        assert base.sha(initial_path)==parent['reference_union']['database_sha256']
        used=[(n,study.bound(parent[n])) for n in previous.OLD_FIELDS]
        historical=previous.audit_records(path,previous.inherited(parent),study.bound(parent['conditioned_core_projections']),prepared,used,indices)
        old_records=study.bound(parent['binary_equivalence_decisions']);s=SnapshotResidualSolver(path);store=CompactEquivalenceStore(s);terminal=TerminalStore(s)
        try:
            for root in initial:assert s._read(root) is not None
            for root in oldext:assert store.legacy.read(root) is not None
            for root in v2:assert store.read(root)['format']==F2
            for root in affine:assert terminal.read(root) is not None
            for r in old_records+records:study.check_answer(s,store,r['source'],dict(r['result'],authority=r['authority']))
            union_check=dict(native=len(s.checked),legacy_equivalences=len(store.legacy.checked),compact_equivalences=len(v2),affine=len(affine),records=len(old_records)+len(records))
        finally:s.close()
        dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest)
    base.write(out/'decisions.json',records)
    sources=dict(p['source_fingerprints']);sources['experiments/validate_cnf_compact_equivalence.py']=base.sha(__file__)
    checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        compact_equivalence_study=study.binding(out/'report.json'),compact_equivalence_decisions=study.binding(out/'decisions.json'),
        compact_equivalence_solver='experiments.cnf_compact_equivalence.CompactBinaryEquivalenceSolver',compact_equivalence_reader='experiments.cnf_compact_equivalence.CompactEquivalenceStore')
    base.write(out/'checkpoint.json',checkpoint)
    pairs=[]
    for repeat in range(2):
        rows={m:base.load(out/f'{m}-{repeat}/report.json')['summary'] for m in study.MODES}
        for control in ('targeted','quotient'):
            pairs.append(dict(repeat=repeat,control=control,**{k:rows['compact'][k]-rows[control][k] for k in ('query_seconds','cold_seconds','complete_worker_seconds')}))
    base.write(out/'attribution.json',dict(pairs=pairs,equal_acquisition=dict(equal),prior_structural_opportunities=study.binding(study.PARENT/'attribution.json'),
        limitations=['Same 68 inputs and empty-archive acquisition policies; no new source coverage or production-prefix claim.',
            'Only negative storage/replay changes. Native children, source outcomes and discovery are checked identical between quotient versions.']))
    result=dict(passed=True,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,source_fingerprints=sources,
        native_preserved=len(initial),native_union=len(union),affine_preserved=len(affine),equivalence_v1_preserved=len(oldext),equivalence_v2_union=len(v2),
        query_audits=6*len(cases),truth_tables=len(truths),old_composed_records=len(previous.inherited(parent)),old_pilot_records=len(old_records),new_records=len(records),
        alternate_native_occurrences=alternatives,audits=audits,historical_cold=historical,union_check=union_check,equal_acquisition=dict(equal),
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result)
    print(base.encode({k:result[k] for k in ('passed','native_union','equivalence_v2_union','query_audits','truth_tables','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
