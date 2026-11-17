#!/usr/bin/env python3
"""Independently reconstruct prefixes/deltas, cold-check proofs, preserve union."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import copy,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_alternative_guard as study
from experiments.cnf_clause_deletion_guard import check_guard,clause_set
from experiments.cnf_proof_choice import compose,audit_portfolio
from experiments.cnf_snapshot_replay import audit
from experiments.validate_cnf_unsat_support import bound
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
base=study.base


def validate(out):
    tick=time.perf_counter();report=base.load(out/'report.json');protocol=bound(report['protocol'])
    for f,h in protocol['source_fingerprints'].items():assert base.sha(f)==h,f
    parent=bound(protocol['parent']);old=bound(protocol['historical_protocol']);trial=bound(protocol['historical_trial'])
    diagnosis=bound(protocol['diagnosis']);assert protocol['cases']==diagnosis['pending_alternative_cases']
    original=bound(old['parent']);records=bound(trial['queries']);assert not trial['setup_ids']
    indices={n:bound(old[f]) for n,f in [('legacy','support_index'),('causal','causal_index')]}
    prepared=compose(indices,dict(legacy=old['support_index'],causal=old['causal_index']))
    catalogs=[(n,bound(e)) for n,e in zip(study.OLD_FIELDS,old['prior_decision_catalogs'])]
    audits=[];alternates=[];probe_rows=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read_archive(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=study.ResidualSolver(path)
            try:return study.rows(s)
            finally:s.close()
        initial=read_archive(original['reference_union'],'initial')
        historical=read_archive(trial['archive'],'historical');by_hash={base.key_sha(k):k for k in historical}
        assert initial.items()<=historical.items() and len(by_hash)==len(historical)
        preserved=read_archive(parent['reference_union'],'union');union=dict(preserved)
        prefix=dict(initial);prefixes={};selected={r['case'] for r in protocol['cases']}
        for row in records:
            if row['visit']==0 and row['case'] in selected:prefixes[row['case']]=dict(prefix)
            assert len(row['new_ids'])==row['new_nodes'] and len(set(row['new_ids']))==row['new_nodes']
            for digest in row['new_ids']:
                k=by_hash[digest];assert k not in prefix;prefix[k]=historical[k]
        assert prefix==historical
        expected=[(r['case'],m) for r in protocol['cases'] for m in [None]+r['matches']]
        assert len(report['samples'])==len(expected)==9
        for entry,(cid,match) in zip(report['samples'],expected):
            data=bound(entry);assert (data['case'],data['match'])==(cid,match)
            before=prefixes[cid];saved=dict(before);delta=bound(data['delta']);rows=bound(data['queries']);assert len(rows)==1
            row=rows[0];oldrow=next(r for r in records if r['case']==cid and r['visit']==0)
            assert row['case']==cid and row['source']==oldrow['source'] and row['answer'] is False
            assert data['prefix']==dict(case=cid,nodes=len(before),payload_units=sum(len(k)+len(v) for k,v in before.items()),row_digest=base.key_sha(base.encode(sorted(before.items()))))
            for k,v in delta:assert k not in saved;saved[k]=v
            assert data['new_nodes']==len(delta) and data['new_payload_units']==sum(len(k)+len(v) for k,v in delta)
            assert data['final_nodes']==len(saved) and data['final_payload_units']==sum(len(k)+len(v) for k,v in saved.items())
            assert data['row_digest']==base.key_sha(base.encode(sorted(saved.items())))
            path=tmp/'arm';base.restore_archive(original['reference_union'],path);s=study.ResidualSolver(path)
            try:
                with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in saved.items() if k not in initial])
                s.db.execute('PRAGMA query_only=ON')
                with patch.object(s,'_expand',side_effect=AssertionError('Fresh validation search')),patch.object(s,'_store',side_effect=AssertionError('Validation publication')):
                    _,target=check_guard(s,row['source'],row['guard']);assert row['child']['root']==s._canonical(target)[2]
                    assert row['child']['metrics']==data['child_metrics'] and not data['repeat_metrics'].get('expanded_nodes',0)
                    if match is None:
                        assert row['guard']==oldrow['guard']
                        assert set(map(base.key_sha,dict(delta)))==set(oldrow['new_ids'])
                        assert all(historical[k]==v for k,v in delta)
                        assert data['child_metrics']['expanded_nodes']==oldrow['child']['metrics']['expanded_nodes']
                    else:
                        assert row['guard']==oldrow['guard_choice']['attempts'][0]['guard']
                        core=indices[match['bank']]['cores'][match['index']]
                        assert core['root'] not in before and core['origin'] in before
                        assert clause_set(core['source'],Counter())<=clause_set(target,Counter())
                        small,_,key=s._canonical(core['source']);assert key==core['root']
                        assert s._read(key,small)['answer'] is False and s._read(row['child']['root'])['answer'] is False
                        assert not data['child_metrics'].get('expanded_nodes',0) and not data['materialization_counts'].get('expanded_nodes',0)
                        assert data['new_nodes']==data['materialization_counts'].get('inserted_nodes',0)+data['publication_counts'].get('support_publications',0)
            finally:s.close()
            cold=audit_portfolio(path,rows,prepared,catalogs,indices)
            assert cold['query_answers']==[False] and cold['lineage']==data['cold']['lineage']
            audits.append(dict(case=cid,match=match,cold=cold));probe_rows+=rows
            for k,v in delta:
                if k in union and union[k]!=v:
                    assert base.load_json(union[k])['answer']==base.load_json(v)['answer']
                    alternates.append(dict(root_sha256=base.key_sha(k),delta=data['delta']))
                union.setdefault(k,v)
        path=tmp/'union';s=study.ResidualSolver(path)
        try:
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in preserved])
            assert study.rows(s)==union and preserved.items()<=union.items()
        finally:s.close()
        # All inherited result catalogs remain authoritative; no fresh decisions
        # are claimed for this diagnostic's already-known source formulas.
        inherited=[]
        for field in study.FIELDS+('alternative_guard_decisions',):inherited+=bound(parent[field])
        direct=bound(parent['reference_decisions'])+bound(parent['model_rotation_decisions'])
        originals=base.load('experiments/results/cnf-join-transfer/cases.json');s=study.ResidualSolver(path)
        try:
            s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_expand',side_effect=AssertionError('Fresh inherited decision search')):
                for d in direct:
                    source=d['source'] if 'source' in d else originals[d['case']]['source'];child=s.solve(source)
                    assert child['root']==d['root'] and child['answer']==d['answer']
                    assert child['model']==(None if d['model'] is None else {int(k):v for k,v in d['model'].items()})
                    inherited.append(dict(case=d['case'],source=source,guard=None,witness=None,child=child,answer=child['answer'],model=child['model']))
        finally:s.close()
        union_audit=audit(path,inherited+probe_rows)
        dest=out/'reference-union';dest.mkdir();archive=base.archive(path,dest)
        _,structural=restore_checkpoint(protocol['parent']['path'],tmp/'patterns')
        checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=protocol['parent'],reference_union=archive,
            source_fingerprints=protocol['source_fingerprints'],pending_guard_probe=study.binding(out/'report.json'))
        base.write(out/'checkpoint.json',checkpoint)
        _,current=restore_checkpoint(out/'checkpoint.json',tmp/'current');assert current==structural
        supplement=check_supplement(out/'checkpoint.json')
    reconstruction=dict(passed=True,protocol=report['protocol'],report=study.binding(out/'report.json'),
        checkpoint=study.binding(out/'checkpoint.json'),preserved_keys=len(preserved),union_keys=len(union),new_keys=len(union)-len(preserved),
        alternate_certificate_occurrences=alternates,inherited_decisions=len(inherited),diagnostic_replays=len(probe_rows),audits=audits,
        union_audit=union_audit,structural=structural,supplemental=supplement,seconds=time.perf_counter()-tick,
        limitations=['All previous payloads and semantic checkpoint fields are preserved. New support proofs extend the durable union; no fresh source-query coverage is claimed.',
            'Every per-arm delta retains its exact certificate, including any alternate certificate excluded by the old-payload-wins union. Reconstruct using the bound initial archive, historical append prefix and delta.',
            'Full independent proof/query replay and both historical index lineages run with fresh SAT search disabled. Original and supplemental structural authority stay separate.'])
    base.write(out/'reconstruction.json',reconstruction)
    print(base.encode({k:reconstruction[k] for k in ('passed','preserved_keys','union_keys','new_keys','inherited_decisions','diagnostic_replays','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
