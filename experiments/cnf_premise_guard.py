"""Prepared near-core recognition with checked strengthened-premise priority.

Core metadata only suggests clauses. A checked UNSAT T+C alone authorizes its
restriction; otherwise the frozen checked-core/subset path must establish it.
Postings and clause sets are private copies, valid for this fixed bank version.
"""
from collections import Counter,defaultdict
from copy import deepcopy
from experiments.cnf_clause_deletion_guard import clause_set,check_guard,FORMAT
from experiments.cnf_guard_chain import publish_guard
from experiments.cnf_residual_dag import restrict


class PremiseGuardSelector:
    def __init__(self,cores):
        self.counts=Counter();self.cores=deepcopy(cores);self.members=[];self.postings=defaultdict(list)
        for i,core in enumerate(self.cores):
            members=frozenset(clause_set(core['source'],self.counts));self.members.append(members)
            for clause in members:self.postings[clause].append(i)
        self.counts['prepared_cores']=len(self.cores)
        self.counts['prepared_memberships']=sum(map(len,self.members))
        self.counts['prepared_clause_keys']=len(self.postings)
        self.counts['prepared_clause_literals']=sum(map(len,self.postings))

    def candidates(self,source):
        members=clause_set(source,self.counts);variables={abs(l) for c in members for l in c};hits=Counter()
        for clause in members:
            ids=self.postings.get(clause,());self.counts['posting_lookups']+=1;self.counts['posting_visits']+=len(ids)
            hits.update(ids)
        ids=sorted(i for i,n in hits.items() if n==len(self.members[i])-1)
        for i in ids:
            self.counts['near_candidates']+=1;clause=next(iter(self.members[i]-members))
            if not clause or not {abs(l) for l in clause}<=variables:continue
            target=restrict(source,{abs(l):l<0 for l in clause},self.counts)
            if clause_set(target,self.counts)==members:continue
            yield i,list(clause)

    def select(self,solver,source):
        self.counts['selection_calls']+=1
        for i,clause in self.candidates(source):
            stronger=[list(c) for c in source]+[clause];cnf,_,key=solver._canonical(stronger)
            node=solver._read(key,cnf,purpose='near_strengthened');self.counts['premise_lookups']+=1
            if node is not None:
                if node['answer'] is not False:self.counts['positive_premises_skipped']+=1;continue
                guard=dict(format=FORMAT,stronger=stronger,stronger_root=key,removed_clause=clause)
                _,target=check_guard(solver,source,guard,self.counts);self.counts['known_premise_choices']+=1
                return dict(core=i,missing_clause=clause,path='known-premise',inserted=False),guard,target
            core=self.cores[i];small,_,root=solver._canonical(core['source'])
            if root!=core['root']:raise ValueError('Unbound fallback core')
            proof=solver._read(root,small,purpose='near_fallback');self.counts['fallback_core_reads']+=1
            if proof is None:self.counts['pending_fallbacks_skipped']+=1;continue
            if proof['answer'] is not False:raise ValueError('Negative fallback core required')
            guard,_,target,inserted=publish_guard(solver,source,core,clause,self.counts)
            self.counts['derived_premise_choices']+=1
            return dict(core=i,missing_clause=clause,path='checked-core',inserted=inserted),guard,target
        return None,None,source
