#!/usr/bin/env python3
"""Independently check rotation witnesses, all cold streams, and preserved union."""
from pathlib import Path
from collections import Counter
import copy,sys,tempfile,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_model_rotation as study
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
from experiments.validate_cnf_clause_deletion_guard import without_times
from experiments.cnf_clause_deletion_guard import check_guard
base=study.base


def bound(entry):
    assert base.sha(entry['path'])==entry['sha256'],entry['path']
    return base.load(entry['path'])


def complete(model,support):return {v:model.get(v,False) for v in support}
def model_dict(model):return {int(k):v for k,v in model.items()}
def false_clauses(source,model):
    assert all(type(v) is bool for v in model.values())
    return [i for i,c in enumerate(source) if not any(model.get(abs(l),False)==(l>0) for l in c)]


def check_rotation(solver,state,catalog,records,limit):
    assert state['format']=='bounded-model-rotation-v1' and state['flip_limit']==limit
    assert len(state['templates'])==len(catalog['templates'])
    attempts=published=failed=literal_scans=0;details=[]
    for ti,t in enumerate(state['templates']):
        expected=catalog['templates'][ti];source=sorted([list(c) for c in {tuple(sorted(set(c))) for c in expected['source']}])
        assert t['source']==source and t['root']==expected['root']
        assert solver._read(t['root'])['answer'] is False
        support={abs(l) for c in source for l in c};seen=set()
        for mi,entry in enumerate(t['models']):
            model=model_dict(entry['model']);cid=entry['clause'];assert set(model)==support
            assert cid not in seen;seen.add(cid);assert false_clauses(source,model)==[cid]
            origin=entry['origin']
            if origin['kind']=='seed':
                seed=next(s for s in catalog['seeds'] if s['root']==origin['root'])
                cnf,names,key=solver._canonical(seed['source']);node=solver._read(key,cnf);assert node['answer'] is True
                assert model==complete({v:node['model'][j] for j,v in enumerate(names)},support)
            elif origin['kind']=='query':
                row=records[origin['index']];assert row['answer'] is True
                assert model==complete(model_dict(row['model']),support)
                assert {tuple(c) for c in row['source']}=={tuple(c) for j,c in enumerate(source) if j!=cid}
            else:
                assert origin['kind']=='rotation'
                prior=state['templates'][origin['template']];a=prior['attempts'][origin['attempt']]
                old=model_dict(prior['models'][a['model']]['model']);old[a['variable']]=not old[a['variable']]
                assert model==complete(old,support)
                if origin['template']==ti:assert a['model']<mi
        assert len(t['attempts'])<=limit
        cursor=literal=0
        for ai,a in enumerate(t['attempts']):
            while literal==len(source[t['models'][cursor]['clause']]):cursor+=1;literal=0
            assert a['model']==cursor
            clause=source[t['models'][cursor]['clause']];assert a['variable']==abs(clause[literal]);literal+=1
            model=model_dict(t['models'][cursor]['model']);model[a['variable']]=not model[a['variable']]
            bad=false_clauses(source,model);assert bad==a['falsified'];literal_scans+=sum(map(len,source))
            if len(bad)==1:
                target=[c for j,c in enumerate(source) if j!=bad[0]];cnf,_,key=solver._canonical(target)
                assert a['root']==key and solver._read(key,cnf)['answer'] is True
                assert bad[0] in seen
            else:assert 'root' not in a and a['published'] is False;failed+=1
            published+=a['published'];attempts+=1
        if len(t['attempts'])<limit:
            while cursor<len(t['models']) and literal==len(source[t['models'][cursor]['clause']]):cursor+=1;literal=0
        assert (t['cursor'],t['next_literal'])==(cursor,literal)
        unprocessed=sum(len(source[m['clause']]) for m in t['models'][cursor:])-literal
        details.append(dict(template=ti,case=expected['case'],witnesses=len(t['models']),attempts=len(t['attempts']),remaining_queued_flips=unprocessed,
                            failed=sum(len(a['falsified'])!=1 for a in t['attempts']),publications=sum(a['published'] for a in t['attempts'])))
    assert state['counts']['rotation_flip_attempts']==attempts and state['counts']['rotation_publications']==published
    assert state['counts']['rotation_scan_literals']==literal_scans
    return dict(attempts=attempts,publications=published,failed=failed,full_scan_literals=literal_scans,templates=details)


def validate(out):
    start=time.perf_counter();report=base.load(out/'report.json');protocol=bound(report['protocol']);catalog=bound(report['cases']);original=bound(protocol['original_cases'])
    for f,h in protocol['source_fingerprints'].items():assert base.sha(f)==h,f
    audits=[];comparisons={};answers={};conflicts=[];attribution=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);parent=bound(protocol['parent']);_,parent_check=restore_checkpoint(protocol['parent']['path'],tmp/'patterns')
        path=tmp/'seed';base.restore_archive(parent['reference_union'],path);seed_check=study.previous.audit(path,[])
        solver=study.ResidualSolver(path)
        try:
            initial=study.rows(solver);assert study.select_cases(solver,original,protocol['template_ids'])==catalog
            with patch.object(solver,'_expand',side_effect=AssertionError('Fresh parent search')):
                for d in bound(parent['reference_decisions']):
                    r=solver.solve(original[d['case']]['source']);assert r['root']==d['root'] and r['answer']==d['answer']
                    assert r['model']==(None if d['model'] is None else model_dict(d['model']))
        finally:solver.close()
        union=dict(initial);selected={k:protocol['parent']['path'] for k in union}
        for sample in report['samples']:
            data=bound(sample);records=bound(data['queries']);state=bound(data['rotation']);mode=sample['mode'];repeat=sample['repeat'];path=tmp/f'{mode}-{repeat}'
            base.restore_archive(data['archive'],path);cold=study.previous.audit(path,records);assert without_times(cold)==without_times(data['cold'])
            assert len(records)==len(catalog['cases'])*protocol['visits']
            solver=study.ResidualSolver(path);rotation_check=None
            try:
                solver.db.execute('PRAGMA query_only=ON');saved=study.rows(solver);assert initial.items()<=saved.items()
                assert base.key_sha(base.encode(sorted(saved.items())))==data['summary']['row_digest']
                inserted=list(data['setup_ids'])
                with patch.object(solver,'_expand',side_effect=AssertionError('Fresh validation search')):
                    if mode=='rotation':rotation_check=check_rotation(solver,state,catalog,records,protocol['flip_limit'])
                    else:assert state is None and not data['setup_ids']
                    for index,row in enumerate(records):
                        case=catalog['cases'][index%len(catalog['cases'])]
                        assert row['source']==case['source'] and row['case']==case['case'] and row['visit']==index//len(catalog['cases'])
                        if row['guard'] is not None:
                            assert mode!='ordinary';fixed,target=check_guard(solver,row['source'],row['guard'])
                            assert model_dict(row['assignment'])==fixed and [list(c) for c in target]==row['target']
                        else:assert row['target']==row['source'] and not row['assignment']
                        assert row['child']['metrics'].get('expanded_nodes',0)<=protocol['node_limit']
                        assert row['new_nodes']==len(set(row['new_ids']));inserted.extend(row['new_ids'])
                        answers[(mode,repeat,row['case'],row['visit'])]=row['answer']
                assert len(inserted)==len(set(inserted)) and set(inserted)==set(map(base.key_sha,set(saved)-set(initial)))
                assert len(saved)-len(initial)==data['summary']['new_nodes']
                for key,payload in saved.items():
                    if key not in union:union[key]=payload;selected[key]=sample['path']
                    elif union[key]!=payload:
                        assert base.load_json(union[key])['answer']==base.load_json(payload)['answer']
                        conflicts.append(dict(key_sha256=base.key_sha(key),selected=selected[key],alternate=sample['path']))
            finally:solver.close();assert base.sha(path)==data['archive']['database_sha256']
            comparisons[(mode,repeat)]=(without_times(records),state,data['archive']['database_sha256'])
            audits.append(dict(mode=mode,repeat=repeat,rotation=rotation_check,**cold))
        for mode in study.MODES:assert comparisons[(mode,0)]==comparisons[(mode,1)]==comparisons[(mode,2)]
        for case in catalog['cases']:
            assert len({answers[(m,r,case['case'],v)] for m in study.MODES for r in range(3) for v in range(2)})==1
            entry=dict(case=case['case'],template_case=case['template_case'],removed_clause=case['removed_clause'])
            for mode in study.MODES:
                row=comparisons[(mode,0)][0][case['case']]
                entry[mode]=dict(new_nodes=row['new_nodes'],expanded=row['child']['metrics'].get('expanded_nodes',0),splits=row['child']['metrics'].get('split_nodes',0),answer=row['answer'])
            attribution.append(entry)
        path=tmp/'union';base.restore_archive(parent['reference_union'],path);solver=study.ResidualSolver(path)
        try:
            with solver.db:solver.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in initial])
            assert initial.items()<=study.rows(solver).items()
        finally:solver.close()
        dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest)
        base.restore_archive(archive,tmp/'cold-union');solver=study.ResidualSolver(tmp/'cold-union');decisions=[]
        try:
            solver.db.execute('PRAGMA query_only=ON')
            with patch.object(solver,'_expand',side_effect=AssertionError('Fresh union search')):
                for key in union:assert solver._read(key) is not None
                for d in bound(parent['reference_decisions']):
                    r=solver.solve(original[d['case']]['source']);assert r['root']==d['root'] and r['answer']==d['answer']
                    assert r['model']==(None if d['model'] is None else model_dict(d['model']))
                for case in catalog['cases']:
                    result=solver.solve(case['source']);assert result['answer']==answers[('ordinary',0,case['case'],0)]
                    decisions.append(dict(case=case['case'],source=case['source'],root=result['root'],answer=result['answer'],model=result['model']))
        finally:solver.close();assert base.sha(tmp/'cold-union')==archive['database_sha256']
        base.write(out/'union-decisions.json',decisions);base.write(out/'alternate-certificates.json',conflicts)
        checkpoint=copy.deepcopy(parent);checkpoint['source_fingerprints']=protocol['source_fingerprints'];checkpoint['parent_checkpoint']=protocol['parent']
        checkpoint['model_rotation_study']=study.binding(out/'report.json');checkpoint['reference_union']=archive
        checkpoint['model_rotation_decisions']=study.binding(out/'union-decisions.json')
        base.write(out/'checkpoint.json',checkpoint)
        _,structural_check=restore_checkpoint(out/'checkpoint.json',tmp/'current');assert structural_check==parent_check
        supplement=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,report_sha256=base.sha(out/'report.json'),checkpoint_sha256=base.sha(out/'checkpoint.json'),
        archives=audits,parent_check=parent_check,supplemental_check=supplement,identical_repetitions=True,all_mode_answers_match=True,
        attribution=attribution,old_reference_union_nodes=len(initial),reference_union_nodes=len(union),new_reference_keys=len(union)-len(initial),
        alternate_certificate_occurrences=len(conflicts),reference_archive=archive,structural_authority_unchanged=True,
        seconds=time.perf_counter()-start,validator_sha256=base.sha(__file__))
    base.write(out/'reconstruction.json',result)
    print(base.encode({k:result[k] for k in ('passed','reference_union_nodes','new_reference_keys','seconds')}))


if __name__=='__main__':validate(Path(sys.argv[1]))
