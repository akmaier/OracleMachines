#!/usr/bin/env python3
"""Check reference histories, guard boundaries, results and preserved authority."""
from pathlib import Path
import copy,sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_clause_deletion_guard as study
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
from experiments.cnf_clause_deletion_guard import check_guard,removed_clause
base=study.base


def bound(entry):
    assert base.sha(entry['path'])==entry['sha256'],entry['path']
    return base.load(entry['path'])


def without_times(value):
    if isinstance(value,dict):return {k:without_times(v) for k,v in value.items() if k!='seconds'}
    if isinstance(value,list):return [without_times(v) for v in value]
    return value


def validate(out):
    started=time.perf_counter();report=base.load(out/'report.json');protocol=bound(report['protocol']);seed=bound(report['seed']);cases=bound(protocol['cases'])
    for f,h in protocol['source_fingerprints'].items():assert base.sha(f)==h,f
    cold=[];repeated={};answers={};attribution=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);parent,parent_check=restore_checkpoint(protocol['parent']['path'],tmp/'patterns')
        parent_supplement=check_supplement(protocol['parent']['path'])
        base.restore_archive(seed['archive'],tmp/'seed');checked=study.audit(tmp/'seed',seed['records'])
        assert without_times(checked)==without_times(seed['cold'])
        solver=study.ResidualSolver(tmp/'seed')
        try:initial=study.rows(solver)
        finally:solver.close()
        assert len(seed['records'])==len(seed['templates'])==12
        for row,template,case in zip(seed['records'],seed['templates'],cases[::2],strict=True):
            assert row['source']==template['source']==case['source'] and row['case']==template['case']==case['case']
            assert row['child']['root']==template['root']
        for sample in report['samples']:
            data=bound(sample);queries=bound(data['queries']);path=tmp/f"{sample['mode']}-{sample['repeat']}"
            base.restore_archive(data['archive'],path);recheck=study.audit(path,queries)
            assert without_times(recheck)==without_times(data['cold']);solver=study.ResidualSolver(path)
            try:
                solver.db.execute('PRAGMA query_only=ON');saved=study.rows(solver)
                assert initial.items()<=saved.items()
                assert base.key_sha(base.encode(sorted(saved.items())))==data['summary']['row_digest']
                inserted=[]
                with patch.object(solver,'_expand',side_effect=AssertionError('Fresh validation search')):
                    for index,row in enumerate(queries):
                        case=cases[1::2][index%12];assert row['source']==case['source'] and row['case']==case['case'] and row['visit']==index//12
                        if row['guard']:
                            fixed,target=check_guard(solver,row['source'],row['guard'])
                            assert {int(k):v for k,v in row['assignment'].items()}==fixed
                            assert [list(c) for c in target]==row['target']
                        else:assert row['target']==row['source'] and not row['assignment']
                        assert row['child']['metrics'].get('expanded_nodes',0)<=protocol['node_limit']
                        assert row['new_nodes']==len(set(row['new_ids']));inserted.extend(row['new_ids'])
                        answers[(sample['mode'],sample['repeat'],row['case'],row['visit'])]=row['answer']
                assert len(inserted)==len(set(inserted)) and set(inserted)==set(map(base.key_sha,set(saved)-set(initial)))
            finally:solver.close();assert base.sha(path)==data['archive']['database_sha256']
            repeated[(sample['mode'],sample['repeat'])]=(without_times(queries),data['archive']['database_sha256'])
            cold.append(dict(mode=sample['mode'],repeat=sample['repeat'],**recheck))
        for mode in study.MODES:assert repeated[(mode,0)]==repeated[(mode,1)]
        for case in cases[1::2]:
            values={answers[(mode,repeat,case['case'],visit)] for mode in study.MODES for repeat in (0,1) for visit in (0,1)}
            assert len(values)==1
        a=repeated[('ordinary',0)][0];b=repeated[('guarded',0)][0]
        for case,x,y in zip(cases[1::2],a,b):
            stronger=seed['records'][case['case']//2];clause=removed_clause(stronger['source'],case['source'])
            attribution.append(dict(case=case['case'],anchor_variables=case['anchor_variables'],removed_clause=clause,
                stronger_answer=stronger['answer'],edited_answer=x['answer'],guard_used=y['guard'] is not None,
                ordinary_nodes=x['new_nodes'],guarded_nodes=y['new_nodes'],
                ordinary_splits=x['child']['metrics'].get('split_nodes',0),guarded_splits=y['child']['metrics'].get('split_nodes',0),
                original_shape=[len({abs(l) for c in case['source'] for l in c}),len(case['source']),sum(map(len,case['source']))],
                target_shape=[len({abs(l) for c in y['target'] for l in c}),len(y['target']),sum(map(len,y['target']))]))
        checkpoint=copy.deepcopy(parent);checkpoint['source_fingerprints']=protocol['source_fingerprints']
        checkpoint['parent_checkpoint']=protocol['parent'];checkpoint['reference_study']=study.binding(out/'report.json')
        # Keep the entire structural archive and both original/supplemental catalogs.
        base.write(out/'checkpoint.json',checkpoint)
        _,union_check=restore_checkpoint(out/'checkpoint.json',tmp/'current');supplement=check_supplement(out/'checkpoint.json')
        assert union_check==parent_check
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),
        archives=cold,seed_checked_nodes=checked['checked_nodes'],parent_check=parent_check,structural_authority_unchanged=True,
        supplemental_check=supplement,identical_repetitions=True,all_mode_answers_match=True,attribution=attribution,
        seconds=time.perf_counter()-started,validator_sha256=base.sha(__file__))
    base.write(out/'reconstruction.json',result);print(base.encode(dict(passed=True,seed_nodes=checked['checked_nodes'],attribution=attribution,seconds=result['seconds'])))


if __name__=='__main__':validate(Path(sys.argv[1]))
