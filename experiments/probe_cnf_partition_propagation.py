#!/usr/bin/env python3
"""Price read-only propagation signals for the already tested partition plans."""
from collections import Counter
from pathlib import Path
from unittest.mock import patch
import sys,tempfile,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiments import compare_cnf_clause_partition as study
from experiments.cnf_clause_partition import branch_sources
from experiments.cnf_clause_deletion_guard import check_guard
from experiments.cnf_residual_dag import propagate,restrict
from experiments.cnf_snapshot_replay import SnapshotResidualSolver
from experiments.validate_cnf_unsat_support import bound
base=study.base


def probe(out):
    start=time.perf_counter();report=base.load(out/'report.json');p=bound(report['protocol']);hp=bound(p['historical_protocol']);trial=bound(p['historical_trial']);records=bound(trial['queries']);results=[];totals=Counter()
    with tempfile.TemporaryDirectory() as td:
        path=Path(td)/'prior-trial';base.restore_archive(trial['archive'],path);s=SnapshotResidualSolver(path)
        try:
            for e in report['samples']:
                data=bound(e);plan=data['plan'];old=next(r for r in records if r['case']==plan['case']);target=old['chain']['source']
                for guard in old['chain']['guards']:_,target=check_guard(s,target,guard)
                counts=Counter();tick=time.perf_counter();children=[(target,{},target)] if plan['core'] is None else branch_sources(target,plan['missing'],counts)[1];branches=[];delta=dict(bound(data['delta']))
                with patch.object(s,'_expand',side_effect=AssertionError('Propagation probe search')),patch.object(s,'_store',side_effect=AssertionError('Probe publication')):
                    for i,(_,_,child) in enumerate(children):
                        cnf,_,key=s._canonical(child);local=Counter();fixed,trace,conflict=propagate(cnf,local);residual=restrict(cnf,fixed,local) if conflict is None else ()
                        proof=base.load_json(delta[key])['proof'];assert proof['kind']=='units'
                        assert proof['trace']==trace and proof.get('conflict')==conflict
                        branches.append(dict(index=i,root=key,terminal_conflict=conflict is not None,trace_steps=len(trace),residual_variables=len({abs(l) for c in residual for l in c}),residual_clauses=len(residual),residual_literals=sum(map(len,residual)),counts=dict(local),observed_expansions=data['branch_reports'][i]['metrics'].get('expanded_nodes',0)))
                        counts.update(local)
                seconds=time.perf_counter()-tick;totals.update(counts)
                results.append(dict(plan=plan,branches=branches,terminal_conflicts=sum(b['terminal_conflict'] for b in branches),nonterminal_branches=sum(not b['terminal_conflict'] for b in branches),nonterminal_literals=sum(b['residual_literals'] for b in branches),counts=dict(counts),seconds=seconds))
        finally:s.close()
    result=dict(report=study.binding(out/'report.json'),probe=study.binding(__file__),cases=results,counts=dict(totals),seconds=time.perf_counter()-start,
        limitations=['Diagnostic only on already tested historical plans, not a deployed or fresh-evaluated selector. Frozen propagation runs without search or publication; produced traces/conflicts match the independently checked native child certificates.',
            'Prior branch solving is used only to compare observed outcomes. Recognition input is the target and ordered missing clauses, never the child proof. Full source proof opening/checking and diagnostic I/O remain in total time; per-plan time includes construction, normalization, propagation and comparison overhead.',
            'A terminal unit conflict predicts a cheap child proof, not the cost of choosing a plan. A nonterminal residual size is not a proof-complexity bound. If two plans tie on such features, the cheaper solve remains unknown.'])
    base.write(out/'propagation-probe.json',result)
    for r in results:print(base.encode({k:r[k] for k in ('plan','terminal_conflicts','nonterminal_branches','nonterminal_literals','seconds')}))


if __name__=='__main__':probe(Path(sys.argv[1]))
