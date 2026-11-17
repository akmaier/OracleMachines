#!/usr/bin/env python3
"""Independently replay disjoint alternatives and preserve every native delta."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_clause_partition as study
from experiments.cnf_clause_partition import check_record,make_record,PartitionBank
from experiments.cnf_clause_deletion_guard import check_guard,clause_set,lift
from experiments.cnf_residual_dag import restrict
from experiments.validate_cnf_guard_chain import independent_chain
from experiments.cnf_guard_chain import check_record as check_chain
from experiments.validate_cnf_unsat_support import bound
from experiments.cnf_snapshot_replay import audit
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
base=study.base


def independent(s,r):
    target=r['source'];steps=[]
    for guard in r['guards']:
        fixed,child=check_guard(s,target,guard);steps.append((target,fixed));target=child
    missing=r['missing_clauses'];members=clause_set(target,Counter());extra=clause_set(missing,Counter())
    assert len(extra)==len(missing)>0 and not extra&members and all(extra)
    assert {abs(l) for c in extra for l in c}<={abs(l) for c in members for l in c}
    premise=[list(c) for c in target]+[list(c) for c in missing];cnf,_,key=s._canonical(premise);assert key==r['stronger_root'] and s._read(key,cnf)['answer'] is False
    assert 0<len(r['children'])<=len(missing);model=None;prefix=[list(c) for c in target];answer=False
    for i,child in enumerate(r['children']):
        clause=missing[i];fixed={abs(l):l<0 for l in clause};residual=restrict(prefix,fixed);got=s.solve(residual)
        assert got['root']==child['root'] and got['answer']==child['answer'] and got['metrics'].get('expanded_nodes',0)==0
        expected=None if child['model'] is None else {int(k):v for k,v in child['model'].items()};assert got['model']==expected
        if got['answer']:
            assert i==len(r['children'])-1;answer=True;model=lift(prefix,fixed,got['model'])
            for source,assignment in reversed(steps):model=lift(source,assignment,model)
        prefix.append(list(clause))
    assert answer or len(r['children'])==len(missing)
    expected=None if r['model'] is None else {int(k):v for k,v in r['model'].items()};assert r['answer']==answer and expected==model
    assert s._canonical(r['source'])[2]==r['query_root']
    return dict(answer=answer,model=model,root=r['query_root'])


def validate(out):
    start=time.perf_counter();report=base.load(out/'report.json');p=bound(report['protocol']);parent=bound(p['parent']);hp=bound(p['historical_protocol']);authority=bound(hp['parent']);trial=bound(p['historical_trial']);records=bound(trial['queries']);diagnosis=bound(p['diagnosis'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    assert p['plans']==study.plans(diagnosis) and len(p['plans'])==len(report['samples'])==11
    bindings=dict(legacy=hp['support_index'],causal=hp['causal_index']);indices={n:bound(e) for n,e in bindings.items()};prepared=study.previous.ordinary.compose(indices,bindings);cores=prepared['cores'];catalogs=[(n,bound(authority[n])) for n in study.OLD_FIELDS]
    audits=[];partitions=[];alternates=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=study.ResidualSolver(path)
            try:return study.rows(s)
            finally:s.close()
        initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final');preserved=read(parent['reference_union'],'union');union=dict(preserved)
        available=dict(initial);prefixes={};by_hash={base.key_sha(k):k for k in final};assert len(by_hash)==len(final)
        for row in records:
            prefixes[row['case']]=dict(available);assert len(row['new_ids'])==row['new_nodes']
            for digest in row['new_ids']:
                key=by_hash[digest];assert key not in available;available[key]=final[key]
        assert available==final
        for i,(plan,entry) in enumerate(zip(p['plans'],report['samples'])):
            data=bound(entry);assert data['plan']==plan;before=prefixes[plan['case']];old=next(r for r in records if r['case']==plan['case']);delta=bound(data['delta']);rs=bound(data['records']);assert len(rs)==1;r=rs[0]
            assert r['source']==old['chain']['source'] and r['guards']==old['chain']['guards'] and r['answer']==old['chain']['answer']==data['answer']
            assert data['prefix_nodes']==len(before) and data['prefix_digest']==base.key_sha(base.encode(sorted(before.items())))
            saved=dict(before)
            for k,v in delta:assert k not in saved;saved[k]=v
            assert data['new_nodes']==len(delta)==int(data['premise_inserted'])+sum(b['metrics'].get('inserted_nodes',0) for b in data['branch_reports'])
            assert data['new_payload_units']==sum(len(k)+len(v) for k,v in delta);assert data['row_digest']==base.key_sha(base.encode(sorted(saved.items())))
            assert data['expanded_nodes']==sum(b['metrics'].get('expanded_nodes',0) for b in data['branch_reports'])
            path=tmp/f'arm-{i}';base.restore_archive(authority['reference_union'],path);s=study.ResidualSolver(path)
            try:
                with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in saved.items() if k not in initial])
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s,'_expand',side_effect=AssertionError('Validation search')),patch.object(s,'_store',side_effect=AssertionError('Validation publication')):
                    if plan['core'] is None:
                        assert set(map(base.key_sha,dict(delta)))==set(old['new_ids']) and all(final[k]==v for k,v in delta)
                        assert check_chain(s,r)==independent_chain(s,r) and data['expanded_nodes']==old['child_metrics'].get('expanded_nodes',0)
                    else:
                        target=r['source']
                        for guard in r['guards']:_,target=check_guard(s,target,guard)
                        core=cores[plan['core']];assert core['root'] in before and s._read(core['root'])['answer'] is False
                        wanted=clause_set(core['source'],Counter());outer=clause_set(target,Counter());assert wanted&outer and wanted-outer==clause_set(plan['missing'],Counter())
                        assert r['missing_clauses']==plan['missing'];assert data['premise_inserted']==(r['stronger_root'] not in before)
                        assert check_record(s,r)==independent(s,r);partitions.append(r)
                    expected_children=[r['child']] if plan['core'] is None else r['children'];assert len(expected_children)==len(data['branch_reports'])
                    for c,b in zip(expected_children,data['branch_reports']):assert c['root']==b['root'] and c['answer']==b['answer']
            finally:s.close()
            cold=study.previous.prior.audit_chain(path,[r],prepared,catalogs,indices) if plan['core'] is None else study.audit_records(path,[r],prepared,catalogs,indices)
            assert cold['native']['lineage']==data['cold']['native']['lineage'];audits.append(dict(plan=plan,cold=cold))
            for k,v in delta:
                if k in union and union[k]!=v:
                    assert base.load_json(union[k])['answer']==base.load_json(v)['answer'];alternates.append(dict(root_sha256=base.key_sha(k),delta=data['delta']))
                union.setdefault(k,v)
        path=tmp/'union';s=study.ResidualSolver(path);rebuilt=[];direct=[]
        try:
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in preserved])
            assert study.rows(s)==union and preserved.items()<=union.items();s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_expand',side_effect=AssertionError('Union search')),patch.object(s,'_store',side_effect=AssertionError('Union publication')):
                for r in partitions:
                    target=r['source']
                    for guard in r['guards']:_,target=check_guard(s,target,guard)
                    children=[];prefix=[list(c) for c in target]
                    for clause in r['missing_clauses']:
                        child=s.solve(restrict(prefix,{abs(l):l<0 for l in clause}));children.append(child);prefix.append(clause)
                        if child['answer']:break
                    rebuilt.append(make_record(s,r['source'],r['guards'],r['missing_clauses'],r['stronger_root'],children))
                bank=PartitionBank(s,rebuilt)
                for r in rebuilt:assert bank.lookup(r['source'])==independent(s,r)
                original=base.load('experiments/results/cnf-join-transfer/cases.json')
                for d in bound(parent['reference_decisions'])+bound(parent['model_rotation_decisions']):
                    source=d['source'] if 'source' in d else original[d['case']]['source'];child=s.solve(source)
                    assert child['root']==d['root'] and child['answer']==d['answer'] and child['model']==(None if d['model'] is None else {int(k):v for k,v in d['model'].items()})
                    direct.append(dict(source=source,guard=None,witness=None,child=child,answer=child['answer'],model=child['model']))
        finally:s.close()
        inherited=direct+sum((bound(parent[f]) for f in study.FIELDS),[]);old_chains=bound(parent['guard_chain_decisions'])+bound(parent['premise_guard_chain_decisions'])
        inherited_audit=audit(path,inherited);chain_audit=study.previous.prior.audit_chain(path,old_chains,prepared,catalogs,indices);partition_audit=study.audit_records(path,rebuilt,prepared,catalogs,indices)
        dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest);base.write(out/'union-partitions.json',rebuilt)
        checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=p['source_fingerprints'],clause_partition_study=study.binding(out/'report.json'),clause_partition_decisions=study.binding(out/'union-partitions.json'))
        base.write(out/'checkpoint.json',checkpoint);_,old_structural=restore_checkpoint(p['parent']['path'],tmp/'old-patterns');_,structural=restore_checkpoint(out/'checkpoint.json',tmp/'patterns');assert structural==old_structural;supplemental=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,protocol=report['protocol'],report=study.binding(out/'report.json'),checkpoint=study.binding(out/'checkpoint.json'),audits=audits,preserved_keys=len(preserved),union_keys=len(union),new_keys=len(union)-len(preserved),alternate_certificate_occurrences=alternates,
        inherited_decisions=len(inherited),inherited_chains=len(old_chains),new_partition_records=len(rebuilt),distinct_partition_sources=len({r['query_root'] for r in rebuilt}),inherited_audit=inherited_audit,chain_audit=chain_audit,partition_audit=partition_audit,structural=structural,supplemental=supplemental,seconds=time.perf_counter()-start)
    base.write(out/'reconstruction.json',result);print(base.encode({k:result[k] for k in ('passed','preserved_keys','union_keys','new_keys','inherited_decisions','inherited_chains','new_partition_records','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
