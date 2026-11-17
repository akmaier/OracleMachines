"""Try bounded alternative deletion guards after the first residual misses.

Selection only reads checked proofs. It neither solves nor materializes a pending
support. The caller still checks the chosen guard, publishes any subset proof,
and checks/lifts the resulting child through the ordinary query path.
"""
from collections import Counter
from experiments.cnf_clause_deletion_guard import check_guard,clause_set


class AlternativeGuardSelector:
    def __init__(self,max_candidates=1):
        if type(max_candidates) is not int or max_candidates<0:raise ValueError('Nonnegative candidate budget required')
        self.max_candidates=max_candidates;self.counts=Counter()

    def select(self,solver,extensions,source,original,portfolio):
        check_guard(solver,source,original,self.counts)
        self.counts['selection_calls']+=1
        trace=dict(original_guard=original,attempts=[],selected=False)
        if self.max_candidates==0:return None,trace
        for guard in extensions.candidates(source,self.counts):
            if guard==original:continue
            self.counts['alternative_candidates']+=1;entry=dict(guard=guard,status='unavailable_guard');trace['attempts'].append(entry)
            normalized,_,key=solver._canonical(guard['stronger'])
            if key!=guard['stronger_root']:raise ValueError('Unbound alternative guard')
            node=solver._read(key,normalized,purpose='alternative_guard')
            if node is not None and node['answer'] is False:
                _,target=check_guard(solver,source,guard,self.counts);cnf,_,key=solver._canonical(target)
                node=solver._read(key,cnf,purpose='alternative_target')
                if node is not None:
                    entry.update(status='known',answer=node['answer']);trace['selected']=True;self.counts['known_choices']+=1
                    return guard,trace
                entry['status']='miss';members=clause_set(target,self.counts)
                for bi,bank in enumerate(portfolio.banks):
                    for ci,(core,wanted) in enumerate(bank.cores):
                        self.counts['support_candidates']+=1;self.counts['support_containment_clauses']+=len(wanted)
                        if not wanted<=members:continue
                        small,_,root=solver._canonical(core['source'])
                        if root!=core['root']:raise ValueError('Unbound alternative support')
                        proof=solver._read(root,small,purpose='alternative_support');self.counts['support_reads']+=1
                        if proof is None:self.counts['pending_hints_skipped']+=1;continue
                        if proof['answer'] is not False:raise ValueError('Negative alternative support required')
                        entry.update(status='ready',core=portfolio.offsets[bi]+ci);trace['selected']=True;self.counts['ready_choices']+=1
                        return guard,trace
            if len(trace['attempts'])>=self.max_candidates:break
        self.counts['selection_misses']+=1
        return None,trace
