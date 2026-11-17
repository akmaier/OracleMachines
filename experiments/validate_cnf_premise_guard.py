#!/usr/bin/env python3
"""Check fresh exclusions, pre-query guard choices, all proofs and chain history."""
from pathlib import Path
from collections import Counter
from unittest.mock import patch
import copy,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_premise_guard as study
from experiments.cnf_clause_deletion_guard import clause_set,check_guard,ExtensionBank
from experiments.cnf_residual_dag import restrict
from experiments.cnf_guard_chain import check_record,make_record,GuardChainBank
from experiments.validate_cnf_guard_chain import independent_chain
from experiments.validate_cnf_terminal_guard import check_selection
from experiments.validate_cnf_unsat_support import bound
from experiments.cnf_snapshot_replay import audit,SnapshotResidualSolver
from experiments.validate_cnf_bootstrap import restore_checkpoint
from experiments.check_cnf_supplemental_queries import check as check_supplement
base=study.base


def expected_choice(s,target,cores,available,mode):
    if mode=='plain':return None
    members=clause_set(target,Counter());variables={abs(l) for c in members for l in c}
    def read(source):
        cnf,_,key=s._canonical(source)
        return key,(s._read(key,cnf) if base.key_sha(key) in available else None)
    for i,core in enumerate(cores):
        wanted=clause_set(core['source'],Counter());missing=wanted-members
        if not wanted&members or len(missing)!=1:continue
        clause=next(iter(missing))
        if not clause or not {abs(l) for l in clause}<=variables:continue
        if clause_set(restrict(target,{abs(l):l<0 for l in clause}),Counter())==members:continue
        stronger=[list(c) for c in target]+[list(clause)];key,premise=read(stronger)
        if mode=='premise-first' and premise is not None:
            if premise['answer'] is not False:continue
            return dict(core=i,missing_clause=list(clause),path='known-premise',inserted=False)
        root,node=read(core['source']);assert root==core['root']
        if node is None:continue
        assert node['answer'] is False
        return dict(core=i,missing_clause=list(clause),path='core-first' if mode=='core-first' else 'checked-core',inserted=premise is None)
    return None


def validate(out):
    started=time.perf_counter();report=base.load(out/'report.json');p=bound(report['protocol']);catalog=bound(report['cases']);parent=bound(p['parent'])
    for f,h in p['source_fingerprints'].items():assert base.sha(f)==h,f
    ordinary=sum((bound(parent[f]) for f in study.FIELDS),[]);inherited_chains=bound(parent['guard_chain_decisions'])
    assert bound(p['previous_decisions'])==ordinary+inherited_chains
    assert p['prior_decision_catalogs']==[parent[f] for f in study.FIELDS]
    bindings=dict(legacy=p['support_index'],causal=p['causal_index']);indices={n:bound(e) for n,e in bindings.items()};prepared=study.ordinary.compose(indices,bindings);cores=prepared['cores']
    used=[(n,bound(parent[n])) for n in study.OLD_FIELDS];audits=[];decisions=None;answers=None;alternates=[];by_mode={}
    assert [(e['repeat'],e['mode']) for e in report['samples']]==[(i,m) for i,order in enumerate(p['orders']) for m in order]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);base.restore_archive(parent['reference_union'],tmp/'initial');s=study.ResidualSolver(tmp/'initial')
        try:
            initial=study.rows(s);assert study.ordinary.eager.previous.inputs(s,p)==catalog
            assert not ({s._canonical(c['source'])[2] for c in catalog['cases']}&{r['query_root'] for r in ordinary+inherited_chains})
        finally:s.close()
        union=dict(initial)
        for num,entry in enumerate(report['samples']):
            data=bound(entry);mode=entry['mode'];records=bound(data['queries']);warm=bound(data['warm']);path=tmp/f'trial-{num}';base.restore_archive(data['archive'],path);s=SnapshotResidualSolver(path)
            try:
                final=study.rows(s);assert initial.items()<=final.items();available=set(map(base.key_sha,initial));by_hash={base.key_sha(k):k for k in final};assert len(by_hash)==len(final)
                assert data['summary']['row_digest']==base.key_sha(base.encode(sorted(final.items())))
                assert len(records)==len(warm)==len(catalog['cases'])==192
                extensions=ExtensionBank(bound(p['bank_catalog'])['bank'])
                for row,case,w in zip(records,catalog['cases'],warm):
                    assert row['case']==case['case']==w['case'] and row['template_case']==case['template_case'] and row['chain']['source']==case['source']
                    ids=row['new_ids'];assert len(ids)==row['new_nodes']==len(set(ids)) and not available.intersection(ids)
                    assert set(row['early_ids'])<=set(ids)
                    normal=dict(row['ordinary'],new_ids=ids);assert normal['source']==case['source']
                    check_selection(s,extensions,normal,prepared,available,'ready',p['alternative_budget'])
                    guards=[] if normal['guard'] is None else [normal['guard']]
                    target=case['source'] if not guards else check_guard(s,case['source'],guards[0])[1]
                    current=available|set(row['early_ids']);key=s._canonical(target)[2];members=clause_set(target,Counter())
                    eligible=bool(guards) and base.key_sha(key) not in current and not any(clause_set(c['source'],Counter())<=members for c in cores)
                    assert eligible==row['eligible']
                    choice=expected_choice(s,target,cores,current,mode) if eligible else None;assert choice==row['choice']
                    assert len(row['chain']['guards'])==len(guards)+int(choice is not None)
                    if choice:
                        extra=row['chain']['guards'][-1];assert extra['stronger']==[list(c) for c in target]+[choice['missing_clause']]
                        assert extra['removed_clause']==choice['missing_clause'];guards.append(extra)
                        assert choice['inserted']==(base.key_sha(extra['stronger_root']) not in current)
                    assert guards==row['chain']['guards'];assert check_record(s,row['chain'])==independent_chain(s,row['chain'])
                    got=GuardChainBank(s,[row['chain']]).lookup(case['source']);assert base.load_json(base.encode(got))==w['result']
                    available.update(ids)
                assert available==set(by_hash)
                summary=data['summary'];assert summary['new_nodes']==len(final)-len(initial)==sum(r['new_nodes'] for r in records)
                assert summary['new_payload_units']==sum(len(k)+len(v) for k,v in final.items() if k not in initial)
                assert summary['expanded_nodes']==sum(r['child_metrics'].get('expanded_nodes',0) for r in records)
                truth=[r['chain']['answer'] for r in records]
                if answers is None:answers=truth
                else:assert answers==truth
                if mode in by_mode:assert final==by_mode[mode]
                else:by_mode[mode]=final
                if mode=='premise-first' and decisions is None:decisions=[r['chain'] for r in records]
            finally:s.close()
            cold=study.prior.audit_chain(path,[r['chain'] for r in records]+inherited_chains,prepared,used,indices);audits.append(dict(mode=mode,repeat=entry['repeat'],cold=cold))
            for k,v in final.items():
                if k in union and union[k]!=v:
                    assert base.load_json(union[k])['answer']==base.load_json(v)['answer'];alternates.append(dict(root_sha256=base.key_sha(k),archive=data['archive']))
                union.setdefault(k,v)
        # Preserve prior native payloads; retained per-trial archives keep all alternatives.
        base.restore_archive(parent['reference_union'],tmp/'union');s=study.ResidualSolver(tmp/'union');direct=[];rebuilt=[]
        try:
            with s.db:s.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',[(k,v) for k,v in union.items() if k not in initial])
            assert study.rows(s)==union and initial.items()<=union.items();s.db.execute('PRAGMA query_only=ON')
            with patch.object(s,'_expand',side_effect=AssertionError('Union search')),patch.object(s,'_store',side_effect=AssertionError('Union publication')):
                for r in decisions:
                    target=r['source']
                    for g in r['guards']:_,target=check_guard(s,target,g)
                    rebuilt.append(make_record(s,r['source'],r['guards'],s.solve(target)))
                for r in inherited_chains:assert check_record(s,r)==independent_chain(s,r)
                original=base.load('experiments/results/cnf-join-transfer/cases.json')
                for d in bound(parent['reference_decisions'])+bound(parent['model_rotation_decisions']):
                    source=d['source'] if 'source' in d else original[d['case']]['source'];child=s.solve(source)
                    assert child['root']==d['root'] and child['answer']==d['answer'];assert child['model']==(None if d['model'] is None else {int(k):v for k,v in d['model'].items()})
                    direct.append(dict(source=source,guard=None,witness=None,child=child,answer=child['answer'],model=child['model']))
        finally:s.close()
        inherited_audit=audit(tmp/'union',direct+ordinary);chain_audit=study.prior.audit_chain(tmp/'union',inherited_chains+rebuilt,prepared,used,indices)
        dest=out/'reference-union';dest.mkdir();archive=base.archive(tmp/'union',dest);base.write(out/'union-chains.json',rebuilt)
        checkpoint=copy.deepcopy(parent);checkpoint.update(parent_checkpoint=p['parent'],reference_union=archive,source_fingerprints=p['source_fingerprints'],premise_guard_study=study.binding(out/'report.json'),premise_guard_chain_decisions=study.binding(out/'union-chains.json'))
        base.write(out/'checkpoint.json',checkpoint);_,old_structural=restore_checkpoint(p['parent']['path'],tmp/'old-patterns');_,structural=restore_checkpoint(out/'checkpoint.json',tmp/'patterns');assert structural==old_structural
        supplemental=check_supplement(out/'checkpoint.json')
    result=dict(passed=True,protocol=report['protocol'],report=study.binding(out/'report.json'),checkpoint=study.binding(out/'checkpoint.json'),audits=audits,
        preserved_keys=len(initial),union_keys=len(union),new_keys=len(union)-len(initial),alternate_certificate_occurrences=alternates,
        inherited_decisions=len(direct)+len(ordinary),inherited_chains=len(inherited_chains),new_chain_decisions=len(rebuilt),inherited_audit=inherited_audit,chain_audit=chain_audit,structural=structural,supplemental=supplemental,seconds=time.perf_counter()-started)
    base.write(out/'reconstruction.json',result);print(base.encode({k:result[k] for k in ('passed','preserved_keys','union_keys','new_keys','inherited_decisions','inherited_chains','new_chain_decisions','seconds')}),flush=True)


if __name__=='__main__':validate(Path(sys.argv[1]))
