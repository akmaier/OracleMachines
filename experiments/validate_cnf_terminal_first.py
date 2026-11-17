#!/usr/bin/env python3
"""Independently check terminal short-circuiting, exact prefixes and retained proofs."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_terminal_first as study
from experiments.validate_cnf_partition_screen import expected_screen,check_composed
from experiments.cnf_residual_dag import propagate,restrict
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.validate_cnf_unsat_support import bound
from experiments.cnf_snapshot_replay import audit
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
base=study.base


def expected_terminal(s,target,cores,available,p):
    if not p['plan_limit'] or not p['core_read_limit']:return expected_screen(s,target,cores,available,p)
    cnf,_,root=s._canonical(target);fixed,trace,conflict=propagate(cnf,Counter())
    if conflict is not None:
        return None,dict(attempts=[],selected=None,core_checks=[],baseline=dict(root=root,trace=trace,conflict=conflict,residual_literals=0),terminal=True)
    plan,record=expected_screen(s,target,cores,available,p);record['terminal']=False;return plan,record


def validate(out):
    start=time.perf_counter();report=base.load(out/'report.json');p=bound(report['protocol']);parent=bound(p['parent'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    samples=[bound(e) for e in report['samples']];assert [(r['cohort'],r['case'],r['mode']) for r in samples]==[(c['name'],i,m) for c in p['cohorts'] for i in c['cases'] for m in p['modes']]
    old_controls=[bound(e) for e in bound(parent['partition_screen_controls'])['samples']];prior_trial=bound(next(e for e in bound(parent['partition_screen_study'])['samples'] if e['mode']=='screened' and e['repeat']==0));prior_rows=bound(prior_trial['queries'])
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=study.ResidualSolver(path)
            try:return study.rows(s)
            finally:s.close()
        preserved=read(parent['reference_union'],'union');union=dict(preserved);prior_native=read(prior_trial['archive'],'previous-trial');audits=[];decisions=[];alternates=[]
        for cohort in p['cohorts']:
            hp=bound(cohort['protocol']);authority=bound(hp['parent']);trial=bound(cohort['trial']);records=bound(trial['queries']);initial=read(authority['reference_union'],'initial');final=read(trial['archive'],'final');prefixes=study.previous.partition_study.prefixes(initial,final,records)
            bindings=dict(legacy=hp['support_index'],causal=hp['causal_index']);indices={n:bound(e) for n,e in bindings.items()};prepared=study.previous.previous.ordinary.compose(indices,bindings);catalogs=[(n,bound(authority[n])) for n in study.OLD_FIELDS]
            for cid in cohort['cases']:
                before=prefixes[cid];old=next(r for r in records if r['case']==cid);original=old.get('record',old.get('chain'));paired={}
                for data in (r for r in samples if r['cohort']==cohort['name'] and r['case']==cid):
                    mode=data['mode'];delta=bound(data['delta']);saved=dict(before);assert data['prefix_nodes']==len(before) and data['prefix_digest']==base.key_sha(base.encode(sorted(before.items())))
                    for k,v in delta:assert k not in saved;saved[k]=v
                    rs=bound(data['records']);assert len(rs)==1;r=rs[0];assert r['source']==original['source'] and r['guards']==original['guards'] and r['answer']==original['answer']
                    assert data['new_nodes']==len(delta)==int(data['premise_inserted'])+sum(c['metrics'].get('inserted_nodes',0) for c in data['children']);assert data['new_payload_units']==sum(len(k)+len(v) for k,v in delta)
                    for field,metric in [('expanded_nodes','expanded_nodes'),('trace_publications','screen_trace_publications')]:assert data[field]==sum(c['metrics'].get(metric,0) for c in data['children'])
                    path=tmp/'arm';base.restore_archive(authority['reference_union'],path);s=study.ResidualSolver(path)
                    try:
                        with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in saved.items() if k not in initial])
                        s.db.execute('PRAGMA query_only=ON')
                        with patch.object(s,'_expand',side_effect=AssertionError('Validation search')),patch.object(s,'_store',side_effect=AssertionError('Validation publication')):
                            target=r['source']
                            for guard in r['guards']:assert guard['stronger_root'] in before;_,target=check_guard(s,target,guard)
                            expected=(expected_screen if mode=='screened' else expected_terminal)(s,target,prepared['cores'],set(map(base.key_sha,before)),p)
                            assert (data['plan'],data['screen'])==expected
                            terminal=mode=='terminal-first' and data['screen'].get('terminal',False);assert terminal==data['terminal']
                            if data['plan']:
                                assert r['format']==study.previous.PARTITION_FORMAT and r['missing_clauses']==data['plan']['missing'];assert data['premise_inserted']==(r['stronger_root'] not in before)
                                children=r['children']
                            else:assert r['format']!=study.previous.PARTITION_FORMAT and not data['premise_inserted'];children=[r['child']]
                            if terminal:
                                assert data['screen']['attempts']==[] and data['screen']['core_checks']==[]
                                assert data['screen_counts'].get('screen_posting_visits',0)==data['screen_counts'].get('screen_plans',0)==0
                                assert children[0]['root']==data['screen']['baseline']['root'] and children[0]['answer'] is False
                            assert len(children)==len(data['children'])
                            for a,b in zip(children,data['children']):assert all(a[k]==b[k] for k in ('root','answer','model'))
                            check_composed(s,r);retained=study.previous.banks(s,[r]);assert study.previous.lookup(retained,r['source'])==check_composed(s,r)
                    finally:s.close()
                    cold=study.previous.audit_records(path,[r],prepared,catalogs,indices);assert cold['native']['lineage']==data['cold']['native']['lineage'];audits.append(dict(cohort=cohort['name'],case=cid,mode=mode,cold=cold));paired[mode]=(data,delta,r);decisions.append(r)
                    for k,v in delta:
                        if k in union and union[k]!=v:assert base.load_json(union[k])['answer']==base.load_json(v)['answer'];alternates.append(dict(root_sha256=base.key_sha(k),delta=data['delta']))
                        union.setdefault(k,v)
                a,da,ra=paired['screened'];b,db,rb=paired['terminal-first']
                if cohort['name']=='older':
                    expected=next(r for r in old_controls if r['case']==cid and r['mode']=='screened');assert dict(da)==dict(bound(expected['delta'])) and ra==bound(expected['records'])[0]
                    assert da==db and ra==rb and a['plan']==b['plan'];assert a['screen']=={k:v for k,v in b['screen'].items() if k!='terminal'} and a['screen_counts']==b['screen_counts']
                else:
                    previous_row=next(r for r in prior_rows if r['case']==cid);previous_delta={k:v for k,v in prior_native.items() if base.key_sha(k) in previous_row['new_ids']};assert dict(da)==previous_delta and ra==previous_row['record']
                    assert dict(db)=={k:v for k,v in final.items() if base.key_sha(k) in old['new_ids']} and rb==original
                    assert b['terminal'] and b['new_nodes']==1 and a['new_nodes']==3
        path=tmp/'union';s=study.ResidualSolver(path);direct=[]
        try:
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in preserved])
            assert study.rows(s)==union;s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_expand',side_effect=AssertionError('Union search')),patch.object(s,'_store',side_effect=AssertionError('Union publication')):
                for r in study.inherited(parent)+decisions:check_composed(s,r)
                original=base.load('experiments/results/cnf-join-transfer/cases.json')
                for d in bound(parent['reference_decisions'])+bound(parent['model_rotation_decisions']):
                    source=d['source'] if 'source' in d else original[d['case']]['source'];child=s.solve(source);assert child['root']==d['root'] and child['answer']==d['answer'] and child['model']==(None if d['model'] is None else {int(k):v for k,v in d['model'].items()})
                    direct.append(dict(source=source,guard=None,witness=None,child=child,answer=child['answer'],model=child['model']))
        finally:s.close()
        ordinary=direct+sum((bound(parent[f]) for f in study.FIELDS),[]);inherited_audit=audit(path,ordinary)
        hp=bound(p['cohorts'][-1]['protocol']);bindings=dict(legacy=hp['support_index'],causal=hp['causal_index']);indices={n:bound(e) for n,e in bindings.items()};prepared=study.previous.previous.ordinary.compose(indices,bindings);catalogs=[(n,bound(parent[n])) for n in study.OLD_FIELDS]
        composed=study.inherited(parent)+decisions;composed_audit=study.previous.audit_records(path,composed,prepared,catalogs,indices)
        if union==preserved:archive=parent['reference_union']
        else:dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest)
        base.write(out/'decisions.json',decisions);checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=p['source_fingerprints'],terminal_first_study=study.binding(out/'report.json'),terminal_first_decisions=study.binding(out/'decisions.json'));base.write(out/'checkpoint.json',checkpoint)
        _,old_structural=restore_checkpoint(p['parent']['path'],tmp/'old-patterns');_,structural=restore_checkpoint(out/'checkpoint.json',tmp/'patterns');assert structural==old_structural;supplemental=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,checkpoint=study.binding(out/'checkpoint.json'),protocol=report['protocol'],report=study.binding(out/'report.json'),audits=audits,preserved_keys=len(preserved),union_keys=len(union),new_keys=len(union)-len(preserved),archive_reused=union==preserved,alternate_certificates=alternates,inherited_decisions=len(ordinary),inherited_composed=len(study.inherited(parent)),new_composed=len(decisions),inherited_audit=inherited_audit,composed_audit=composed_audit,structural=structural,supplemental=supplemental,seconds=time.perf_counter()-start)
    base.write(out/'reconstruction.json',result);print(base.encode({k:result[k] for k in ('passed','preserved_keys','union_keys','new_keys','archive_reused','inherited_decisions','inherited_composed','new_composed','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
