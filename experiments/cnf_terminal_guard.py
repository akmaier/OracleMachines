"""Optionally derive a pending alternative from a checked terminal unit conflict.

Keep the ready-only selector's candidate budget and ready-first ordering. Only
after it misses, inspect pending matches under those same checked alternatives.
A terminal origin allows at most one core publication; the caller retains the
ordinary guard, subset, child-check and model-lifting path. This is a row bound,
not a constant-time or optimal-cost guarantee. Live sessions are append-only.
"""
from experiments.cnf_alternative_guard import AlternativeGuardSelector
from experiments.cnf_clause_deletion_guard import check_guard,clause_set


class TerminalGuardSelector(AlternativeGuardSelector):
    def select(self,solver,extensions,source,original,portfolio):
        chosen,trace=super().select(solver,extensions,source,original,portfolio)
        if chosen is not None:return chosen,trace
        for attempt in trace['attempts']:
            if attempt['status']!='miss':continue
            guard=attempt['guard'];_,target=check_guard(solver,source,guard,self.counts)
            members=clause_set(target,self.counts);attempt['terminal_checks']=[]
            for bi,bank in enumerate(portfolio.banks):
                for ci,(core,wanted) in enumerate(bank.cores):
                    self.counts['terminal_support_candidates']+=1
                    self.counts['terminal_containment_clauses']+=len(wanted)
                    if not wanted<=members:continue
                    small,_,root=solver._canonical(core['source'])
                    if root!=core['root']:raise ValueError('Unbound terminal support')
                    if solver._read(root,small,purpose='terminal_pending') is not None:
                        raise ValueError('Ready-only selection missed an available support')
                    origin=solver._read(core['origin'],purpose='terminal_origin')
                    self.counts['terminal_origin_reads']+=1
                    if origin is not None and origin['answer'] is not False:
                        raise ValueError('Negative terminal origin required')
                    terminal=(origin is not None and origin['proof']['kind']=='units'
                              and origin['proof'].get('conflict') is not None)
                    index=portfolio.offsets[bi]+ci
                    attempt['terminal_checks'].append(dict(core=index,terminal=terminal))
                    if not terminal:continue
                    before=solver.counts['inserted_nodes'];derived=bank.extractor.extract(core['origin'])
                    published=solver.counts['inserted_nodes']-before
                    if derived['root']!=root or not 0<=published<=1:
                        raise ValueError('Terminal derivation changed root or publication bound')
                    node=solver._read(root,small,purpose='terminal_derived')
                    if node is None or node['answer'] is not False:raise ValueError('Checked terminal core required')
                    self.counts['terminal_choices']+=1;self.counts['terminal_materialization_nodes']+=published
                    self.counts['selection_misses']-=1
                    attempt.update(status='terminal',core=index);trace['selected']=True
                    return guard,trace
        return None,trace
