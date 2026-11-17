#!/usr/bin/env python3
"""Price six pending alternative supports on exact historical query prefixes.

This is a post-hoc diagnostic, not a new policy or fresh coverage experiment.
Each arm starts with identical proof payloads and a cold live checker. Derivation
cannot call SAT search. Per-arm proof deltas retain every certificate without
duplicating the complete inherited database. The validator checks those deltas.
"""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_alternative_guard as study
from experiments.cnf_alternative_guard import AlternativeGuardSelector
from experiments.cnf_clause_deletion_guard import ExtensionBank,check_guard,clause_set,propose,lift
from experiments.cnf_clause_witness_reuse import reuse_witness
from experiments.cnf_proof_choice import ProofChoiceBank,compose,audit_portfolio
from experiments.cnf_unsat_support import CoreBank,checked_subset
from experiments.validate_cnf_unsat_support import bound
base=study.base
PARENT=Path('experiments/results/cnf-alternative-guard')
FILES=('experiments/probe_cnf_pending_guards.py','experiments/validate_cnf_pending_guards.py')


def install(solver,items):
    with solver.db:
        solver.db.executemany('INSERT INTO cnf_residual_v1 VALUES (?,?)',items)


def prefix(initial,final,records,case):
    """Only payloads appended strictly before the first visit to case are usable."""
    saved=dict(initial);by_hash={base.key_sha(k):k for k in final};seen=set()
    assert len(by_hash)==len(final) and initial.items()<=final.items()
    for row in records:
        if row['case']==case and row['visit']==0:return saved
        assert len(row['new_ids'])==row['new_nodes']
        for digest in row['new_ids']:
            key=by_hash[digest]
            assert key not in saved and key not in seen
            saved[key]=final[key];seen.add(key)
    raise ValueError('Missing first-visit query')


def prepare(s,source,protocol,indices):
    """Replay the normal first-target miss and bounded ready-only selector."""
    counts=Counter();bank=CoreBank(s,bound(protocol['cores']))
    extensions=ExtensionBank(bound(protocol['bank_catalog'])['bank'],counts)
    portfolio=ProofChoiceBank(s,indices['legacy'],indices['causal'])
    normalized,_,key=s._canonical(source);assert s._read(key,normalized) is None
    assert bank.reuse(source) is None and reuse_witness(s,extensions,source,counts) is None
    guard=propose(s,extensions,source,counts);assert guard is not None
    assignment,target=check_guard(s,source,guard,counts)
    normalized,_,key=s._canonical(target);assert s._read(key,normalized) is None
    assert portfolio.reuse(target) is None
    selector=AlternativeGuardSelector(1);chosen,trace=selector.select(s,extensions,source,guard,portfolio)
    assert chosen is None and len(trace['attempts'])==1 and trace['attempts'][0]['status']=='miss'
    return guard,assignment,target,trace,portfolio,dict(counts),dict(selector.counts)


def run(out):
    out.mkdir(exist_ok=False);started=time.perf_counter()
    parent=base.load(PARENT/'checkpoint.json');old=base.load(PARENT/'protocol.json')
    authority=bound(old['parent']);trial=base.load(PARENT/'alternative-0/report.json')
    records=bound(trial['queries']);diagnosis=base.load(PARENT/'cost-attribution.json')
    cases=diagnosis['pending_alternative_cases'];assert [r['case'] for r in cases]==[23,85,103]
    indices={n:bound(old[f]) for n,f in [('legacy','support_index'),('causal','causal_index')]}
    bindings=dict(legacy=old['support_index'],causal=old['causal_index']);prepared=compose(indices,bindings)
    catalogs=[(n,bound(e)) for n,e in zip(study.OLD_FIELDS,old['prior_decision_catalogs'])]
    sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    protocol=dict(parent=study.binding(PARENT/'checkpoint.json'),historical_protocol=study.binding(PARENT/'protocol.json'),
        historical_trial=study.binding(PARENT/'alternative-0/report.json'),diagnosis=study.binding(PARENT/'cost-attribution.json'),
        source_fingerprints=sources,cases=cases,
        limitations=['Post-hoc individual proof pricing on cases already retained in the parent checkpoint; no new coverage or deployable selection rule.',
            'Exact pre-query payload prefix, cold live checker for every arm. This does not reproduce warm in-stream caches or extractor memo tables.',
            'One sample per arm. Wall times are descriptive, not speedup evidence. Full cold proof/query and lineage audit, serialization, retained bytes and peak-state counts are reported separately.',
            'All six pending matches are tried individually, including dominated choices. Candidate identity comes from the prior diagnosis; no efficient cost oracle is assumed.',
            'Derivation, subset publication and repeated reuse disable fresh SAT search. Baseline deliberately allows the ordinary solver. Later stream interactions are not evaluated.'])
    base.write(out/'protocol.json',protocol);samples=[];prefixes=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td);base.restore_archive(authority['reference_union'],tmp/'initial')
        s=study.ResidualSolver(tmp/'initial')
        try:initial=study.rows(s)
        finally:s.close()
        base.restore_archive(trial['archive'],tmp/'final');s=study.ResidualSolver(tmp/'final')
        try:final=study.rows(s)
        finally:s.close()
        assert not trial['setup_ids']
        for case in cases:
            cid=case['case'];oldrow=next(r for r in records if r['case']==cid and r['visit']==0)
            saved=prefix(initial,final,records,cid);prefix_path=tmp/f'prefix-{cid}'
            shutil.copyfile(tmp/'initial',prefix_path);s=study.AccountedResidualSolver(prefix_path)
            try:install(s,[(k,v) for k,v in saved.items() if k not in initial]);assert study.rows(s)==saved
            finally:s.close()
            prefixes.append(dict(case=cid,nodes=len(saved),payload_units=sum(len(k)+len(v) for k,v in saved.items()),
                row_digest=base.key_sha(base.encode(sorted(saved.items())))))
            for match in [None]+case['matches']:
                label='baseline' if match is None else f"{match['bank']}-{match['index']}"
                dest=out/f'{cid}-{label}';dest.mkdir();path=tmp/'arm';shutil.copyfile(prefix_path,path)
                tick=time.perf_counter();s=study.AccountedResidualSolver(path);opened=time.perf_counter()-tick
                try:
                    tick=time.perf_counter();guard,assignment,target,trace,portfolio,recognition,selection=prepare(s,oldrow['source'],old,indices)
                    assert guard==oldrow['guard'] and trace==oldrow['guard_choice']
                    preparation_seconds=time.perf_counter()-tick;preparation_counts=dict(s.counts)
                    materialization={};materialization_counts={};materialization_seconds=0.;publication_seconds=0.;publication_counts={}
                    before_nodes=s.archive_storage()[0]
                    if match is not None:
                        bi=0 if match['bank']=='legacy' else 1;core=indices[match['bank']]['cores'][match['index']]
                        guard=trace['attempts'][0]['guard'];assignment,target=check_guard(s,oldrow['source'],guard)
                        assert clause_set(core['source'],Counter())<=clause_set(target,Counter())
                        small,_,root=s._canonical(core['source']);assert root==core['root'] and s._read(root,small) is None
                        with patch.object(s,'_expand',side_effect=AssertionError('Fresh support derivation search')):
                            before=Counter(s.counts);tick=time.perf_counter()
                            extractor=portfolio.banks[bi].extractor;derived=extractor.extract(core['origin'])
                            assert derived['root']==root and s._read(root,small)['answer'] is False
                            materialization_seconds=time.perf_counter()-tick;materialization_counts=dict(s.counts-before)
                            materialization=dict(extractor.counts)
                            tick=time.perf_counter();counts=Counter();inserted,target_root=checked_subset(s,target,core['source'],counts)
                            publication_seconds=time.perf_counter()-tick;publication_counts=dict(counts)
                            tick=time.perf_counter();child=s.solve(target);child_seconds=time.perf_counter()-tick
                        assert not child['answer'] and child['metrics'].get('expanded_nodes',0)==0
                    else:
                        tick=time.perf_counter();child=s.solve(target);child_seconds=time.perf_counter()-tick
                    assert child['answer']==oldrow['answer'] is False
                    if match is None:assert child['metrics']['expanded_nodes']==case['expansions']
                    row=dict(case=cid,visit=0,source=oldrow['source'],guard=guard,witness=None,child=child,answer=False,model=None)
                    after_first=study.rows(s);assert saved.items()<=after_first.items()
                    tick=time.perf_counter()
                    with patch.object(s,'_expand',side_effect=AssertionError('Fresh repeat search')):
                        if match is None:repeat=s.solve(target)
                        else:
                            fresh=ProofChoiceBank(s,indices['legacy'],indices['causal'])
                            hit=fresh.reuse(target);assert hit is not None and hit['choice']=='ready';repeat=s.solve(target)
                    repeat_seconds=time.perf_counter()-tick
                    assert not repeat['answer'] and study.rows(s)==after_first
                    delta=[(k,v) for k,v in after_first.items() if k not in saved]
                    retained=s.archive_storage();assert retained[0]-before_nodes==len(delta)
                finally:s.close()
                tick=time.perf_counter();base.write(dest/'delta.json',delta);base.write(dest/'queries.json',[row])
                serialization_seconds=time.perf_counter()-tick
                cold=audit_portfolio(path,[row],prepared,catalogs,indices)
                result=dict(case=cid,match=match,queries=study.binding(dest/'queries.json'),delta=study.binding(dest/'delta.json'),
                    prefix=prefixes[-1],new_nodes=len(delta),new_payload_units=sum(len(k)+len(v) for k,v in delta),
                    final_nodes=retained[0],final_payload_units=retained[1],delta_bytes=(dest/'delta.json').stat().st_size,
                    query_bytes=(dest/'queries.json').stat().st_size,open_seconds=opened,preparation_seconds=preparation_seconds,
                    materialization_seconds=materialization_seconds,publication_seconds=publication_seconds,child_seconds=child_seconds,repeat_seconds=repeat_seconds,
                    serialization_seconds=serialization_seconds,preparation_counts=preparation_counts,recognition_counts=recognition,
                    selection_counts=selection,materialization_counts=materialization_counts,extractor_counts=materialization,
                    publication_counts=publication_counts,child_metrics=child['metrics'],repeat_metrics=repeat['metrics'],cold=cold,
                    row_digest=base.key_sha(base.encode(sorted(after_first.items()))))
                base.write(dest/'report.json',result);samples.append(study.binding(dest/'report.json'))
                print(base.encode(dict(case=cid,arm=label,new_nodes=len(delta),expansions=child['metrics'].get('expanded_nodes',0),
                    materialization_nodes=materialization_counts.get('inserted_nodes',0),support_nodes=materialization.get('support_nodes',0))),flush=True)
    base.write(out/'report.json',dict(protocol=study.binding(out/'protocol.json'),samples=samples,prefixes=prefixes,seconds=time.perf_counter()-started))


if __name__=='__main__':run(Path(sys.argv[1]))
