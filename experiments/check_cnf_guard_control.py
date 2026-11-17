#!/usr/bin/env python3
"""Untimed frozen-baseline parity and historical guard-selection regression."""
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_alternative_guard as study
from experiments import compare_cnf_incremental_causal as frozen
from experiments.cnf_alternative_guard import AlternativeGuardSelector
from experiments.cnf_proof_choice import ProofChoiceBank,compose,audit_portfolio
from experiments.cnf_clause_deletion_guard import ExtensionBank,check_guard,clause_set
from experiments.cnf_snapshot_replay import FROZEN_AUDIT
from experiments.validate_cnf_snapshot_replay import semantic
from experiments.validate_cnf_unsat_support import bound
base=study.base


def check(out):
    tick=time.perf_counter();protocol=base.load(out/'protocol.json');catalog=base.load(out/'cases.json');reference=base.load(out/'first-0/report.json')
    with tempfile.TemporaryDirectory() as td:
        temp=Path(td);dest=temp/'baseline'
        with (out/'parity-replay.txt').open('w') as log,redirect_stdout(log):frozen.worker(dest,protocol,catalog,'fixed')
        old=base.load(dest/'report.json');records=bound(old['queries']);new=bound(reference['queries'])
        assert semantic(records)==semantic([{k:v for k,v in r.items() if k!='guard_choice'} for r in new])
        assert old['archive']['database_sha256']==reference['archive']['database_sha256']
        parity=dict(passed=True,frozen_worker=study.binding('experiments/compare_cnf_incremental_causal.py'),database_sha256=old['archive']['database_sha256'],
            semantic_queries_identical=True,expanded_nodes=old['summary']['expanded_nodes'],new_nodes=old['summary']['new_nodes'],
            limitation='Untimed replay recomputes the frozen baseline. Its identical proof artifact is already retained by first-0; this is not a no-search validation pass.')
        historical=Path('experiments/results/cnf-incremental-causal');hp=base.load(historical/'protocol.json');parent=bound(hp['parent'])
        hd=base.load(historical/'fixed-0/report.json');hr=bound(hd['queries'])[121];assert hr['case']==121 and hr['visit']==0 and hr['child']['metrics']['expanded_nodes']==20
        path=temp/'historical';base.restore_archive(parent['reference_union'],path);s=study.AccountedResidualSolver(path);initial=study.rows(s)
        bindings=dict(legacy=hp['support_index'],causal=hp['causal_index']);indices={n:bound(e) for n,e in bindings.items()};prepared=compose(indices,bindings)
        used=[(n,bound(e)) for n,e in zip(study.OLD_FIELDS,hp['prior_decision_catalogs'])];selector=AlternativeGuardSelector(1)
        try:
            bank=ProofChoiceBank(s,indices['legacy'],indices['causal']);extensions=ExtensionBank(bound(hp['bank_catalog'])['bank'])
            with patch.object(s,'_expand',side_effect=AssertionError('Historical fresh search')):
                _,target=check_guard(s,hr['source'],hr['guard']);cnf,_,root=s._canonical(target);assert s._read(root,cnf) is None
                members=clause_set(target,Counter());assert not any(wanted<=members for b in bank.banks for _,wanted in b.cores)
                before=study.rows(s)
                with patch.object(s,'_store',side_effect=AssertionError('Selection publication')):guard,trace=selector.select(s,extensions,hr['source'],hr['guard'],bank)
                assert guard is not None and trace['attempts'][-1]['status']=='ready' and study.rows(s)==before
                fixed,target=check_guard(s,hr['source'],guard);hit=bank.reuse(target);assert hit is not None and hit['choice']=='ready'
                child=s.solve(target);assert child['answer'] is False and child['metrics'].get('expanded_nodes',0)==0
                row=dict(case=121,visit=0,source=hr['source'],guard=guard,guard_choice=trace,witness=None,child=child,answer=False,model=None)
                saved=study.rows(s);assert initial.items()<=saved.items() and len(saved)-len(initial)==1
        finally:s.close()
        dest=out/'historical-control';dest.mkdir();base.write(dest/'queries.json',[row]);archive=base.archive(path,dest)
        cold=audit_portfolio(path,[row],prepared,used,indices);independent=FROZEN_AUDIT(path,[row]);assert independent['query_answers']==[False]
        control=dict(passed=True,original_protocol=study.binding(historical/'protocol.json'),original_queries=hd['queries'],initial_union=parent['reference_union'],
            historical_case=121,historical_in_stream_expansions=20,controlled_expansions=0,new_proof_rows=1,selector_counts=dict(selector.counts),
            queries=study.binding(dest/'queries.json'),archive=archive,cold=cold,independent_cold=independent,
            limitation='Restores the original 19543-key snapshot and validates the selected alternative with no fresh SAT search. The old 20-node count comes from its historical stream, not a new isolated matched runtime. The regression archive is retained separately from the fresh-query union.')
    result=dict(passed=True,checker=study.binding(__file__),current_report=study.binding(out/'report.json'),baseline_parity=parity,historical_control=control,seconds=time.perf_counter()-tick)
    base.write(out/'control-check.json',result);print(base.encode(dict(passed=True,baseline_parity=True,historical_case=121,controlled_expansions=0,new_control_proof_rows=1,seconds=result['seconds'])))


if __name__=='__main__':check(Path(sys.argv[1]))
