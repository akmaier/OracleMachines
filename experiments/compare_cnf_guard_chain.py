#!/usr/bin/env python3
"""Controlled historical pricing of one extra checked missing-clause guard."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import shutil,sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_terminal_guard as previous
from experiments import probe_cnf_pending_guards as prefix_tools
from experiments.cnf_accounted_residuals import AccountedResidualSolver
from experiments.cnf_proof_choice import compose,audit_portfolio
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.cnf_guard_chain import propose_missing_clause,publish_guard,make_record,check_record,GuardChainBank
from experiments.validate_cnf_unsat_support import bound
base=previous.base;binding=previous.binding;rows=previous.rows;ResidualSolver=previous.ResidualSolver
PARENT=Path('experiments/results/cnf-terminal-guard')
FIELDS=previous.FIELDS+('terminal_guard_decisions',);OLD_FIELDS=previous.OLD_FIELDS
FILES=('experiments/cnf_guard_chain.py','solver/test_cnf_guard_chain.py','experiments/compare_cnf_guard_chain.py','experiments/validate_cnf_guard_chain.py')


def audit_chain(path,records,prepared,catalogs,indices):
    tick=time.perf_counter();native=audit_portfolio(path,[],prepared,catalogs,indices)
    started=time.perf_counter();s=SnapshotResidualSolver(path)
    try:
        answers=[check_record(s,r)['answer'] for r in records]
        bank=GuardChainBank(s,records)
        assert [bank.lookup(r['source'])['answer'] for r in records]==answers
    finally:s.close()
    return dict(native=native,chain_answers=answers,chain_seconds=time.perf_counter()-started,seconds=time.perf_counter()-tick)


def run(out):
    out.mkdir(exist_ok=False);started=time.perf_counter()
    p=base.load(PARENT/'protocol.json');authority=bound(p['parent']);trial=base.load(PARENT/'ready-0/report.json')
    records=bound(trial['queries']);diagnosis=base.load(PARENT/'missing-clause-probe.json');cases=diagnosis['cases']
    bindings=dict(legacy=p['support_index'],causal=p['causal_index']);indices={n:bound(e) for n,e in bindings.items()}
    cores=indices['legacy']['cores']+indices['causal']['cores'];prepared=compose(indices,bindings)
    catalogs=[(n,bound(e)) for n,e in zip(OLD_FIELDS,p['prior_decision_catalogs'])]
    sources=dict(base.load(PARENT/'validation.json')['source_fingerprints'])
    for f,h in sources.items():assert base.sha(f)==h,f
    sources.update({f:base.sha(f) for f in FILES})
    protocol=dict(parent=binding(PARENT/'checkpoint.json'),historical_protocol=binding(PARENT/'protocol.json'),historical_trial=binding(PARENT/'ready-0/report.json'),
        diagnosis=binding(PARENT/'missing-clause-probe.json'),source_fingerprints=sources,cases=[r['case'] for r in cases],
        limitations=['One controlled sample per arm on eight previously identified queries. Exact persistent pre-query prefix, cold live caches; neither new coverage nor a stable speedup estimate.',
            'First ready one-missing-clause core in legacy/causal order; clause is nonempty and uses existing target variables. No beneficial choice or optimal restriction is assumed.',
            'The extra negative premise is a native checked subset certificate. The remaining child is solved normally; composed conclusions persist as independently replayable guard-chain sidecars and an optional verified lookup bank.',
            'All native archive nodes keep their existing proof format and pass the frozen full audit. The ordinary root table does not acquire a native proof of each composed conclusion.',
            'Open, preparation, recognition, premise publication, child solve, chain checking, warm-bank setup/lookup, serialization and full cold proof/query/lineage costs are reported separately. No peak RSS or later-stream effect measured.'])
    base.write(out/'protocol.json',protocol);samples=[];prefixes=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        def read_archive(entry,name):
            path=tmp/name;base.restore_archive(entry,path);s=ResidualSolver(path)
            try:return rows(s)
            finally:s.close()
        initial=read_archive(authority['reference_union'],'initial');final=read_archive(trial['archive'],'final')
        assert not trial['setup_ids']
        for case in cases:
            cid=case['case'];old=next(r for r in records if r['case']==cid and not r['visit'])
            tick=time.perf_counter();saved=prefix_tools.prefix(initial,final,records,cid);prefix=tmp/f'prefix-{cid}'
            shutil.copyfile(tmp/'initial',prefix);s=AccountedResidualSolver(prefix)
            try:prefix_tools.install(s,[(k,v) for k,v in saved.items() if k not in initial]);assert rows(s)==saved
            finally:s.close()
            prefix_record=dict(case=cid,nodes=len(saved),row_digest=base.key_sha(base.encode(sorted(saved.items()))),seconds=time.perf_counter()-tick);prefixes.append(prefix_record)
            for mode in ('baseline','chain'):
                dest=out/f'{cid}-{mode}';dest.mkdir();path=tmp/'arm';shutil.copyfile(prefix,path)
                tick=time.perf_counter();s=AccountedResidualSolver(path);open_seconds=time.perf_counter()-tick
                try:
                    tick=time.perf_counter();guard,_,target,trace,_,recognition,selection=prefix_tools.prepare(s,old['source'],p,indices)
                    assert guard==old['guard'] and trace==old['guard_choice']
                    preparation_seconds=time.perf_counter()-tick;preparation_counts=dict(s.counts);guards=[guard]
                    choice=None;near_counts=Counter();premise_counts=Counter();premise_solver_counts={};premise_seconds=selection_seconds=0.;inserted=False
                    if mode=='chain':
                        before=Counter(s.counts);tick=time.perf_counter();choice=propose_missing_clause(s,target,cores,near_counts)
                        selection_seconds=time.perf_counter()-tick;near_solver_counts=dict(s.counts-before)
                        if choice is not None:
                            before=Counter(s.counts);tick=time.perf_counter()
                            with patch.object(s,'_expand',side_effect=AssertionError('Fresh guard premise search')):
                                extra,_,target,inserted=publish_guard(s,target,cores[choice['core']],choice['missing_clause'],premise_counts)
                            guards.append(extra);premise_seconds=time.perf_counter()-tick;premise_solver_counts=dict(s.counts-before)
                    else:near_solver_counts={}
                    tick=time.perf_counter();child=s.solve(target);child_seconds=time.perf_counter()-tick
                    assert child['answer']==old['answer']
                    if mode=='baseline':assert child['metrics']['expanded_nodes']==old['child']['metrics']['expanded_nodes']
                    tick=time.perf_counter();record=make_record(s,old['source'],guards,child);composition_seconds=time.perf_counter()-tick
                    after=rows(s);assert saved.items()<=after.items();delta=[(k,v) for k,v in after.items() if k not in saved]
                    with patch.object(s,'_expand',side_effect=AssertionError('Fresh chain-bank search')),patch.object(s,'_store',side_effect=AssertionError('Chain-bank publication')):
                        tick=time.perf_counter();bank=GuardChainBank(s,[record]);warm_setup_seconds=time.perf_counter()-tick
                        tick=time.perf_counter();warm=bank.lookup(old['source']);warm_lookup_seconds=time.perf_counter()-tick
                    assert warm['answer']==record['answer'] and rows(s)==after
                finally:s.close()
                tick=time.perf_counter();base.write(dest/'delta.json',delta);base.write(dest/'chains.json',[record]);serialization_seconds=time.perf_counter()-tick
                cold=audit_chain(path,[record],prepared,catalogs,indices)
                result=dict(case=cid,mode=mode,choice=choice,answer=record['answer'],guards=len(guards),prefix=prefix_record,
                    delta=binding(dest/'delta.json'),chains=binding(dest/'chains.json'),new_nodes=len(delta),new_payload_units=sum(len(k)+len(v) for k,v in delta),
                    delta_bytes=(dest/'delta.json').stat().st_size,chain_bytes=(dest/'chains.json').stat().st_size,premise_inserted=inserted,
                    open_seconds=open_seconds,preparation_seconds=preparation_seconds,selection_seconds=selection_seconds,premise_seconds=premise_seconds,
                    child_seconds=child_seconds,composition_seconds=composition_seconds,warm_setup_seconds=warm_setup_seconds,warm_lookup_seconds=warm_lookup_seconds,
                    serialization_seconds=serialization_seconds,preparation_counts=preparation_counts,recognition_counts=recognition,selection_counts=selection,
                    near_counts=dict(near_counts),near_solver_counts=near_solver_counts,premise_counts=dict(premise_counts),premise_solver_counts=premise_solver_counts,
                    child_metrics=child['metrics'],bank_counts=dict(bank.counts),cold=cold,row_digest=base.key_sha(base.encode(sorted(after.items()))))
                base.write(dest/'report.json',result);samples.append(binding(dest/'report.json'))
                print(base.encode(dict(case=cid,mode=mode,answer=record['answer'],choice=choice,new_nodes=len(delta),expansions=child['metrics'].get('expanded_nodes',0))),flush=True)
    base.write(out/'report.json',dict(protocol=binding(out/'protocol.json'),samples=samples,prefixes=prefixes,seconds=time.perf_counter()-started))


if __name__=='__main__':run(Path(sys.argv[1]))
