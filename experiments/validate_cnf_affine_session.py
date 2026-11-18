#!/usr/bin/env python3
"""Chronological independent validation and preservation of affine session runs."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,json,shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_affine_session as study
from experiments.validate_cnf_affine_completion import expected,check_result
from experiments.validate_cnf_affine_negative import audit_counts
from experiments.cnf_affine_negative import TABLE,CHAIN,compile_proof,check_composed
from experiments.cnf_affine_session import TerminalStore
from experiments.cnf_clause_deletion_guard import check_guard,ExtensionBank
from experiments.validate_cnf_terminal_guard import check_selection
from experiments.validate_cnf_premise_guard import expected_choice
from experiments.cnf_guard_chain import make_record
from experiments.cnf_cross_family import truth_table
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
base=study.base;bound=study.bound


def ext_rows(s):return dict(s.db.execute(f'SELECT id,payload FROM {TABLE} ORDER BY id'))


def validate(out):
    began=time.perf_counter();report=base.load(out/'report.json');p=bound(report['protocol']);parent=bound(p['parent'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    sources=dict(p['source_fingerprints']);sources['experiments/validate_cnf_affine_session.py']=base.sha(__file__)
    oldv=base.load(study.PARENT/'validation.json');manifests=dict(oldv['parent_manifests'])
    path=study.PARENT/'manifest.json';manifests[str(path)]=dict(sha256=base.sha(path),artifacts_checked=len(base.load(path)['artifacts']))
    artifacts=0
    for name,entry in manifests.items():
        assert base.sha(name)==entry['sha256'],name
        m=base.load(name);assert len(m['artifacts'])==entry['artifacts_checked']
        for name,h in m['artifacts'].items():assert base.sha(name)==h,name
        artifacts+=len(m['artifacts'])
    assert artifacts==7399 and len(manifests)==103
    old=study.inherited(parent);catalog=bound(report['cases']);assert bound(p['previous_decisions'])==study.exclusions(parent)
    truth={c['case']:truth_table(c['source']) for c in catalog['cases'] if c['family']!='neighbour-control'}
    base.write(out/'truth.json',truth)
    collected=[];alternatives=[];audits=[];counts=Counter();by_mode={};answers=None
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);initial_path=tmp/'initial';base.restore_archive(parent['reference_union'],initial_path)
        s=study.native.ResidualSolver(initial_path)
        try:
            initial=study.native.rows(s);initial_ext=ext_rows(s)
            assert study.prior.inputs(s,p)==catalog
            keys={s._canonical(c['source'])[2] for c in catalog['cases']}
            assert len(keys)==60 and not keys&set(initial) and not keys&{r['query_root'] for r in old}
            _,_,indices,prepared,_=study.prep.setup(s,p)
        finally:s.close()
        assert len(initial)==26743 and len(initial_ext)==7
        union=dict(initial);extensions=dict(initial_ext)
        used=[(n,bound(parent[n])) for n in study.prior.OLD_FIELDS]
        assert [(e['repeat'],e['mode']) for e in report['samples']]==[(i,m) for i,order in enumerate(p['orders']) for m in order]
        for number,entry in enumerate(report['samples']):
            data=bound(entry);mode=entry['mode'];rows=bound(data['queries']);warm=bound(data['warm']);path=tmp/f'trial-{number}'
            base.restore_archive(data['archive'],path);s=SnapshotResidualSolver(path);store=TerminalStore(s)
            try:
                final=study.native.rows(s);ext=ext_rows(s);assert initial.items()<=final.items() and initial_ext.items()<=ext.items()
                available=set(map(base.key_sha,initial));ext_available=set(initial_ext);by_hash={base.key_sha(k):k for k in final}
                assert len(by_hash)==len(final) and len(rows)==len(warm)==60
                bank=ExtensionBank(bound(p['bank_catalog'])['bank'])
                for row,case,w in zip(rows,catalog['cases'],warm):
                    r=row['record'];assert row['case']==case['case']==w['case'] and r['source']==case['source']
                    ids=set(row['new_ids']);ordinary_ids=set(row['ordinary_ids']);near_ids=set(row['near_ids'])
                    assert len(ids)==row['new_nodes']==len(row['new_ids']) and not ids&available
                    assert not ordinary_ids&near_ids and ordinary_ids|near_ids<=ids
                    normal=dict(row['ordinary'],new_ids=row['new_ids'])
                    check_selection(s,bank,normal,prepared,available,'ready',p['alternative_budget'])
                    guards=[] if normal['guard'] is None else [normal['guard']]
                    target=case['source'] if not guards else check_guard(s,case['source'],guards[0])[1]
                    current=available|ordinary_ids;eligible=bool(guards) and not normal['target_known'] and normal['cofactor'] is None
                    assert eligible==row['near_eligible']
                    near=expected_choice(s,target,prepared['cores'],current,'premise-first') if eligible else None
                    assert near==row['near_choice']
                    if near:
                        g=r['guards'][len(guards)];assert g['stronger']==[list(c) for c in target]+[near['missing_clause']]
                        assert near_ids==({base.key_sha(g['stronger_root'])} if near['inserted'] else set())
                        _,target=check_guard(s,target,g);guards.append(g)
                    else:assert not near_ids
                    current|=near_ids;cnf,names,root=s._canonical(target);local=base.key_sha(root) not in current
                    assert row['familiarity']==dict(root=root,known_after_preparation=not local,guards=len(guards),variables=len(names),clauses=len(cnf),literals=sum(map(len,cnf)))
                    hit=mode=='session' and root in ext_available
                    assert row['extension_lookup_hit']==hit
                    if hit:
                        assert row['admission'] is None and row['local_choice'] is None and row['extension']
                        assert not row['child']['metrics'].get('affine_negative_inserted_nodes',0)
                    elif row['extension']:
                        assert mode=='session' and local
                        choice,trace=expected(s,target,4,{by_hash[h] for h in current},row['admission'])
                        assert choice==row['local_choice'] and trace==row['admission']
                        e=trace['affine_bridge'];assert e['status'] in ('linear-conflict','space-exhausted')
                        assert root not in ext_available and root in ext
                        node=json.loads(ext[root]);assert node['proof']==compile_proof(e)
                        audit_counts(e,row['child']['metrics']);counts['publication_counter_audits']+=1
                        if e['status']=='space-exhausted':assert row['child']['metrics']['affine_negative_packed_literals']==sum(len(cnf[cid]) for cid in set(e['rejected']))
                        assert row['child']['metrics'].get('expanded_nodes',0)==0
                        assert row['child']['metrics']['affine_negative_inserted_nodes']==1
                        ext_available.add(root)
                    if row['extension']:
                        assert r['format']==CHAIN and r['guards']==guards and r['child']['root']==root and row['premise'] is None
                        assert row['new_nodes']==len(ordinary_ids)+len(near_ids)
                        got=check_composed(store,r)
                    else:
                        assert not hit
                        got=check_result(s,row,target,guards,'affine',local,4,{by_hash[h] for h in current})
                        assert row['new_nodes']==len(ordinary_ids)+len(near_ids)+sum(c['metrics'].get('inserted_nodes',0) for c in (row['child'],row['premise']) if c)
                    if mode=='session':
                        metrics=row['extension_lookup_metrics'];assert metrics.get('affine_negative_database_lookups',0)+metrics.get('affine_negative_memory_hits',0)==1
                    if case['case'] in truth:assert got['answer']==truth[case['case']]['answer']
                    assert base.load_json(base.encode(got))==w['result']
                    counts['query_audits']+=1;available.update(ids)
                assert available==set(by_hash) and ext_available==set(ext)
                summary=data['summary'];assert all(summary[k]==v for k,v in study.summarize(rows).items())
                assert summary['new_nodes']==len(final)-len(initial)==sum(r['new_nodes'] for r in rows)
                assert summary['new_payload_units']==sum(len(k)+len(v) for k,v in final.items() if k not in initial)
                assert summary['new_extension_nodes']==len(ext)-len(initial_ext)
                assert summary['new_extension_bytes']==sum(len(k)+len(v) for k,v in ext.items() if k not in initial_ext)
                assert data['cold']['extension']['metrics'].get('chain_child_disk_hits',0)==0
                current_answers=[r['record']['answer'] for r in rows]
                if answers is None:answers=current_answers
                else:assert answers==current_answers
                if mode in by_mode:assert (final,ext)==by_mode[mode]
                else:by_mode[mode]=(final,ext)
                if entry['repeat']==0:collected.extend(r['record'] for r in rows)
            finally:s.close()
            # Replay all legacy, projection and versioned chain evidence anew.
            cold=study.audit_records(path,old+[r['record'] for r in rows],bound(parent['conditioned_core_projections']),prepared,used,indices)
            audits.append(dict(mode=mode,repeat=entry['repeat'],cold=cold))
            for key,value in final.items():
                if key in union and union[key]!=value:alternatives.append(dict(archive=data['archive'],root_sha256=base.key_sha(key)))
                union.setdefault(key,value)
            for key,value in ext.items():
                if key in extensions:assert extensions[key]==value
                extensions.setdefault(key,value)
        path=tmp/'union';shutil.copyfile(initial_path,path);s=study.native.ResidualSolver(path);store=TerminalStore(s)
        try:
            with s.db:
                s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in initial])
                s.db.executemany(f'INSERT INTO {TABLE} VALUES (?,?)',[(k,v) for k,v in extensions.items() if k not in initial_ext])
            assert study.native.rows(s)==union and ext_rows(s)==extensions
            s.db.execute('PRAGMA query_only=ON');new_native=[];new_negative=[]
            with patch.object(s,'_expand',side_effect=AssertionError('Union search')),patch.object(s,'_store',side_effect=AssertionError('Union write')):
                for r in collected:
                    if r['format']==CHAIN:check_composed(store,r);new_negative.append(r)
                    else:
                        target=r['source']
                        for g in r['guards']:_,target=check_guard(s,target,g)
                        new_native.append(make_record(s,r['source'],r['guards'],s.solve(target)))
                for root in extensions:assert store.read(root) is not None
        finally:s.close()
        cold=study.audit_records(path,old+new_native+new_negative,bound(parent['conditioned_core_projections']),prepared,used,indices)
        dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest)
    base.write(out/'native-decisions.json',bound(parent['affine_completion_decisions'])+new_native)
    base.write(out/'negative-decisions.json',bound(parent['affine_negative_decisions'])+new_negative)
    base.write(out/'new-decisions.json',new_native+new_negative)
    checkpoint=copy.deepcopy(parent)
    checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=sources,
        affine_completion_decisions=study.binding(out/'native-decisions.json'),affine_negative_decisions=study.binding(out/'negative-decisions.json'),
        affine_session_study=study.binding(out/'report.json'),affine_session_reader='experiments.cnf_affine_session.TerminalStore')
    base.write(out/'checkpoint.json',checkpoint)
    result=dict(passed=True,source_fingerprints=sources,parent_manifests=manifests,prior_artifacts_unchanged=artifacts,
        native_preserved=len(initial),native_union=len(union),extension_preserved=len(initial_ext),extension_union=len(extensions),
        new_native_records=len(new_native),new_negative_records=len(new_negative),inherited_records=len(old),
        counter_audits=dict(counts),audits=audits,union_cold=cold,alternative_native_occurrences=alternatives,
        checkpoint=study.binding(out/'checkpoint.json'),seconds=time.perf_counter()-began)
    base.write(out/'validation.json',result)
    print(base.encode({k:result[k] for k in ('passed','native_union','extension_union','new_native_records','new_negative_records','counter_audits','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
