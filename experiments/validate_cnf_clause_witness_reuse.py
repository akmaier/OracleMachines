#!/usr/bin/env python3
"""Cold replay every arm and retain all earlier and new reference results."""
from pathlib import Path
import copy,sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_clause_witness_reuse as study
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
from experiments.validate_cnf_clause_deletion_guard import without_times
from experiments.cnf_clause_witness_reuse import check_witness
from experiments.cnf_clause_deletion_guard import check_guard
base=study.base


def bound(entry):
    assert base.sha(entry['path'])==entry['sha256'],entry['path']
    return base.load(entry['path'])


def validate(out):
    start=time.perf_counter();report=base.load(out/'report.json');protocol=bound(report['protocol']);seed=bound(report['seed'])
    cases=bound(protocol['cases']);prior_report=bound(protocol['prior_report']);audits=[];comparisons={};answers={};conflicts=[]
    for f,h in protocol['source_fingerprints'].items():assert base.sha(f)==h,f
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);parent,parent_check=restore_checkpoint(protocol['parent']['path'],tmp/'patterns')
        base.restore_archive(seed['archive'],tmp/'seed');seed_check=study.previous.audit(tmp/'seed',seed['records'])
        assert without_times(seed_check)==without_times(seed['cold'])
        solver=study.ResidualSolver(tmp/'seed')
        try:initial=study.rows(solver)
        finally:solver.close()
        union={};selected_from={};old_checks=[];old_archives={}
        # Old certificates win ties; every alternative remains in its immutable archive.
        for i,sample in enumerate(prior_report['samples']):
            old=bound(sample);records=bound(old['queries']);path=tmp/f'old-{i}';base.restore_archive(old['archive'],path)
            cold=study.previous.audit(path,records);assert without_times(cold)==without_times(old['cold'])
            old_checks.append(dict(mode=sample['mode'],repeat=sample['repeat'],nodes=cold['checked_nodes']))
            solver=study.ResidualSolver(path)
            try:saved=study.rows(solver)
            finally:solver.close()
            for key,payload in saved.items():
                if key not in union:union[key]=payload;selected_from[key]=sample['path']
                elif union[key]!=payload:
                    assert base.load_json(union[key])['answer']==base.load_json(payload)['answer']
                    conflicts.append(dict(key_sha256=base.key_sha(key),selected=selected_from[key],alternate=sample['path']))
            old_archives[sample['mode']]=old['archive']['database_sha256']
        old_union_nodes=len(union)
        for sample in report['samples']:
            data=bound(sample);records=bound(data['queries']);mode=sample['mode'];repeat=sample['repeat'];path=tmp/f'{mode}-{repeat}'
            base.restore_archive(data['archive'],path);cold=study.audit(path,records)
            assert without_times(cold)==without_times(data['cold'])
            if mode in old_archives:assert data['archive']['database_sha256']==old_archives[mode]
            solver=study.ResidualSolver(path)
            try:
                solver.db.execute('PRAGMA query_only=ON');saved=study.rows(solver);assert initial.items()<=saved.items()
                assert base.key_sha(base.encode(sorted(saved.items())))==data['summary']['row_digest']
                inserted=[];published=0
                with patch.object(solver,'_expand',side_effect=AssertionError('Fresh validation search')):
                    for index,row in enumerate(records):
                        case=cases[1::2][index%12]
                        assert row['source']==case['source'] and row['case']==case['case'] and row['visit']==index//12
                        if row['witness'] is not None:
                            assert mode=='witness' and row['guard'] is None and row['child']['answer'] is True
                            model=check_witness(solver,row['source'],row['witness'])
                            assert model=={int(k):v for k,v in row['model'].items()}
                            assert row['child']['metrics'].get('expanded_nodes',0)==0
                            assert row['premise_counts'].get('inserted_nodes',0)==1
                            assert row['guard_counts']['published_witness_roots']==1 and row['new_nodes']==1
                            published+=1
                        if row['guard'] is not None:
                            fixed,target=check_guard(solver,row['source'],row['guard'])
                            assert {int(k):v for k,v in row['assignment'].items()}==fixed
                            assert [list(c) for c in target]==row['target']
                        else:assert row['target']==row['source'] and not row['assignment']
                        assert row['child']['metrics'].get('expanded_nodes',0)<=protocol['node_limit']
                        assert row['new_nodes']==len(set(row['new_ids']));inserted.extend(row['new_ids'])
                        answers[(mode,repeat,row['case'],row['visit'])]=row['answer']
                assert published==data['summary']['witness_publications']
                assert len(inserted)==len(set(inserted)) and set(inserted)==set(map(base.key_sha,set(saved)-set(initial)))
                for key,payload in saved.items():
                    if key not in union:union[key]=payload;selected_from[key]=sample['path']
                    elif union[key]!=payload:
                        assert base.load_json(union[key])['answer']==base.load_json(payload)['answer']
                        conflicts.append(dict(key_sha256=base.key_sha(key),selected=selected_from[key],alternate=sample['path']))
            finally:solver.close();assert base.sha(path)==data['archive']['database_sha256']
            comparisons[(mode,repeat)]=(without_times(records),data['archive']['database_sha256'])
            audits.append(dict(mode=mode,repeat=repeat,**cold))
        for mode in study.MODES:
            assert comparisons[(mode,0)]==comparisons[(mode,1)]==comparisons[(mode,2)]
        for case in cases[1::2]:
            assert len({answers[(mode,r,case['case'],v)] for mode in study.MODES for r in range(3) for v in range(2)})==1
        attribution=[]
        for i,case in enumerate(cases[1::2]):
            entry=dict(case=case['case'],anchor_variables=case['anchor_variables'])
            for mode in study.MODES:
                row=comparisons[(mode,0)][0][i]
                entry[mode]=dict(new_nodes=row['new_nodes'],expanded=row['child']['metrics'].get('expanded_nodes',0),
                    splits=row['child']['metrics'].get('split_nodes',0),witness=row['witness'] is not None,answer=row['answer'])
            attribution.append(entry)
        path=tmp/'union';base.restore_archive(bound(prior_report['samples'][0])['archive'],path);solver=study.ResidualSolver(path)
        try:
            kept=study.rows(solver)
            with solver.db:solver.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in kept])
            assert kept.items()<=study.rows(solver).items()
        finally:solver.close()
        dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest)
        base.restore_archive(archive,tmp/'cold-union');solver=study.ResidualSolver(tmp/'cold-union');decisions=[]
        try:
            solver.db.execute('PRAGMA query_only=ON')
            with patch.object(solver,'_expand',side_effect=AssertionError('Fresh union search')):
                for key in union:assert solver._read(key) is not None
                for case in cases[1::2]:
                    result=solver.solve(case['source']);assert result['answer']==answers[('ordinary',0,case['case'],0)]
                    decisions.append(dict(case=case['case'],root=result['root'],answer=result['answer'],model=result['model']))
        finally:solver.close();assert base.sha(tmp/'cold-union')==archive['database_sha256']
        base.write(out/'union-decisions.json',decisions);base.write(out/'alternate-certificates.json',conflicts)
        checkpoint=copy.deepcopy(parent);checkpoint['source_fingerprints']=protocol['source_fingerprints'];checkpoint['parent_checkpoint']=protocol['parent']
        checkpoint['witness_reuse_study']=study.binding(out/'report.json');checkpoint['reference_union']=archive
        checkpoint['reference_decisions']=study.binding(out/'union-decisions.json')
        base.write(out/'checkpoint.json',checkpoint)
        _,structural_check=restore_checkpoint(out/'checkpoint.json',tmp/'current');assert structural_check==parent_check
        supplement=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),
        old_archives=old_checks,archives=audits,seed_nodes=seed_check['checked_nodes'],parent_check=parent_check,supplemental_check=supplement,
        identical_repetitions=True,unchanged_control_archives=True,all_mode_answers_match=True,attribution=attribution,
        old_reference_union_nodes=old_union_nodes,reference_union_nodes=len(union),new_reference_keys=len(union)-old_union_nodes,
        alternate_certificate_occurrences=len(conflicts),reference_archive=archive,structural_authority_unchanged=True,
        seconds=time.perf_counter()-start,validator_sha256=base.sha(__file__))
    base.write(out/'reconstruction.json',result);print(base.encode(dict(passed=True,reference_union_nodes=len(union),new_reference_keys=len(union)-old_union_nodes,seconds=result['seconds'],attribution=attribution)))


if __name__=='__main__':validate(Path(sys.argv[1]))
