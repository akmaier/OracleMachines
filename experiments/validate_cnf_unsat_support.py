#!/usr/bin/env python3
"""Cold-check derived cores, query containment, all arms and the durable union."""
from pathlib import Path
import copy,sys,tempfile,time
from collections import Counter
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_unsat_support as study
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
from experiments.validate_cnf_clause_deletion_guard import without_times
from experiments.cnf_clause_deletion_guard import check_guard,lift,clause_set
base=study.base


def bound(item):
    assert base.sha(item['path'])==item['sha256'],item['path']
    return base.load(item['path'])


def check_cores(solver,cores,sources):
    by_label={s['label']:s['source'] for s in sources}
    for core in cores:
        original=by_label[core['label']];source=core['source']
        assert clause_set(source,Counter())<=clause_set(original,Counter())
        assert solver._canonical(original)[2]==core['origin']
        cnf,_,key=solver._canonical(source);assert key==core['root']
        assert solver._read(key,cnf)['answer'] is False
    return len(cores)


def validate(out):
    start=time.perf_counter();report=base.load(out/'report.json');protocol=bound(report['protocol']);catalog=bound(report['cases']);parent=bound(protocol['parent'])
    for f,h in protocol['source_fingerprints'].items():assert base.sha(f)==h,f
    audits=[];comparisons={};answers={};conflicts=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);_,structural=restore_checkpoint(protocol['parent']['path'],tmp/'patterns')
        path=tmp/'parent';base.restore_archive(parent['reference_union'],path);solver=study.ResidualSolver(path)
        try:initial=study.rows(solver);assert study.inputs(solver,parent,protocol['per_template'])==catalog
        finally:solver.close()
        union=dict(initial);selected={k:protocol['parent']['path'] for k in union}
        def merge(saved,origin):
            for key,payload in saved.items():
                if key not in union:union[key]=payload;selected[key]=origin
                elif union[key]!=payload:
                    assert base.load_json(union[key])['answer']==base.load_json(payload)['answer']
                    conflicts.append(dict(key_sha256=base.key_sha(key),selected=selected[key],alternate=origin))
        screen_check=None
        if protocol['screen']:
            screen=bound(protocol['screen'])
            for f,h in screen['sources'].items():assert base.sha(f)==h
            path=tmp/'screen';base.restore_archive(screen['archive'],path);screen_check=study.old.previous.audit(path,[]);solver=study.ResidualSolver(path)
            try:
                solver.db.execute('PRAGMA query_only=ON');saved=study.rows(solver);assert initial.items()<=saved.items()
                with patch.object(solver,'_expand',side_effect=AssertionError('Fresh screen check')):check_cores(solver,screen['cores'],catalog['support_sources'])
                merge(saved,protocol['screen']['path'])
            finally:solver.close();assert base.sha(path)==screen['archive']['database_sha256']
        for sample in report['samples']:
            data=bound(sample);records=bound(data['queries']);cores=bound(data['cores']);mode=sample['mode'];repeat=sample['repeat'];path=tmp/f'{mode}-{repeat}'
            base.restore_archive(data['archive'],path);cold=study.old.previous.audit(path,records);assert without_times(cold)==without_times(data['cold'])
            assert len(records)==len(catalog['cases'])*protocol['visits']
            solver=study.ResidualSolver(path)
            try:
                solver.db.execute('PRAGMA query_only=ON');saved=study.rows(solver);assert initial.items()<=saved.items()
                assert base.key_sha(base.encode(sorted(saved.items())))==data['summary']['row_digest']
                inserted=list(data['setup_ids']);hits=0
                with patch.object(solver,'_expand',side_effect=AssertionError('Fresh validation search')):
                    check_cores(solver,cores,catalog['support_sources'])
                    if mode=='guarded':assert not cores and not data['setup_ids']
                    if mode=='three':assert len(cores)==3 and all(c['label'].startswith('template-') for c in cores)
                    for index,row in enumerate(records):
                        case=catalog['cases'][index%len(catalog['cases'])]
                        assert row['case']==case['case'] and row['source']==case['source'] and row['visit']==index//len(catalog['cases'])
                        if row['core']:
                            core=cores[row['core']['core']];assert clause_set(core['source'],Counter())<=clause_set(row['source'],Counter())
                            assert row['answer'] is False and row['guard'] is None and row['witness'] is None
                            assert row['child']['root']==row['core']['root']==case['root']
                            assert row['child']['metrics'].get('expanded_nodes',0)==0
                            assert row['new_nodes']==1 and row['core']['inserted'];hits+=row['visit']==0
                        if row['guard'] is not None:
                            fixed,target=check_guard(solver,row['source'],row['guard'])
                            assert {int(k):v for k,v in row['assignment'].items()}==fixed and [list(c) for c in target]==row['target']
                        else:assert row['target']==row['source'] and not row['assignment']
                        assert row['new_nodes']==len(set(row['new_ids']));inserted.extend(row['new_ids'])
                        assert row['child']['metrics'].get('expanded_nodes',0)<=protocol['node_limit']
                        answers[(mode,repeat,row['case'],row['visit'])]=row['answer']
                assert hits==data['summary']['core_hits']
                assert len(inserted)==len(set(inserted)) and set(inserted)==set(map(base.key_sha,set(saved)-set(initial)))
                merge(saved,sample['path'])
            finally:solver.close();assert base.sha(path)==data['archive']['database_sha256']
            comparisons[(mode,repeat)]=(without_times(records),cores,data['archive']['database_sha256']);audits.append(dict(mode=mode,repeat=repeat,cores=len(cores),**cold))
        for mode in study.MODES:assert comparisons[(mode,0)]==comparisons[(mode,1)]==comparisons[(mode,2)]
        for case in catalog['cases']:
            assert len({answers[(m,r,case['case'],v)] for m in study.MODES for r in range(3) for v in range(2)})==1
        path=tmp/'union';base.restore_archive(parent['reference_union'],path);solver=study.ResidualSolver(path)
        try:
            with solver.db:solver.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in initial])
            assert initial.items()<=study.rows(solver).items()
        finally:solver.close()
        dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest);base.restore_archive(archive,tmp/'cold-union');solver=study.ResidualSolver(tmp/'cold-union');decisions=[]
        try:
            solver.db.execute('PRAGMA query_only=ON')
            with patch.object(solver,'_expand',side_effect=AssertionError('Fresh union search')):
                for key in union:assert solver._read(key) is not None
                original=base.load('experiments/results/cnf-join-transfer/cases.json')
                inherited=bound(parent['reference_decisions'])+bound(parent['model_rotation_decisions'])
                for d in inherited:
                    r=solver.solve(d.get('source',original[d['case']]['source'] if d['case']<len(original) else []))
                    assert r['root']==d['root'] and r['answer']==d['answer']
                    assert r['model']==(None if d['model'] is None else {int(k):v for k,v in d['model'].items()})
                for case in catalog['cases']:
                    row=comparisons[('all',0)][0][case['case']];cnf,_,key=solver._canonical(case['source']);old=solver._read(key,cnf)
                    guard=None if old is not None else row['guard']
                    if guard is None:fixed={};target=case['source']
                    else:fixed,target=check_guard(solver,case['source'],guard)
                    child=solver.solve(target);assert child['answer']==answers[('guarded',0,case['case'],0)]
                    model=lift(case['source'],fixed,child['model']) if child['answer'] else None
                    decisions.append(dict(case=case['case'],source=case['source'],query_root=key,guard=guard,witness=None,child=child,answer=child['answer'],model=model))
        finally:solver.close();assert base.sha(tmp/'cold-union')==archive['database_sha256']
        union_check=study.old.previous.audit(tmp/'cold-union',decisions)
        base.write(out/'union-decisions.json',decisions);base.write(out/'alternate-certificates.json',conflicts)
        checkpoint=copy.deepcopy(parent);checkpoint['source_fingerprints']=protocol['source_fingerprints'];checkpoint['parent_checkpoint']=protocol['parent']
        checkpoint['unsat_support_study']=study.binding(out/'report.json');checkpoint['unsat_support_decisions']=study.binding(out/'union-decisions.json');checkpoint['reference_union']=archive
        base.write(out/'checkpoint.json',checkpoint)
        _,current=restore_checkpoint(out/'checkpoint.json',tmp/'current');assert current==structural;supplement=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),archives=audits,screen=screen_check,
        parent_check=structural,supplemental_check=supplement,union_check=union_check,identical_repetitions=True,all_mode_answers_match=True,
        old_reference_union_nodes=len(initial),reference_union_nodes=len(union),new_reference_keys=len(union)-len(initial),reference_archive=archive,
        alternate_certificate_occurrences=len(conflicts),inherited_decisions_checked=len(inherited),direct_query_decisions=sum(r['guard'] is None for r in decisions),
        structural_authority_unchanged=True,seconds=time.perf_counter()-start,validator_sha256=base.sha(__file__))
    base.write(out/'reconstruction.json',result);print(base.encode({k:result[k] for k in ('passed','reference_union_nodes','new_reference_keys','direct_query_decisions','seconds')}))


if __name__=='__main__':validate(Path(sys.argv[1]))
