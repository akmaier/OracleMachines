#!/usr/bin/env python3
"""Prove matched logical archives and decisions while auditing both accounting paths."""
from pathlib import Path
import copy,sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_incremental_archive as study
from experiments.validate_cnf_unsat_support import bound,check_cores
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
from experiments.cnf_accounted_residuals import TABLE,CENSUS,TRIGGERS
from experiments.cnf_clause_deletion_guard import check_guard,lift,clause_set
from collections import Counter
base=study.base


def semantic(value):
    if isinstance(value,dict):return {k:semantic(v) for k,v in value.items() if k not in ('seconds','accounting_reads','accounting_reconstructions')}
    if isinstance(value,list):return [semantic(v) for v in value]
    return value


def validate(out):
    start=time.perf_counter();report=base.load(out/'report.json');protocol=bound(report['protocol']);catalog=bound(report['cases']);parent=bound(protocol['parent'])
    for f,h in protocol['source_fingerprints'].items():assert base.sha(f)==h,f
    cores=bound(protocol['cores']);bank_catalog=bound(protocol['bank_catalog']);bound(protocol['template_catalog']);assert protocol['previous_decisions']==parent['unsat_support_decisions']
    comparisons={};audits=[];archives={};baseline=None;baseline_records=None
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);_,structural=restore_checkpoint(protocol['parent']['path'],tmp/'patterns')
        base.restore_archive(parent['reference_union'],tmp/'parent');solver=study.ResidualSolver(tmp/'parent')
        try:initial=study.rows(solver);assert study.inputs(solver,protocol)==catalog
        finally:solver.close()
        for sample in report['samples']:
            data=bound(sample);records=bound(data['queries']);mode=sample['mode'];repeat=sample['repeat'];path=tmp/f'{mode}-{repeat}'
            assert data['cores']==protocol['cores'];base.restore_archive(data['archive'],path)
            cold=study.prior.old.previous.audit(path,records);assert semantic(cold)==semantic(data['cold'])
            assert len(records)==len(catalog['cases'])*protocol['visits']
            solver=study.ResidualSolver(path)
            try:
                solver.db.execute('PRAGMA query_only=ON');saved=study.rows(solver);assert initial.items()<=saved.items()
                assert base.key_sha(base.encode(sorted(saved.items())))==data['summary']['row_digest']
                if baseline is None:baseline=dict(saved);baseline_records=records;baseline_archive=data['archive']
                else:assert saved==baseline
                totals=solver.db.execute(CENSUS).fetchone();assert totals==(data['accounting']['final_nodes'],data['accounting']['final_payload_units'])
                metadata=solver.db.execute('SELECT 1 FROM sqlite_master WHERE name=?',(TABLE,)).fetchone()
                if mode=='scanned':assert metadata is None and data['accounting']['censuses'] is None
                else:
                    assert metadata is not None and data['accounting']['censuses']==1
                    assert solver.db.execute(f'SELECT nodes,payload_units,dirty FROM {TABLE} WHERE singleton=1').fetchone()==(*totals,0)
                    for suffix,body in TRIGGERS.items():
                        name=TABLE+'_'+suffix
                        assert solver.db.execute("SELECT sql FROM sqlite_master WHERE type='trigger' AND name=?",(name,)).fetchone()==(f'CREATE TRIGGER {name} {body}',)
                inserted=[]
                with patch.object(solver,'_expand',side_effect=AssertionError('Fresh validation search')):
                    check_cores(solver,cores,bank_catalog['support_sources'])
                    for index,row in enumerate(records):
                        case=catalog['cases'][index%len(catalog['cases'])]
                        assert row['case']==case['case'] and row['source']==case['source'] and row['visit']==index//len(catalog['cases'])
                        if row['core']:
                            core=cores[row['core']['core']];assert clause_set(core['source'],Counter())<=clause_set(row['source'],Counter())
                            assert row['answer'] is False and row['guard'] is None and row['witness'] is None
                            assert row['child']['root']==row['core']['root']==case['root']
                            assert row['child']['metrics'].get('expanded_nodes',0)==0
                        if row['guard']:
                            fixed,target=check_guard(solver,row['source'],row['guard'])
                            assert {int(k):v for k,v in row['assignment'].items()}==fixed and [list(c) for c in target]==row['target']
                        else:assert row['target']==row['source'] and not row['assignment']
                        assert row['child']['metrics'].get('expanded_nodes',0)<=protocol['node_limit']
                        assert row['new_nodes']==len(set(row['new_ids']));inserted.extend(row['new_ids'])
                new=set(saved)-set(initial)
                assert len(inserted)==len(set(inserted)) and set(inserted)==set(map(base.key_sha,new))
                assert len(new)==data['summary']['new_nodes']
                if mode=='delta':
                    assert data['accounting']['cursor']['delta_reads']==len(records)+1
                    assert data['accounting']['cursor']['delta_rows']==len(new)
                    units=sum(solver.db.execute('SELECT length(id)+length(payload) FROM cnf_residual_v1 WHERE id=?',(k,)).fetchone()[0] for k in new)
                    assert data['accounting']['cursor']['delta_payload_units']==units
                    assert data['accounting']['full_row_snapshots']==3
                else:assert data['accounting']['full_row_snapshots']==4+2*len(records)
            finally:solver.close();assert base.sha(path)==data['archive']['database_sha256']
            comparisons[(mode,repeat)]=semantic(records);archives[(mode,repeat)]=data['archive']['database_sha256'];audits.append(dict(mode=mode,repeat=repeat,accounting=data['accounting'],**cold))
        assert all(value==semantic(baseline_records) for value in comparisons.values())
        path=tmp/'union';base.restore_archive(baseline_archive,path);dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest)
        base.restore_archive(archive,tmp/'cold-union');solver=study.ResidualSolver(tmp/'cold-union');decisions=[]
        try:
            solver.db.execute('PRAGMA query_only=ON')
            with patch.object(solver,'_expand',side_effect=AssertionError('Fresh union search')):
                for key in baseline:assert solver._read(key) is not None
                original=base.load('experiments/results/cnf-join-transfer/cases.json')
                inherited=bound(parent['reference_decisions'])+bound(parent['model_rotation_decisions'])
                for d in inherited:
                    source=d['source'] if 'source' in d else original[d['case']]['source'];r=solver.solve(source)
                    assert r['root']==d['root'] and r['answer']==d['answer']
                    assert r['model']==(None if d['model'] is None else {int(k):v for k,v in d['model'].items()})
                for case in catalog['cases']:
                    row=baseline_records[case['case']];cnf,_,key=solver._canonical(case['source']);known=solver._read(key,cnf)
                    guard=None if known is not None else row['guard']
                    if guard is None:fixed={};target=case['source']
                    else:fixed,target=check_guard(solver,case['source'],guard)
                    child=solver.solve(target);assert child['answer']==row['answer'];model=lift(case['source'],fixed,child['model']) if child['answer'] else None
                    decisions.append(dict(case=case['case'],source=case['source'],query_root=key,guard=guard,witness=None,child=child,answer=child['answer'],model=model))
        finally:solver.close();assert base.sha(tmp/'cold-union')==archive['database_sha256']
        old_sidecars=bound(parent['unsat_support_decisions'])
        inherited_check=study.prior.old.previous.audit(tmp/'cold-union',old_sidecars)
        union_check=study.prior.old.previous.audit(tmp/'cold-union',decisions)
        base.write(out/'union-decisions.json',decisions)
        checkpoint=copy.deepcopy(parent);checkpoint['source_fingerprints']=protocol['source_fingerprints'];checkpoint['parent_checkpoint']=protocol['parent']
        checkpoint['incremental_archive_study']=study.binding(out/'report.json');checkpoint['incremental_archive_decisions']=study.binding(out/'union-decisions.json');checkpoint['reference_union']=archive
        base.write(out/'checkpoint.json',checkpoint);_,current=restore_checkpoint(out/'checkpoint.json',tmp/'current');assert current==structural;supplement=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),archives=audits,parent_check=structural,
        supplemental_check=supplement,union_check=union_check,inherited_guarded_check=inherited_check,inherited_decisions_checked=len(inherited)+len(old_sidecars),
        identical_logical_archives=True,identical_query_evidence_excluding_accounting_metrics=True,
        ledger_delta_archives_identical=all(archives[('ledger',r)]==archives[('delta',r)] for r in range(3)),
        old_reference_union_nodes=len(initial),reference_union_nodes=len(baseline),new_reference_keys=len(baseline)-len(initial),reference_archive=archive,
        direct_query_decisions=sum(r['guard'] is None for r in decisions),structural_authority_unchanged=True,seconds=time.perf_counter()-start,validator_sha256=base.sha(__file__))
    base.write(out/'reconstruction.json',result);print(base.encode({k:result[k] for k in ('passed','reference_union_nodes','new_reference_keys','direct_query_decisions','ledger_delta_archives_identical','seconds')}))


if __name__=='__main__':validate(Path(sys.argv[1]))
