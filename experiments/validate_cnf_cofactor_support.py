#!/usr/bin/env python3
"""Check cofactor provenance, antichain coverage, answers and preserved unions."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_cofactor_support as study
from experiments.validate_cnf_unsat_support import bound,check_cores
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
from experiments.validate_cnf_snapshot_replay import semantic
from experiments.cnf_snapshot_replay import FROZEN_AUDIT
from experiments.cnf_accounted_residuals import CENSUS,TABLE
from experiments.cnf_clause_deletion_guard import check_guard,lift,clause_set
base=study.base


def check_bank(solver,prepared,catalogs):
    if prepared is None:return
    allcores=prepared['all_cores'];indices=prepared['retained_indices'];members=[clause_set(c['source'],Counter()) for c in allcores]
    assert prepared['cores']==[allcores[i] for i in indices] and len(set(indices))==len(indices)
    assert len({tuple(sorted(m)) for m in members})==len(members)
    assert [d['core'] for d in prepared['dominance']]==list(range(len(members)))
    for d in prepared['dominance']:assert d['retained'] in indices and members[d['retained']]<=members[d['core']]
    for i in indices:
        for j in indices:
            if i!=j:assert not members[i]<=members[j]
    expected=[(name,row['case']) for name,records in catalogs for row in records if row['answer'] is False and row['guard'] is not None]
    assert [(o['catalog'],o['case']) for o in prepared['origins']]==expected
    lookup={(name,row['case']):row for name,records in catalogs for row in records};first={}
    for origin in prepared['origins']:
        row=lookup[(origin['catalog'],origin['case'])];_,target=check_guard(solver,row['source'],row['guard'])
        assert solver._canonical(row['source'])[2]==origin['query_root']==row['query_root']
        cnf,_,key=solver._canonical(target);assert key==origin['child_root']==row['child']['root']
        assert solver._read(key,cnf)['answer'] is False
        core=allcores[origin['core']];assert members[origin['core']]<=clause_set(target,Counter())
        small,_,root=solver._canonical(core['source']);assert root==core['root'] and solver._read(root,small)['answer'] is False
        first.setdefault(origin['core'],key)
    assert len(first)==len(allcores)
    for i,key in first.items():assert allcores[i]['origin']==key


def validate(out):
    tick=time.perf_counter();report=base.load(out/'report.json');protocol=bound(report['protocol']);catalog=bound(report['cases']);parent=bound(protocol['parent'])
    for f,h in protocol['source_fingerprints'].items():assert base.sha(f)==h,f
    oldcores=bound(protocol['cores']);bank=bound(protocol['bank_catalog']);bound(protocol['template_catalog'])
    assert protocol['prior_decision_catalogs']==[parent[f] for f in study.FIELDS]
    catalogs=[(name,bound(entry)) for name,entry in zip(study.FIELDS,protocol['prior_decision_catalogs'])]
    inherited_sidecars=sum((r for _,r in catalogs),[]);assert inherited_sidecars==bound(protocol['previous_decisions']) and len(inherited_sidecars)==576
    assert [(s['repeat'],s['mode']) for s in report['samples']]==[(r,m) for r,order in enumerate(protocol['orders']) for m in order]
    audits=[];by_mode={};baseline_records=None;alternates=0
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);_,structural=restore_checkpoint(protocol['parent']['path'],tmp/'patterns')
        base.restore_archive(parent['reference_union'],tmp/'parent');solver=study.ResidualSolver(tmp/'parent')
        try:initial=study.rows(solver);assert study.previous.inputs(solver,protocol)==catalog
        finally:solver.close()
        union=dict(initial)
        for sample in report['samples']:
            data=bound(sample);records=bound(data['queries']);prepared=bound(data['cofactor_bank']);mode=sample['mode'];path=tmp/f"{mode}-{sample['repeat']}"
            assert data['summary']['mode']==mode and (prepared is None)==(mode=='current')
            base.restore_archive(data['archive'],path);cold=FROZEN_AUDIT(path,records)
            assert semantic(cold)==semantic({k:v for k,v in data['cold'].items() if k!='snapshot'})
            assert len(records)==len(catalog['cases'])*protocol['visits']
            solver=study.ResidualSolver(path)
            try:
                solver.db.execute('PRAGMA query_only=ON');saved=study.rows(solver);assert initial.items()<=saved.items()
                assert base.key_sha(base.encode(sorted(saved.items())))==data['summary']['row_digest']
                if mode not in by_mode:by_mode[mode]=(saved,semantic(records),prepared,data['archive']['database_sha256'])
                else:assert by_mode[mode]==(saved,semantic(records),prepared,data['archive']['database_sha256'])
                if baseline_records is None:baseline_records=records
                assert [r['answer'] for r in records]==[r['answer'] for r in baseline_records]
                totals=solver.db.execute(CENSUS).fetchone();accounting=data['accounting']
                assert totals==(accounting['final_nodes'],accounting['final_payload_units']) and accounting['censuses']==1
                assert solver.db.execute(f'SELECT nodes,payload_units,dirty FROM {TABLE}').fetchone()==(*totals,0)
                assert data['cold']['snapshot']==dict(censuses=1,metadata_reads=len(records),nodes=totals[0],payload_units=totals[1],complete_frozen_audit=True)
                inserted=list(data['setup_ids']);assert len(inserted)==data['summary']['preparation_nodes']
                with patch.object(solver,'_expand',side_effect=AssertionError('Fresh validation search')):
                    check_cores(solver,oldcores,bank['support_sources']);check_bank(solver,prepared,catalogs)
                    for index,row in enumerate(records):
                        case=catalog['cases'][index%len(catalog['cases'])]
                        assert row['case']==case['case'] and row['source']==case['source'] and row['visit']==index//len(catalog['cases'])
                        if row['guard']:
                            fixed,target=check_guard(solver,row['source'],row['guard'])
                            assert {int(k):v for k,v in row['assignment'].items()}==fixed and [list(c) for c in target]==row['target']
                        else:assert row['target']==row['source'] and not row['assignment']
                        if row['core']:
                            c=oldcores[row['core']['core']];assert clause_set(c['source'],Counter())<=clause_set(row['source'],Counter())
                            assert row['child']['root']==row['core']['root']==case['root'] and row['answer'] is False
                        if row['cofactor']:
                            assert prepared is not None and row['guard'] is not None and row['core'] is None and row['witness'] is None and row['target_known'] is False
                            c=prepared['cores'][row['cofactor']['core']];assert clause_set(c['source'],Counter())<=clause_set(row['target'],Counter())
                            assert row['cofactor']['root']==row['child']['root']==solver._canonical(row['target'])[2]
                            assert row['answer'] is False and row['child']['metrics'].get('expanded_nodes',0)==0
                        assert row['new_nodes']==len(set(row['new_ids']));inserted.extend(row['new_ids'])
                new=set(saved)-set(initial);assert len(inserted)==len(set(inserted)) and set(inserted)==set(map(base.key_sha,new))
                assert len(new)==data['summary']['new_nodes']==accounting['cursor']['delta_rows']
                assert accounting['cursor']['delta_reads']==len(records)+1 and accounting['full_row_snapshots']==3
                units=sum(solver.db.execute('SELECT length(id)+length(payload) FROM cnf_residual_v1 WHERE id=?',(k,)).fetchone()[0] for k in new)
                assert accounting['cursor']['delta_payload_units']==units
                if sample['repeat']==0:
                    for key,payload in saved.items():
                        if key in union and union[key]!=payload:alternates+=1
                        union.setdefault(key,payload)
            finally:solver.close();assert base.sha(path)==data['archive']['database_sha256']
            audits.append(dict(mode=mode,repeat=sample['repeat'],**cold))
        path=tmp/'union';base.restore_archive(parent['reference_union'],path);solver=study.ResidualSolver(path)
        try:
            with solver.db:solver.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,union[k]) for k in sorted(set(union)-set(initial))])
        finally:solver.close()
        dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest);solver=study.ResidualSolver(path);decisions=[]
        try:
            solver.db.execute('PRAGMA query_only=ON')
            with patch.object(solver,'_expand',side_effect=AssertionError('Fresh union search')):
                for key in union:assert solver._read(key) is not None
                original=base.load('experiments/results/cnf-join-transfer/cases.json');inherited=bound(parent['reference_decisions'])+bound(parent['model_rotation_decisions'])
                for d in inherited:
                    source=d['source'] if 'source' in d else original[d['case']]['source'];r=solver.solve(source)
                    assert r['root']==d['root'] and r['answer']==d['answer'] and r['model']==(None if d['model'] is None else {int(k):v for k,v in d['model'].items()})
                for case in catalog['cases']:
                    row=baseline_records[case['case']];cnf,_,key=solver._canonical(case['source']);known=solver._read(key,cnf);guard=None if known is not None else row['guard']
                    if guard is None:fixed={};target=case['source']
                    else:fixed,target=check_guard(solver,case['source'],guard)
                    child=solver.solve(target);assert child['answer']==row['answer'];model=lift(case['source'],fixed,child['model']) if child['answer'] else None
                    decisions.append(dict(case=case['case'],source=case['source'],query_root=key,guard=guard,witness=None,child=child,answer=child['answer'],model=model))
                check_bank(solver,by_mode['cofactor'][2],catalogs)
        finally:solver.close();assert base.sha(path)==archive['database_sha256']
        inherited_check=FROZEN_AUDIT(path,inherited_sidecars);union_check=FROZEN_AUDIT(path,decisions);base.write(out/'union-decisions.json',decisions)
        checkpoint=copy.deepcopy(parent);checkpoint['source_fingerprints']=protocol['source_fingerprints'];checkpoint['parent_checkpoint']=protocol['parent']
        checkpoint['cofactor_support_study']=study.binding(out/'report.json');checkpoint['cofactor_support_decisions']=study.binding(out/'union-decisions.json')
        checkpoint['cofactor_support_bank']=study.binding(out/'cofactor-0/cofactor-bank.json');checkpoint['reference_union']=archive
        base.write(out/'checkpoint.json',checkpoint);_,current=restore_checkpoint(out/'checkpoint.json',tmp/'current');assert current==structural;supplement=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),archives=audits,parent_check=structural,
        supplemental_check=supplement,union_check=union_check,inherited_guarded_check=inherited_check,inherited_decisions_checked=len(inherited)+len(inherited_sidecars),
        identical_repetitions_within_mode=True,matched_answers=True,alternate_certificate_occurrences=alternates,
        old_reference_union_nodes=len(initial),reference_union_nodes=len(union),new_reference_keys=len(union)-len(initial),reference_archive=archive,
        direct_query_decisions=sum(r['guard'] is None for r in decisions),structural_authority_unchanged=True,seconds=time.perf_counter()-tick,validator_sha256=base.sha(__file__))
    base.write(out/'reconstruction.json',result);print(base.encode({k:result[k] for k in ('passed','reference_union_nodes','new_reference_keys','direct_query_decisions','alternate_certificate_occurrences','seconds')}))


if __name__=='__main__':validate(Path(sys.argv[1]))
