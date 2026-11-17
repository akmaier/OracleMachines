#!/usr/bin/env python3
"""Reconstruct prefix arms, replay guard composition, and extend native/sidecar state."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_guard_chain as study
from experiments.cnf_clause_deletion_guard import check_guard,clause_set,lift
from experiments.cnf_residual_dag import restrict
from experiments.cnf_guard_chain import check_record,make_record,GuardChainBank
from experiments.cnf_proof_choice import compose
from experiments.cnf_snapshot_replay import audit
from experiments.validate_cnf_unsat_support import bound
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
base=study.base


def independent_chain(s,record):
    current=record['source'];steps=[]
    for guard in record['guards']:
        assignment,child=check_guard(s,current,guard);steps.append((current,assignment));current=child
    # The native solver is permitted only to load a checked existing child.
    result=s.solve(current);assert result['metrics'].get('expanded_nodes',0)==0
    assert result['root']==record['child']['root'] and result['answer']==record['child']['answer']==record['answer']
    model=result['model']
    expected=record['child']['model'];expected=None if expected is None else {int(k):v for k,v in expected.items()}
    assert model==expected
    if result['answer']:
        for source,assignment in reversed(steps):model=lift(source,assignment,model)
    expected=record['model'];expected=None if expected is None else {int(k):v for k,v in expected.items()}
    assert model==expected
    assert s._canonical(record['source'])[2]==record['query_root']
    return dict(answer=result['answer'],model=model,root=record['query_root'])


def validate(out):
    tick=time.perf_counter();report=base.load(out/'report.json');p=bound(report['protocol']);parent=bound(p['parent'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    historical=bound(p['historical_protocol']);authority=bound(historical['parent']);trial=bound(p['historical_trial']);records=bound(trial['queries'])
    diagnosis=bound(p['diagnosis']);assert p['cases']==[r['case'] for r in diagnosis['cases']]
    bindings=dict(legacy=historical['support_index'],causal=historical['causal_index']);indices={n:bound(e) for n,e in bindings.items()}
    cores=indices['legacy']['cores']+indices['causal']['cores'];prepared=compose(indices,bindings)
    catalogs=[(n,bound(e)) for n,e in zip(study.OLD_FIELDS,historical['prior_decision_catalogs'])]
    audits=[];alternates=[];candidate_records=[];summaries=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=study.ResidualSolver(path)
            try:return study.rows(s)
            finally:s.close()
        initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final')
        preserved=read(parent['reference_union'],'union');union=dict(preserved)
        by_hash={base.key_sha(k):k for k in final};assert len(by_hash)==len(final) and initial.items()<=final.items() and not trial['setup_ids']
        prefix=dict(initial);prefixes={}
        for row in records:
            if not row['visit'] and row['case'] in p['cases']:prefixes[row['case']]=dict(prefix)
            assert len(row['new_ids'])==row['new_nodes']
            for digest in row['new_ids']:
                key=by_hash[digest];assert key not in prefix;prefix[key]=final[key]
        assert prefix==final
        expected=[(cid,mode) for cid in p['cases'] for mode in ('baseline','chain')]
        assert len(expected)==len(report['samples'])==16
        for entry,(cid,mode) in zip(report['samples'],expected):
            data=bound(entry);assert (data['case'],data['mode'])==(cid,mode)
            before=prefixes[cid];saved=dict(before);delta=bound(data['delta']);chains=bound(data['chains']);assert len(chains)==1
            row=chains[0];old=next(r for r in records if r['case']==cid and not r['visit'])
            assert row['source']==old['source'] and row['answer']==old['answer']==data['answer']
            assert data['prefix']['nodes']==len(before) and data['prefix']['row_digest']==base.key_sha(base.encode(sorted(before.items())))
            for k,v in delta:assert k not in saved;saved[k]=v
            assert data['new_nodes']==len(delta)==data['child_metrics'].get('inserted_nodes',0)+int(data['premise_inserted'])
            assert data['new_payload_units']==sum(len(k)+len(v) for k,v in delta)
            assert data['row_digest']==base.key_sha(base.encode(sorted(saved.items())))
            path=tmp/f'arm-{len(audits)}';base.restore_archive(authority['reference_union'],path);s=study.ResidualSolver(path)
            try:
                with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in saved.items() if k not in initial])
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s,'_expand',side_effect=AssertionError('Fresh validation search')),patch.object(s,'_store',side_effect=AssertionError('Validation publication')):
                    assert row['guards'][0]==old['guard'];_,target=check_guard(s,row['source'],old['guard']);choice=None
                    if mode=='chain':
                        members={tuple(sorted(c)) for c in target};variables={abs(l) for c in members for l in c}
                        for i,core in enumerate(cores):
                            wanted={tuple(sorted(c)) for c in core['source']};missing=wanted-members
                            if not wanted&members or len(missing)!=1:continue
                            clause=next(iter(missing))
                            if not clause or not {abs(l) for l in clause}<=variables:continue
                            reduced=restrict(target,{abs(l):l<0 for l in clause})
                            if {tuple(sorted(c)) for c in reduced}==members:continue
                            assert s._canonical(core['source'])[2]==core['root']
                            if core['root'] not in before:continue
                            assert s._read(core['root'])['answer'] is False
                            choice=dict(core=i,missing_clause=list(clause));break
                    assert choice==data['choice'] and len(row['guards'])==data['guards']==1+int(choice is not None)
                    if choice is not None:
                        guard=row['guards'][1];assert guard['stronger']==[list(c) for c in target]+[choice['missing_clause']]
                        assert guard['removed_clause']==choice['missing_clause']
                        assert data['premise_inserted']==(guard['stronger_root'] not in before)
                        assert clause_set(cores[choice['core']]['source'],Counter())<=clause_set(guard['stronger'],Counter())
                    if mode=='baseline':
                        assert set(map(base.key_sha,dict(delta)))==set(old['new_ids']) and all(final[k]==v for k,v in delta)
                        assert data['child_metrics']['expanded_nodes']==old['child']['metrics']['expanded_nodes']
                    assert check_record(s,row)==independent_chain(s,row)
            finally:s.close()
            cold=study.audit_chain(path,chains,prepared,catalogs,indices)
            assert cold['chain_answers']==data['cold']['chain_answers']==[row['answer']]
            assert cold['native']['lineage']==data['cold']['native']['lineage']
            audits.append(dict(case=cid,mode=mode,cold=cold))
            if mode=='chain':candidate_records.append(row)
            summaries.append(dict(case=cid,mode=mode,answer=row['answer'],new_nodes=len(delta),expanded_nodes=data['child_metrics'].get('expanded_nodes',0)))
            for key,payload in delta:
                if key in union and union[key]!=payload:
                    assert base.load_json(union[key])['answer']==base.load_json(payload)['answer']
                    alternates.append(dict(root_sha256=base.key_sha(key),delta=data['delta']))
                union.setdefault(key,payload)
        path=tmp/'union';s=study.ResidualSolver(path);decisions=[];direct=[]
        try:
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in preserved])
            assert study.rows(s)==union and preserved.items()<=union.items();s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_expand',side_effect=AssertionError('Fresh union search')),patch.object(s,'_store',side_effect=AssertionError('Union publication')):
                for row in candidate_records:
                    target=row['source']
                    for guard in row['guards']:_,target=check_guard(s,target,guard)
                    child=s.solve(target);assert child['answer']==row['answer']
                    decisions.append(make_record(s,row['source'],row['guards'],child))
                bank=GuardChainBank(s,decisions)
                for row in decisions:assert bank.lookup(row['source'])==independent_chain(s,row)
                original=base.load('experiments/results/cnf-join-transfer/cases.json')
                for d in bound(parent['reference_decisions'])+bound(parent['model_rotation_decisions']):
                    source=d['source'] if 'source' in d else original[d['case']]['source'];child=s.solve(source)
                    assert child['root']==d['root'] and child['answer']==d['answer'] and child['model']==(None if d['model'] is None else {int(k):v for k,v in d['model'].items()})
                    direct.append(dict(source=source,guard=None,witness=None,child=child,answer=child['answer'],model=child['model']))
        finally:s.close()
        inherited=direct+sum((bound(parent[field]) for field in study.FIELDS),[]);inherited_audit=audit(path,inherited)
        chain_audit=study.audit_chain(path,decisions,prepared,catalogs,indices)
        dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest);base.write(out/'union-chains.json',decisions)
        _,structural=restore_checkpoint(p['parent']['path'],tmp/'patterns')
        checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=p['source_fingerprints'],
            guard_chain_study=study.binding(out/'report.json'),guard_chain_decisions=study.binding(out/'union-chains.json'))
        base.write(out/'checkpoint.json',checkpoint);_,current=restore_checkpoint(out/'checkpoint.json',tmp/'current');assert structural==current
        supplemental=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,protocol=report['protocol'],report=study.binding(out/'report.json'),checkpoint=study.binding(out/'checkpoint.json'),
        audits=audits,arm_summaries=summaries,preserved_keys=len(preserved),union_keys=len(union),new_keys=len(union)-len(preserved),
        alternate_certificate_occurrences=alternates,inherited_decisions=len(inherited),inherited_audit=inherited_audit,chain_audit=chain_audit,
        chain_decisions=len(decisions),structural=structural,supplemental=supplemental,seconds=time.perf_counter()-tick,
        limitations=['Native proof payloads remain compatible with the frozen checker. Composed conclusions require the bound sidecars and optional GuardChainBank; they are not asserted to be native root-table proofs.',
            'All prior payloads and semantic fields are retained. Different per-arm certificates remain in their deltas; union old-payload priority may require rebuilding a valid SAT chain witness.',
            'Historical prefix trials provide no fresh coverage or stable timing/generalization claim. Recognition, publication, remaining solving, sidecar verification and retention all remain charged.'])
    base.write(out/'reconstruction.json',result);print(base.encode({k:result[k] for k in ('passed','preserved_keys','union_keys','new_keys','inherited_decisions','chain_decisions','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
