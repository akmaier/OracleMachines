#!/usr/bin/env python3
"""Independent cofactor-coordinate, native-proof and persistent-prefix checks."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_conditioned_core as study
from experiments.cnf_clause_deletion_guard import check_guard,clause_set
from experiments.cnf_residual_dag import restrict,propagate
from experiments.validate_cnf_partition_screen import check_composed
from experiments.cnf_snapshot_replay import audit
from experiments.validate_cnf_unsat_support import bound
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
base=study.base


def direct_restriction(source,fixed):
    return [[lit for lit in clause if abs(lit) not in fixed] for clause in source if not any(abs(lit) in fixed and fixed[abs(lit)]==(lit>0) for lit in clause)]


def validate(out):
    start=time.perf_counter();report=base.load(out/'report.json');p=bound(report['protocol']);parent=bound(p['parent']);hp=bound(p['historical_protocol']);authority=bound(hp['parent']);trial=bound(p['historical_trial']);records=bound(trial['queries']);probe=bound(p['probe'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    assert p['cofactor_acquisition']=='unit-propagation-to-two-CNF-v1'
    samples=[bound(e) for e in report['samples']];assert [(r['case'],r['mode']) for r in samples]==[(t['case'],m) for t in p['targets'] for m in p['modes']]
    bindings=dict(legacy=hp['support_index'],causal=hp['causal_index']);indices={n:bound(e) for n,e in bindings.items()};prepared=study.history.previous.ordinary.compose(indices,bindings);catalogs=[(n,bound(authority[n])) for n in study.OLD_FIELDS]
    audits=[];decisions=[];projections=[];alternates=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=study.ResidualSolver(path)
            try:return study.rows(s)
            finally:s.close()
        initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final');preserved=read(parent['reference_union'],'union');union=dict(preserved);prefixes=study.history.partition_study.prefixes(initial,final,records)
        for selection in p['targets']:
            cid=selection['case'];probe_row=next(r for r in probe['cases'] if r['case']==cid);candidate=next(r for r in probe_row['conditioning']['guard_only']['examples'] if r['core']==selection['core']);assert selection['missing']==candidate['missing_clauses']
            old=next(r for r in records if r['case']==cid);before=prefixes[cid]
            for data in (r for r in samples if r['case']==cid):
                mode=data['mode'];missing=selection['missing'] if not mode.endswith('reverse') else list(reversed(selection['missing']));assert data['core']==selection['core'] and data['missing']==missing
                assert data['prefix_nodes']==len(before) and data['prefix_digest']==base.key_sha(base.encode(sorted(before.items())))
                delta=bound(data['delta']);saved=dict(before)
                for k,v in delta:assert k not in saved;saved[k]=v
                rs=bound(data['records']);ps=bound(data['projections']);assert len(rs)==1;r=rs[0];assert r['source']==old['record']['source'] and r['guards']==old['record']['guards'] and r['answer']==old['record']['answer']
                acquisitions=[c for c in (data['cofactor'],data['premise_child']) if c is not None]
                assert data['expanded_nodes']==sum(c['metrics'].get('expanded_nodes',0) for c in data['children']+acquisitions)
                assert data['new_nodes']==len(delta)==sum(c['metrics'].get('inserted_nodes',0) for c in data['children'])+data['premise_metrics'].get('inserted_nodes',0)+(0 if data['cofactor'] is None else data['cofactor']['metrics'].get('inserted_nodes',0))
                assert data['new_payload_units']==sum(len(k)+len(v) for k,v in delta)
                path=tmp/'arm';shutil.copyfile(tmp/'initial',path);s=study.ResidualSolver(path)
                try:
                    with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in saved.items() if k not in initial])
                    s.db.execute('PRAGMA query_only=ON')
                    with patch.object(s,'_expand',side_effect=AssertionError('Validation search')),patch.object(s,'_store',side_effect=AssertionError('Validation publication')):
                        fixed={};target=r['source']
                        for guard in r['guards']:
                            assert guard['stronger_root'] in before;part,target=check_guard(s,target,guard)
                            for var,bit in part.items():assert var not in fixed or fixed[var]==bit;fixed[var]=bit
                        assert {str(k):v for k,v in fixed.items()}==probe_row['conditioning']['guard_assignments']
                        expected_projection=direct_restriction(prepared['cores'][selection['core']]['source'],fixed);cf,_,key=s._canonical(expected_projection)
                        if mode.startswith('conditioned'):
                            assert len(ps)==1;pr=ps[0];assert pr['parent_source']==prepared['cores'][selection['core']]['source'] and pr['parent_root']==prepared['cores'][selection['core']]['root'] and pr['parent_root'] in before
                            assert pr['assignment']==[[v,b] for v,b in sorted(fixed.items())] and pr['source']==expected_projection and pr['root']==key
                            study.check_projection(s,pr);assert data['cofactor_was_known']==(key in before)
                            if key not in before:
                                forced,trace,conflict=propagate(cf,Counter());residual=restrict(cf,forced);assert conflict is not None or all(len(c)<=2 for c in residual)
                                observed=data['cofactor']['conditioning_screen'];assert observed==dict(root=key,trace=trace,conflict=conflict,residual_literals=0 if conflict is not None else sum(map(len,residual)))
                            else:assert data['cofactor']['conditioning_screen'] is None
                            assert data['cofactor']['root']==key and data['cofactor']['answer'] is False
                            assert clause_set(expected_projection,Counter())-clause_set(target,Counter())==clause_set(missing,Counter());projections.append(pr)
                        else:assert ps==[] and data['cofactor'] is None and data['cofactor_was_known'] is None
                        if mode=='baseline':
                            assert r==old['record'] and dict(delta)=={k:v for k,v in final.items() if base.key_sha(k) in old['new_ids']}
                            assert data['premise_child'] is None and not data['premise_inserted'];expected_children=[r['child']]
                        else:
                            assert r['missing_clauses']==missing;stronger=[list(c) for c in target]+missing;normalized,_,root=s._canonical(stronger);assert root==r['stronger_root'] and s._read(root,normalized)['answer'] is False
                            if mode.startswith('direct'):assert data['premise_child']['root']==root and data['premise_child']['answer'] is False
                            else:assert data['premise_child'] is None and data['premise_inserted']==(root not in before and root!=key)
                            expected_children=r['children']
                        contained=None
                        if all(len(c)==1 for c in missing):
                            clause=[-c[0] for c in missing]
                            if clause_set([clause],Counter())<=clause_set(target,Counter()):contained=clause
                        assert contained==data['contained_clause'];assert len(expected_children)==len(data['children'])
                        for a,b in zip(expected_children,data['children']):assert all(a[k]==b[k] for k in ('root','answer','model'))
                        check_composed(s,r);banks=study.history.banks(s,[r]);assert study.history.lookup(banks,r['source'])==check_composed(s,r)
                finally:s.close()
                cold=study.audit_records(path,[r],ps,prepared,catalogs,indices);assert cold['composed']['native']['lineage']==data['cold']['composed']['native']['lineage'];audits.append(dict(case=cid,mode=mode,cold=cold));decisions.append(r)
                for k,v in delta:
                    if k in union and union[k]!=v:assert base.load_json(union[k])['answer']==base.load_json(v)['answer'];alternates.append(dict(root_sha256=base.key_sha(k),delta=data['delta']))
                    union.setdefault(k,v)
        path=tmp/'union';s=study.ResidualSolver(path);rebuilt=[];direct=[]
        try:
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in preserved])
            assert study.rows(s)==union;s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_expand',side_effect=AssertionError('Union search')),patch.object(s,'_store',side_effect=AssertionError('Union publication')):
                for r in decisions:
                    target=r['source']
                    for g in r['guards']:_,target=check_guard(s,target,g)
                    if r['format']==study.history.PARTITION_FORMAT:
                        prefix=[list(c) for c in target];children=[]
                        for clause in r['missing_clauses']:
                            child=s.solve(restrict(prefix,{abs(l):l<0 for l in clause}));children.append(child);prefix.append(clause)
                            if child['answer']:break
                        rebuilt.append(study.history.partition_record(s,r['source'],r['guards'],r['missing_clauses'],r['stronger_root'],children))
                    else:rebuilt.append(study.history.chain_record(s,r['source'],r['guards'],s.solve(target)))
                for r in study.inherited(parent)+rebuilt:check_composed(s,r)
                for r in projections:study.check_projection(s,r)
                original=base.load('experiments/results/cnf-join-transfer/cases.json')
                for d in bound(parent['reference_decisions'])+bound(parent['model_rotation_decisions']):
                    source=d['source'] if 'source' in d else original[d['case']]['source'];child=s.solve(source);assert child['root']==d['root'] and child['answer']==d['answer'] and child['model']==(None if d['model'] is None else {int(k):v for k,v in d['model'].items()})
                    direct.append(dict(source=source,guard=None,witness=None,child=child,answer=child['answer'],model=child['model']))
        finally:s.close()
        ordinary=direct+sum((bound(parent[f]) for f in study.FIELDS),[]);inherited_audit=audit(path,ordinary);used=[(n,bound(parent[n])) for n in study.OLD_FIELDS];composed_audit=study.audit_records(path,study.inherited(parent)+rebuilt,projections,prepared,used,indices)
        if union==preserved:archive=parent['reference_union']
        else:dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest)
        base.write(out/'decisions.json',rebuilt);base.write(out/'projections.json',projections);checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=p['source_fingerprints'],conditioned_core_study=study.binding(out/'report.json'),conditioned_core_decisions=study.binding(out/'decisions.json'),conditioned_core_projections=study.binding(out/'projections.json'));base.write(out/'checkpoint.json',checkpoint)
        _,old_structural=restore_checkpoint(p['parent']['path'],tmp/'old-patterns');_,structural=restore_checkpoint(out/'checkpoint.json',tmp/'patterns');assert structural==old_structural;supplemental=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,checkpoint=study.binding(out/'checkpoint.json'),protocol=report['protocol'],report=study.binding(out/'report.json'),audits=audits,preserved_keys=len(preserved),union_keys=len(union),new_keys=len(union)-len(preserved),alternate_certificates=alternates,inherited_decisions=len(ordinary),inherited_composed=len(study.inherited(parent)),new_composed=len(rebuilt),projection_records=len(projections),inherited_audit=inherited_audit,composed_audit=composed_audit,structural=structural,supplemental=supplemental,seconds=time.perf_counter()-start)
    base.write(out/'reconstruction.json',result);print(base.encode({k:result[k] for k in ('passed','preserved_keys','union_keys','new_keys','inherited_decisions','inherited_composed','new_composed','projection_records','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
